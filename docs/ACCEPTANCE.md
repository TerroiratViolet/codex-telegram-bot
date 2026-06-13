# 验收与故障处理

## A. 代码可运行

```powershell
.\.venv\Scripts\python.exe -m schedule_bot --smoke-test "/ping"
```

通过标准：输出包含 `pong`。

## B. 自动检查

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
```

通过标准：两个命令退出码均为 0，测试没有失败。

## C. Bot 可响应

本地启动后，在 Telegram 发送 `/start`、`/ping` 和普通文字。

通过标准：三种消息都在数秒内收到预期回复。

## D. 变更可审查

创建功能分支和 Pull Request。

通过标准：

- Files changed 能看到准确差异。
- CI 的 `test` 为绿色。
- PR 描述包含行为、测试结果和部署影响。
- `main` 规则阻止未通过 CI 的直接合并。

## E. 服务可发布

Railway 从 GitHub 的 `main` 部署，Variables 中存在 `TELEGRAM_BOT_TOKEN`。

通过标准：

- Railway Deployment 为 Success。
- `/healthz` 返回 `{"status": "ok"}`。
- Telegram `/ping` 回复正常。
- Railway 日志不包含 Telegram API 请求 URL 或 Bot Token。

## 常见故障

### 提示 Missing TELEGRAM_BOT_TOKEN

确认项目根目录有 `.env`，名称不是 `.env.txt`，变量名完全是 `TELEGRAM_BOT_TOKEN`。

### Telegram 没有回复

1. 确认本地程序仍在运行。
2. 确认 Token 没有多余空格。
3. 确认没有同时运行本地和 Railway 两个长轮询实例。
4. 检查终端或 Railway Deploy Logs。
5. 如果 Token 曾泄露，立刻在 BotFather 撤销并生成新 Token。

### CI 失败

打开 GitHub Actions 的失败步骤，复制错误信息给 Codex，要求它修复并再次运行全部验收命令。不要绕过检查。

### Railway 健康检查失败

确认应用监听平台提供的 `PORT`，路径是 `/healthz`，服务生成了 Domain，并检查 Deploy Logs 中是否先出现 Python 异常。
