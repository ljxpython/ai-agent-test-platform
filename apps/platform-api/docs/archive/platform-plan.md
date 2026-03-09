# 平台规划

## 目标

在不重写 LangGraph 运行时协议的前提下，构建多租户 AI 平台能力（租户、项目、智能体管理、权限与治理）。

## 分层架构

- 运行时平面（Runtime Plane）：LangGraph 负责 `threads/runs/stream/checkpoints`。
- 控制平面（Control Plane）：当前 FastAPI 代理负责鉴权、租户、项目、策略、审计、配额。
- 数据平面（Data Plane）：PostgreSQL 保存平台核心元数据与审计数据。

## 设计原则

- 代理边界保持 LangGraph API 兼容，不破坏 `agent-chat-ui` 调用方式。
- 平台能力通过控制平面叠加，不侵入运行时协议。
- 优先使用成熟开源组件，避免重复造轮子。

## 推荐开源组件

- 身份与单点登录：Keycloak（OIDC/SAML）
- 细粒度授权：OpenFGA（关系模型授权）
- 网关与限流：Kong 或 Traefik
- 观测与指标：OpenTelemetry + Prometheus + Grafana（可选 Langfuse）

## 分阶段计划

### 第一阶段：透传基础能力（已完成）

- 全路径透明透传。
- SSE 流式透传。
- `.env` 配置化上游地址。
- 请求 ID、结构化日志、错误分类（502/504）。

### 第二阶段：身份与租户模型（进行中）

- 接入 IdP（Keycloak）。
- 增加租户感知中间件。
- 建立核心表：`users/tenants/memberships`。

### 第三阶段：项目与智能体管理（进行中）

- 增加表：`projects/agents/runtime_bindings`。
- 平台智能体 ID 与 `assistant_id/graph_id` 做映射。
- 提供项目与智能体管理 API。

### 第四阶段：权限与治理

- 接入 OpenFGA 鉴权检查。
- 增加配额、限流、审计日志。

### 第五阶段：交付与运营

- 环境发布流（dev/staging/prod）。
- 版本发布与回滚元数据。
- 成本归因看板（租户/项目/智能体）。

### 第六阶段：前端平台化改造（规划完成）

- 基于 `agent-chat-ui` 进行渐进改造，不做重写。
- 拆分平台壳与聊天壳：`租户/项目` 上下文前置到全局。
- 新增平台页面：`agents/runtime-bindings/audit/stats/export/settings`。
- 统一平台 API 封装层（BFF-lite 转发 + 错误/分页规范）。
- 已完成第一条关键链路：运行时请求自动注入 `x-tenant-id` / `x-project-id`。
- 已完成第二条关键链路：`agents/runtime-bindings/audit/stats` 页面最小读能力打通。
- 已完成第三条关键链路：平台页基础交互（分页/筛选/导出入口）与 403 友好提示。
- 已完成前端回归自动化：Playwright 用例覆盖平台壳、核心列表页与 403 提示一致性。
- 已完成第四条关键链路：排序、页大小切换、审计时间范围过滤。
- 已完成 Step 1：标准 Keycloak 浏览器登录流（OIDC Code + PKCE）。
- 详见：`docs/frontend-platform-plan.md`。

## PostgreSQL 核心表（初版）

- `tenants(id, name, slug, status, created_at)`
- `users(id, external_subject, email, created_at)`
- `memberships(id, tenant_id, user_id, role, created_at)`
- `projects(id, tenant_id, name, created_at)`
- `agents(id, project_id, name, graph_id, runtime_base_url, description, created_at)`
- `runtime_bindings(id, agent_id, environment, langgraph_assistant_id, langgraph_graph_id, runtime_base_url, created_at)`
- `audit_logs(id, tenant_id, project_id, actor_id, action, resource_type, resource_id, metadata_json, created_at)`

## 当前里程碑结论

第二至第四阶段核心后端能力已完成并可用，已进入前端平台化改造阶段。

## 当前代码落地进度（以代码为准）

- 前端完成度：约 `92%`
  - 已完成：平台壳、上下文切换、运行时头透传、agents/runtime-bindings/audit/stats 读能力、分页/筛选/导出入口、403 友好提示、Playwright 回归用例。
  - 未完成：settings/export 完整化与平台页写操作闭环。
- 后端完成度：约 `94%`
  - 已完成：透传、Keycloak、租户/项目/智能体、OpenFGA、审计、日志、CI 冒烟。
  - 已完成交付与运营收尾（CI 徽章与失败诊断、跨环境模板、RBAC/OpenFGA 回滚脚本）。
  - 未完成：`app/services` 分层下沉。

## 接下来分步执行（一次只做一步）

### Step 1（下一步立即执行）

标准 Keycloak 浏览器登录流（OIDC Code + PKCE）

- 目标：移除前端固定用户名/密码换 token 方案。
- 完成标准：
  - 前端登录跳转 Keycloak 成功。
  - 回调换 token 成功并可访问平台/API。
  - 旧自动 token 方案仅保留开发兼容开关。

状态：已完成。

### Step 2

后端交付与运维收尾

- 目标：补齐生产可运维基础。
- 完成标准：
  - CI 徽章与失败诊断文档可直接使用。
  - dev/staging/prod 配置模板齐全。
  - RBAC 与 OpenFGA 回滚脚本可执行并有文档。

状态：已完成。

### Step 3

控制平面分层重构（`app/services`）

- 目标：把业务规则从 `app/api/platform.py` 下沉到 service 层。
- 完成标准：
  - API 层仅保留参数/权限边界。
  - service 层承载核心业务流程。
  - 回归测试通过，接口行为不变。

状态：已完成。

本轮落地：
- 新增 `app/services/platform_service.py`，承接 tenant/membership/project/agent/runtime-binding/audit 业务流程。
- `app/api/platform.py` 已重构为薄路由层，仅保留参数约束、响应模型与响应头处理。
- 接口路径、状态码语义、分页头（`x-total-count`）与 OpenFGA 同步行为保持不变。

第二轮落地：
- `app/services` 已按领域拆分：`platform_common/tenant/membership/project/agent/binding/audit`。
- `app/services/platform_service.py` 保留兼容导出，避免 API 层改动扩大。
- 新增契约回归测试：`tests/test_platform_api_contract.py`（分页头、CSV 导出契约、审计响应结构）。
- 尾项补齐：新增 400/403/404 错误契约测试，确认错误状态码与 `detail` 文案稳定。
- 验证结果：`PYTHONPATH=. uv run pytest -q`（6 passed），`PYTHONPATH=. uv run python scripts/smoke_e2e.py`（PASS）。

### Step 4

前端平台页能力补齐（写操作与完整流程）

- 目标：补齐 agents/runtime-bindings/audit 的完整操作闭环。
- 完成标准：
  - 创建/更新/删除路径可用。
  - 错误态、权限态、空态一致。
  - Playwright 用例覆盖关键写流程。

状态：已完成。

本轮落地：
- 后端新增写路径：`PATCH /_platform/agents/{agent_id}`、`DELETE /_platform/agents/{agent_id}/bindings/{binding_id}`。
- 前端补齐写闭环：agents 支持 create/update/delete，runtime-bindings 支持 upsert/delete 与编辑回填。
- 回归覆盖扩展到写流程：`agent-chat-ui/tests/platform-regression.spec.ts` 新增 create/update/delete/upsert 场景。
- 验证结果：`PYTHONPATH=. uv run pytest -q`（8 passed）、`PYTHONPATH=. uv run python scripts/smoke_e2e.py`（PASS）、`cd agent-chat-ui && pnpm exec playwright test tests/platform-regression.spec.ts`（8 passed）。
- 增强回归补齐跨租户/跨项目切换场景：写操作目标项目正确性与 403 权限拒绝提示一致性（Playwright 10 passed）。
