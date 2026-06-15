# Codex working agreement

This repository is a small Python Telegram bot maintained by a beginner.

## Required workflow

1. Read `README.md` and the relevant files before editing.
2. For every new feature module, read `docs/MODULE_DEVELOPMENT_PLAYBOOK.md` before coding,
   use its module requirement form, and prompt the user to fill or confirm each required field.
3. Keep Telegram transport code in `schedule_bot/handlers.py`.
4. Keep reply text and business rules in `schedule_bot/responses.py` so they are easy to test.
5. Never put a bot token, API key, password, or `.env` content in code, tests, logs, commits, or PR text.
6. Never log tarot questions, user answers, generated psychological hypotheses, or full Telegram updates.
7. Tarot analysis is an administrator-only reflective aid, not diagnosis or treatment. Keep consent,
   uncertainty language, crisis escalation guidance, and the admin-only delivery boundary intact.
8. For every behavior change, add or update a test in `tests/`.
9. Run all acceptance commands before finishing:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m schedule_bot --smoke-test "/start"
```

10. Summarize changed behavior, files, test results, and any deployment impact.
11. Do not deploy directly from a feature branch. Open a pull request and merge only after CI passes.

## Design limits

- Prefer standard library code and existing dependencies.
- Keep functions short and names explicit.
- Do not add a database until a requested feature needs persistent data.
- Keep one production replica while the bot uses long polling.
- Preserve `/start`, `/help`, `/ping`, and plain-text echo behavior unless the task explicitly changes them.
