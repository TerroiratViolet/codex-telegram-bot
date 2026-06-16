from schedule_bot.responses import ABOUT_TEXT, reply_for_text


def test_start_uses_first_name() -> None:
    reply = reply_for_text("/start", first_name="Jay")
    assert reply is not None
    assert "Jay" in reply
    assert "成功运行" in reply
    assert "/ping" in reply
    assert "/about" in reply
    assert "/whoami" in reply
    assert "/llmcheck" in reply
    assert "/tarot" in reply
    assert "/help" not in reply


def test_help_is_ignored_to_avoid_common_command_clashes() -> None:
    assert reply_for_text("/help") is None
    assert reply_for_text("/help@other_bot") is None


def test_about_describes_bot() -> None:
    assert reply_for_text("/about") == ABOUT_TEXT
    assert "TerroirTester" in ABOUT_TEXT
    assert "Codex 完整开发流程" in ABOUT_TEXT


def test_ping_reports_online() -> None:
    assert reply_for_text("/ping") == "pong：Bot 正常在线。"


def test_command_with_bot_username_is_supported() -> None:
    assert reply_for_text("/ping@my_test_bot") == "pong：Bot 正常在线。"


def test_plain_text_is_not_echoed() -> None:
    reply = reply_for_text("  今天开会  ")

    assert reply is not None
    assert "你说" not in reply
    assert "/start" in reply
    assert "/help" not in reply


def test_unknown_slash_command_is_ignored_to_avoid_clashes() -> None:
    assert reply_for_text("/missing") is None
