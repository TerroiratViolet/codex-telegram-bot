import logging

from schedule_bot.app import configure_logging


def test_http_client_loggers_never_emit_info_requests() -> None:
    configure_logging("INFO")

    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("httpcore").level == logging.WARNING
    assert logging.getLogger("openai").level == logging.WARNING
