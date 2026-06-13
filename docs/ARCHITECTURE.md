# 架构说明

## 五个层次

1. **Telegram**：用户发送消息。BotFather 只负责创建身份和 Token。
2. **Python Bot**：`handlers.py` 接收消息，`responses.py` 决定回复。
3. **GitHub**：保存每个版本，分支隔离工作，Pull Request 展示差异。
4. **GitHub Actions**：自动执行 Ruff、Pytest 和 smoke test。
5. **Railway**：只部署已经合并到 `main` 的代码，并保存生产 Token。

## 为什么业务规则与 Telegram 分开

直接在 Telegram handler 中写全部逻辑，会导致每次测试都要连接 Telegram。现在 `reply_for_text()` 是普通 Python 函数，因此 Codex 可以快速验证输入和输出，CI 也不需要真实 Token。

## 为什么使用长轮询

长轮询对第一个 Bot 最简单：不需要配置 Telegram webhook、TLS 或公开回调地址。代价是生产环境只能运行一个副本。需要高流量或多个副本时，再改为 webhook。

## 为什么有健康端点

Telegram 长轮询本身没有网页。`/healthz` 给部署平台一个明确的“进程活着”信号。它不显示 Token，也不表示 Telegram API 一定可达；最终生产验收仍以 Telegram `/ping` 为准。

## 什么时候增加数据库

以下需求才需要数据库：

- 日程在服务重启后仍保存
- 多用户各自拥有设置
- 提醒任务需要持久化
- 需要审计或历史记录

推荐下一阶段使用 Railway PostgreSQL 和 SQLAlchemy/Alembic。不要用容器内部文件保存重要数据，因为重新部署后文件可能消失。

## 密钥边界

- 本地：真实 Token 仅在 `.env`。
- GitHub：此项目的 CI 不需要 Token。
- Railway：真实 Token 仅在 Variables。
- Codex：只看到变量名称，不应看到变量值。
- HTTP 客户端固定使用 `WARNING` 日志级别，避免 Telegram API URL 中的 Token
  出现在部署日志。
