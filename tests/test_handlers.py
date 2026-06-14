import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from schedule_bot.config import Settings
from schedule_bot.handlers import (
    TAROT_INTROS,
    _is_expected_reply,
    build_application,
    tarot_consent,
    tarot_start,
)
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
