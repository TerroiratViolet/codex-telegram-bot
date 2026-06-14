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

## F. 塔罗权限与交互验收

准备两个 Telegram 账号：

- 管理员账号：数字 ID 已加入 `TELEGRAM_ADMIN_USER_IDS`。
- 普通用户账号：未加入管理员白名单。

逐项检查：

1. 普通用户发送 `/tarot`，Bot 回复只有 Terroir 管理员可用。
2. 管理员私聊 Bot 发送 `/start` 和 `/whoami`，数字 ID 与 Railway 配置一致。
3. 管理员在私聊中直接发送 `/tarot`，Bot 提示必须在群组回复用户。
4. 管理员在群组回复普通用户并发送 `/tarot`：
   - 管理员私聊收到管理员专属图片。
   - 群组出现用户专属授权图片和两个按钮。
   - 邀请文字 `@` 普通用户。
5. 第三个群成员尝试点击按钮，Bot 拒绝。
6. 普通用户点击“暂不参加”，流程结束，不再收集答案。
7. 重新发起后，普通用户点击“我愿意开始”。
8. 普通用户依次回复问题 A、问题 B、问题 C：
   - 问题 A 后群组显示随机经典牌面并 `@` 用户。
   - 问题 B/C 都要求回复对应 Bot 消息。
   - 普通群聊消息不会被误收集。
9. 回答完成后：
   - 群组只显示“已交给 Terroir”的提示。
   - 群组不显示任何 LLM 心理分析。
   - 管理员私聊收到分析。

## G. 塔罗分析内容验收

管理员私聊内容必须包含：

- 一句话总览。
- 用户实际原话与推论的区别。
- 问题 B 和问题 C 的独立投射假设。
- 价值观、人生观、世界观线索。
- 光明面、阴影面和原型张力。
- 用户对问题 A 可能真正需要的东西。
- 回到问题 A 的具体回答。
- 管理员可以继续追问的问题。
- 可供管理员手动改写的回复草稿。
- “不是心理诊断”的边界提醒。

分析不得把牌义写成预言，不得使用确定性的精神疾病标签。

## H. 塔罗故障验收

1. 临时移除 `OPENAI_API_KEY` 后完成 A/B/C：
   - Bot 仍能完成群组流程。
   - 只在管理员私聊提示 LLM 未配置。
2. 使用无效 OpenAI Key：
   - 用户只看到回答已收好。
   - 管理员私聊收到分析失败提示。
   - Railway 日志不包含用户 A/B/C 原文、API Key 或 Telegram Token。
3. 在 A/B/C 任一步等待超过两小时：
   - 会话过期。
   - 用户可以重新接受邀请。
4. Railway 重启后：
   - 未完成会话被清除。
   - `/ping` 与新 `/tarot` 仍可正常使用。
