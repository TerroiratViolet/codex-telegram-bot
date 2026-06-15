import asyncio
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telegram.error import TelegramError

from schedule_bot.config import Settings
from schedule_bot.handlers import (
    TAROT_CONSENT_IMAGES,
    TAROT_INTROS,
    _is_expected_reply,
    build_application,
    llmcheck,
    tarot_consent,
    tarot_start,
    tarot_text_router,
)
from schedule_bot.tarot_cards import TAROT_DECK
from schedule_bot.tarot_sessions import TarotSession, TarotSessionStore, TarotStage


def _settings(*, with_gemini: bool = False, with_openai: bool = False) -> Settings:
    return Settings(
        telegram_bot_token="123456:TEST_TOKEN",
        telegram_admin_user_ids=frozenset({42}),
        llm_provider="openai" if with_openai else "gemini",
        gemini_api_key="test-gemini-key" if with_gemini else "",
        gemini_model="gemini-test-model",
        gemini_fallback_model="",
        openai_api_key="test-key" if with_openai else "",
        openai_model="test-model",
        openai_fallback_model="fallback-model",
        port=8080,
        log_level="INFO",
    )


def test_application_registers_tarot_state_and_admin_ids() -> None:
    application = build_application(_settings())

    assert isinstance(application.bot_data["tarot_store"], TarotSessionStore)
    assert application.bot_data["tarot_admin_ids"] == frozenset({42})
    assert "tarot_analyzer" not in application.bot_data


def test_tarot_intros_include_requested_tone() -> None:
    combined = "\n".join(TAROT_INTROS)

    assert "Terroir" in combined
    assert "紫罗兰酒馆" in combined
    assert "未知" in combined
    assert "光" in combined
    assert "阴影" in combined
    assert "原型" in combined
    assert all("集体潜意识" in introduction for introduction in TAROT_INTROS)


def test_tarot_answer_must_reply_to_the_exact_prompt() -> None:
    session = TarotSession(
        session_id="session",
        group_chat_id=-100,
        admin_user_id=1,
        target_user_id=2,
        target_display_name="参与者",
        target_username=None,
        stage=TarotStage.AWAITING_QUESTION_A,
        created_at=datetime.now(UTC),
        expected_reply_to_message_id=55,
    )
    correct_update = SimpleNamespace(
        effective_message=SimpleNamespace(
            reply_to_message=SimpleNamespace(message_id=55)
        )
    )
    wrong_update = SimpleNamespace(
        effective_message=SimpleNamespace(
            reply_to_message=SimpleNamespace(message_id=56)
        )
    )

    assert _is_expected_reply(correct_update, session)
    assert not _is_expected_reply(wrong_update, session)


def test_plain_text_without_tarot_session_is_ignored() -> None:
    message = SimpleNamespace(
        text="管理员在群里的普通聊天",
        reply_text=AsyncMock(),
    )
    update = SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=42),
        effective_chat=SimpleNamespace(id=-100),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={"tarot_store": TarotSessionStore(), "tarot_analyzer": None}
        )
    )

    asyncio.run(tarot_text_router(update, context))

    message.reply_text.assert_not_awaited()


def test_non_admin_cannot_start_tarot() -> None:
    message = SimpleNamespace(reply_text=AsyncMock())
    update = SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=99),
        effective_chat=SimpleNamespace(id=-100, type="group"),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(bot_data={"tarot_admin_ids": frozenset({42})})
    )

    asyncio.run(tarot_start(update, context))

    message.reply_text.assert_awaited_once_with("这项仪式只对 Terroir 管理员开放。")


def test_llmcheck_reports_configured_analyzer_status() -> None:
    class FakeAnalyzer:
        provider_name = "Gemini"

        def check_connection(self):
            return SimpleNamespace(
                ok=True,
                message="Gemini 连接正常，模型 gemini-test-model 可用。",
            )

    message = SimpleNamespace(reply_text=AsyncMock())
    update = SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=42),
        effective_chat=SimpleNamespace(id=42, type="private"),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={
                "tarot_store": TarotSessionStore(),
                "tarot_admin_ids": frozenset({42}),
                "tarot_analyzer": FakeAnalyzer(),
            }
        )
    )

    asyncio.run(llmcheck(update, context))

    assert message.reply_text.await_count == 2
    assert "正在检查 Gemini" in message.reply_text.await_args_list[0].args[0]
    assert "占卜助手检查通过" in message.reply_text.await_args_list[1].args[0]


def test_llmcheck_requires_admin_and_openai_configuration() -> None:
    non_admin_message = SimpleNamespace(reply_text=AsyncMock())
    non_admin_update = SimpleNamespace(
        effective_message=non_admin_message,
        effective_user=SimpleNamespace(id=99),
        effective_chat=SimpleNamespace(id=-100, type="group"),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={
                "tarot_store": TarotSessionStore(),
                "tarot_admin_ids": frozenset({42}),
            }
        )
    )

    asyncio.run(llmcheck(non_admin_update, context))

    non_admin_message.reply_text.assert_awaited_once_with(
        "这项检查只对 Terroir 管理员开放。"
    )

    admin_message = SimpleNamespace(reply_text=AsyncMock())
    admin_update = SimpleNamespace(
        effective_message=admin_message,
        effective_user=SimpleNamespace(id=42),
        effective_chat=SimpleNamespace(id=42, type="private"),
    )

    asyncio.run(llmcheck(admin_update, context))

    admin_message.reply_text.assert_awaited_once_with(
        "占卜助手尚未配置：推荐在 Railway Variables 中设置 GEMINI_API_KEY，"
        "并设置 LLM_PROVIDER=gemini。"
    )


def test_llmcheck_sends_detailed_results_privately_from_group() -> None:
    class FakeAnalyzer:
        provider_name = "Gemini"

        def check_connection(self):
            return SimpleNamespace(
                ok=False,
                message="Gemini API Key 无效，或当前 Google AI 项目没有权限使用配置的模型。",
            )

    group_message = SimpleNamespace(reply_text=AsyncMock())
    admin_dm = AsyncMock()
    update = SimpleNamespace(
        effective_message=group_message,
        effective_user=SimpleNamespace(id=42),
        effective_chat=SimpleNamespace(id=-100, type="group"),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={
                "tarot_store": TarotSessionStore(),
                "tarot_admin_ids": frozenset({42}),
                "tarot_analyzer": FakeAnalyzer(),
            }
        ),
        bot=SimpleNamespace(send_message=admin_dm),
    )

    asyncio.run(llmcheck(update, context))

    group_message.reply_text.assert_awaited_once_with(
        "占卜助手检查结果只会私聊给管理员。"
    )
    assert admin_dm.await_count == 2
    assert all(call.kwargs["chat_id"] == 42 for call in admin_dm.await_args_list)
    assert "正在检查 Gemini" in admin_dm.await_args_list[0].kwargs["text"]
    assert "占卜助手检查失败" in admin_dm.await_args_list[1].kwargs["text"]
    assert "没有权限使用配置的模型" in admin_dm.await_args_list[1].kwargs["text"]


def test_tarot_start_sends_separate_admin_and_user_interfaces() -> None:
    store = TarotSessionStore()
    message = SimpleNamespace(
        reply_to_message=SimpleNamespace(
            from_user=SimpleNamespace(
                id=7,
                full_name="参与者",
                username="guest",
                is_bot=False,
            )
        ),
        reply_text=AsyncMock(),
        reply_photo=AsyncMock(return_value=SimpleNamespace(message_id=12)),
    )
    update = SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=42),
        effective_chat=SimpleNamespace(id=-100, type="group"),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={
                "tarot_store": store,
                "tarot_admin_ids": frozenset({42}),
                "tarot_analyzer": SimpleNamespace(provider_name="Gemini"),
            }
        ),
        bot=SimpleNamespace(send_photo=AsyncMock()),
    )

    asyncio.run(tarot_start(update, context))

    context.bot.send_photo.assert_awaited_once()
    admin_kwargs = context.bot.send_photo.await_args.kwargs
    assert admin_kwargs["chat_id"] == 42
    assert "Terroir 管理界面" in admin_kwargs["caption"]
    assert "占卜助手：Gemini" in admin_kwargs["caption"]
    assert "分析只会送到这里" in admin_kwargs["caption"]

    message.reply_photo.assert_awaited_once()
    user_kwargs = message.reply_photo.await_args.kwargs
    assert Path(user_kwargs["photo"].name) in TAROT_CONSENT_IMAGES
    assert "@guest" in user_kwargs["caption"]
    assert "牌面是镜子，不是答案" in user_kwargs["caption"]
    assert "你的描述会比标准牌义更重要" in user_kwargs["caption"]
    assert "我愿意开始" in [
        button.text
        for row in user_kwargs["reply_markup"].inline_keyboard
        for button in row
    ]
    assert "暂不参加" in [
        button.text
        for row in user_kwargs["reply_markup"].inline_keyboard
        for button in row
    ]
    assert "仅私聊发送给 Terroir" in user_kwargs["caption"]
    assert store.get_active_for_user(-100, 7) is not None


def test_tarot_start_does_not_invite_user_if_admin_private_chat_fails() -> None:
    store = TarotSessionStore()
    message = SimpleNamespace(
        reply_to_message=SimpleNamespace(
            from_user=SimpleNamespace(
                id=7,
                full_name="参与者",
                username=None,
                is_bot=False,
            )
        ),
        reply_text=AsyncMock(),
        reply_photo=AsyncMock(),
    )
    update = SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=42),
        effective_chat=SimpleNamespace(id=-100, type="group"),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={
                "tarot_store": store,
                "tarot_admin_ids": frozenset({42}),
            }
        ),
        bot=SimpleNamespace(
            send_photo=AsyncMock(side_effect=TelegramError("private chat not found"))
        ),
    )

    asyncio.run(tarot_start(update, context))

    message.reply_photo.assert_not_awaited()
    message.reply_text.assert_awaited_once()
    assert "无法私聊管理员" in message.reply_text.await_args.args[0]
    assert store.get_active_for_user(-100, 7) is None


def test_other_user_cannot_accept_someone_elses_invitation() -> None:
    store = TarotSessionStore()
    session = store.create(
        group_chat_id=-100,
        admin_user_id=42,
        target_user_id=7,
        target_display_name="参与者",
        target_username=None,
    )
    query = SimpleNamespace(
        data=f"tarot:yes:{session.session_id}",
        answer=AsyncMock(),
    )
    update = SimpleNamespace(
        callback_query=query,
        effective_user=SimpleNamespace(id=8),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={"tarot_store": store, "tarot_analyzer": None}
        )
    )

    asyncio.run(tarot_consent(update, context))

    query.answer.assert_awaited_once_with(
        "只有被邀请的用户可以选择。",
        show_alert=True,
    )
    assert store.get(session.session_id).stage == TarotStage.AWAITING_CONSENT


def test_tarot_consent_prompts_reflective_situation_question() -> None:
    store = TarotSessionStore()
    session = store.create(
        group_chat_id=-100,
        admin_user_id=42,
        target_user_id=7,
        target_display_name="参与者",
        target_username="guest",
    )
    query = SimpleNamespace(
        data=f"tarot:yes:{session.session_id}",
        answer=AsyncMock(),
        edit_message_reply_markup=AsyncMock(),
        message=SimpleNamespace(
            reply_text=AsyncMock(return_value=SimpleNamespace(message_id=88))
        ),
    )
    update = SimpleNamespace(
        callback_query=query,
        effective_user=SimpleNamespace(id=7),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={"tarot_store": store, "tarot_analyzer": None}
        )
    )

    asyncio.run(tarot_consent(update, context))

    query.answer.assert_awaited_once_with("占卜练习开始。")
    prompt = query.message.reply_text.await_args.args[0]
    assert "想通过这次占卜理解的处境" in prompt
    assert "最困惑、最在意、最想看清" in prompt
    assert "会不会" not in prompt
    saved = store.get(session.session_id)
    assert saved is not None
    assert saved.stage == TarotStage.AWAITING_QUESTION_A
    assert saved.expected_reply_to_message_id == 88


def test_card_upload_failure_ends_session(
    monkeypatch,
) -> None:
    store = TarotSessionStore()
    session = store.create(
        group_chat_id=-100,
        admin_user_id=42,
        target_user_id=7,
        target_display_name="参与者",
        target_username=None,
    )
    store.save(
        session.with_updates(
            stage=TarotStage.AWAITING_QUESTION_A,
            expected_reply_to_message_id=55,
        )
    )
    message = SimpleNamespace(
        message_id=56,
        text="我该不该离开现在的工作？",
        reply_to_message=SimpleNamespace(message_id=55),
        reply_photo=AsyncMock(side_effect=TelegramError("upload failed")),
        reply_text=AsyncMock(),
    )
    update = SimpleNamespace(
        effective_message=message,
        effective_user=SimpleNamespace(id=7),
        effective_chat=SimpleNamespace(id=-100),
    )
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={"tarot_store": store, "tarot_analyzer": None}
        )
    )
    monkeypatch.setattr("schedule_bot.handlers.draw_tarot_card", lambda: TAROT_DECK[0])

    asyncio.run(tarot_text_router(update, context))

    ended = store.get(session.session_id)
    assert ended is not None
    assert ended.stage == TarotStage.COMPLETE
    message.reply_text.assert_awaited_once_with(
        "牌面图片暂时无法发送，请让 Terroir 稍后重新发起这次练习。"
    )


def test_complete_tarot_analysis_is_sent_only_to_admin(
    monkeypatch,
) -> None:
    class FakeAnalyzer:
        received_session = None

        def analyze(self, session):
            self.received_session = session
            return "私密参考分析：投射假设与问题 A 的具体回答。"

    def user_update(
        *,
        text: str,
        reply_to_message_id: int,
        prompt_message_id: int,
    ):
        message = SimpleNamespace(
            text=text,
            reply_to_message=SimpleNamespace(message_id=reply_to_message_id),
            reply_photo=AsyncMock(
                return_value=SimpleNamespace(message_id=prompt_message_id)
            ),
            reply_text=AsyncMock(
                return_value=SimpleNamespace(message_id=prompt_message_id)
            ),
        )
        return (
            SimpleNamespace(
                effective_message=message,
                effective_user=SimpleNamespace(id=7),
                effective_chat=SimpleNamespace(id=-100),
            ),
            message,
        )

    store = TarotSessionStore()
    session = store.create(
        group_chat_id=-100,
        admin_user_id=42,
        target_user_id=7,
        target_display_name="参与者",
        target_username="guest",
    )
    store.save(
        session.with_updates(
            stage=TarotStage.AWAITING_QUESTION_A,
            expected_reply_to_message_id=10,
        )
    )
    analyzer = FakeAnalyzer()
    admin_send = AsyncMock()
    context = SimpleNamespace(
        application=SimpleNamespace(
            bot_data={"tarot_store": store, "tarot_analyzer": analyzer}
        ),
        bot=SimpleNamespace(send_message=admin_send),
    )
    monkeypatch.setattr("schedule_bot.handlers.draw_tarot_card", lambda: TAROT_DECK[0])

    question_update, question_message = user_update(
        text="问题 A：我是否应该离开现在的工作？",
        reply_to_message_id=10,
        prompt_message_id=20,
    )
    asyncio.run(tarot_text_router(question_update, context))

    answer_b_update, answer_b_message = user_update(
        text="问题 B：我先看到悬崖、白玫瑰和远山。",
        reply_to_message_id=20,
        prompt_message_id=30,
    )
    asyncio.run(tarot_text_router(answer_b_update, context))

    answer_c_update, answer_c_message = user_update(
        text="问题 C：他想自由前进，也担心跌落。",
        reply_to_message_id=30,
        prompt_message_id=40,
    )
    asyncio.run(tarot_text_router(answer_c_update, context))

    completed = store.get(session.session_id)
    assert completed is not None
    assert completed.stage == TarotStage.COMPLETE
    assert completed.question_a == "问题 A：我是否应该离开现在的工作？"
    assert completed.answer_b == "问题 B：我先看到悬崖、白玫瑰和远山。"
    assert completed.answer_c == "问题 C：他想自由前进，也担心跌落。"
    assert completed.card == TAROT_DECK[0]
    assert analyzer.received_session == completed.with_updates(
        stage=TarotStage.ANALYZING
    )

    question_message.reply_photo.assert_awaited_once()
    answer_b_message.reply_text.assert_awaited_once()
    answer_c_message.reply_text.assert_awaited_once()
    assert "私密参考分析" not in answer_c_message.reply_text.await_args.args[0]
    assert "联想和故事" in answer_c_message.reply_text.await_args.args[0]
    assert "最重要的材料" in answer_c_message.reply_text.await_args.args[0]

    assert admin_send.await_count == 2
    assert all(call.kwargs["chat_id"] == 42 for call in admin_send.await_args_list)
    assert "私密参考分析" in admin_send.await_args_list[-1].kwargs["text"]
