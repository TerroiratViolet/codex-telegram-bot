from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from schedule_bot.responses import reply_for_text

LOGGER = logging.getLogger(__name__)


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    message = update.effective_message
    if message is None:
        return

    first_name = update.effective_user.first_name if update.effective_user else "朋友"
    await message.reply_text(reply_for_text(message.text or "", first_name=first_name))


async def log_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.error("Unhandled update error. update=%r", update, exc_info=context.error)


def build_application(token: str) -> Application:
    application = Application.builder().token(token).build()
    for command in ("start", "help", "ping"):
        application.add_handler(CommandHandler(command, reply))
    application.add_handler(MessageHandler(filters.COMMAND, reply))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    application.add_error_handler(log_error)
    return application

