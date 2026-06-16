from __future__ import annotations

START_TEMPLATE = (
    "你好，{name}！\n\n"
    "这个 Bot 已经成功运行。\n"
    "发送 /start 查看可用命令。\n\n"
    "可用命令：\n"
    "/ping - 检查 Bot 是否在线\n"
    "/about - 了解这个 Bot\n"
    "/whoami - 查看自己的 Telegram 数字 ID\n"
    "/llmcheck - 管理员检查占卜助手连接与模型权限\n"
    "/tarot - 管理员回复某位用户后发起塔罗投射练习"
)

ABOUT_TEXT = "TerroirTester\n用于演示 Codex 完整开发流程"


def reply_for_text(text: str, first_name: str = "朋友") -> str | None:
    """Return a deterministic reply that can be tested without Telegram."""
    normalized = text.strip()
    command = normalized.split(maxsplit=1)[0].lower() if normalized else ""
    command = command.split("@", maxsplit=1)[0]

    if command == "/start":
        return START_TEMPLATE.format(name=first_name)
    if command == "/help":
        return None
    if command == "/ping":
        return "pong：Bot 正常在线。"
    if command == "/about":
        return ABOUT_TEXT
    if command.startswith("/"):
        return None
    if not normalized:
        return "请发送文字，或发送 /start 查看可用命令。"

    return "普通文字我不会复述。请发送 /start 查看可用命令。"
