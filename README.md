# Codex Telegram Bot：从零到可发布

[![CI](https://github.com/TerroiratViolet/codex-telegram-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/TerroiratViolet/codex-telegram-bot/actions/workflows/ci.yml)

这是一个给初学者使用的最小完整项目。它不是只展示几行 Bot 代码，而是包含：

- 可运行的 Telegram Bot
- 不连接 Telegram 也能执行的本地模拟
- 自动测试和代码检查
- Git 版本历史与 Pull Request 审查模板
- GitHub Actions 持续集成
- Docker 与 Railway 发布配置
- 面向 Codex 的固定工作规则

## 1. 先理解完整闭环

```text
手机或电脑向 Codex 描述需求
        ↓
Codex 从 main 创建功能分支
        ↓
修改代码 + 修改测试 + 本地检查
        ↓
推送 GitHub 并创建 Pull Request
        ↓
GitHub Actions 自动验收
        ↓
你阅读差异并合并
        ↓
Railway 从 main 自动发布
        ↓
在 Telegram 输入 /ping 验收生产环境
```

不要让 Codex 直接修改生产服务器，也不要把 Token 发在聊天、Issue 或代码里。GitHub 是唯一的代码事实来源，Pull Request 是上线闸门，Railway 的 Variables 是生产密钥存放处。

## 2. 项目结构

```text
schedule_bot/
  app.py          启动 Bot 与健康检查
  config.py       读取环境变量
  handlers.py     把 Telegram 消息交给回复规则
  responses.py    可测试的回复规则
tests/            自动验收
.github/          CI、Issue 和 PR 模板
AGENTS.md         Codex 每次工作都必须遵守的规则
Dockerfile        统一部署环境
railway.json      Railway 发布与健康检查
```

第一版故意不使用数据库。只有当需求涉及“重启后仍要保留的日程、用户设置或历史记录”时，才增加 PostgreSQL。

## 3. 本机首次安装

本项目使用 Python 3.13。当前 Windows 已安装 Git、Python 和 GitHub CLI。

在 PowerShell 中进入项目目录：

```powershell
cd C:\Users\Jay\Documents\Bot
```

创建项目专用虚拟环境：

```powershell
python -m venv .venv
```

如果 Windows 仍把 `python` 指向应用商店，使用完整路径：

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
```

安装依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

也可以用一次性脚本完成创建环境、安装和验收：

```powershell
.\scripts\bootstrap.ps1
```

## 4. 不需要 Token 的第一次验收

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m schedule_bot --smoke-test "/start"
.\.venv\Scripts\python.exe -m schedule_bot --smoke-test "今天开会"
```

以后可直接运行：

```powershell
.\scripts\verify.ps1
```

预期结果：

- Ruff 没有错误。
- Pytest 全部通过。
- `/start` 输出欢迎语。
- 普通文字输出 `你说：今天开会`。

## 5. 创建 Telegram Bot

1. 在 Telegram 搜索官方账号 `@BotFather`，核对账号带官方认证标记。
2. 发送 `/newbot`。
3. 按提示填写显示名称。
4. 填写以 `bot` 结尾的唯一用户名。
5. BotFather 会返回 Token。Token 等同密码，不要粘贴进 Codex 对话、GitHub Issue 或代码。
6. 在项目根目录复制配置模板：

```powershell
Copy-Item .env.example .env
notepad .env
```

7. 只在本机 `.env` 中把占位值替换为真实 Token。`.gitignore` 已阻止 `.env` 被提交。

启动真实 Bot：

```powershell
.\.venv\Scripts\python.exe -m schedule_bot
```

然后在 Telegram 中依次发送：

```text
/start
/ping
你好
```

预期收到欢迎语、在线确认和 `你说：你好`。按 `Ctrl+C` 停止本地 Bot。

## 6. Git 和 GitHub

初始化只做一次：

```powershell
git init -b main
git add .
git commit -m "Initial production-ready Telegram bot"
gh auth login
gh repo create codex-telegram-bot --public --source . --remote origin --push
```

登录时选择 GitHub.com、HTTPS 和浏览器登录。示例使用公开仓库，是因为 GitHub Free 可以在公开仓库免费强制分支保护。代码中没有 Token，所以公开代码本身是安全的。

如果代码必须保密，可把 `--public` 改为 `--private`。但 GitHub 官方目前要求 GitHub Pro、Team 或 Enterprise 才能在私有仓库使用受保护分支。GitHub Free 私有仓库仍可使用 PR 和 CI，只是平台不会强制阻止你直接推送 `main`。

日常修改永远使用分支：

```powershell
git switch main
git pull
git switch -c feature/add-about-command
```

修改和测试完成后：

```powershell
git add .
git commit -m "Add about command"
git push -u origin feature/add-about-command
gh pr create --fill
```

打开 Pull Request，等待绿色 CI，再检查 Files changed，最后合并。不要在 CI 失败时合并。

## 7. GitHub 必做设置

仓库创建后，在 GitHub 网页进入：

`Settings > Rules > Rulesets > New ruleset > New branch ruleset`

设置：

1. 名称填 `Protect main`。
2. Enforcement status 选 `Active`。
3. Target branches 包含默认分支 `main`。
4. 开启 Require a pull request before merging。
5. 开启 Require status checks to pass。
6. 选择 CI 中的 `test` 检查。
7. 开启 Block force pushes。
8. 保存。

这样手机上的 Codex 只能交付 PR，不能绕过你的审查直接替换生产代码。若你选择 GitHub Free 私有仓库，则把“必须走 PR”作为人工规则执行，或升级 GitHub Pro 后开启强制规则。

## 8. Railway 发布

这里选择 Railway，是因为它可以连接 GitHub、读取 Dockerfile、保存 Variables、自动从 `main` 发布，并支持健康检查。平台可能收费，请在 Railway 中设置 Usage limit。

1. 登录 Railway 并连接 GitHub。
2. 选择 `New Project > Deploy from GitHub repo`。
3. 选择 `codex-telegram-bot` 仓库。
4. 打开服务的 `Variables`。
5. 新增 `TELEGRAM_BOT_TOKEN`，值为 BotFather Token。
6. 新增 `LOG_LEVEL=INFO`。
7. 不要手工设置 `PORT`，Railway 会提供。
8. 确认只运行一个 Replica。长轮询 Bot 不能同时运行多个副本。
9. 在 Networking 中生成一个 Railway Domain，让 `/healthz` 可以被平台检查。
10. 等部署状态变为 Success。
11. 打开 Deploy Logs，确认出现健康端口和 Bot 启动日志。
12. 在 Telegram 发送 `/ping`，预期收到 `pong：Bot 正常在线。`

以后每次合并到 `main`，Railway 会自动重新构建并发布。不要让功能分支直接连接生产部署。

## 9. 手机 Codex 工作方式

Codex Web 可以连接 GitHub 仓库、在云环境执行任务并创建 Pull Request。手机上使用浏览器打开 Codex，选择这个 GitHub 仓库。

第一次任务建议完整写：

```text
请阅读 AGENTS.md 和 README.md。
为 Telegram Bot 增加 /about 命令。
回复应包含 Bot 名称和“用于演示 Codex 完整开发流程”。
保持现有 /start、/help、/ping 和普通文字功能不变。
添加自动测试，运行 AGENTS.md 中的全部验收命令。
不要修改或索取任何 Token。
完成后创建 Pull Request，不要直接部署或合并。
```

以后仍然要写清楚四件事：

1. 输入是什么。
2. 预期输出是什么。
3. 哪些旧行为不能改变。
4. 必须测试并创建 PR。

不要只说“优化一下 Bot”。模糊任务会产生难以验收的改动。

## 10. 每次变更的验收表

- [ ] Codex 阅读了 `AGENTS.md`。
- [ ] 改动位于功能分支，不是 `main`。
- [ ] 新功能有测试。
- [ ] Ruff 通过。
- [ ] Pytest 通过。
- [ ] Smoke test 通过。
- [ ] Pull Request 中没有 Token 或 `.env`。
- [ ] GitHub Actions 为绿色。
- [ ] 你阅读了 Files changed。
- [ ] 合并后 Railway 部署成功。
- [ ] Telegram 中 `/ping` 成功。
- [ ] 新功能按示例工作。

更详细的架构和故障处理见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 与 [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)。

## 11. 塔罗投射分析助手

### 11.1 它做什么

管理员 Terroir 在群组中回复某位用户的消息并发送 `/tarot`。Bot 会：

1. 验证发起人是否在管理员数字 ID 白名单中。
2. 私聊管理员显示紫罗兰酒馆管理界面，确认管理员能够接收最终分析。
3. 在群组中 `@` 被邀请用户，显示另一张用户界面图片和明确的授权按钮。
4. 用户点击“我愿意开始”后，依次收集：
   - 问题 A：用户真正想问的问题。
   - 问题 B：用户第一眼在随机牌面中看见了什么。
   - 问题 C：用户如何理解牌面，以及它与问题 A 的关系。
5. 从 22 张 Rider–Waite–Smith 大阿尔卡那中随机抽取一张，在群组中显示并
   `@` 用户。
6. 把问题 A、回答 B/C 和该牌的结构化象征资料发送给 OpenAI Responses API。
7. 仅在管理员与 Bot 的私聊中发送分析。群组用户不会看到 LLM 的心理解释。

Bot 把牌当作“投射性反思的镜面”，不把牌义当预言，也不把 LLM 输出当心理诊断。
管理员必须人工阅读、判断和改写后，才决定是否回复用户。

### 11.2 为什么用户必须“回复”Bot

问题 A、B、C 都会弹出 Telegram 的回复输入框。用户应该回复对应的 Bot 消息，
不要直接在群组中另发一条普通消息。

这样有两个好处：

- Telegram 的群组隐私模式可以保持开启，Bot 不需要读取整个群组的所有聊天。
- Bot 不会把用户在群组里的其他普通发言误当作塔罗答案。

### 11.3 配置管理员

Telegram 权限必须使用数字 ID，不能只比较容易修改的用户名。

1. 管理员先私聊 Bot，发送 `/start`。
2. 发送 `/whoami`。
3. Bot 会回复类似 `123456789` 的数字。
4. 本地 `.env` 或 Railway Variables 增加：

```text
TELEGRAM_ADMIN_USER_IDS=123456789
```

多个管理员使用英文逗号分隔：

```text
TELEGRAM_ADMIN_USER_IDS=123456789,987654321
```

### 11.4 配置 OpenAI

ChatGPT 登录和 OpenAI API 是两套独立的使用入口。这个 Bot 需要 OpenAI API Key，
API 调用可能产生费用。

1. 打开 [OpenAI API Keys](https://platform.openai.com/api-keys)。
2. 创建仅供这个 Bot 使用的 Key。
3. 不要把 Key 发给 Codex，也不要提交进 GitHub。
4. 在本地 `.env` 或 Railway Variables 增加：

```text
OPENAI_API_KEY=你的真实Key
OPENAI_MODEL=gpt-5.2
```

生产环境最终需要以下变量：

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_USER_IDS
OPENAI_API_KEY
OPENAI_MODEL
LOG_LEVEL=WARNING
```

用户的 A/B/C 回答和牌面象征资料会在用户同意后发送给 OpenAI，代码明确设置
`store=False`。不要引导用户输入身份证件、地址、密码、详细医疗记录等不必要信息。

### 11.5 群组使用流程

1. 把 Bot 加入群组。
2. 管理员先在私聊中向 Bot 发送 `/start`，保证 Bot 可以回传私密分析。
3. 在群组中找到要邀请的用户消息。
4. 回复该消息并发送 `/tarot`。
5. 被邀请用户本人点击“我愿意开始”或“暂不参加”。
6. 用户依次回复问题 A、牌面问题 B、问题 C。
7. 管理员回到与 Bot 的私聊，阅读 LLM 参考分析。
8. 管理员根据实际关系和上下文自行判断，并手动回复用户。

未经配置的用户发送 `/tarot` 会被拒绝；其他群成员也不能替被邀请者点击授权按钮。

### 11.6 隐私与运行限制

- 塔罗会话只保存在当前进程内存，不写数据库、不写日志。
- 会话两小时后自动过期。
- Railway 重新部署或进程重启会清除尚未完成的会话。
- 当前仍应只运行一个 Railway Replica。
- LLM 出错时，Bot 只通知管理员，不把错误或内部提示暴露给用户。
- 若回答出现自伤、伤人、虐待或极端绝望迹象，提示词要求优先建议现实中的紧急服务、
  危机热线或合格心理健康专业人员，不继续浪漫化塔罗解释。

### 11.7 图片与牌面来源

- 管理员图与用户授权图由项目专门生成，分别位于
  `schedule_bot/assets/tarot-admin.png` 和 `schedule_bot/assets/tarot-consent.png`。
- 牌面使用 1909 年 Rider–Waite–Smith 大阿尔卡那图像，通过 Wikimedia Commons
  公共文件地址显示。
- 每张牌在 `schedule_bot/tarot_cards.py` 中定义视觉元素、原型、光明面、阴影面和
  投射观察重点。LLM 必须结合用户自己的 B/C 回答，不能只输出固定牌义。
