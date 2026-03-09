# 执行状态

## 2026-03 自建认证重构状态（最新）

- 当前以 `docs/self-hosted-auth-rbac-mvp.md` 为唯一执行基线。
- Keycloak/OpenFGA 兼容链路已停止维护并开始物理删除。
- 旧 `/_platform/*` 与 legacy service 目录已进入清理阶段。
- CI 冒烟工作流 `.github/workflows/smoke-e2e.yml` 已移除（按当前重构策略）。

## 当前焦点

前后端收尾开发（Step 4 已完成）

## 总体进度

- 阶段1（透传基础）：100%
- 阶段2（身份与租户）：100%
- 阶段3（项目/智能体/审计/OpenFGA）：100%
- 阶段4（高级治理与自动化测试）：80%
- 阶段5（前端平台化改造）：100%

## 状态看板

- [x] FastAPI 全路径透明透传
- [x] SSE 流式透传
- [x] `.env` 上游配置
- [x] 请求 ID 透传与结构化日志
- [x] 上游超时/传输错误分类（504/502）
- [x] 基础契约冒烟验证（`/_proxy/health`、`/info`）

## 暂缓项

- [x] Keycloak 对接（JWT 验签）
- [x] OpenFGA 集成

## 第二阶段已完成项（本轮）

1. 新增数据库模型骨架：`tenants/users/memberships`。
2. 新增数据库会话与建表入口（可通过开关控制启用）。
3. 新增租户上下文中间件骨架（`x-tenant-id` / `x-user-id`）。
4. 完成中间件开关验证：`REQUIRE_TENANT_CONTEXT=true` 时无租户头返回 `400`。
5. 新增 Keycloak JWT 验签中间件骨架（JWKS、issuer/audience、401/502 映射）。
6. 完成 Keycloak 本地联调并跑通 `agent-proxy` audience。
7. 新增 `sub -> users.external_subject` 自动入库。
8. 新增 Alembic 迁移框架与首版迁移（`20260228_0001`）。
9. 新增租户成员校验：有 `x-tenant-id` 且无 membership 时返回 `403`。
10. 新增平台管理 API：创建租户、查询租户、管理成员（owner/admin）。
11. 新增项目与智能体管理 API：projects/agents/runtime_bindings。
12. 新增角色权限矩阵：`owner/admin` 写、`member` 只读。
13. 新增 Alembic 迁移 `20260228_0002`：runtime_bindings 表与索引。
14. 新增审计日志模型与迁移 `20260228_0003`：`audit_logs`。
15. 新增统一请求审计：平台 API 与透传请求均写入 `audit_logs`。
16. 新增审计查询 API：`GET /_platform/tenants/{tenant_ref}/audit-logs`（owner/admin）。
17. 列表接口统一分页/排序：`limit/offset/sort_by/sort_order` + `x-total-count`。
18. 新增透传细粒度策略开关：`RUNTIME_ROLE_ENFORCEMENT_ENABLED`。
19. 新增 OpenFGA 集成骨架：模型文件、初始化脚本、tuple 同步、透传 check 接入。
20. 新增 OpenFGA tuple 回收：删除成员/项目/智能体时同步删除关系。
21. 新增透传 `x-agent-id` 资源映射校验与 agent 级 OpenFGA check。
22. 新增端到端自动化冒烟脚本：`scripts/smoke_e2e.py`。
23. 新增 GitHub Actions CI：`.github/workflows/smoke-e2e.yml`。
24. 新增审计聚合统计 API：`GET /_platform/tenants/{tenant_ref}/audit-logs/stats`。
25. 新增审计导出 API：`GET /_platform/tenants/{tenant_ref}/audit-logs/export`（CSV）。
26. 新增 OpenFGA 模型版本管理流程：版本化模型目录与迁移脚本。

## 前端平台化调研完成项（本轮）

1. 完成 `agent-chat-ui` 现有架构盘点：`layout/page/providers(client,stream,thread)` 边界识别。
2. 明确改造原则：保留聊天核心，平台能力外置到 app shell 与平台页面。
3. 输出 IA 与页面蓝图：`chat/agents/runtime-bindings/audit/stats/export/settings`。
4. 明确状态边界：`AppContext` 与 `ChatRuntimeState`、`DomainQueryState` 解耦。
5. 明确 API 策略：前端统一走 Next Route Handlers（BFF-lite），统一错误与分页语义。
6. 明确鉴权策略：Keycloak 登录 + OpenFGA 后端判定，前端仅做 UX 反馈。
7. 产出实施文档：`docs/frontend-platform-plan.md`。

## 前端平台化已落地项（Phase 1，本轮）

1. 新增 `workspace` 路由壳：`/workspace/layout` + 顶部导航。
2. 旧入口 `src/app/page.tsx` 改为重定向到 `/workspace/chat`。
3. 聊天页迁移到 `src/app/workspace/chat/page.tsx`，保留原 `ThreadProvider/StreamProvider/ArtifactProvider` 调用链。
4. 新增租户/项目上下文 Provider：`src/providers/WorkspaceContext.tsx`（query 参数持久化）。
5. 新增范围切换组件：`src/components/platform/scope-switcher.tsx`。
6. 新增最小平台 API 封装：`src/lib/platform-api/{client,tenants,projects,types}.ts`。
7. 新增占位页面：`workspace/agents`、`workspace/runtime-bindings`、`workspace/audit`、`workspace/stats`。
8. 构建验证通过：`pnpm build`（仅存在既有 lint warnings，无新增阻断错误）。
9. 新增前后端日志落盘系统：`logs/backend.log`、`logs/frontend-server.log`、`logs/frontend-client.log`。
10. 新增日志文档：`docs/logging-system.md`。
11. 已将运行时透传实现从 `main.py` 抽离到 `app/api/proxy/runtime_passthrough.py`（入口路由保持不变）。
12. 已完成运行时上下文头透传：`StreamProvider/ThreadProvider` 自动注入 `x-tenant-id` / `x-project-id`。
13. 已完成平台页最小读能力：`agents/runtime-bindings/audit/stats` 页面接入真实列表查询。
14. `platform-api` 已补齐模块：`agents/runtime-bindings/audit/stats`。
15. 已完成平台页基础交互：分页（agents/runtime-bindings/audit）、筛选（audit）、导出入口（audit CSV）。
16. 已完成平台页错误态统一：新增 `platform-api/errors.ts`，403 提示一致。
17. 已新增 Playwright 回归用例：`tests/platform-regression.spec.ts`（4 条通过）。
18. 已完成平台页排序与页大小切换：`agents/runtime-bindings`。
19. 已完成审计时间范围过滤：`from_time/to_time`。
20. 已完成 Step 1：前端标准 OIDC 登录流（Code + PKCE）与回调换 token。
21. 已完成 Step 2：CI 徽章与失败诊断文档。
22. 已完成 Step 2：跨环境模板（dev/staging/prod）。
23. 已完成 Step 2：RBAC membership 回滚脚本与 OpenFGA model 回滚脚本。

## 下一步

1. 持续补充端到端回归覆盖（跨租户/跨项目切换下的写操作与权限拒绝）。
2. 进入后续体验优化与运维治理增量迭代。

## Step 4 本轮完成项

1. 后端新增 agent 更新接口：`PATCH /_platform/agents/{agent_id}`。
2. 后端新增 runtime binding 删除接口：`DELETE /_platform/agents/{agent_id}/bindings/{binding_id}`。
3. 前端 `agents` 页面已支持 create/update/delete 全流程。
4. 前端 `runtime-bindings` 页面已支持 upsert/delete 与编辑回填。
5. 前端平台 API 客户端新增 `PATCH` 能力，并补齐写操作封装。
6. 后端契约测试新增更新/删除路径断言，`PYTHONPATH=. uv run pytest -q` 结果 `8 passed`。
7. 后端冒烟验证通过：`PYTHONPATH=. uv run python scripts/smoke_e2e.py`（PASS）。
8. 前端构建验证通过：`cd agent-chat-ui && pnpm build`。
9. 前端 Playwright 回归扩展并通过：`cd agent-chat-ui && pnpm exec playwright test tests/platform-regression.spec.ts`（8 passed）。
10. Step 4 增强回归已落地：新增跨租户/跨项目切换下写操作目标校验与 403 权限拒绝场景。
11. 增强回归验证通过：`cd agent-chat-ui && pnpm exec playwright test tests/platform-regression.spec.ts`（10 passed）。

## Step 3 本轮完成项

1. 新增 service 层文件：`app/services/platform_service.py`。
2. 将平台核心业务流程从 `app/api/platform.py` 下沉到 service 层（tenant/membership/project/agent/runtime bindings/audit）。
3. `app/api/platform.py` 改为薄路由，保留参数校验、响应模型和 `x-total-count` 头处理。
4. 保持错误语义与行为契约不变（400/401/403/404/409/503）。
5. 验证通过：`python3 -m py_compile app/api/platform.py app/services/platform_service.py`（第一轮）。
6. 已完成第二轮拆分：新增 `app/services/platform_common.py`、`tenant_service.py`、`membership_service.py`、`project_service.py`、`agent_service.py`、`binding_service.py`、`audit_service.py`。
7. `app/services/platform_service.py` 改为兼容导出层，API 路由调用保持不变。
8. 新增契约回归测试：`tests/test_platform_api_contract.py`。
9. 新一轮验证通过：`PYTHONPATH=. uv run pytest -q`（3 passed）、`PYTHONPATH=. uv run python scripts/smoke_e2e.py`（PASS）。
10. 已补齐 Step 3 尾项：新增 400/403/404 契约断言，验证错误码与 `detail` 文案稳定。
11. 尾项验证通过：`PYTHONPATH=. uv run pytest -q`（6 passed）、`PYTHONPATH=. uv run python scripts/smoke_e2e.py`（PASS）。

## 步骤执行规则

- 每次只做一个 Step，完成后再进入下一个。
- 每个 Step 完成必须满足：代码落地 + 构建/测试验证 + 文档更新。
