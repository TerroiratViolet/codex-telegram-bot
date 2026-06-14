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

## 塔罗功能的数据流

```text
管理员回复用户并发送 /tarot
        ↓ 管理员数字 ID 白名单
Bot 先确认能私聊管理员
        ↓
群组中显示用户授权图片与按钮
        ↓ 仅被邀请用户可以点击
问题 A → 随机大阿尔卡那牌面 → 回答 B → 回答 C
        ↓
内存会话状态机（两小时过期，不写日志或数据库）
        ↓
牌面结构化资料 + A/B/C → 已配置的 LLM provider（默认 Gemini）
        ↓
管理员私聊中的参考分析
        ↓
管理员人工判断并手动回复用户
```

### 权限边界

- `TELEGRAM_ADMIN_USER_IDS` 是发起 `/tarot` 的唯一权限来源。
- 用户授权按钮绑定会话 ID 和目标用户数字 ID。
- LLM 输出只发送给发起该会话的管理员数字 ID。
- Bot 在确认能私聊管理员之前，不会向用户发出邀请。

### 状态机

`AWAITING_CONSENT` → `AWAITING_QUESTION_A` → `AWAITING_ANSWER_B` →
`AWAITING_ANSWER_C` → `ANALYZING` → `COMPLETE`

用户拒绝时进入 `DECLINED`。同一群组、同一用户同时只能有一个活动会话。

问题 A/B/C 必须回复 Bot 对应的消息。这样即使目标用户在群里进行其他对话，
也不会被误收集为塔罗材料。

### 牌组

`tarot_cards.py` 定义 22 张大阿尔卡那。每张牌包含：

- 中文名和英文名
- 随 Docker 镜像发布的本地牌面文件
- 可观察的画面元素
- 原型主题
- 光明面与阴影面
- 建议关注的投射方向

这些字段是 LLM 的背景材料，不是对用户的固定结论。

### LLM 安全边界

`tarot_analysis.py` 明确要求：

- 观察与推论分开。
- 使用“可能、也许、可以追问验证”等不确定措辞。
- 不使用精神疾病标签，不声称完成心理诊断。
- 回到问题 A，提供可行动的答案和管理员手动回复草稿。
- 出现危机信号时把安全支持放在塔罗解释之前。
- 设置 `store=False`，避免创建可继续使用的 API 响应记录。

用户答案不会进入普通应用日志。异常日志只记录会话 ID 或 Telegram update ID。
