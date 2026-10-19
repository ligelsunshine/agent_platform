from agent_platform.common.errors import AgentPlatformError, ErrorCode


def test_error_keeps_code_message_and_retryable() -> None:
    err = AgentPlatformError(ErrorCode.CONFIG_INVALID, "缺少配置", retryable=True)

    assert err.code is ErrorCode.CONFIG_INVALID
    assert err.message == "缺少配置"
    assert err.retryable
    assert str(err) == "[CONFIG_INVALID] 缺少配置"


def test_error_is_not_retryable_by_default() -> None:
    assert not AgentPlatformError(ErrorCode.INTERNAL_ERROR, "x").retryable
