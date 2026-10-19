import json
import logging
from collections.abc import Iterator

import pytest

from agent_platform.common.logging_config import bind_run_id, configure_logging


@pytest.fixture(autouse=True)
def _restore_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)


def test_json_format_contains_run_id(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "json")

    with bind_run_id("run_abc"):
        logging.getLogger("demo").info("工具完成: %s", "log_search")

    record = json.loads(capsys.readouterr().err.strip())
    assert record["msg"] == "工具完成: log_search"
    assert record["run_id"] == "run_abc"
    assert record["level"] == "INFO"
    assert record["ts"].endswith("+00:00")


def _raise_value_error() -> None:
    raise ValueError("boom")


def test_json_format_includes_exception(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "json")

    try:
        _raise_value_error()
    except ValueError:
        logging.getLogger("demo").exception("失败")

    record = json.loads(capsys.readouterr().err.strip())
    assert "ValueError: boom" in record["exc_info"]


def test_text_format_resets_run_id_after_context(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "text")

    with bind_run_id("run_xyz"):
        logging.getLogger("demo").info("inside")
    logging.getLogger("demo").info("outside")

    lines = capsys.readouterr().err.strip().splitlines()
    assert "[run_id=run_xyz] inside" in lines[0]
    assert "[run_id=None] outside" in lines[1]


def test_level_filters_lower_records(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("WARNING", "text")

    logging.getLogger("demo").info("hidden")

    assert capsys.readouterr().err == ""
