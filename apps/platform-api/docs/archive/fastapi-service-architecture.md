# FastAPI 服务启动与架构规范

## 1. 启动入口

- 服务入口模块：`main:app`
- 本地启动：`uvicorn main:app --reload --host 0.0.0.0 --port 8011`
- 生产启动：`uvicorn main:app --host 0.0.0.0 --port 8011 --workers 2`

## 2. 目录职责

- `main.py`：应用装配入口（路由注册、生命周期、全局中间件挂载）
- `app/api/`：接口层（控制面、运行面、透传/兼容）
- `app/services/`：业务编排与领域逻辑
- `app/middleware/`：认证、租户上下文、审计与请求链路
- `app/db/`：数据模型、访问层、会话与迁移相关
- `app/config.py`：环境变量与配置加载

## 3. 路由边界

### 3.1 逻辑边界（推荐）

- `/_platform/*`：控制面（治理能力）
- `/_runtime/*`：运行面（LangGraph 同构主入口，推荐长期使用）
- `/api/*`：透传/兼容入口（当前前端调用路径，可逐步收敛）

### 3.2 当前实现边界（现状）

- `app/api/frontend_passthrough.py`：`/api/{full_path:path}` 形式的 catch-all 透传机制
- `main.py`：`/{full_path:path}` 全局 catch-all 兜底透传

### 3.3 演进建议

- 保留 catch-all 作为过渡能力，但逐步将正式调用收敛到 `/_runtime/*`
- 新功能优先在 `/_runtime/*` 显式路由定义，避免长期依赖全局 catch-all

## 4. 中间件顺序

- 推荐链路：`request-id -> auth context -> tenant context -> audit logging -> router`
- 原则：先认证，后授权，再审计

## 5. 平台职责边界

- 平台负责：
  - 鉴权（调用主体身份校验）
  - 隔离（`project_id + assistant_id + thread_id` 归属校验）
  - 审计（请求、拒绝、错误、关键事件）
  - 安全上下文注入（如 `tenant_id/user_id/role/permissions`）
- 平台不负责：
  - 改写 LangGraph 核心执行语义
  - 发明与 LangGraph 冲突的参数和事件语义

## 6. 同构透传原则

- 入参同构：`assistant_id/config/context/metadata/input/command/...` 原样透传
- 查询同构：`limit/offset/sort_by/sort_order/select/...` 原样透传
- 响应同构：状态码、错误码、响应结构尽量保持一致
- 流式同构：SSE `event/data` 原样透传，不二次封装

## 7. 最小运行验收

- 健康检查：`GET /_proxy/health`
- 核心链路：
  - assistants 搜索
  - threads 创建
  - runs/wait 与 runs/stream
- 最小错误码集合：
  - `403`（无权限/隔离拒绝）
  - `409`（冲突）
  - `424`（下游依赖失败）

## 8. 文档维护约定

- 新增运行面能力时，同步更新本文件的“路由边界”和“同构透传原则”
- 新增中间件或调整顺序时，同步更新“中间件顺序”章节

## 9. 改造清单（最小版）

### 9.1 目标

- 先实现“可用且稳定”的 `/_runtime/*` 主入口。
- 保证同构透传：原样入参、原样响应、原样 SSE。

### 9.2 必做项（MVP）

- 在应用层新增显式路由：`/_runtime/{full_path:path}`。
- 该路由直接调用透传执行函数，保持 method/query/body/header 原样转发。
- 保留现有 `/api/{full_path:path}` 与 `/{full_path:path}` 作为兼容入口。
- 前端优先切换高频调用到 `/_runtime/*`：
  - `/assistants/search`
  - `/threads`
  - `/threads/search`
  - `/threads/{thread_id}/state`
  - `/threads/{thread_id}/history`
  - `/threads/{thread_id}/runs/wait`
  - `/threads/{thread_id}/runs/stream`

### 9.3 MVP 验收

- 同一请求分别直连 LangGraph 与经 `/_runtime/*` 代理，状态码一致。
- JSON 响应结构一致（不重命名字段，不二次包装错误）。
- SSE 事件流一致（`event/data` 不改写）。
- 服务与前端构建通过。

## 10. 改造清单（全量版）

### 10.1 覆盖范围（基于当前 OpenAPI）

- 上游 OpenAPI：`http://localhost:8123/openapi.json`
- 当前统计：约 `50` 个 path、`63` 个 operation。
- 全量覆盖按域推进：
  - `assistants/*`
  - `threads/*`
  - `runs/*`
  - `store/*`
  - `mcp/*`
  - `a2a/*`
  - `internal/capabilities/*`（按安全策略决定是否开放）

### 10.2 全量任务包

- 路由治理：正式调用统一收敛 `/_runtime/*`，将全局 catch-all 降级为兜底能力。
- 契约治理：新增 OpenAPI 快照文件并在 CI 做差异检测。
- 透传治理：建立路径白名单/黑名单，防止误暴露内部接口。
- 观测治理：完善 request-id、审计字段、失败分类（超时/连接/策略拒绝）。
- 兼容治理：`/api/*` 逐步退场，保留迁移窗口与告警。

### 10.3 全量验收

- 高优先级接口（assistants/threads/runs）100% 同构回归通过。
- 关键错误场景（401/403/404/409/424/502/504）返回语义稳定。
- 与前端、其他 LangGraph 产品完成联调，确认无需额外字段适配层。

## 11. 实施规划（阶段化）

- Phase 1（本周）：上线 `/_runtime/*` + 前端高频接口切换 + MVP 回归。
- Phase 2（下周）：补齐剩余 OpenAPI 端点同构验证 + CI 契约校验。
- Phase 3（稳定期）：缩减 `/api/*` 兼容面，最终只保留必要兼容入口。
