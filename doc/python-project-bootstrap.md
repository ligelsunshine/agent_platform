# Python 项目创建规范

| 项目 | 内容 |
| --- | --- |
| 文档版本 | v0.2 |
| 更新时间 | 2026-10-19 |
| 适用范围 | 新建 Python 3.12+ 服务端 / 工具类项目 |
| 工具基线 | uv 0.13、ruff 0.17、mypy strict、pytest 8、import-linter 2、pre-commit 4 |
| 验证方式 | 第 5 节 `pyproject.toml` 与 6.6 节代码骨架已在临时项目中实测：ruff、mypy、pytest + 覆盖率门槛、import-linter 全部通过，越层导入可被拦截；其余模板未单独实测 |

本文是新建 Python 项目的“开工清单”。目标是在写第一行业务代码之前，把**项目级、全局性**的约束一次约定清楚，并尽可能交给工具自动执行，而不是靠人记忆。

## 1. 为什么要在第一天约定

越晚统一，改造成本越高。下表是成熟项目里最常见的“后补痛点”：

| 约束 | 第一天约定的成本 | 后补的典型代价 |
| --- | --- | --- |
| 包结构与导入方式 | 建几个目录 | 全量改 import、打包失败、测试路径混乱 |
| 分层依赖规则 | 一段 import-linter 配置 | 循环依赖已形成，只能大规模拆分 |
| 错误码体系 | 一个枚举 + 一个基类 | 各模块抛裸异常，API 无法稳定映射错误 |
| 日志规范 | 一个初始化函数 | 日志格式不一，无法检索、无法关联请求 |
| 配置管理 | 一个 Settings 类 | 配置散落在 `os.environ` 调用中，难以审计 |
| 并发模型 | 一句话决策 | 同步/异步混用，阻塞事件循环，难以排查 |
| 时间与 ID | 一条规则 | 存量数据时区混乱，无法安全迁移 |
| lint / 类型规则 | 配置文件 | 开启新规则时出现上千个存量告警 |
| Git 与提交规范 | `git init` | 早期历史不可追溯，无法生成变更日志 |

**原则：凡是“全局性、改了要动所有文件”的约束，都必须在第一天落地；凡是能用工具检查的约束，都不只写在文档里。**

## 2. 开工检查清单

优先级说明：

- **P0**：写第一行业务代码前必须完成，后补代价高。
- **P1**：接入第一个外部依赖、第一张表或第一次部署前完成。
- **P2**：项目进入多人协作或正式发布前完成。

| # | 优先级 | 约束项 | 落地物 | 自动化检查 |
| --- | --- | --- | --- | --- |
| 1 | P0 | Python 版本与运行时 | `.python-version`、`requires-python` | uv |
| 2 | P0 | 包结构：src 布局 + 单一顶层包 | `src/<pkg>/` | 打包、导入 |
| 3 | P0 | 导入规则：绝对导入、禁止相对导入 | ruff 配置 | ruff `TID` |
| 4 | P0 | 分层依赖规则 | import-linter 契约 | `lint-imports` |
| 5 | P0 | 依赖管理策略 | `pyproject.toml`、`uv.lock` | `uv sync --locked` |
| 6 | P0 | 代码风格与 lint 规则集 | ruff 配置 | ruff |
| 7 | P0 | 类型系统 | mypy strict + Pydantic 插件 | mypy |
| 8 | P0 | Docstring 与注释 | AGENTS.md | ruff `D` |
| 9 | P0 | 命名与语言 | AGENTS.md | ruff `N` |
| 10 | P0 | 配置管理 | `Settings` 类、`.env.example` | 启动校验 |
| 11 | P0 | 日志规范 | `configure_logging()` | ruff `T20`、`G`、`LOG` |
| 12 | P0 | 异常与错误码 | `ErrorCode`、`AppError` | ruff `BLE`、`TRY`、`B904` |
| 13 | P0 | 并发模型 | AGENTS.md 决策 | ruff `ASYNC` |
| 14 | P0 | 时间、ID、编码、路径 | AGENTS.md | ruff `DTZ`、`PTH` |
| 15 | P0 | 数据契约 | Pydantic 基类约定 | mypy + 单测 |
| 16 | P0 | 测试规范与覆盖率门槛 | pytest / coverage 配置 | `fail_under` |
| 17 | P0 | Git 仓库与提交规范 | `.gitignore`、提交约定 | pre-commit |
| 18 | P0 | 统一命令入口 | `Makefile` | `make check` |
| 19 | P0 | 提交前检查 | `.pre-commit-config.yaml` | pre-commit |
| 20 | P0 | 编辑器一致性 | `.editorconfig` | 编辑器 |
| 21 | P0 | 文档位置与 AI 协作约束 | `README.md`、`AGENTS.md`、`doc/` | 评审 |
| 22 | P1 | 安全与密钥 | 密钥规则、扫描 | gitleaks、ruff `S`、依赖审计 |
| 23 | P1 | 持久化与迁移 | 迁移目录与版本表 | 迁移测试 |
| 24 | P1 | CI | CI 配置 | 与 `make check` 一致 |
| 25 | P2 | 版本与变更日志 | SemVer、changelog | 发布流程 |
| 26 | P2 | 容器化与部署 | Dockerfile、运行手册 | 镜像构建 |

## 3. 各项约定详解

### 3.1 Python 版本与运行时

- 用 `.python-version` 固定**小版本**（如 `3.12`），uv 会自动下载对应解释器。
- 应用类项目把 `requires-python` 收窄到单一小版本，例如 `>=3.12,<3.13`，避免锁文件为未来版本求解出不同依赖；库类项目才需要声明更宽的范围并做多版本矩阵测试。
- 升级 Python 小版本是一次显式变更：同时修改 `.python-version`、`requires-python`、ruff `target-version`、mypy `python_version`，并重新跑全量检查。

### 3.2 包结构：src 布局 + 单一顶层包

```text
src/
  my_service/          # 唯一顶层包，与项目名对应
    __init__.py
    py.typed
    core/
    features/
    infra/
    app/
```

- 必须使用 `src/` 布局，避免测试意外导入工作目录中的未安装代码。
- `src/` 下**只有一个顶层包**。不要直接在 `src/` 下放 `common`、`app`、`utils` 这类通用名字：它们会与第三方包或标准库冲突，也无法打包发布。
- 项目以可安装包的方式管理（`[build-system]` 使用 `uv_build`），`uv sync` 会以可编辑模式安装，测试和脚本都通过 `import my_service` 使用代码，不再依赖 `pythonpath` 之类的路径注入。
- `__init__.py` 只放模块 docstring 和必要的公开导出，不放业务逻辑和副作用代码。
- 添加 `py.typed`，声明包内类型信息可被外部使用。

### 3.3 导入规则

- 一律使用绝对导入：`from my_service.core.errors import AppError`。
- 禁止相对导入（ruff `flake8-tidy-imports.ban-relative-imports = "all"`）。
- 仅用于类型标注的导入放入 `if TYPE_CHECKING:`（ruff `TC` 规则自动提示）。
- 通过 `banned-api` 明确禁止危险或过时的 API，例如 `pickle`。
- 禁止通配导入 `from x import *`。
- 模块名不得与标准库同名（ruff `A005`），例如日志配置模块命名为 `logging_config.py` 而不是 `logging.py`，避免遮蔽 `import logging`。

### 3.4 分层依赖规则

先确定分层，再用 import-linter 固化。通用分层如下（自上而下，只允许上层依赖下层）：

| 层 | 职责 | 允许依赖 |
| --- | --- | --- |
| `app` | 入口：API、CLI、Worker、对象组装（bootstrap） | 所有下层 |
| `features` | 具体业务能力或策略，彼此独立 | `core` |
| `infra` | 外部系统适配器：数据库、HTTP、子进程、MCP 等 | `core` |
| `core` | 领域模型、端口（接口）、错误码、通用能力 | 仅标准库与基础依赖 |

- `features` 与 `infra` 互不依赖：业务代码只依赖 `core` 中定义的端口，具体实现在 `app` 中组装注入（依赖倒置）。
- 对象在 `app/bootstrap.py` 中显式组装，不使用隐式全局单例。
- 只有被**第二个**使用方需要的能力，才提升到 `core`，避免公共层膨胀。

以 agent-platform（根包 `agent_platform`）为例的映射：`common` ≈ `core`，`agents` ≈ `features`，`infra`、`app` 同名；`evaluation` 与 `agents`、`infra` 同层，契约写法为 `app → agents | evaluation | infra → common`。

### 3.5 依赖管理

- 只用 uv：`uv add <pkg>`、`uv add --dev <pkg>`、`uv remove <pkg>`；禁止 `pip install` 进项目环境。
- `uv.lock` 必须提交；CI 和部署使用 `uv sync --locked`，锁文件与 `pyproject.toml` 不一致即失败。
- 运行时依赖写版本区间：`>=当前版本,<下一个大版本`；开发依赖可只写下限。
- 新增**运行时**依赖需要说明理由（解决什么问题、为何不用标准库），重要依赖记录为 ADR。
- 开发依赖按用途放入 `[dependency-groups]`，不放进运行时依赖。
- 定期执行依赖安全审计（见 3.17）。

### 3.6 代码风格与 lint 规则集

- ruff 同时负责格式化和 lint，不再引入 black、isort、flake8。
- 规则集**第一天就开到目标强度**。在空项目上开规则成本为零，在存量代码上开规则会产生大量告警。
- 行宽统一为 100。
- 局部豁免必须带规则码和原因：`# noqa: S603  原因：参数已白名单校验`；禁止裸 `# noqa`。
- 规则选择与含义见第 5 节模板注释。

### 3.7 类型系统

- mypy `strict = true`，并开启 `warn_unreachable`、`ignore-without-code` 等额外检查。
- 所有公开函数和方法必须完整标注参数与返回类型（ruff `ANN`）。
- 跨模块边界禁止裸 `dict` / `Any`：使用 Pydantic 模型、`dataclass` 或 `TypedDict`。
- `# type: ignore` 必须带错误码，如 `# type: ignore[arg-type]`，并说明原因。
- 使用 Pydantic 的 mypy 插件，让模型构造参数也能被类型检查。

### 3.8 Docstring 与注释

- 每个模块有一行中文摘要的模块 docstring，说明模块职责。
- 公开类、Agent、Tool、契约、异常、配置使用 Google Style 完整 docstring：首行类摘要，并包含 `Attributes` 或 `Args` 节；构造参数写在类 docstring 的 `Args` 中，`__init__` 不单独写 docstring。
- 公开方法和公开函数使用 Google Style 完整 docstring：首行摘要，并包含 `Args` 和 `Returns` 节。
- 调用方需要感知的异常写在 `Raises:` 中，说明异常类型、错误码和触发条件。
- 私有辅助方法（`_` 前缀）和模块级工具函数使用一行 docstring 说明职责。
- 首行摘要用中文一句话说明“做什么”，不写实现细节；节关键字使用英文：`Args:`、`Returns:`、`Raises:`、`Attributes:`。
- 注释解释“为什么”，不重复代码“做了什么”；禁止提交被注释掉的代码（ruff `ERA`）。
- `TODO` 必须带负责人或任务编号，例如 `TODO(ethan): ...`，不允许无主 TODO 长期存在。

### 3.9 命名与语言

- 标识符（模块、类、函数、变量、配置键、错误码、日志字段名）一律使用英文。
- 模块和函数 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE_CASE`，私有成员 `_` 前缀。
- Docstring、注释、面向用户的错误说明使用中文。
- 日志的结构化字段名使用英文 `snake_case`，便于检索；日志消息文本可以使用中文。
- 布尔变量和函数使用 `is_` / `has_` / `can_` / `should_` 前缀。

### 3.10 配置管理

- 所有配置集中在一个 `Settings` 类（pydantic-settings），启动时一次性加载和校验，校验失败直接退出。
- 业务代码不直接读 `os.environ`；配置通过构造参数注入，而不是全局导入。
- 环境变量使用统一前缀，如 `MY_SERVICE_`；嵌套配置使用 `__` 分隔。
- 优先级固定为：显式参数 > 环境变量 > `.env` > 代码默认值。
- 密钥类配置使用 `SecretStr`，`repr` 和日志中自动隐藏。
- 提交 `.env.example`（列出全部配置项与说明，不含真实值），`.env` 永不提交。
- 配置项变更时同步更新 `.env.example` 和配置说明文档。

### 3.11 日志规范

- 使用标准库 `logging`，每个模块 `logger = logging.getLogger(__name__)`。
- 只在程序入口（`app/bootstrap.py`、CLI `main`）调用一次 `configure_logging()`；库代码禁止配置根 logger。
- 禁止使用 `print` 输出运行信息（ruff `T20`）；只有 CLI 面向用户的输出例外。
- 禁止在日志调用中使用 f-string 拼接（ruff `G004`），使用 `logger.info("tool finished: %s", name)` 或 `extra={...}` 结构化字段。
- 生产环境输出 JSON 单行日志，开发环境输出可读文本，由配置切换。
- 必备字段：时间（UTC ISO 8601）、级别、logger 名、消息；请求级字段（`request_id` / `run_id` / `trace_id`）通过 `contextvars` 自动注入。
- 级别语义：
  - `ERROR`：需要人工处理的失败；
  - `WARNING`：已降级或可自动恢复的异常情况；
  - `INFO`：业务里程碑（请求开始/结束、关键状态变化）；
  - `DEBUG`：排查细节，生产默认关闭。
- 捕获异常后需要记录时使用 `logger.exception(...)` 保留堆栈。
- 日志中禁止出现密钥、令牌、密码和完整个人敏感信息；外部输入写日志前截断并脱敏。

### 3.12 异常与错误码

- 定义唯一的应用异常基类（如 `AppError`），携带 `code`、`message`、`retryable`；调用方需要感知的异常都继承它。
- 错误码用 `StrEnum` 集中定义在 `core/errors.py`，格式为 `<领域>_<原因>`，如 `CONFIG_INVALID`、`LLM_TIMEOUT`、`TOOL_ARGUMENT_INVALID`。
- 错误码一经发布不得复用、不得改变含义；废弃时保留定义并标注。
- 错误码与 HTTP 状态码 / CLI 退出码的映射只在 `app` 层做一次。
- 禁止裸 `except:` 和无理由的 `except Exception:`（ruff `BLE`、`E722`）；转换异常时使用 `raise NewError(...) from exc`（ruff `B904`）保留原因链。
- 禁止吞掉异常：捕获后必须处理、转换或重新抛出；不得吞掉 `asyncio.CancelledError`。
- 失败关闭：外部输入或模型输出校验失败时，返回明确错误，不得猜测或静默降级为“成功”。
- 错误码清单维护在 `doc/error-codes.md`。

### 3.13 并发模型

在第一天就明确一种模型，不混用。推荐服务端项目采用：

- I/O 边界（HTTP、数据库、子进程、MCP、外部 API）统一使用 `async`；纯计算逻辑保持同步函数。
- `async` 函数中禁止阻塞调用（ruff `ASYNC`）：子进程使用 `asyncio.create_subprocess_exec`，阻塞库通过 `asyncio.to_thread` 隔离。
- 每一次外部调用都必须有显式超时（`asyncio.timeout(...)` 或客户端超时参数），不存在“无限等待”。
- 并发上限显式控制（`asyncio.Semaphore`、连接池大小），不允许无界 `gather`。
- 取消必须向上传播；清理逻辑放在 `finally` 或异步上下文管理器中。
- 测试使用 `pytest-asyncio` 的 `auto` 模式。

### 3.14 时间、ID、编码与路径

- 时间：只使用带时区的 `datetime.now(UTC)`（ruff `DTZ`）；存储和传输使用 UTC ISO 8601；只在展示层转换时区；计算耗时使用 `time.monotonic()`。
- 时间和随机数在需要可测试的地方通过参数或端口注入（如 `Clock`），保证测试确定性。
- ID：对外暴露的 ID 不使用自增主键；使用带类型前缀的 UUID，如 `run_<uuid4 hex>`，便于从日志一眼识别类型。
- 编码：所有文本读写显式指定 `encoding="utf-8"`；源码文件统一 UTF-8 + LF。
- 路径：使用 `pathlib.Path`（ruff `PTH`）；不依赖当前工作目录，路径来自配置或基于 `Path(__file__)` 推导。

### 3.15 数据契约

- 进出系统边界的数据（API 请求/响应、外部系统返回、模型输出、持久化记录）全部使用 Pydantic v2 模型校验。
- 内部契约默认 `ConfigDict(extra="forbid", frozen=True)`：拒绝未知字段、不可变。
- 读取第三方返回时可以对未知字段使用 `extra="ignore"`（宽进），但对外输出必须是严格模型（严出）。
- 需要持久化或跨进程传递的结构带 `schema_version` 字段，便于兼容演进。
- 层内部的简单值对象可以使用 `@dataclass(frozen=True, slots=True)`。

### 3.16 测试规范

- 目录：`tests/unit`（镜像 `src` 结构）、`tests/integration`、按需增加 `tests/eval`；共享夹具放 `conftest.py` 或 `tests/fixtures/`。
- 单元测试禁止访问网络、真实外部进程和真实时钟睡眠；外部依赖用 Fake 实现替代，Fake 实现同样遵守端口契约。
- 需要外部依赖的测试必须打 marker（如 `integration`），默认命令可以选择性跳过。
- 测试命名表达行为：`test_<行为>_<条件>_<期望>`。
- 覆盖率使用分支覆盖并设置门槛（`fail_under`），低于门槛 CI 失败；门槛只升不降。
- pytest 开启 `--strict-markers`、`--strict-config`、`xfail_strict`，并把警告当作错误，确需忽略的第三方警告逐条声明。
- 修复缺陷必须先补一个能复现问题的回归测试。
- 测试之间不得依赖执行顺序和共享可变状态。

### 3.17 安全与密钥

- 密钥只来自环境变量或密钥管理系统；不写入代码、配置文件、测试数据和日志。
- 提交前用 gitleaks 扫描密钥；pre-commit 启用 `detect-private-key`。
- ruff 开启 `S`（bandit 规则）；局部豁免必须写明原因。
- 禁止 `eval`、`exec`、对不可信数据使用 `pickle`；子进程必须使用参数列表，禁止 `shell=True`。
- 所有外部输入视为不可信：做长度限制、类型校验和脱敏。
- 默认最小权限：数据库只读账号、工具只读、文件访问限定目录。
- 定期执行依赖漏洞审计，例如 `uvx pip-audit`，CI 中至少每周一次。

### 3.18 持久化与迁移

- 第一张表之前确定迁移方式：使用编号的只前进迁移脚本（如 `0001_init.sql`）或迁移工具，并在库中记录 `schema_version`。
- 已发布的迁移脚本不得修改，只能追加新迁移。
- 迁移在应用启动或独立命令中执行，必须有测试验证“空库 → 最新版本”可成功。
- SQLite 默认开启 `foreign_keys=ON`、WAL 模式，并设置 `busy_timeout`。
- 运行时数据库文件放在 `data/` 等被 `.gitignore` 忽略的目录。

### 3.19 Git 与提交规范

- 项目创建当天执行 `git init`，第一次提交只包含骨架和工程配置。
- 提交信息使用 Conventional Commits：`<type>(<scope>): <摘要>`，type 取 `feat`、`fix`、`refactor`、`test`、`docs`、`chore`、`perf`、`build`、`ci`；摘要可用中文。
- 分支命名：`feat/<主题>`、`fix/<主题>`、`chore/<主题>`；主分支保护，合并前 `make check` 必须通过。
- 小步提交：一个提交只做一件事，重构与行为变更分开。
- 不提交：虚拟环境、缓存、覆盖率文件、`.env`、运行数据、大文件；`uv.lock` 必须提交。

### 3.20 统一命令入口与自动化

- 用 `Makefile` 提供统一入口，本地、pre-commit 和 CI 执行**同一套命令**，避免“本地通过、CI 失败”。
- pre-commit 中的 ruff、mypy、import-linter 使用 `language: system` + `uv run`，版本与 `uv.lock` 保持一致，不在两处维护版本。
- CI 步骤：`uv sync --locked` → `make check` →（定期）依赖审计。

### 3.21 文档与 AI 协作约束

- 根目录只保留 `README.md`（项目简介、快速开始、文档入口）和 `AGENTS.md`（AI 编码助手与开发者的项目约束），其余文档统一放在 `doc/`。
- `doc/` 推荐结构：`architecture.md`、`adr/NNNN-<主题>.md`、`error-codes.md`、`configuration.md`、`changelog.md`，并用 `doc/README.md` 做索引。
- `AGENTS.md` 写“必须遵守的规则和常用命令”，保持简短；长篇设计放 `doc/` 并链接。
- 架构、配置、错误码变更必须同步更新对应文档。

### 3.22 版本与变更日志

- 使用语义化版本 SemVer；版本号只在 `pyproject.toml` 中维护，代码通过 `importlib.metadata.version()` 读取。
- 每次发布更新 `doc/changelog.md`，按 `新增 / 变更 / 修复 / 移除` 分类。

## 4. 标准目录模板

```text
my-service/
├── .editorconfig
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── AGENTS.md
├── Makefile
├── README.md
├── pyproject.toml
├── uv.lock
├── doc/
│   ├── README.md
│   ├── architecture.md
│   ├── error-codes.md
│   ├── configuration.md
│   ├── changelog.md
│   └── adr/
├── scripts/                 # 一次性或运维脚本，不被业务代码导入
├── data/                    # 运行时数据，整体被 .gitignore 忽略
├── src/
│   └── my_service/
│       ├── __init__.py
│       ├── py.typed
│       ├── core/
│       │   ├── __init__.py
│       │   ├── errors.py
│       │   ├── settings.py
│       │   └── logging_config.py
│       ├── features/
│       ├── infra/
│       └── app/
│           ├── __init__.py
│           ├── bootstrap.py
│           └── main.py
└── tests/
    ├── conftest.py
    ├── fixtures/
    ├── unit/
    └── integration/
```

## 5. `pyproject.toml` 模板

将 `my-service` / `my_service` 替换为实际项目名。`[build-system]` 以 `uv init --package` 生成的版本为准。

```toml
[project]
name = "my-service"
version = "0.1.0"
description = "一句话说明项目做什么。"
readme = "README.md"
requires-python = ">=3.12,<3.13"
dependencies = [
    "pydantic>=2.10,<3",
    "pydantic-settings>=2.7,<3",
]

[dependency-groups]
dev = [
    "import-linter>=2.1",
    "mypy>=1.14",
    "pre-commit>=4.0",
    "pytest>=8.3",
    "pytest-asyncio>=0.25",
    "pytest-cov>=6.0",
    "ruff>=0.9",
]

[build-system]
requires = ["uv_build>=0.13.1,<0.14.0"]
build-backend = "uv_build"

# ---------- ruff：格式化 + lint ----------
[tool.ruff]
target-version = "py312"
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E", "W", "F",  # pycodestyle / pyflakes 基础错误
    "I",            # import 排序
    "N",            # 命名规范
    "D",            # docstring
    "UP",           # 使用新语法
    "B",            # 常见缺陷
    "A",            # 禁止遮蔽内置名
    "C4",           # 推导式
    "DTZ",          # 禁止无时区 datetime
    "T20",          # 禁止 print
    "SIM", "RET", "PIE",  # 简化写法
    "PTH",          # 使用 pathlib
    "PT",           # pytest 风格
    "S",            # 安全（bandit）
    "BLE",          # 禁止宽泛 except
    "TRY",          # 异常写法
    "LOG", "G",     # 日志写法
    "ASYNC",        # 异步中的阻塞调用
    "TID",          # 导入限制
    "TC",           # 仅类型导入
    "ERA",          # 被注释掉的代码
    "PL",           # pylint 规则
    "C90",          # 圈复杂度
    "ANN",          # 类型标注
    "RUF",          # ruff 自有规则
]
ignore = [
    "D107",     # 构造参数写在类 docstring 的 Args 中
    "D415",     # 中文摘要不要求英文句末标点
    "RUF001", "RUF002", "RUF003",  # 允许中文全角标点
    "TRY003",   # 允许异常携带上下文消息
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"pickle".msg = "禁止反序列化不可信数据，使用 JSON + Pydantic。"

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["D", "S101", "ANN", "PLR2004", "SLF001"]
"scripts/**/*.py" = ["T20"]

[tool.ruff.format]
docstring-code-format = true

# ---------- mypy：严格类型检查 ----------
[tool.mypy]
python_version = "3.12"
strict = true
mypy_path = "src"
files = ["src", "tests"]
warn_unreachable = true
enable_error_code = ["ignore-without-code", "redundant-expr", "truthy-bool", "possibly-undefined"]
plugins = ["pydantic.mypy"]

[tool.pydantic-mypy]
init_forbid_extra = true
init_typed = true
warn_required_dynamic_aliases = true

# ---------- pytest + 覆盖率 ----------
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = ["-ra", "--strict-markers", "--strict-config", "--import-mode=importlib"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
xfail_strict = true
filterwarnings = ["error"]
markers = [
    "integration: 依赖本地外部进程或服务的集成测试",
]

[tool.coverage.run]
branch = true
source_pkgs = ["my_service"]

[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = true
exclude_also = ["if TYPE_CHECKING:", "raise NotImplementedError", "@overload"]

# ---------- import-linter：分层依赖 ----------
[tool.importlinter]
root_packages = ["my_service"]

[[tool.importlinter.contracts]]
name = "分层依赖：app -> features | infra -> core"
type = "layers"
layers = [
    "my_service.app",
    "my_service.features | my_service.infra",
    "my_service.core",
]
```

## 6. 其他文件模板

### 6.1 `Makefile`

```makefile
.PHONY: install fmt lint type test cov check

install:
	uv sync --locked
	uv run pre-commit install

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run lint-imports

type:
	uv run mypy

test:
	uv run pytest

cov:
	uv run pytest --cov --cov-report=term-missing

check: lint type cov
```

### 6.2 `.pre-commit-config.yaml`

`rev` 使用 `pre-commit autoupdate` 固定为具体版本后提交。

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: vX.Y.Z
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: detect-private-key

  - repo: https://github.com/gitleaks/gitleaks
    rev: vX.Y.Z
    hooks:
      - id: gitleaks

  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check
        entry: uv run ruff check --fix
        language: system
        types: [python]
      - id: ruff-format
        name: ruff format
        entry: uv run ruff format
        language: system
        types: [python]
      - id: mypy
        name: mypy
        entry: uv run mypy
        language: system
        pass_filenames: false
        types: [python]
      - id: import-linter
        name: import-linter
        entry: uv run lint-imports
        language: system
        pass_filenames: false
        types: [python]
```

### 6.3 `.editorconfig`

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

[*.{yml,yaml,json}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
```

### 6.4 `.gitignore`

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.import_linter_cache/
.coverage
.coverage.*
coverage.xml
htmlcov/
dist/
build/
.env
.env.*
!.env.example
data/
*.log
.DS_Store
.idea/
.vscode/
```

### 6.5 `.env.example`

```dotenv
# 运行环境：dev / test / prod
MY_SERVICE_ENV=dev
# 日志级别：DEBUG / INFO / WARNING / ERROR
MY_SERVICE_LOG_LEVEL=INFO
# 外部服务访问令牌：真实值只放在本地 .env 或密钥系统中
MY_SERVICE_API_TOKEN=
```

### 6.6 核心代码骨架

`src/my_service/core/errors.py`：

```python
"""系统错误码与异常基类。"""

from enum import StrEnum


class ErrorCode(StrEnum):
    """系统错误码，格式为 `<领域>_<原因>`，发布后不得复用或改义。"""

    CONFIG_INVALID = "CONFIG_INVALID"
    UPSTREAM_TIMEOUT = "UPSTREAM_TIMEOUT"


class AppError(Exception):
    """应用异常基类，所有调用方需要感知的异常都继承它。

    Args:
        code: 稳定的错误码。
        message: 面向调用方的错误说明，不得包含密钥或个人敏感信息。
        retryable: 调用方是否可以安全重试。

    Attributes:
        code: 稳定的错误码。
        retryable: 调用方是否可以安全重试。

    """

    def __init__(self, code: ErrorCode, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
```

`src/my_service/core/settings.py`：

```python
"""应用运行配置的加载与校验。"""

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用运行配置，只从环境变量和本地 .env 读取。

    Attributes:
        env: 运行环境。
        log_level: 日志级别。
        api_token: 外部服务访问令牌，使用 SecretStr 防止被误打印。

    """

    model_config = SettingsConfigDict(env_prefix="MY_SERVICE_", env_file=".env", frozen=True)

    env: Literal["dev", "test", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    api_token: SecretStr | None = None
```

### 6.7 `AGENTS.md` 骨架

```markdown
# <项目名> 项目约束

## 项目目标
一段话说明项目解决什么问题、不做什么。

## 架构边界
- 分层与依赖方向（与 import-linter 契约一致）。
- 对象组装位置；禁止全局单例。
- 引入新框架 / 新运行时依赖的审批规则。

## 技术栈
- Python 版本、包管理、质量工具、服务框架、存储。

## 工程规范
- Docstring 与注释、命名与语言、类型与数据契约。
- 配置、日志、错误码、并发、时间与 ID 规则（链接 doc/ 中详细说明）。

## 安全约束
- 密钥来源、禁止的 API、外部输入处理。

## 文档规范
- 文档位置与索引维护规则。

## 常用命令
make install / make fmt / make check

## 当前阶段
当前阶段目标、已完成事项、下一步。
```

## 7. 创建步骤

```bash
# 1. 创建项目与仓库
uv init --package --name my-service --python 3.12 my-service
cd my-service
git init

# 2. 按第 4 节建立目录，按第 5、6 节写入配置文件

# 3. 安装依赖
uv add "pydantic>=2.10,<3" "pydantic-settings>=2.7,<3"
uv add --dev ruff mypy pytest pytest-asyncio pytest-cov import-linter pre-commit

# 4. 安装提交前检查并固定 hook 版本
uv run pre-commit install
uv run pre-commit autoupdate

# 5. 全量检查
make check

# 6. 第一次提交
git add .
git commit -m "chore: 初始化项目骨架与工程约束"
```

## 8. 验收标准

满足以下全部条件，才算项目“开工就绪”：

- [ ] `uv sync --locked` 成功，`uv.lock` 已提交。
- [ ] `make check` 全部通过：ruff、格式检查、import-linter、mypy strict、pytest 与覆盖率门槛。
- [ ] 人为写一个越层导入，`lint-imports` 能够报错。
- [ ] 人为写一个 `print`、无时区 `datetime.now()`、裸 `except`，ruff 能够报错。
- [ ] pre-commit 已安装，提交时自动运行检查。
- [ ] `Settings`、`ErrorCode` / `AppError`、`configure_logging()` 骨架已存在并有单元测试。
- [ ] `.env.example` 与 `Settings` 字段一致；`.env` 被忽略。
- [ ] `README.md`、`AGENTS.md`、`doc/README.md`、`doc/architecture.md` 已建立。
- [ ] 仓库已初始化，第一次提交只包含骨架与工程配置。

## 9. 变更记录

| 版本 | 日期 | 变更 |
| --- | --- | --- |
| v0.1 | 2026-10-19 | 初版：开工检查清单、22 项全局约定、配置模板与验收标准 |
| v0.2 | 2026-10-19 | 补充模块名不得遮蔽标准库（A005）；日志模块模板改为 `logging_config.py`；分层映射改为 agent-platform |
