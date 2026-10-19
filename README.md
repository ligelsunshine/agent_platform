# agent-platform

Agent 研发平台：在 `common` / `infra` 中沉淀 Agent 公共框架与基础设施能力，在 `agents/` 下承载多个具体 Agent（首个为问题定位 Agent `incident_agent`），由 `app` 统一对外提供 API。

## 快速开始

```bash
make install   # 安装依赖与 pre-commit 钩子
make check     # lint + 分层检查 + 类型检查 + 测试与覆盖率
```

## 目录

```text
src/agent_platform/
├── common/      # Agent 公共框架
├── infra/       # 通用基础设施适配器
├── evaluation/  # 通用评测框架
├── agents/      # 具体 Agent，彼此独立
│   └── incident_agent/
└── app/         # 对外 API 与对象组装
```

## 文档

- 项目约束：[AGENTS.md](AGENTS.md)
- 文档索引：[doc/README.md](doc/README.md)
- 架构设计：[doc/architecture.md](doc/architecture.md)
