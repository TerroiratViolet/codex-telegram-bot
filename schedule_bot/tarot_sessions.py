from __future__ import annotations

import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from schedule_bot.tarot_cards import TarotCard


class TarotStage(StrEnum):
    AWAITING_CONSENT = "awaiting_consent"
    AWAITING_QUESTION_A = "awaiting_question_a"
    AWAITING_ANSWER_B = "awaiting_answer_b"
    AWAITING_ANSWER_C = "awaiting_answer_c"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    DECLINED = "declined"


@dataclass(frozen=True)
class TarotSession:
    session_id: str
    group_chat_id: int
    admin_user_id: int
    target_user_id: int
    target_display_name: str
    target_username: str | None
    stage: TarotStage
    created_at: datetime
    question_a: str | None = None
    answer_b: str | None = None
    answer_c: str | None = None
    card: TarotCard | None = None
    expected_reply_to_message_id: int | None = None

    def with_updates(self, **changes: object) -> TarotSession:
        return replace(self, **changes)


class TarotSessionStore:
    def __init__(self, *, ttl: timedelta = timedelta(hours=2)) -> None:
        self._sessions: dict[str, TarotSession] = {}
        self._ttl = ttl

    def create(
        self,
        *,
        group_chat_id: int,
        admin_user_id: int,
        target_user_id: int,
        target_display_name: str,
        target_username: str | None,
    ) -> TarotSession:
        self.remove_expired()
        existing = self.get_active_for_user(group_chat_id, target_user_id)
        if existing is not None:
            raise ValueError("This user already has an active tarot session in this chat.")

        session = TarotSession(
            session_id=secrets.token_urlsafe(6),
            group_chat_id=group_chat_id,
            admin_user_id=admin_user_id,
            target_user_id=target_user_id,
            target_display_name=target_display_name,
            target_username=target_username,
            stage=TarotStage.AWAITING_CONSENT,
            created_at=datetime.now(UTC),
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> TarotSession | None:
        self.remove_expired()
        return self._sessions.get(session_id)

    def save(self, session: TarotSession) -> TarotSession:
        self._sessions[session.session_id] = session
        return session

    def get_active_for_user(self, chat_id: int, user_id: int) -> TarotSession | None:
        self.remove_expired()
        terminal = {TarotStage.COMPLETE, TarotStage.DECLINED}
        return next(
            (
                session
                for session in self._sessions.values()
                if session.group_chat_id == chat_id
                and session.target_user_id == user_id
                and session.stage not in terminal
            ),
            None,
        )

    def remove_expired(self, *, now: datetime | None = None) -> None:
        current = now or datetime.now(UTC)
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if current - session.created_at > self._ttl
        ]
        for session_id in expired_ids:
            del self._sessions[session_id]
