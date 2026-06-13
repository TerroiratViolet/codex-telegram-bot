from __future__ import annotations

import logging

from schedule_bot.config import Settings
from schedule_bot.handlers import build_application
from schedule_bot.health import start_health_server


def run() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=settings.log_level,
    )

    start_health_server(settings.port)
    logging.getLogger(__name__).info("Health endpoint listening on port %s", settings.port)

    application = build_application(settings.telegram_bot_token)
    application.run_polling(drop_pending_updates=True)

