from pathlib import Path

import pytest

from agent_platform.common.errors import AgentPlatformError, ErrorCode
from agent_platform.common.settings import load_settings


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for key in ("AGENT_PLATFORM_ENV", "AGENT_PLATFORM_LOG_LEVEL", "AGENT_PLATFORM_LOG_FORMAT"):
        monkeypatch.delenv(key, raising=False)


def test_load_settings_uses_defaults() -> None:
    settings = load_settings()

    assert settings.env == "dev"
    assert settings.log_level == "INFO"
    assert settings.log_format == "text"


def test_load_settings_reads_prefixed_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_PLATFORM_ENV", "prod")
    monkeypatch.setenv("AGENT_PLATFORM_LOG_FORMAT", "json")

    settings = load_settings()

    assert settings.env == "prod"
    assert settings.log_format == "json"


def test_load_settings_reads_dotenv_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("AGENT_PLATFORM_LOG_LEVEL=DEBUG\n", encoding="utf-8")

    assert load_settings().log_level == "DEBUG"


def test_load_settings_rejects_invalid_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_PLATFORM_LOG_LEVEL", "VERBOSE")

    with pytest.raises(AgentPlatformError) as exc_info:
        load_settings()

    assert exc_info.value.code is ErrorCode.CONFIG_INVALID
    assert "log_level" in exc_info.value.message
