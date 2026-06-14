from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_admin_user_ids: frozenset[int]
    openai_api_key: str
    openai_model: str
    port: int
    log_level: str

    @classmethod
    def from_env(cls, *, load_env_file: bool = True) -> Settings:
        if load_env_file:
            load_dotenv()

        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token or token == "replace-with-token-from-botfather":
            raise ValueError(
                "Missing TELEGRAM_BOT_TOKEN. Copy .env.example to .env "
                "and add your BotFather token."
            )

        raw_admin_ids = os.getenv("TELEGRAM_ADMIN_USER_IDS", "")
        try:
            admin_ids = frozenset(
                int(value.strip()) for value in raw_admin_ids.split(",") if value.strip()
            )
        except ValueError as error:
            raise ValueError(
                "TELEGRAM_ADMIN_USER_IDS must contain numeric Telegram user IDs "
                "separated by commas."
            ) from error

        raw_port = os.getenv("PORT", "8080")
        try:
            port = int(raw_port)
        except ValueError as error:
            raise ValueError("PORT must be a whole number, for example 8080.") from error

        if not 0 <= port <= 65535:
            raise ValueError("PORT must be between 0 and 65535.")

        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if openai_api_key == "replace-with-openai-api-key":
            openai_api_key = ""

        return cls(
            telegram_bot_token=token,
            telegram_admin_user_ids=admin_ids,
            openai_api_key=openai_api_key,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.2").strip() or "gpt-5.2",
            port=port,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
