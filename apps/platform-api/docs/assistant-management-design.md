# Assistant 管理页面与接口设计方案（落地稿）

## 1. 目标

- 为 `workspace/assistants` 提供完整管理能力：列表展示、编辑、创建、删除。
- Assistant 创建时必须绑定项目与创建者，并支持动态参数（对齐 graph entrypoint 的运行参数能力）。
- 前端只调用平台后端，后端负责项目隔离、审计、参数校验与 LangGraph 对接。

## 2. 范围与非目标

### 2.1 范围

- 管理面：Assistant 列表、详情、创建、编辑、删除。
- 数据面：Assistant 主数据与 LangGraph assistant 映射。
- 参数面：`config/context/metadata` 动态参数白名单校验。

### 2.2 非目标

- 本文不包含运行时聊天协议改造（`/api/langgraph/runs*`）。
- 本文不包含历史接口下线执行细节，仅给迁移路径。

## 3. 术语与模型

- `Assistant`：项目内可管理的智能体实例。
- `graph_id`：LangGraph 图标识（同一 graph 可对应多个 assistants）。
- `langgraph_assistant_id`：LangGraph 运行时目标 ID。
- 动态参数：创建/编辑时传入的 `config`、`context`、`metadata`。

建议平台表结构（可扩展现有 `agents` 或新增 `project_assistants`）：

- `id` (uuid, pk)
- `project_id` (uuid, not null, index)
- `graph_id` (text, not null)
- `langgraph_assistant_id` (text, not null, unique)
- `name` (text, nullable)
- `description` (text, nullable)
- `config` (jsonb, not null, default `{}`)
- `context` (jsonb, not null, default `{}`)
- `metadata` (jsonb, not null, default `{}`)
- `status` (text, not null, default `active`)
- `created_by` (uuid/text, not null)
- `updated_by` (uuid/text, not null)
- `created_at` / `updated_at`

## 4. 后端接口设计（管理面）

统一前缀沿用 `/_management/*`：

1) 列表查询

- `GET /_management/projects/{project_id}/assistants?graph_id=&q=&limit=&offset=`
- 返回：分页列表，包含展示字段 + `langgraph_assistant_id`。

2) 创建 Assistant

- `POST /_management/projects/{project_id}/assistants`
- 请求体：

```json
{
  "graph_id": "assistant",
  "name": "support-bot",
  "description": "客服助手",
  "config": {"model": "gpt-4.1"},
  "context": {"locale": "zh-CN"},
  "metadata": {"channel": "web"}
}
```

- 服务端强制注入：
  - `project_id`（来自 path）
  - `created_by`/`updated_by`（来自认证上下文）
  - `metadata.project_id` 与审计字段（防前端伪造）
- 行为：
  - 校验动态参数白名单。
  - 调用 `/api/langgraph/assistants` 创建上游 assistant。
  - 保存平台映射记录。

3) 详情查询

- `GET /_management/assistants/{assistant_id}`

4) 编辑

- `PATCH /_management/assistants/{assistant_id}`
- 可更新：`name/description/config/context/metadata/status`
- 服务端更新 `updated_by` 与 `updated_at`。

5) 删除

- `DELETE /_management/assistants/{assistant_id}`
- 策略：默认软删（推荐），并可配置是否同步删除 LangGraph assistant。

6) 动态参数 Schema

- `GET /_management/graphs/{graph_id}/assistant-parameter-schema`
- 用于前端动态表单渲染（字段类型、必填、默认值、可选枚举）。

## 5. 动态参数治理策略

结合你在 `graph_entrypoint.py` 的动态能力（`config/context` 合并与 runtime 参数解析），建议：

- 白名单允许：模型、温度、工具开关、业务上下文。
- 黑名单禁止：身份边界字段（如项目归属、用户身份、权限角色）。
- 类型校验：字符串/数字/布尔/对象/数组严格校验。
- 版本控制：schema 响应带 `schema_version`，前后端可灰度升级。

## 6. 前端页面设计

### 6.1 列表页 `workspace/assistants`

- 表格列：`name / graph_id / status / updated_at / created_by / actions`。
- 支持：搜索、按 graph 过滤、分页、行内编辑入口。
- 操作：`Edit`、`Clone`、`Delete`、`Open in Chat`。

### 6.2 创建页 `workspace/assistants/new`

- 三步表单：
  1. 选择 `graph_id`
  2. 基础信息（name/description）
  3. 动态参数（config/context/metadata）
- 动态参数区由 schema 渲染，避免写死字段。

### 6.3 编辑体验

- 与创建页复用同一表单组件。
- 编辑保存只提交 diff 字段（减少误覆盖风险）。

## 7. 权限、审计与错误码

- 权限：
  - 读取：项目成员可读（按角色配置）。
  - 写入：仅 `admin/editor`（示例）。
- 审计事件：
  - `assistant.create`
  - `assistant.update`
  - `assistant.delete`
  - `assistant.create_failed`
- 建议错误码：
  - `assistant_name_conflict`
  - `assistant_param_invalid`
  - `assistant_project_denied`
  - `assistant_upstream_create_failed`

## 8. 最小实施计划

1. 后端：新增 `/_management/assistants*` 与 schema 接口。
2. 前端：新增 `workspace/assistants` 列表页。
3. 前端：新增 `workspace/assistants/new` 创建页与动态参数组件。
4. 联调：创建 -> 编辑 -> 删除 -> Chat 跳转全链路验证。

## 9. 验收标准

- 可在指定项目下创建 Assistant，并看到 `created_by/project_id` 正确落库。
- 动态参数非法值被后端拒绝，错误码可读。
- 列表页可筛选、分页、编辑、删除，且操作有审计记录。
- 创建后的 Assistant 能在 Chat 目标选择中被正确使用。
