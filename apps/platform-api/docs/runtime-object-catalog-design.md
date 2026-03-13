# Runtime 对象目录与平台主数据设计

## 1. 目标

- 为 `graph / assistant / model / tool` 四类对象建立一套长期可演进的数据边界。
- 明确谁是平台主数据，谁只是运行时发现结果。
- 为后续管理台、同步任务、审计与治理策略提供统一的数据模型基础。

## 2. 设计结论（先拍板）

### 2.1 真相源划分

- `assistant`：平台控制面主数据（source of truth）。
- `graph`：运行时发现目录（catalog snapshot） + 平台治理覆盖。
- `model`：运行时能力快照（catalog snapshot） + 平台治理覆盖。
- `tool`：运行时能力快照（catalog snapshot） + 平台治理覆盖。

一句话：

> Assistant 归平台管；Graph / Model / Tool 先按“上游发现 + 平台缓存 + 平台治理”处理，不直接升格为平台唯一真相源。

### 2.2 为什么这样分

- `assistant` 已经具备平台主数据特征：
  - 有本地数据库模型。
  - 有管理 CRUD。
  - 有 `langgraph_assistant_id` 上游映射。
  - 有项目归属和审计语义。
- `graph` 当前不是独立上游目录真源，而是从 assistant 集合归并出来。
- `model / tool` 当前只是 `/_management/runtime/*` 透传出来的运行时 capability，不适合作为平台唯一真相源。

## 3. 领域边界

### 3.1 Assistant

- 语义：平台内可管理的业务对象。
- 职责：
  - 归属某个项目。
  - 保存平台侧展示与治理字段。
  - 保存对 LangGraph runtime assistant 的映射关系。
- 典型字段：
  - `project_id`
  - `name`
  - `description`
  - `graph_id`
  - `langgraph_assistant_id`
  - `config/context/metadata`
  - `status`

### 3.2 Graph

- 语义：runtime 中可创建/运行 assistant 的图目录项。
- 职责：
  - 提供 graph 目录展示。
  - 保存 graph 的发现结果与平台侧治理字段。
- 不承担：
  - 运行时唯一真相源。
  - thread/run 的直接归属关系。

### 3.3 Model

- 语义：runtime 暴露的模型能力目录项。
- 职责：
  - 提供模型目录与默认模型信息。
  - 保存平台对模型的启用、排序、默认策略覆盖。

### 3.4 Tool

- 语义：runtime 暴露的工具目录项。
- 职责：
  - 提供工具目录展示。
  - 保存平台对工具的启用、展示、备注等治理字段。

## 4. 目标表结构

## 4.1 Assistant（平台主数据）

建议方向：

- 继续沿用现有 `agents + assistant_profiles` 聚合，或者后续收敛为单表。
- 当前如果不做大迁移，可以先保留双表语义：
  - `agents`：身份与绑定
  - `assistant_profiles`：配置与治理

### 4.1.1 `agents`

- `id` uuid pk
- `project_id` uuid not null index
- `name` text not null
- `graph_id` text not null
- `runtime_base_url` text not null
- `langgraph_assistant_id` text not null
- `description` text not null default `''`
- `created_at`

建议新增或收紧约束：

- unique(`project_id`, `name`)
- unique(`project_id`, `langgraph_assistant_id`)

### 4.1.2 `assistant_profiles`

- `id` uuid pk
- `agent_id` uuid unique not null
- `status` text not null default `active`
- `config` jsonb not null default `{}`
- `context` jsonb not null default `{}`
- `metadata_json` jsonb not null default `{}`
- `created_by` uuid not null
- `updated_by` uuid not null
- `created_at`
- `updated_at`

### 4.1.3 后续可选统一表

如果后面觉得 `agents + assistant_profiles` 认知成本太高，可以统一收敛为：

- `assistants`
  - `id`
  - `project_id`
  - `name`
  - `description`
  - `graph_id`
  - `runtime_id` / `runtime_base_url`
  - `langgraph_assistant_id`
  - `status`
  - `config_json`
  - `context_json`
  - `metadata_json`
  - `created_by`
  - `updated_by`
  - `created_at`
  - `updated_at`

## 4.2 Graph 目录表

建议新表：`runtime_catalog_graphs`

- `id` uuid pk
- `runtime_id` text not null
- `graph_key` text not null
- `display_name` text nullable
- `description` text nullable
- `source_type` text not null
  - 例如：`assistant_search` / `graph_src_scan` / `manual`
- `raw_payload_json` jsonb not null default `{}`
- `sync_status` text not null default `ready`
- `last_seen_at` timestamptz nullable
- `last_synced_at` timestamptz nullable
- `is_deleted` boolean not null default `false`
- `created_at`
- `updated_at`

建议约束：

- unique(`runtime_id`, `graph_key`)

## 4.3 Model 目录表

建议新表：`runtime_catalog_models`

- `id` uuid pk
- `runtime_id` text not null
- `model_key` text not null
- `display_name` text nullable
- `is_default_runtime` boolean not null default `false`
- `raw_payload_json` jsonb not null default `{}`
- `sync_status` text not null default `ready`
- `last_seen_at` timestamptz nullable
- `last_synced_at` timestamptz nullable
- `is_deleted` boolean not null default `false`
- `created_at`
- `updated_at`

建议约束：

- unique(`runtime_id`, `model_key`)

## 4.4 Tool 目录表

建议新表：`runtime_catalog_tools`

- `id` uuid pk
- `runtime_id` text not null
- `tool_key` text not null
- `name` text not null
- `source` text nullable
- `description` text nullable
- `raw_payload_json` jsonb not null default `{}`
- `sync_status` text not null default `ready`
- `last_seen_at` timestamptz nullable
- `last_synced_at` timestamptz nullable
- `is_deleted` boolean not null default `false`
- `created_at`
- `updated_at`

建议约束：

- unique(`runtime_id`, `tool_key`)

说明：

- `tool_key` 不建议只用 `name`。
- 更稳的做法是 `source:name`，如果未来上游提供版本或更稳定 identity，再升级 key 规则。

## 4.5 Project 治理覆盖表

这里不要把 `project_id` 直接塞进 catalog 主表，而是单独建 policy 表。

### 4.5.1 `project_graph_policies`

- `id` uuid pk
- `project_id` uuid not null
- `graph_catalog_id` uuid not null
- `is_enabled` boolean not null default `true`
- `display_order` int nullable
- `note` text nullable
- `updated_by` uuid nullable
- `updated_at` timestamptz not null

约束：

- unique(`project_id`, `graph_catalog_id`)

### 4.5.2 `project_model_policies`

- `id` uuid pk
- `project_id` uuid not null
- `model_catalog_id` uuid not null
- `is_enabled` boolean not null default `true`
- `is_default_for_project` boolean not null default `false`
- `temperature_default` numeric nullable
- `note` text nullable
- `updated_by` uuid nullable
- `updated_at` timestamptz not null

约束：

- unique(`project_id`, `model_catalog_id`)

### 4.5.3 `project_tool_policies`

- `id` uuid pk
- `project_id` uuid not null
- `tool_catalog_id` uuid not null
- `is_enabled` boolean not null default `true`
- `display_order` int nullable
- `note` text nullable
- `updated_by` uuid nullable
- `updated_at` timestamptz not null

约束：

- unique(`project_id`, `tool_catalog_id`)

## 5. 同步策略

## 5.1 Assistant：请求内双写 + 状态补偿

Assistant 继续按控制面对象处理。

建议流程：

1. 平台管理接口接收创建/更新/删除请求。
2. 先调用上游 LangGraph assistant API。
3. 上游成功后再写平台数据库。
4. 若 DB 写失败，记录 `sync_status=error` 或进入补偿任务。

建议补充字段：

- `sync_status`
- `last_sync_error`
- `last_synced_at`

原因：

- 当前 assistant 已经是平台管理对象。
- 但如果只做“先上游后本地”而没有补偿，容易留下孤儿 assistant。

## 5.2 Graph / Model / Tool：拉取快照，不做请求内强同步

这三类不建议在页面请求里直接强同步。

建议采用三种刷新方式：

1. 手动刷新（管理页按钮）
2. 启动时刷新（可选）
3. 定时刷新（后台任务）

默认读取：

- 页面读平台库快照
- 页面展示 `last_synced_at`
- 用户需要最新状态时再点刷新

## 5.3 Graph 同步来源

Graph 现在有两个潜在来源：

- `assistants.search` 聚合去重
- graph 源码 / `langgraph.json` 扫描

因此 graph 同步时必须保留：

- `runtime_id`
- `source_type`

否则会把不同来源的 graph 误认为一个对象。

## 5.4 删除策略

对 catalog 对象，不建议上游消失就物理删除。

建议策略：

- 标记 `is_deleted=true`
- 更新 `last_seen_at`
- 页面默认隐藏，但保留审计与历史追踪能力

## 6. 冲突规则

### 6.1 平台治理字段优先

以下字段以平台库为准：

- `is_enabled`
- `display_order`
- `project default`
- `note`

### 6.2 运行时能力字段以上游为准

以下字段以上游快照为准：

- `display_name`
- `description`
- `is_default_runtime`
- `raw_payload_json`

### 6.3 project_id 的处理原则

- `assistant.project_id`：当前就是强语义字段。
- `graph/model/tool` 主表：先不直接放 `project_id`。
- `project_id` 应该进入各自的 policy 表，表达“这个项目能不能用”。

原因：

- 当前 `model/tool` 更像 runtime 全局目录。
- 不是天然项目私有对象。
- 如果一开始就把 `project_id` 塞进 catalog 主表，会把“目录对象”和“项目治理关系”混成一层。

## 7. 前后端读取建议

### 7.1 管理台 Assistant 页

- 读平台主数据（assistant）
- 不依赖 runtime capability 快照
- 默认不直接请求 LangGraph 上游
- 只有以下动作才请求上游：
  - create
  - update
  - delete（启用 runtime 删除时）
  - resync

### 7.2 Runtime Models / Tools 页

- 读 `runtime_catalog_models`
- 读 `runtime_catalog_tools`
- 展示最近一次刷新时间
- 支持手动刷新
- 默认读取平台数据库快照
- 只有点击 `Refresh` 时，才请求上游 LangGraph capability 接口并回写平台库

### 7.3 Graph 目录页

- 读 `runtime_catalog_graphs`
- 如果后续需要“项目可用 graph”，再叠加 `project_graph_policies`
- 默认读取平台数据库快照
- 只有点击 `Refresh` 时，才请求上游 LangGraph assistant/graph 来源并回写平台库

### 7.4 统一运行规则（拍板）

- 不调用 refresh / resync：读平台数据库
- 调用 refresh / resync：打 LangGraph 上游，再回写平台数据库

按对象区分：

- `assistant`
  - 默认读平台主数据
  - `resync` 才去上游重新拉取单对象并回写
- `graph`
  - 默认读 catalog 快照
  - `refresh` 才去上游重建目录快照
- `model/tool`
  - 默认读 catalog 快照
  - `refresh` 才去上游重拉 capability 并回写

## 8. 实施顺序

### 第一步：收敛 assistant 模型

- 保持 `assistant = 平台主数据` 这件事不再摇摆。
- 决定继续沿用 `agents + assistant_profiles`，还是统一成单表。

### 第二步：新增 `runtime_catalog_models`

- 来源简单。
- 页面价值立刻可见。
- 风险最低。

### 第三步：新增 `runtime_catalog_tools`

- 与 models 模式一致。
- 继续复用 runtime capabilities 刷新链路。

### 第四步：新增 `runtime_catalog_graphs`

- 但要明确它是“目录快照”，不是强真相源。

### 第五步：新增 `project_*_policies`

- 进入项目级治理。
- 这一步才真正让 `project_id` 与 model/tool/graph 发生平台治理关系。

## 9. 当前不做的事情

- 不把 `thread/run/checkpoint` 纳入平台主数据。
- 不把 `graph/model/tool` 升格为平台唯一真相源。
- 不做请求内强同步。
- 不在第一阶段引入复杂多 runtime 发布编排。

## 10. 风险点

### 10.1 Assistant 双写漂移

- 上游成功，本地失败，会留下孤儿 assistant。
- 必须有补偿机制或错误状态字段。

### 10.2 Graph 来源不单一

- assistant 聚合和源码扫描可能冲突。
- 不能只靠 `graph_id` 作为唯一语义。

### 10.3 Model / Tool 未来会出现多 runtime 撞名

- 一旦有多个 runtime / 环境，`model_id` 和 `tool_name` 可能重复但语义不同。
- 所以 `runtime_id` 必须是一等维度。

## 11. 最终拍板

当前阶段的统一结论：

- `assistant = 主数据`
- `graph/model/tool = catalog snapshot + governance overlay`

这套方案最符合当前代码现状，也最适合平滑演进到后续的项目治理能力。

## 12. 实施任务清单

### Phase 1：数据库基础

- `app/db/models.py`
  - 新增 `RuntimeCatalogGraph`
  - 新增 `RuntimeCatalogModel`
  - 新增 `RuntimeCatalogTool`
  - 新增 `ProjectGraphPolicy`
  - 新增 `ProjectModelPolicy`
  - 新增 `ProjectToolPolicy`
  - 为 `Agent` 补唯一约束设计
- `migrations/versions/*`
  - 建 `runtime_catalog_models`
  - 建 `runtime_catalog_tools`
  - 建 `runtime_catalog_graphs`
  - 建 `project_graph_policies`
  - 建 `project_model_policies`
  - 建 `project_tool_policies`
  - 补 `agents(project_id, name)` 唯一约束
  - 补 `agents(project_id, langgraph_assistant_id)` 唯一约束

### Phase 2：数据访问层

- `app/db/access.py`
  - 新增 `upsert_runtime_model_catalog_items`
  - 新增 `upsert_runtime_tool_catalog_items`
  - 新增 `upsert_runtime_graph_catalog_items`
  - 新增 `list_runtime_model_catalog_items`
  - 新增 `list_runtime_tool_catalog_items`
  - 新增 `list_runtime_graph_catalog_items`
  - 新增 `upsert_project_model_policy`
  - 新增 `upsert_project_tool_policy`
  - 新增 `upsert_project_graph_policy`
  - 新增 `list_project_model_policies`
  - 新增 `list_project_tool_policies`
  - 新增 `list_project_graph_policies`

### Phase 3：同步服务

- 新增 `app/services/runtime_catalog_sync.py`
  - `sync_models_from_runtime(...)`
  - `sync_tools_from_runtime(...)`
  - `sync_graphs_from_runtime(...)`
  - `mark_missing_catalog_items_deleted(...)`

### Phase 4：管理接口改造

- `app/api/management/runtime_capabilities.py`
  - 从“纯透传”改成“读平台库”
  - 支持 refresh 能力
- 新增 catalog 查询接口
  - `GET /_management/catalog/models`
  - `GET /_management/catalog/tools`
  - `GET /_management/catalog/graphs`
  - `POST /_management/catalog/models/refresh`
  - `POST /_management/catalog/tools/refresh`
  - `POST /_management/catalog/graphs/refresh`

### Phase 5：Assistant 同步状态

- 为 assistant 增加：
  - `sync_status`
  - `last_sync_error`
  - `last_synced_at`
- `app/api/management/assistants.py`
  - 创建/更新/删除时维护同步状态
  - 双写失败时给出可恢复状态

### Phase 6：项目治理接口

- 新增管理接口
  - `GET /_management/projects/{project_id}/model-policies`
  - `PUT /_management/projects/{project_id}/model-policies/{catalog_id}`
  - `GET /_management/projects/{project_id}/tool-policies`
  - `PUT /_management/projects/{project_id}/tool-policies/{catalog_id}`
  - `GET /_management/projects/{project_id}/graph-policies`
  - `PUT /_management/projects/{project_id}/graph-policies/{catalog_id}`

### Phase 7：前端接入

- `apps/platform-web/src/lib/management-api/runtime.ts`
  - 改成读 catalog 接口
  - 增加 refresh 调用
- Runtime 页面
  - 展示 `last_synced_at`
  - 展示 `sync_status`
  - 支持手动 refresh

### 验收标准

- 不依赖上游在线时，也能展示最近一次 `models/tools/graphs` 快照
- 手动 refresh 可以更新 catalog 快照
- assistant 双写失败不会留下无状态漂移
- 页面能看到 `last_synced_at` 与 `sync_status`
