from __future__ import annotations

START_TEMPLATE = (
    "你好，{name}！\n\n"
    "这个 Bot 已经成功运行。\n"
    "发送 /help 查看命令，或直接发一段文字让我复述。"
)

HELP_TEXT = (
    "可用命令：\n"
    "/start - 显示欢迎信息\n"
    "/help - 显示帮助\n"
    "/ping - 检查 Bot 是否在线\n\n"
    "你也可以直接发送普通文字。"
)


def reply_for_text(text: str, first_name: str = "朋友") -> str:
    """Return a deterministic reply that can be tested without Telegram."""
    normalized = text.strip()
    command = normalized.split(maxsplit=1)[0].lower() if normalized else ""
    command = command.split("@", maxsplit=1)[0]

    if command == "/start":
        return START_TEMPLATE.format(name=first_name)
    if command == "/help":
        return HELP_TEXT
    if command == "/ping":
        return "pong：Bot 正常在线。"
    if command.startswith("/"):
        return "我还不认识这个命令。发送 /help 查看可用命令。"
    if not normalized:
        return "请发送文字，或发送 /help 查看可用命令。"

    return f"你说：{normalized}"

