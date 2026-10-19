"""平台运行配置的加载与校验。"""

from typing import Literal

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent_platform.common.errors import AgentPlatformError, ErrorCode

type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
type LogFormat = Literal["text", "json"]


class Settings(BaseSettings):
    """平台运行配置，只从环境变量和本地 .env 读取，启动时一次性校验。

    Attributes:
        env: 运行环境。
        log_level: 日志级别。
        log_format: 日志格式，开发用 text，生产用 json。

    """

    model_config = SettingsConfigDict(
        env_prefix="AGENT_PLATFORM_",
        env_file=".env",
        env_file_encoding="utf-8",
        frozen=True,
    )

    env: Literal["dev", "test", "prod"] = "dev"
    log_level: LogLevel = "INFO"
    log_format: LogFormat = "text"


def load_settings() -> Settings:
    """加载并校验平台配置。

    Returns:
        校验通过的平台配置。

    Raises:
        AgentPlatformError: 错误码 `CONFIG_INVALID`，环境变量或 .env 中的配置值不合法时抛出。

    """
    try:
        return Settings()
    except ValidationError as exc:
        fields = ", ".join(str(error["loc"][0]) for error in exc.errors() if error["loc"])
        raise AgentPlatformError(ErrorCode.CONFIG_INVALID, f"配置校验失败: {fields}") from exc
