import pytest

from schedule_bot.config import Settings


def test_settings_require_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("PORT", "8080")

    with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
        Settings.from_env(load_env_file=False)


def test_settings_read_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "123, 456")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = Settings.from_env(load_env_file=False)

    assert settings.telegram_bot_token == "test-token"
    assert settings.telegram_admin_user_ids == frozenset({123, 456})
    assert settings.openai_api_key == "test-openai-key"
    assert settings.openai_model == "test-model"
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"


def test_settings_reject_non_numeric_admin_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_IDS", "Terroir")

    with pytest.raises(ValueError, match="numeric Telegram user IDs"):
        Settings.from_env(load_env_file=False)


def test_optional_tarot_settings_default_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.delenv("TELEGRAM_ADMIN_USER_IDS", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    settings = Settings.from_env(load_env_file=False)

    assert settings.telegram_admin_user_ids == frozenset()
    assert settings.openai_api_key == ""
    assert settings.openai_model == "gpt-5.2"


def test_openai_placeholder_is_not_treated_as_a_real_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "replace-with-openai-api-key")

    settings = Settings.from_env(load_env_file=False)

    assert settings.openai_api_key == ""
