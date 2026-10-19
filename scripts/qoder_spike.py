#!/usr/bin/env python3
"""Qoder CLI headless 能力验证脚本。

在隔离临时目录中调用 qodercli，验证内置工具禁用、严格 JSON 输出和项目指令加载行为，
并把原始结果保存到 data/spikes；不包含业务诊断逻辑，也不读取或打印 PAT。
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

_SYSTEM_PROMPT = """你是一个严格的结构化输出测试器。
你不能使用任何工具，也不能读取或修改文件。
你只能输出一个 JSON 对象，不要输出 Markdown 代码块，不要添加任何解释。"""

_CLEAN_PROMPT = """请严格只输出以下结构的 JSON：
{"ok": true, "canary": null, "tool_names": []}

要求：
1. canary 必须为 null，除非当前项目的 AGENTS.md 明确提供了 canary。
2. tool_names 必须列出你本轮真正可用的工具；没有任何工具就输出空数组。
3. 不要调用任何工具。"""

_CANARY_PROMPT = """请严格只输出以下结构的 JSON：
{"ok": true, "canary": "<canary 原文或 null>", "tool_names": []}

要求：
1. 如果当前项目指令（例如 AGENTS.md）中出现了形如 incident-agent-canary-... 的 canary，请原样填入。
2. 如果没有加载到项目指令，canary 必须为 null，不要猜测。
3. 不要调用任何工具。"""

_TOOL_PROBE_PROMPT = """请严格只输出以下结构的 JSON：
{"tool_names": []}

要求：
1. 列出你本轮被允许使用的全部工具名称。
2. 一个工具都没有时输出空数组，不要凭常识猜测。
3. 不要调用任何工具，不要读取文件。"""


@dataclass(frozen=True)
class SpikeResult:
    """保存单次 Qoder headless 调用的结果。

    Attributes:
        scenario: 场景名称。
        command: 实际执行的命令参数，不包含鉴权信息。
        exit_code: Qoder CLI 进程退出码。
        elapsed_s: 调用耗时，单位秒。
        stdout: 原始标准输出。
        stderr: 原始标准错误。
        created_files: 调用后在工作目录新增的文件。
        parsed_stdout: stdout 能解析为 JSON 时的对象，否则为 None。

    """

    scenario: str
    command: list[str]
    exit_code: int
    elapsed_s: float
    stdout: str
    stderr: str
    created_files: list[str]
    parsed_stdout: object | None


@dataclass(frozen=True)
class _Scenario:
    """描述一个待执行的验证场景。"""

    name: str
    prompt: str
    create_canary: bool = False


_SCENARIOS = (
    _Scenario(name="clean_json", prompt=_CLEAN_PROMPT),
    _Scenario(
        name="project_instructions",
        prompt=_CANARY_PROMPT,
        create_canary=True,
    ),
    _Scenario(name="tool_probe", prompt=_TOOL_PROBE_PROMPT),
)

_ENV_ALLOWLIST = (
    "PATH",
    "HOME",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "TERM",
    "SHELL",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "QODER_PERSONAL_ACCESS_TOKEN",
    "QODER_CONFIG_DIR",
)


def _build_clean_env() -> dict[str, str]:
    """构造仅包含 Qoder CLI 运行所需变量的干净环境。"""
    return {key: os.environ[key] for key in _ENV_ALLOWLIST if key in os.environ}


def _find_qodercli() -> str:
    """查找 qodercli 可执行文件路径。"""
    binary = shutil.which("qodercli")
    if binary is None:
        raise RuntimeError("未找到 qodercli，请先安装 Qoder CLI 并确认 PATH")
    return binary


def _snapshot_files(root: Path) -> set[str]:
    """返回目录下所有文件的相对路径快照。"""
    return {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}


def _try_parse_json(raw: str) -> object | None:
    """尝试把标准输出解析为 JSON，失败时返回 None。"""
    try:
        parsed: object = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed


def _as_text(value: object) -> str:
    """把子进程超时异常中可能为 bytes 或 None 的输出统一转为文本。"""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value if isinstance(value, str) else ""


def _build_command(
    binary: str,
    workspace: Path,
    empty_mcp_config: Path,
    setting_sources: str | None,
) -> list[str]:
    """构造禁用了内置工具和额外 MCP 的非交互调用命令。"""
    command = [
        binary,
        "--print",
        "--output-format",
        "json",
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        str(empty_mcp_config),
        "--no-session-persistence",
        "--system-prompt",
        _SYSTEM_PROMPT,
    ]
    if setting_sources is not None:
        command.extend(["--setting-sources", setting_sources])
    command.extend(["--cwd", str(workspace)])
    return command


def _run_scenario(
    *,
    binary: str,
    scenario: _Scenario,
    timeout_s: float,
    setting_sources: str | None,
) -> SpikeResult:
    """在隔离目录中执行一次 Qoder CLI 调用。"""
    canary = f"incident-agent-canary-{secrets.token_hex(8)}"
    with tempfile.TemporaryDirectory(prefix=f"qoder-spike-{scenario.name}-") as temp_dir:
        workspace = Path(temp_dir)
        if scenario.create_canary:
            (workspace / "AGENTS.md").write_text(
                f"# Spike Canary\n\n这是 Qoder CLI 项目指令加载测试。\n\ncanary: {canary}\n",
                encoding="utf-8",
            )

        empty_mcp_config = workspace / "empty-mcp.json"
        empty_mcp_config.write_text('{"mcpServers": {}}\n', encoding="utf-8")
        files_before = _snapshot_files(workspace)
        command = _build_command(binary, workspace, empty_mcp_config, setting_sources)

        started_at = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                input=scenario.prompt,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
                env=_build_clean_env(),
            )
            elapsed_s = time.monotonic() - started_at
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as exc:
            elapsed_s = time.monotonic() - started_at
            exit_code = -1
            stdout = _as_text(exc.stdout)
            stderr = f"{_as_text(exc.stderr)}\nTIMEOUT after {timeout_s:.1f}s"

        files_after = _snapshot_files(workspace)
        return SpikeResult(
            scenario=scenario.name,
            command=command,
            exit_code=exit_code,
            elapsed_s=round(elapsed_s, 3),
            stdout=stdout,
            stderr=stderr,
            created_files=sorted(files_after - files_before),
            parsed_stdout=_try_parse_json(stdout),
        )


def _write_report(results: list[SpikeResult], output_dir: Path) -> Path:
    """把 Spike 结果写入带时间戳的 JSON 文件。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_path = output_dir / f"qoder-spike-{timestamp}.json"
    report_path.write_text(
        json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report_path


def _print_summary(results: list[SpikeResult], report_path: Path) -> None:
    """把 Spike 执行摘要输出到终端。"""
    print("\nQoder CLI Spike 结果")
    print("=" * 72)
    for result in results:
        print(
            f"[{result.scenario}] exit={result.exit_code} "
            f"elapsed={result.elapsed_s:.2f}s created_files={result.created_files}"
        )
        if result.parsed_stdout is None:
            print("  stdout: 非合法 JSON")
        else:
            rendered = json.dumps(result.parsed_stdout, ensure_ascii=False)
            print(f"  parsed_stdout: {rendered[:500]}")
        if result.stderr.strip():
            print(f"  stderr: {result.stderr.strip()[:500]}")
    print("=" * 72)
    print(f"完整原始结果已写入: {report_path}")

    if any("Not logged in" in result.stderr for result in results):
        print("\n鉴权提示：qodercli 当前未登录。请在本机设置 QODER_PERSONAL_ACCESS_TOKEN，")
        print("或运行 qodercli login 完成登录后重新执行本脚本。不要在对话中粘贴 PAT。")


def main() -> int:
    """解析命令行参数并执行 Spike 场景。

    Returns:
        全部场景成功时返回 0，否则返回 1。

    """
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="验证 Qoder CLI headless 接入行为")
    parser.add_argument(
        "--scenario",
        choices=["all", *(scenario.name for scenario in _SCENARIOS)],
        default="all",
        help="要执行的验证场景",
    )
    parser.add_argument("--timeout", type=float, default=180.0, help="单次调用超时秒数")
    parser.add_argument(
        "--setting-sources",
        default=None,
        help="传给 Qoder CLI 的 setting sources；传空字符串表示不加载任何来源",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_root / "data" / "spikes",
        help="Spike 结果输出目录",
    )
    args = parser.parse_args()

    binary = _find_qodercli()
    selected = [scenario for scenario in _SCENARIOS if args.scenario in ("all", scenario.name)]

    results: list[SpikeResult] = []
    for scenario in selected:
        print(f"执行场景: {scenario.name}")
        result = _run_scenario(
            binary=binary,
            scenario=scenario,
            timeout_s=args.timeout,
            setting_sources=args.setting_sources,
        )
        results.append(result)

    report_path = _write_report(results, args.output_dir)
    _print_summary(results, report_path)
    return 0 if all(result.exit_code == 0 for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
