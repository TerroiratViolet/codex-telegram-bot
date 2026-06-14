import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telegram.error import TelegramError

from schedule_bot.config import Settings
from schedule_bot.handlers import (
    TAROT_INTROS,
    _is_expected_reply,
    build_application,
    tarot_consent,
    tarot_start,
    tarot_text_router,
)
from schedule_bot.tarot_cards import MAJOR_ARCANA
from schedule_bot.tarot_sessions import TarotSession, TarotSessionStore, TarotStage


def _settings(*, with_openai: bool = False) -> Settings:
    return Settings(
        telegram_bot_token="123456:TEST_TOKEN",
        telegram_admin_user_ids=frozenset({42}),
        openai_api_key="test-key" if with_openai else "",
        openai_model="test-model",
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
    monkeypatch.setattr(
        "schedule_bot.handlers.draw_major_arcana",
        lambda: MAJOR_ARCANA[0],
    )

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
    monkeypatch.setattr(
        "schedule_bot.handlers.draw_major_arcana",
        lambda: MAJOR_ARCANA[0],
    )

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
    assert completed.card == MAJOR_ARCANA[0]
    assert analyzer.received_session == completed.with_updates(
        stage=TarotStage.ANALYZING
    )

    question_message.reply_photo.assert_awaited_once()
    answer_b_message.reply_text.assert_awaited_once()
    answer_c_message.reply_text.assert_awaited_once()
    assert "私密参考分析" not in answer_c_message.reply_text.await_args.args[0]

    assert admin_send.await_count == 2
    assert all(call.kwargs["chat_id"] == 42 for call in admin_send.await_args_list)
    assert "私密参考分析" in admin_send.await_args_list[-1].kwargs["text"]
