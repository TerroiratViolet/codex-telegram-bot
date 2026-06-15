from pathlib import Path

ROOT_DIR = Path(__file__).parents[1]


def test_module_development_playbook_captures_repeatable_workflow() -> None:
    playbook = (ROOT_DIR / "docs" / "MODULE_DEVELOPMENT_PLAYBOOK.md").read_text(
        encoding="utf-8"
    )

    required_sections = [
        "核心需求提炼",
        "最小成功标准",
        "模块需求填写表",
        "Codex 标准执行流程",
        "边界与注意事项",
        "互动样本",
        "后续升级路径",
        "新模块开工确认清单",
    ]
    for section in required_sections:
        assert section in playbook

    required_intake_fields = [
        "模块名称",
        "一句话目标",
        "触发方式",
        "完整交互步骤",
        "权限规则",
        "数据与隐私",
        "外部服务",
        "安全边界",
        "最小验收",
        "后续升级路径",
    ]
    for field in required_intake_fields:
        assert field in playbook

    assert "不要直接部署" in playbook
    assert "Railway Variables" in playbook
    assert ".\\.venv\\Scripts\\python.exe -m pytest" in playbook


def test_agents_requires_playbook_for_new_feature_modules() -> None:
    agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")

    assert "docs/MODULE_DEVELOPMENT_PLAYBOOK.md" in agents
    assert "new feature module" in agents
    assert "prompt the user to fill or confirm each required field" in agents
