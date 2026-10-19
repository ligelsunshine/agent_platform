"""平台日志初始化与请求级上下文注入。"""

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import override

from agent_platform.common.settings import LogFormat, LogLevel

_run_id: ContextVar[str | None] = ContextVar("run_id", default=None)

_TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s [run_id=%(run_id)s] %(message)s"


class _RunIdFilter(logging.Filter):
    """把当前上下文的 run_id 注入每条日志记录。"""

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        """为日志记录补充 run_id 字段。"""
        record.run_id = _run_id.get()
        return True


class _JsonFormatter(logging.Formatter):
    """把日志记录格式化为单行 JSON，便于日志平台检索。"""

    @override
    def format(self, record: logging.LogRecord) -> str:
        """将日志记录转换为 JSON 字符串。"""
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "run_id": getattr(record, "run_id", None),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: LogLevel, log_format: LogFormat) -> None:
    """初始化根 logger，只允许在程序入口调用一次。

    Args:
        level: 日志级别。
        log_format: 日志格式，`text` 为可读文本，`json` 为单行 JSON。

    Returns:
        None。

    """
    handler = logging.StreamHandler()
    handler.addFilter(_RunIdFilter())
    if log_format == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(_TEXT_FORMAT))
    logging.basicConfig(level=level, handlers=[handler], force=True)


@contextmanager
def bind_run_id(run_id: str) -> Iterator[None]:
    """在上下文范围内为日志绑定 run_id，退出后自动恢复。

    Args:
        run_id: 本次 Agent 运行的唯一标识。

    Returns:
        上下文管理器；在 with 块内输出的日志都会携带该 run_id。

    """
    token = _run_id.set(run_id)
    try:
        yield
    finally:
        _run_id.reset(token)
