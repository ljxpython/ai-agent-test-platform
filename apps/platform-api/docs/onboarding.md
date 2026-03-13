# 开发者上手路径

这份文档只解决一个问题：新开发者第一次进入 `apps/platform-api`，应该按什么顺序读、改哪里、怎么避免走错方向。

## 1. 先建立正确心智模型

当前 `platform-api` 不是旧版 transparent proxy，而是：

- 平台管理面后端
- LangGraph SDK 风格网关
- 平台数据库与自建认证/RBAC 服务

如果你需要确认当前真实边界，请先读：`docs/current-architecture.md`。

## 2. 建议阅读顺序

### 第一天必读

1. `../README.md`
2. `docs/current-architecture.md`
3. `docs/local-dev.md`
4. `docs/testing.md`

### 按需深读

- 改 Assistant 管理：`docs/assistant-management-design.md`
- 改 runtime catalog：`docs/runtime-object-catalog-design.md`
- 改数据库运维：`docs/postgres-operations.md`
- 遇到常见故障：`docs/error-playbook.md`

## 3. 当前模块地图

```text
app/
  api/
    management/        # 管理面 API
    langgraph/         # LangGraph SDK 风格网关 API
  bootstrap/
    lifespan.py        # 启动/关闭、DB、bootstrap admin
  db/
    models.py          # SQLAlchemy 模型
    access.py          # 数据访问函数
    init_db.py         # 核心表初始化
    session.py         # engine/session 工厂
  middleware/
    auth_context.py    # 当前用户上下文
    audit_log.py       # 审计中间件
    request_context.py # request id / trace 上下文
  services/
    langgraph_sdk/     # LangGraph client 与 scope guard
    runtime_catalog_sync.py
    graph_parameter_schema.py
```

## 4. 你要改什么，就去哪里

### 新增/修改管理面接口

- 路由：`app/api/management/`
- 数据访问：`app/db/access.py`
- 模型：`app/db/models.py`
- 复杂业务逻辑：优先下沉到 `app/services/`

### 新增/修改 LangGraph 代理能力

- 路由：`app/api/langgraph/`
- 上游 client / project scope：`app/services/langgraph_sdk/`

### 新增 runtime catalog / schema /治理逻辑

- `app/services/runtime_catalog_sync.py`
- `app/services/graph_parameter_schema.py`
- 如需持久化，配合 `app/db/models.py` / `app/db/access.py`

### 修改鉴权 / 项目边界 / 审计

- `app/middleware/auth_context.py`
- `app/services/langgraph_sdk/scope_guard.py`
- `app/middleware/audit_log.py`
- `app/api/management/common.py`

## 5. 当前最重要的约定

- 管理面统一走 `/_management/*`
- LangGraph 网关统一走 `/api/langgraph/*`
- 项目边界统一依赖 `x-project-id`
- 当前启动链路以 `app/factory.py` + `app/bootstrap/lifespan.py` 为准
- 当前 DB 初始化默认依赖 `PLATFORM_DB_AUTO_CREATE` + `create_core_tables()`
- 文档里凡是提到 retired passthrough、Keycloak/OpenFGA、`agent-chat-ui` 旧结构的内容，都不再作为当前开发基线

## 6. 最小工作流

1. `cp .env.example .env`
2. 准备 PostgreSQL
3. 启动 `uv run uvicorn main:app --reload --port 2024`
4. 跑最小测试：`PYTHONPATH=. uv run pytest tests/test_self_hosted_auth_basics.py`
5. 如果改了真实 LangGraph 集成，再按需跑 integration test
