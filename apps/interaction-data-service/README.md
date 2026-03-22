# Interaction Data Service

`apps/interaction-data-service` 是用于承接交互结果的独立服务。

它的目标不是接管平台现有主数据，也不是做通用数据库代理，而是专门承接：

- agent 产出的结构化业务结果
- 平台需要查询和展示的交互数据
- 结果类型注册、版本校验、类型路由

## 当前职责边界

### 负责

- 定义 agent 与平台共享的结果写入契约
- 提供结果记录的 HTTP CRUD 接口
- 维护公共登记表与业务结果表
- 根据 `record_type` 路由不同业务结果的落库与查询

### 不负责

- 用户鉴权、登录、token 签发
- 项目、成员、RBAC 管理
- LangGraph graph 执行
- assistant / catalog 主数据
- 聊天 transcript 存储

## 当前状态

当前目录已经有代码与设计文档，但整体仍处于持续收敛阶段。

当前更准确的理解是：

- 已经存在可供排查和继续演进的真实代码
- README 主要说明服务边界、目标接口和与其他应用的关系
- `docs/README.md` 与专题设计文档更适合用来查当前表、接口和后续收敛方向
- 它目前不属于根级 `README.md` 中默认联调的四个应用集合

已经明确的设计结论：

- 与现有平台共用 PostgreSQL，但只维护自己的表
- 服务间通信优先 HTTP，不做公共 MCP
- 每个业务 agent 自己定义本地 LangGraph tools
- agent 的 tool 分别调用不同的 HTTP 接口，而不是统一落库入口
- 统一的是契约、元数据和类型路由，不是所有业务表结构

当前规划中的 API 主轴是：

- `POST /api/records`
- `GET /api/records`
- `GET /api/records/{record_id}`
- `PATCH /api/records/{record_id}`
- `DELETE /api/records/{record_id}`

服务内部仍以 `record_type` 做 schema 校验、handler 分发和业务表路由。

这里说的 `/api/records*` 是目标收敛方向；如果你当前是在排查已经存在的实现与数据流，请优先参考 `docs/README.md` 中记录的 `/api/usecase-generation/*` 现状接口。

## 推荐阅读顺序

1. `README.md`
2. `docs/README.md`
3. `docs/service-design.md`
4. `docs/usecase-workflow-design.md`

## 建议目录

```text
apps/interaction-data-service/
  README.md
  docs/
  app/
    api/
    db/
    handlers/
    schemas/
    services/
  tests/
```

## 与其他应用的关系

```text
runtime-service
  -> agent local tools
    -> interaction-data-service

platform-web
  -> platform-api
    -> interaction-data-service
```

说明：

- `platform-api` 继续负责鉴权、项目上下文和聚合访问
- `interaction-data-service` 只负责结果域
- `platform-web` 仍然通过 `platform-api` 读取平台视图

## 文档目录

- `docs/README.md`：文档导航
- `docs/service-design.md`：第一版正式设计稿
- `docs/usecase-workflow-design.md`：用例生成工作流专题设计稿
