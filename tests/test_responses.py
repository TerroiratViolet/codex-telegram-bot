from schedule_bot.responses import ABOUT_TEXT, HELP_TEXT, reply_for_text


def test_start_uses_first_name() -> None:
    reply = reply_for_text("/start", first_name="Jay")
    assert "Jay" in reply
    assert "成功运行" in reply


def test_help_lists_core_commands() -> None:
    assert reply_for_text("/help") == HELP_TEXT
    assert "/start" in HELP_TEXT
    assert "/ping" in HELP_TEXT
    assert "/about" in HELP_TEXT
    assert "/whoami" in HELP_TEXT
    assert "/llmcheck" in HELP_TEXT
    assert "/tarot" in HELP_TEXT


def test_about_describes_bot() -> None:
    assert reply_for_text("/about") == ABOUT_TEXT
    assert "TerroirTester" in ABOUT_TEXT
    assert "Codex 完整开发流程" in ABOUT_TEXT


def test_ping_reports_online() -> None:
    assert reply_for_text("/ping") == "pong：Bot 正常在线。"


def test_command_with_bot_username_is_supported() -> None:
    assert reply_for_text("/ping@my_test_bot") == "pong：Bot 正常在线。"


def test_plain_text_is_echoed() -> None:
    assert reply_for_text("  今天开会  ") == "你说：今天开会"


def test_unknown_command_has_safe_help() -> None:
    assert "/help" in reply_for_text("/missing")
