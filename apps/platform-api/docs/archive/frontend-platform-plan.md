# 前端平台化改造方案（agent-chat-ui）

## 目标

在不重写 `agent-chat-ui` 聊天核心的前提下，渐进升级为平台 UI，覆盖：租户、项目、智能体、运行时绑定、审计与统计。

## 关键约束

- 保持 LangGraph 运行时透传兼容，不破坏现有聊天调用链。
- 文档与实施说明统一中文。
- 优先复用成熟开源模式，避免重复造轮子。
- 不假设后端不存在的接口，仅消费已落地能力。

## 信息架构（IA）

一级导航建议：

- 工作台（Chat）
- 智能体管理（Agents）
- 运行时绑定（Runtime Bindings）
- 审计（Audit）
- 统计与导出（Stats / Export）
- 项目设置（Project Settings）

全局上下文固定为：`租户 -> 项目`。

## 路由与布局建议

建议从单页聊天壳，拆成「平台壳 + 聊天壳」：

```txt
src/app/
  (platform)/layout.tsx          # 平台壳：顶部上下文切换、侧边导航、统一错误边界
  (platform)/workspace/chat/page.tsx
  (platform)/workspace/agents/page.tsx
  (platform)/workspace/runtime-bindings/page.tsx
  (platform)/workspace/audit/page.tsx
  (platform)/workspace/stats/page.tsx
  (platform)/workspace/export/page.tsx
  (platform)/workspace/settings/page.tsx
  page.tsx                       # 兼容入口：重定向到 /workspace/chat
```

## 状态边界（必须解耦）

- `AppContext`：仅管理 `tenant/project/currentAgent` 与全局上下文切换。
- `ChatRuntimeState`：仅管理 `thread/stream/input`（复用现有 `StreamProvider/ThreadProvider`）。
- `DomainQueryState`：仅管理平台列表与筛选（agents/bindings/audit/stats/export）。

约束：聊天状态与管理页状态禁止互相写入，切换租户/项目时必须重置 thread 上下文，避免跨项目污染。

## API 层策略（BFF-lite）

浏览器统一调用 Next Route Handlers（同域），由前端服务端再转发后端平台 API 与运行时 API：

- 统一注入：`Authorization`、`x-tenant-id`、`x-project-id`（如果需要）
- 统一错误模型：`401/403/429/5xx`
- 统一分页头处理：`x-total-count`
- 统一重试与超时策略（仅幂等读请求）

建议文件组织：

```txt
src/lib/platform-api/
  client.ts          # fetch 封装、错误标准化、分页头解析
  tenants.ts
  projects.ts
  agents.ts
  runtime-bindings.ts
  audit.ts
  stats.ts
  types.ts
```

## 鉴权与授权落点

- 登录态由 Keycloak 负责。
- 页面级操作权限以后端 OpenFGA 判定为准。
- 前端只做 UX 处理（按钮隐藏/禁用、403 兜底提示），不在前端实现权限真规则。

## 分阶段实施

### Phase 1：平台壳 + 上下文切换 + Chat 平滑迁移

- 新增平台 layout 与 `tenant/project` 切换器。
- 保留现有聊天体验，默认落地 `workspace/chat`。
- 旧路由重定向到新路径，保持无感迁移。
- 已完成运行时上下文请求头透传：`StreamProvider` 与 `ThreadProvider` 自动注入 `x-tenant-id` / `x-project-id`。

### Phase 2：Agents 与 Runtime Bindings 管理

- 新增 Agent 列表/创建/编辑页。
- 新增 Runtime Binding 列表与环境切换。
- 与后端 `/_platform/*` 保持 1:1 对齐。
- 已完成最小读能力：`agents/runtime-bindings` 页面可基于当前 `tenant/project` 直接读取列表数据。
- 已补充分页交互（Prev/Next）与基础错误态（含 403 友好提示）。
- 已补充排序与页大小切换（agents/runtime-bindings）。

### Phase 3：审计、统计、导出与项目设置

- 新增审计日志查询、聚合统计页面。
- 新增 CSV 导出入口与下载反馈。
- 补齐项目设置页（只放已实现后端能力）。
- 已完成最小读能力：`audit/stats` 页面可读取租户审计列表与聚合统计。
- 已补充审计筛选（plane/method/path_prefix/status）与 CSV 导出入口。
- 已补充审计时间范围过滤（from_time/to_time）与页大小切换。

## 可借鉴开源项目（优先借鉴模式，不硬搬代码）

- `open-webui/open-webui`：聊天主路径 + 管理入口并存的导航组织。
- `langfuse/langfuse`：可观测与筛选分析页的信息密度与查询体验。
- `supabase/supabase`（Studio）：控制台 IA、资源侧栏、环境感知。
- `appsmithorg/appsmith`：复杂列表、表单编辑、权限控制台交互节奏。
- `ToolJet/ToolJet`：多环境管理、内部工具平台化导航分层。

## 风险与防线

- 风险：继续在单页 `page.tsx` 堆功能 -> 形成超级组件。
  - 防线：优先拆壳层与领域模块，保持聊天域独立。
- 风险：query 参数键空间冲突导致状态串扰。
  - 防线：平台域与聊天域独立 key 前缀与 URL 策略。
- 风险：前端直连后端导致 CORS 与鉴权问题反复出现。
  - 防线：统一通过 Next Route Handlers 转发。
- 风险：仅前端隐藏按钮导致“权限错觉”。
  - 防线：所有关键写操作以后端 OpenFGA 结果为准。

## 本仓库建议改造清单

- `agent-chat-ui/src/app/layout.tsx`：注入平台壳级 Provider。
- `agent-chat-ui/src/app/page.tsx`：改为重定向入口。
- `agent-chat-ui/src/providers/Stream.tsx`：保留聊天职责，不扩展平台状态。
- `agent-chat-ui/src/providers/Thread.tsx`：保留线程职责，不混入租户/项目逻辑。
- `agent-chat-ui/src/providers/client.ts`：扩展为 runtime + platform 的统一 client 门面。
- `agent-chat-ui/src/lib/platform-api/*`：新增平台 API 封装与类型。

## 验收标准

- 不破坏现有聊天路径（回归通过）。
- 切换租户/项目后无跨项目 thread 污染。
- 平台页面统一错误与分页行为。
- 403 场景前后端行为一致（前端提示 + 后端拒绝）。

## 回归检查（已落地）

- 新增 Playwright 回归用例：`agent-chat-ui/tests/platform-regression.spec.ts`。
- 覆盖项：
  - 平台壳与 chat 主路径可访问。
  - agents/runtime-bindings 页面基础数据加载。
  - 403 权限错误文案一致性。
- 当前回归结果：`10 passed`。
- 运行方式：`cd agent-chat-ui && pnpm exec playwright test tests/platform-regression.spec.ts`。

## Step 4 进展（已完成）

- `agents` 页面已补齐写操作闭环：创建、更新、删除。
- `runtime-bindings` 页面已补齐写操作闭环：upsert、删除，并支持从列表回填编辑。
- 平台 API 客户端与封装已补齐写方法：`POST/DELETE/PATCH`。
- 写流程回归覆盖已扩展并通过：create/update/delete/upsert。
- 增强回归已补齐跨租户/跨项目场景：切换作用域后的写操作目标校验与 403 权限拒绝提示一致性。

## 认证进展（Step 1 已完成）

- 已落地标准 Keycloak 浏览器登录流（OIDC Authorization Code + PKCE）。
- 新增页面与接口：
  - `auth/login`
  - `auth/callback`
  - `/api/auth/oidc/token`
- 已新增 workspace 登录/登出入口（OIDC 开关启用时可见）。

## 联动进展（后端 Step 3）

- 控制平面 API 已进入 service 分层重构，`/_platform/*` 行为契约保持不变。
- 前端当前无需改动即可继续使用现有平台 API 封装。
- 后端已完成 Step 3 第二轮领域拆分（tenant/membership/project/agent/binding/audit），前端接口消费路径保持不变。
- 后端 Step 3 已完成（含错误契约回归），前端可按原 API 继续推进 Step 4 写操作闭环。
