"""平台统一错误码与异常基类。"""

from enum import StrEnum


class ErrorCode(StrEnum):
    """平台错误码，格式为 `<领域>_<原因>`，发布后不得复用或改变含义。

    Attributes:
        CONFIG_INVALID: 配置缺失或校验失败。
        INTERNAL_ERROR: 未归类的内部错误，出现时应补充更具体的错误码。

    """

    CONFIG_INVALID = "CONFIG_INVALID"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AgentPlatformError(Exception):
    """平台异常基类，所有调用方需要感知的异常都必须继承它。

    Args:
        code: 稳定的错误码，调用方据此分支处理。
        message: 面向调用方的错误说明，不得包含密钥或个人敏感信息。
        retryable: 调用方是否可以安全重试。

    Attributes:
        code: 稳定的错误码。
        message: 面向调用方的错误说明。
        retryable: 调用方是否可以安全重试。

    """

    def __init__(self, code: ErrorCode, message: str, *, retryable: bool = False) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.retryable = retryable
