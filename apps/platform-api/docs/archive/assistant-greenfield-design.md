# Assistant 绿地架构草案（评审稿）

## 目标与范围

- 本文定义 Assistant 绿地方案，直接对齐 LangGraph 官方主链路：`assistant -> thread -> run`。
- 本次只覆盖文档设计，不做兼容历史行为的迁移实现。
- 目标是消除“双重 assistant 语义”（平台 profile vs 运行时 target）带来的复杂度。

## 术语统一（Assistant vs Agent）

- 本方案中 `assistant` 等同于业务上的“智能体实例”（过去口语中的 agent）。
- 为避免双语义，文档、接口、前端文案统一使用 `assistant`，不再新增 `agent` 术语。
- 若历史代码仍出现 `agent` 命名，视为技术债逐步清理，不作为新设计词汇。

## 分层与边界

### 控制面（Control Plane）

- 职责：管理租户、项目、Assistant 元数据、权限策略、审计日志。
- 数据：保存平台主数据，不保存运行时 thread/run 实体。
- API 前缀：`/_platform/*`，只暴露平台治理能力。

### 运行面（Runtime Plane）

- 职责：承接聊天执行链路，透传 LangGraph 运行时接口。
- 对齐对象：`threads`、`runs`、`stream`。
- 约束：运行面不再接受平台自定义 assistant 绑定语义，执行时只使用控制面已落地的 assistant 关系。

### 面间契约

- 控制面在创建 Assistant 时，即完成 LangGraph Assistant 创建并保存映射。
- 运行面只消费“项目内可用 assistant_id”，不再要求前端手工输入运行时 langgraph ID。

## 领域模型（Domain Model）

### 核心实体

- `Tenant`：租户边界。
- `Project`：租户内隔离单元，Assistant、Thread 访问均以项目为最小授权域。
- `Assistant`：项目内唯一业务对象，包含平台元数据与 `langgraph_assistant_id`。
- `ThreadRef`：运行时 thread 的平台侧引用，至少记录 `project_id + assistant_id + thread_id` 关联。

### 强约束

- `Assistant.project_id` 必填且不可跨项目复用。
- 任意 `thread/run` 请求必须可回溯到单一 `project_id`。
- 明确禁止跨项目共享 Assistant，不提供共享开关。

## API 边界（实现导向）

### Chat 调用路径决策（必须拍板）

- 推荐主路径：`前端 -> 平台 Runtime Plane -> LangGraph API`。
- 不建议浏览器长期直连 LangGraph 作为主链路，否则项目级隔离、审计、统一鉴权会变弱。
- 本地调试可保留直连开关，但生产与联调默认走平台 Runtime Plane。

### 控制面 API

- `POST /_platform/assistants`
  - 输入：`project_id`、`name`、可选描述。
  - 动作：
    1) 权限校验（项目写权限）。
    2) 调用 LangGraph SDK 创建 assistant。
    3) 在平台库落 Assistant 记录（含 `langgraph_assistant_id`）。
  - 输出：平台 assistant 对象，包含运行时映射字段。
- `GET /_platform/projects/{project_id}/assistants`
  - 返回项目内 assistant 列表，不返回其他项目数据。
- `DELETE /_platform/assistants/{assistant_id}`
  - 动作：先删运行时 assistant，再删平台记录；失败时按回滚策略处理。

### 运行面 API

- 继续透传 LangGraph 官方线程与运行接口。
- 入口必须携带项目上下文（头或会话上下文），服务端据此校验 assistant 归属。
- 对不属于当前项目的 assistant/thread 一律返回 `403`。

## LangGraph 同构入参能力（1:1 契约）

### 设计目标

- 运行面优先提供与 LangGraph 一致的 API 契约（路径语义、请求字段、响应结构）。
- 前端可按 LangGraph 官方对象模型直接调用，减少平台适配层与字段映射逻辑。

### 契约原则

- 请求参数同构：`assistant_id/config/context/metadata/input/command/...` 原样透传，不做字段重命名。
- 查询参数同构：`limit/offset/sort_by/sort_order/select/...` 原样透传。
- 返回结构同构：状态码、错误码、响应体结构尽量与 LangGraph 保持一致。
- 流式同构：SSE `event/data` 原样透传，不二次包装事件语义。

### 平台处理边界

- 平台允许做“边界治理”，但不改变 LangGraph 业务语义：
  - 鉴权（调用主体身份校验）
  - 项目隔离（`project_id + assistant_id + thread_id` 归属校验）
  - 审计（请求链路与拒绝事件记录）
  - 安全注入（可信上下文如 `tenant_id/user_id/role/permissions`）
- 平台不应做“业务改写”：不改写核心字段含义，不发明与 LangGraph 冲突的新执行语义。

### 路由策略建议

- `/_runtime/*`：作为 LangGraph 同构主入口（推荐给正式调用）。
- `/api/*`：可保留为前端友好兼容层，逐步收敛为薄封装或迁移到同构入口。

### SDK 路由组织（已确认）

- 对外前缀统一为：`/api/langgraph/*`。
- 代码实现按域拆分，不放在单一大文件：
  - `app/api/langgraph/assistants.py`
  - `app/api/langgraph/threads.py`
  - `app/api/langgraph/runs.py`
  - `app/api/langgraph/store.py`（后续按需）
- 聚合入口：`app/api/langgraph/__init__.py` 导出统一 router。
- 装配方式：`app/factory.py` 仅 `include_router(langgraph_router)`。
- 迁移策略：
  - 已由 SDK 实现的端点优先走 SDK handler；
  - 未实现端点继续走现有 passthrough 兼容路径，分阶段替换。

### 迁移原则（先后端后前端）

- 迁移过程中，前端先保持当前调用方式不变，避免在后端未稳定前引入双侧变更风险。
- 后端先完成同构能力：请求/响应/SSE 与 LangGraph 保持 1:1，并补齐隔离校验与错误语义。
- 待后端能力稳定且验证通过后，再统一切换前端到目标入口（如 `/api/langgraph/*`）。
- 旧入口按兼容策略分阶段下线，不做一次性切断。

## LangGraph Assistant 参数调研（来自本地 OpenAPI）

> 来源：`http://localhost:8123/openapi.json`（对应 `http://localhost:8123/docs#tag/assistants`）

### 创建：`POST /assistants`

- 必填：`graph_id`
- 可选：`assistant_id`、`config`、`context`、`metadata`、`if_exists`、`name`、`description`
- `if_exists`：`raise | do_nothing`（默认 `raise`）

### 更新：`PATCH /assistants/{assistant_id}`

- 可选：`graph_id`、`config`、`context`、`metadata`、`name`、`description`

### 查询/统计

- `POST /assistants/search`：`metadata`、`graph_id`、`name`、`limit`、`offset`、`sort_by`、`sort_order`、`select`
- `POST /assistants/count`：`metadata`、`graph_id`、`name`

## 平台字段到 LangGraph 参数映射建议（v0）

- 平台 `assistant.name` -> LangGraph `name`
- 平台 `assistant.description` -> LangGraph `description`
- 平台 `assistant.template/config` -> LangGraph `config`
- 平台 `assistant.context` -> LangGraph `context`
- 平台扩展标签（`project_id`、`tenant_id`、`environment`）-> LangGraph `metadata`
- 平台内部主键不直接暴露为 LangGraph 主键；若需要幂等，优先使用请求级幂等键或受控 `assistant_id` 策略

## 动态传参能力设计（Assistant + Run）

### 目标

- 支持“创建时静态配置 + 运行时动态覆盖”两层参数模型。
- 在不破坏项目隔离与鉴权边界前提下，让 Agent 能按请求动态调整行为。

### 两层参数模型

- Assistant 层（静态）：`POST /assistants` 的 `config/context/metadata`
  - 用于长期默认值（如默认模型、默认 system_prompt、默认工具策略）。
- Run 层（动态）：`POST /threads/{thread_id}/runs` 或 `.../runs/stream` 的 `config/context/metadata`
  - 用于单次覆盖（如本次 `temperature`、本次 `model_id`、本次工具开关）。

### 合并优先级（建议）

1. 平台强制安全上下文（最高优先级，不可覆盖）：`tenant_id/user_id/role/permissions`
2. Run 请求动态参数（单次）
3. Assistant 静态参数（默认）
4. 服务端环境默认值（最低）

### 安全白名单（建议）

- 允许前端动态覆盖：
  - `model_id`
  - `system_prompt`
  - `temperature`
  - `max_tokens`
  - `top_p`
  - `enable_local_tools`
  - `local_tools`
  - `enable_local_mcp`
  - `mcp_servers`
- 禁止前端覆盖（仅可信后端注入）：
  - `tenant_id`
  - `user_id`
  - `role`
  - `permissions`
  - 其他鉴权/组织边界字段

### 控制面契约扩展建议

- `POST /_platform/projects/{project_id}/assistants` 增加可选字段：
  - `default_config`（映射 LangGraph `config`）
  - `default_context`（映射 LangGraph `context`）
  - `default_metadata`（映射 LangGraph `metadata`）

### 运行面契约扩展建议

- `POST /_runtime/projects/{project_id}/assistants/{assistant_id}/threads/{thread_id}/runs`
  - 增加可选字段：`runtime_config/runtime_context/runtime_metadata`
  - 平台做白名单过滤后再透传到 LangGraph `config/context/metadata`

### 请求示例（运行时动态覆盖）

```json
{
  "input": {
    "messages": [
      {"role": "user", "content": "请给我一版发布计划"}
    ]
  },
  "runtime_config": {
    "temperature": 0.2,
    "max_tokens": 1200
  },
  "runtime_context": {
    "model_id": "openai/gpt-4.1",
    "system_prompt": "你是资深发布经理"
  },
  "runtime_metadata": {
    "trace_tag": "release-plan"
  }
}
```

### 与当前 graph_src_v2 对齐说明

- 现有 `assistant_agent` 已支持从 `configurable/context` 读取并解析动态参数。
- 因此新增能力主要是平台层契约与白名单治理，不需要改变 LangGraph 官方能力模型。

## API 契约草案（v1）

### 1) 创建 Assistant（控制面）

- `POST /_platform/projects/{project_id}/assistants`
- Header：`Idempotency-Key: <uuid>`（推荐）

```json
{
  "name": "customer-support",
  "description": "客服智能体",
  "graph_id": "assistant",
  "config": {"model": "gpt-4.1"},
  "context": {"locale": "zh-CN"},
  "environment": "dev"
}
```

```json
{
  "id": "asst_pf_01",
  "project_id": "prj_01",
  "name": "customer-support",
  "description": "客服智能体",
  "status": "active",
  "environment": "dev",
  "langgraph_assistant_id": "a5c2...",
  "created_at": "2026-03-03T13:00:00Z"
}
```

### 2) 列表与详情（控制面）

- `GET /_platform/projects/{project_id}/assistants`
- `GET /_platform/assistants/{assistant_id}`

### 3) 更新 Assistant（控制面）

- `PATCH /_platform/assistants/{assistant_id}`

```json
{
  "name": "customer-support-v2",
  "description": "客服智能体升级版",
  "config": {"temperature": 0.2},
  "context": {"locale": "zh-CN"}
}
```

### 4) 删除 Assistant（控制面）

- `DELETE /_platform/assistants/{assistant_id}`
- 返回：`202 Accepted`（异步删除）或 `200 OK`（同步完成）

### 5) 发起 Run（运行面）

- `POST /_runtime/projects/{project_id}/assistants/{assistant_id}/threads/{thread_id}/runs`

```json
{
  "input": {
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  },
  "stream_mode": "messages"
}
```

### 6) 错误码约定（最小集合）

- `403 assistant_project_denied`：assistant 不属于当前项目
- `409 assistant_name_conflict`：同项目命名冲突
- `409 assistant_not_ready`：assistant 未进入 `active`
- `424 assistant_provision_failed`：底层 LangGraph 创建失败

## 生命周期与状态机

### Assistant 状态

- `creating`：控制面已接收创建请求，尚未完成双写。
- `active`：LangGraph 与平台记录均成功，允许发起 run。
- `deleting`：进入删除流程，禁止新 run。
- `failed`：创建或删除流程失败，等待补偿任务。

### 状态迁移规则

- `creating -> active`：LangGraph 创建成功 + 平台写库成功。
- `creating -> failed`：任一步骤失败。
- `active -> deleting`：收到删除请求并通过权限校验。
- `deleting -> terminal(removed)`：双端删除成功。
- `deleting -> failed`：任一步骤失败，进入补偿。

## 回滚与幂等

### 创建流程

- 幂等键：`project_id + normalized_name`（或请求幂等键 header）。
- 若 LangGraph 创建成功、平台写库失败：
  - 立即触发补偿删除 LangGraph assistant。
  - 补偿失败则落 `failed` 并进入异步重试队列。

### 删除流程

- 删除接口要求幂等：重复删除返回成功态（资源不存在视为成功）。
- 若平台已删、LangGraph 未删：记录墓碑并持续重试运行时删除。
- 若 LangGraph 已删、平台未删：继续清理平台记录，不回滚运行时删除。

## 权限模型

- 读：项目成员可读项目内 assistants。
- 写：`owner/admin` 可创建、更新、删除 assistants。
- 运行时执行：
  - 校验调用者具备项目访问权限。
  - 校验 `assistant_id` 与 `thread_id` 均归属当前项目。
- 审计：记录 assistant 创建/删除、run 发起、拒绝访问事件。

## 前端改造点（简化）

- Assistant 创建页不再暴露“手工填写 langgraph_assistant_id / graph_id / runtime 绑定 ID”输入框。
- 表单最小化为业务必填字段（名称、描述等），运行时映射由后端创建时自动完成。
- Chat 页选择 assistant 后直接进入 thread/run，不再出现“手工运行时绑定”步骤。
- 项目切换时只加载当前项目 assistants，清空其他项目缓存，避免跨项目残留。

## 移除的遗留逻辑

- 移除“平台 assistant profile 与 LangGraph assistant target 分离维护”的双轨模型。
- 移除 environment-mapping 中手工维护 `langgraph_assistant_id` 的主路径依赖。
- 移除前端初始化页对运行时 ID 的人工录入要求。
- 移除为兼容旧绑定模型而存在的分支判断与兜底回填逻辑。

## 实施顺序建议

1. 控制面先落地“创建即绑定”接口与状态字段。
2. 前端改为最小化 Assistant 表单并下线手工绑定输入。
3. 运行面加严项目归属校验（assistant/thread 双校验）。
4. 清理遗留字段与无效分支，补齐回归测试与审计事件断言。

## 待拍板决策（3项）

1. Assistant 命名冲突策略：同项目下“重名拒绝”还是“重名允许+唯一后缀”。
2. 创建失败补偿机制：同步重试上限后转异步队列，还是全异步 Saga。
3. 删除语义：是否保留短期墓碑（用于审计与幂等查询）及保留时长。

## 实施分步计划（已确认）

### 第 1 步：后端数据模型收敛（Assistant 单语义）

- 将现有 `Agent` 语义收敛为平台 Assistant 单语义对象。
- Assistant 主记录中保留运行时主键映射（`langgraph_assistant_id`）。
- 标记并准备下线 `RuntimeBinding` 链路，不再作为前端运行时必需依赖。

### 第 2 步：控制面接口改造（create 即绑定）

- `POST /_platform/assistants` 创建时直接调用 LangGraph SDK `assistants.create`。
- 保存平台 assistant 与 `langgraph_assistant_id` 绑定关系。
- `list/get/update/delete` 全部围绕单一 assistant 语义。

### 第 3 步：运行面强校验接入

- 在 `/api/langgraph/*` 执行前做归属校验：`project_id + assistant_id + thread_id`。
- 跨项目或不匹配请求统一返回 `403`。
- 保持请求/响应/SSE 同构，不改写 LangGraph 字段语义。

### 第 4 步：前端切换为单一 assistant 语义

- `WorkspaceContext`、`Stream`、agents 页面只保留 `assistantId`。
- 移除 `assistant profile -> environment mapping -> langgraph_assistant_id` 自动映射链。
- 运行时调用统一走平台 `/api/langgraph/*`。

### 第 5 步：清理与下线旧逻辑

- 下线 environment-mappings 相关页面/API/类型。
- 移除历史 `graph_id/runtime_base_url` 作为前端运行时输入语义。
- 保留必要迁移窗口后，移除兼容分支。

## Assistant 接口收敛策略（避免多套接口长期并存）

- 目标长期形态只保留两层：
  - 控制面：`/_platform/assistants*`（项目内创建/管理/权限/审计）
  - 同构运行面：`/api/langgraph/assistants*`（LangGraph 1:1 契约）
- 旧兼容层 `/api/assistants*` 仅作迁移过渡，不再新增能力。

### 分阶段收敛

1. 冻结旧兼容接口：`/api/assistants*` 只保留兼容，不再扩展。
2. 替代能力就绪：`/_platform/*` 覆盖管理场景，`/api/langgraph/*` 覆盖同构场景。
3. 前端全面切换：管理调用 `/_platform/*`，运行调用 `/api/langgraph/*`。
4. 下线旧兼容层：先返回弃用信号，再删除路由与实现。

## MVP 落地清单（已确认）

### P0（必须）

- 统一语义：仅保留 `assistant` 术语，不再新增 `agent` 命名。
- 创建即绑定：控制面创建 assistant 时同步调用 LangGraph `POST /assistants` 并保存 `langgraph_assistant_id`。
- 运行面强校验：对 `project_id + assistant_id + thread_id` 做归属校验，不归属返回 `403`。
- 动态参数白名单：仅允许覆盖模型与推理参数，禁止覆盖身份与组织边界字段。

### P1（强烈建议）

- 前端最小化：下线手工 runtime binding 输入，路径收敛为“选项目 -> 创建/选 assistant -> 聊天”。
- 幂等与补偿：创建支持 `Idempotency-Key`；创建/删除失败进入补偿队列。
- 错误码统一：至少覆盖 `assistant_project_denied`、`assistant_not_ready`、`assistant_name_conflict`、`assistant_provision_failed`。

### MVP 验收标准

- 新建 assistant 后无需手工绑定即可发起 run。
- 跨项目 assistant/thread 调用被拒绝且有审计记录。
- 合法动态参数可生效，非法动态参数被过滤或拒绝。
- 重试创建请求不产生重复 assistant（幂等生效）。

## 整体联调清单（当前阶段）

### A. 控制面联调（`/_platform/*`）

- `POST /_platform/assistants`：创建 assistant 后响应必须包含 `langgraph_assistant_id`。
- `GET /_platform/projects/{project_id}/assistants`：列表返回 `langgraph_assistant_id`，前端可直接用于运行目标解析。
- `PATCH /_platform/assistants/{assistant_id}`：更新后 `langgraph_assistant_id` 不应被空值覆盖。
- `DELETE /_platform/assistants/{assistant_id}`：若存在 canonical id，需先同步删除 LangGraph assistant。

### B. 运行面联调（`/api/langgraph/*`）

- 所有带 `assistant_id` 的运行请求：必须校验 assistant 属于当前 `x-project-id`。
- 所有 thread-scoped 请求：必须校验 thread metadata 中项目归属与 `x-project-id` 一致。
- `threads/search` 与 `threads/count`：请求 metadata 自动注入 `project_id`。
- 归属失败统一返回：
  - `403 assistant_project_denied`
  - `403 thread_project_denied`

### C. 前端联调（`agent-chat-ui`）

- `WorkspaceContext` 仅使用单一 query key：`assistantId`。
- `Stream` 不再调用 environment-mappings API；运行目标取 `assistant.langgraph_assistant_id || assistant.id`。
- 运行调用统一走平台同构前缀：`/api/langgraph/*`。
- `runtime-bindings` 页面为只读下线提示；导航中移除 Environments 入口。

### D. 验收命令（最小）

- 后端：
  - `python3 -m py_compile app/services/agent_service.py app/services/langgraph_sdk/scope_guard.py app/api/langgraph/threads.py app/api/langgraph/runs.py`
- 前端：
  - `cd agent-chat-ui && pnpm lint`

### E. 手工验证路径

1. 选择 tenant/project，创建 assistant。
2. 确认 assistants 列表出现 `langgraph_assistant_id`。
3. 进入 chat 发起对话（create thread + run stream）。
4. 切换到无权限项目或构造错误 project header，确认收到 403 归属错误。
5. 删除 assistant，确认控制面与 LangGraph 侧对象一致清理。

## 故障记录：`/_platform/projects/{project_id}/assistants` 返回 500

### 现象

- 请求示例：`GET /_platform/projects/<project_id>/assistants?limit=20&offset=0&sort_by=created_at&sort_order=desc`
- 日志现象：`500 Internal Server Error`

### 根因

- 代码已引入 `agents.langgraph_assistant_id` 字段（Step 1），但数据库表结构未同步。
- `agents` 表缺少 `langgraph_assistant_id` 列时，控制面查询/序列化会触发 SQL 错误并表现为 500。

### 修复方式

1. 新增 Alembic 迁移：
   - `migrations/versions/20260304_0004_add_agents_langgraph_assistant_id.py`
2. 迁移内容：
   - `ALTER TABLE agents ADD COLUMN IF NOT EXISTS langgraph_assistant_id VARCHAR(128) NOT NULL DEFAULT ''`
   - `CREATE INDEX IF NOT EXISTS ix_agents_langgraph_assistant_id ON agents(langgraph_assistant_id)`

### 数据库迁移命令

> 说明：当前 Alembic 环境要求显式提供 `DATABASE_URL`。

```bash
DATABASE_URL="$(python3 - <<'PY'
from pathlib import Path
for line in Path('.env').read_text().splitlines():
    if line.startswith('DATABASE_URL='):
        print(line.split('=',1)[1])
        break
PY
)" uv run alembic upgrade head
```

### 验证方式

1. 校验列存在（`agents` 表应包含 `langgraph_assistant_id`）。
2. 重新请求 `/_platform/projects/{project_id}/assistants`，确认不再出现 500。
3. 若服务已运行，建议重启后复测。
