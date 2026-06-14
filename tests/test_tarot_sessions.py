from datetime import UTC, datetime, timedelta

import pytest

from schedule_bot.tarot_sessions import TarotSessionStore, TarotStage


def _create_session(store: TarotSessionStore):
    return store.create(
        group_chat_id=-100,
        admin_user_id=1,
        target_user_id=2,
        target_display_name="参与者",
        target_username="guest",
    )


def test_session_starts_at_explicit_consent() -> None:
    session = _create_session(TarotSessionStore())

    assert session.stage == TarotStage.AWAITING_CONSENT
    assert session.question_a is None
    assert session.answer_b is None
    assert session.answer_c is None
    assert session.card is None
    assert session.expected_reply_to_message_id is None


def test_only_one_active_session_per_user_and_group() -> None:
    store = TarotSessionStore()
    _create_session(store)

    with pytest.raises(ValueError, match="active tarot session"):
        _create_session(store)


def test_terminal_session_allows_a_new_invitation() -> None:
    store = TarotSessionStore()
    session = _create_session(store)
    store.save(session.with_updates(stage=TarotStage.DECLINED))

    new_session = _create_session(store)

    assert new_session.session_id != session.session_id


def test_expired_session_is_removed() -> None:
    store = TarotSessionStore(ttl=timedelta(minutes=10))
    session = _create_session(store)

    store.remove_expired(now=datetime.now(UTC) + timedelta(minutes=11))

    assert store.get(session.session_id) is None
