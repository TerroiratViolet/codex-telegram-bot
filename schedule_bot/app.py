from __future__ import annotations

import logging

from schedule_bot.config import Settings
from schedule_bot.handlers import build_application
from schedule_bot.health import start_health_server


def configure_logging(log_level: str) -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=log_level,
    )

    # HTTP client INFO messages include the Telegram Bot API URL, which contains the token.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


def run() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    start_health_server(settings.port)
    logging.getLogger(__name__).info("Health endpoint listening on port %s", settings.port)

    application = build_application(settings)
    application.run_polling(drop_pending_updates=True)
