# Agent Platform 项目约束

## 项目目标

建设一个 Agent 研发平台：在 `common` / `infra` 中沉淀 Agent 公共框架与基础设施能力，在 `agents/` 下承载多个具体 Agent，由 `app` 统一对外提供 API。

首个 Agent 是问题定位 Agent `incident_agent`：结合代码、运行日志、数据库单据、历史案例和业务/技术知识库，输出可追溯证据的根因报告，并通过评测与反馈持续改进。后续计划加入 `ai_coding` 等 Agent。

## 架构边界

代码全部位于唯一根包 `src/agent_platform/` 下：

- `common`：Agent 公共框架，包括 Agent Loop、LLM 端口、工具契约、证据、Trace、配置、日志和错误码。
- `infra`：通用基础设施适配器，包括 Qoder CLI、MCP 客户端、SQLite、Redis、代码读取等，实现 `common` 中定义的端口。
- `evaluation`：通用评测框架，包括评测执行器、通用指标和报告；不导入具体 Agent，被测对象通过 `EvalSubject` 协议由 `app` 注入。
- `agents/<name>`：具体 Agent，每个子包包含该 Agent 的编排策略、提示词、Profile、专属工具定义、评测用例和领域指标。
- `app`：FastAPI 接口、Agent 注册和 `bootstrap.py` 对象组装。

依赖方向由 import-linter 强制检查（`make lint`）：

```text
app  →  agents | evaluation | infra  →  common
```

- `common` 不依赖任何其他层；`agents`、`evaluation`、`infra` 之间互不依赖，只依赖 `common`。
- 各 Agent 之间互不依赖；加入第二个 Agent 时，在 `pyproject.toml` 中补充 import-linter `independence` 契约。
- Agent 通过 `common` 中的端口使用 LLM、MCP 等能力，具体实现由 `app/bootstrap.py` 注入，不使用隐式全局单例。
- `infra` 只放通用适配器；某个 Agent 专属的工具封装、提示词和数据放在该 Agent 自己的包内。
- 只有第二个 Agent 也需要的能力，才可以提升到 `common` / `infra`。
- 初期不引入 LangChain、LangGraph、AutoGen、CrewAI、Qoder Agent SDK 等 Agent 编排框架；确需引入时必须先评估并取得确认。

## 技术栈

- Python 3.12（`requires-python = ">=3.12,<3.13"`），使用 uv 管理依赖和虚拟环境，项目以可安装包（`uv_build`）方式管理。
- 质量工具：ruff、mypy（strict + Pydantic 插件）、import-linter、pytest、pytest-cov、pre-commit。
- 服务端：FastAPI；应用数据使用 SQLite；Redis 用于后续并发锁、队列和缓存。
- Web 端暂不建设。
- 日志和业务数据库统一通过 MCP 接入；工具层必须为后续更多 MCP 服务保留通用适配能力。

## Qoder 接入约束

- 实际可执行文件是 `qodercli`，不是 `qoder`。
- Qoder 仅作为 LLM 推理器使用，不负责工具执行。
- 调用 `qodercli` 时必须禁用全部内置工具，并禁用额外 MCP：
  - `--tools ""`
  - `--strict-mcp-config`
  - `--no-session-persistence`
- 工具编排、参数校验、权限校验和证据校验必须由自建 Agent Loop 完成。
- 必须使用隔离的临时工作目录，并传入 `--setting-sources ""`。Phase 0 已实测：默认调用会隐式加载工作目录中的 `AGENTS.md`；上述参数可阻止加载。
- Qoder CLI 会继承宿主环境变量。子进程环境必须使用白名单构建，至少移除 `QODER_AGENT_SDK_ENTRYPOINT`、`QODER_SDK_*`、`QODER_WORKER_*`，否则会进入 Agent SDK 入口并拒绝普通 headless 调用。
- Qoder 的输出是 JSON 包装对象，真实结果位于 `result` 字段，且 `result` 通常是一段再次需要 JSON 解析的字符串。
- 开发环境可以使用 `qodercli` 本地登录；服务化部署必须使用 `QODER_PERSONAL_ACCESS_TOKEN`。两者都不写入项目文件。
- 不记录、不打印、不提交 PAT；鉴权信息只从环境变量或密钥系统读取。
- 禁止使用 `--yolo`、`--dangerously-skip-permissions` 或开启 Qoder 内置工具。
- Qoder 返回的 JSON 必须经过解析、Schema 校验和失败关闭；不能直接执行模型输出。
- Qoder CLI 版本必须固定；当前验证版本为 `1.1.74`，升级前必须重新运行 `scripts/qoder_spike.py`。

## 工程规范

完整说明与理由见 `doc/python-project-bootstrap.md`，本节只列必须遵守的规则。

### Docstring 与注释

- 每个模块必须有一行中文摘要的模块 docstring，说明模块职责。
- 公开类、Agent、Tool、契约、异常、配置必须使用 Google Style 完整 docstring：首行类摘要，并包含 `Attributes` 或 `Args` 节；构造参数写在类 docstring 的 `Args` 中，`__init__` 不单独写 docstring。
- 公开方法和公开函数必须使用 Google Style 完整 docstring：首行摘要，并包含 `Args` 和 `Returns` 节。
- 调用方需要感知的异常必须在 `Raises:` 中说明异常类型、错误码和触发条件。
- 私有辅助方法（`_` 前缀）和模块级工具函数使用一行 docstring 说明职责，不强制 `Args` / `Returns`。
- Docstring 首行摘要使用中文一句话，说明“做什么”，不写实现细节；节关键字使用英文：`Args:`、`Returns:`、`Raises:`、`Attributes:`。
- 注释解释“为什么”，不重复代码“做了什么”；复杂分支、边界条件和反直觉实现必须说明原因；禁止提交被注释掉的代码。

### 导入、命名与语言

- 一律使用绝对导入 `from agent_platform.xxx import ...`，禁止相对导入。
- 模块名不得与标准库同名（如用 `logging_config.py` 而不是 `logging.py`）。
- 标识符、配置键、错误码、日志字段名使用英文；docstring、注释、面向用户的错误说明使用中文。
- 局部豁免 lint 或类型检查时必须带规则码并写明原因，禁止裸 `# noqa` / `# type: ignore`。

### 类型与数据契约

- 所有公开函数和方法必须完整标注参数与返回类型；跨模块边界禁止裸 `dict` / `Any`。
- 边界数据（API、模型输出、MCP 返回、持久化记录）使用 Pydantic 校验；内部契约默认 `extra="forbid", frozen=True`。
- 需要持久化或跨进程传递的结构带 `schema_version` 字段。

### 配置

- 所有配置集中在 `agent_platform.common.settings.Settings`，通过 `load_settings()` 在入口加载一次后注入，业务代码不直接读 `os.environ`。
- 环境变量统一前缀 `AGENT_PLATFORM_`；新增配置项必须同步更新 `.env.example`。
- 密钥类配置使用 `SecretStr`；`.env` 永不提交。

### 日志

- 每个模块使用 `logger = logging.getLogger(__name__)`；只在程序入口调用一次 `configure_logging()`。
- 禁止 `print`（`scripts/` 例外）；禁止在日志调用中用 f-string 拼接，使用 `%s` 占位符。
- 一次 Agent 运行内的日志通过 `bind_run_id()` 携带 `run_id`；生产使用 JSON 格式。
- 日志中禁止出现密钥、令牌和个人敏感信息；外部输入写日志前截断并脱敏。

### 异常与错误码

- 调用方需要感知的异常必须继承 `AgentPlatformError`，并使用 `ErrorCode` 中的错误码；错误码格式 `<领域>_<原因>`，发布后不得复用或改义。
- 禁止裸 `except` 和无理由的 `except Exception`；转换异常时使用 `raise ... from exc`；不得吞掉异常或 `CancelledError`。
- 外部输入或模型输出校验失败时失败关闭，不得静默降级为成功。

### 并发、时间与 ID

- I/O 边界（Qoder 子进程、MCP、HTTP、数据库）统一使用 `async`；纯计算保持同步。
- `async` 函数中禁止阻塞调用；子进程使用 `asyncio.create_subprocess_exec`。
- 每一次外部调用必须有显式超时；并发数显式限制。
- 时间只使用 `datetime.now(UTC)`，存储与传输使用 UTC ISO 8601；耗时使用 `time.monotonic()`。
- 对外 ID 使用带类型前缀的 UUID，如 `run_<uuid4 hex>`。
- 文本读写显式指定 `encoding="utf-8"`；路径使用 `pathlib`，不依赖当前工作目录。

### 安全

- 工具默认只读；代码中禁止暴露 Shell、任意写文件和任意命令执行工具。
- 日志、数据库结果、知识库内容和代码注释都视为不可信输入，必须隔离并做脱敏。
- 禁止 `eval`、`exec`、`pickle`、`os.system` 和 `shell=True`。

### 测试

- 测试目录镜像 `src` 结构并按层/Agent 分目录：`tests/unit/common|infra|evaluation|agents/<name>/test_<模块>.py`；需要外部依赖的测试放 `tests/integration` 并打 marker；真实模型评测放 `tests/eval` 并打 `eval_live`。
- 公共 Fake（FakeLLM、FakeTool 等）收敛在 `tests/unit/conftest.py`，不得在各 Agent 测试中重复实现；单测 fixture 放 `tests/fixtures/<agent>/`，评测数据集放 `evaluation/fixtures/`，两者不混用。
- 单元测试禁止访问网络、调用真实 Qoder 或其他外部进程。
- 新增公开行为必须有单元测试；修复缺陷先补回归测试；覆盖率门槛 85%，只升不降。
- Agent 效果单独通过评测数据集衡量。

### Git

- 提交信息使用 Conventional Commits：`<type>(<scope>): <摘要>`，摘要可用中文。
- 提交前 pre-commit 自动运行 ruff、mypy、import-linter 和密钥扫描，禁止 `--no-verify`。
- `uv.lock` 必须提交；`.env`、`data/`、缓存不提交。

## 文档规范

- 根目录只保留 `README.md`（简介、快速开始、文档入口）和 `AGENTS.md`（项目约束），其余所有项目文档统一放在 `doc/`。
- 架构基线文档：`doc/architecture.md`；架构或关键设计变更必须同步更新该文档及其“变更记录”。
- 新建 Python 项目参考：`doc/python-project-bootstrap.md`。
- 文档文件名使用小写 kebab-case；新增或删除文档时同步更新 `doc/README.md` 索引。

## 常用命令

```bash
make install   # uv sync --locked + 安装 pre-commit 钩子
make fmt       # 格式化并自动修复
make lint      # ruff + 格式检查 + import-linter 分层检查
make type      # mypy strict
make test      # pytest
make check     # lint + type + 覆盖率测试，提交前必须通过
```

## 当前阶段

Phase 0 已完成：安装并验证 `qodercli 1.1.74`，创建平台骨架、Qoder Spike 脚本，以及配置、日志、错误码公共骨架和全部工程约束。已验证：

- 普通 headless JSON 输出可用，单次正常调用约 5～8 秒；
- `--tools ""` 下模型报告无可用工具，且未创建文件；
- 默认会加载项目 `AGENTS.md`，`--setting-sources ""` 可阻止加载；
- 输出结构为 `{"type":"result","result":"<JSON 字符串>",...}`。

尚未实现业务诊断 Agent。下一步是 Phase 1：用 Fake LLM 和假工具在 `common` 中打通最小 Agent Loop。
