from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
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

        raw_port = os.getenv("PORT", "8080")
        try:
            port = int(raw_port)
        except ValueError as error:
            raise ValueError("PORT must be a whole number, for example 8080.") from error

        if not 0 <= port <= 65535:
            raise ValueError("PORT must be between 0 and 65535.")

        return cls(
            telegram_bot_token=token,
            port=port,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
