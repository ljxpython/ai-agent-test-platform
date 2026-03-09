# 平台管理 API（第二阶段）

## 启用条件

- `.env` 里启用：`PLATFORM_DB_ENABLED=true`
- Keycloak 验签已打通：`KEYCLOAK_AUTH_ENABLED=true`

## API 列表

- `GET /_platform/tenants`：查询当前用户所属租户
- `POST /_platform/tenants`：创建租户，并把当前用户设为 `owner`
- `POST /_platform/tenants/{tenant_ref}/memberships`：新增/更新租户成员（仅 `owner/admin`）
- `DELETE /_platform/tenants/{tenant_ref}/memberships/{user_ref}`：删除租户成员（仅 `owner/admin`）
- `GET /_platform/tenants/{tenant_ref}/projects`：查询租户项目（有 membership 即可）
- `POST /_platform/projects`：创建项目（仅 `owner/admin`）
- `DELETE /_platform/projects/{project_id}`：删除项目（仅 `owner/admin`）
- `GET /_platform/projects/{project_id}/assistants`：查询项目下 assistant profile（有 membership 即可）
- `POST /_platform/assistants`：创建 assistant profile（仅 `owner/admin`）
- `DELETE /_platform/assistants/{assistant_id}`：删除 assistant profile（仅 `owner/admin`）
- `GET /_platform/tenants/{tenant_ref}/audit-logs`：查询租户审计日志（仅 `owner/admin`）
- `GET /_platform/tenants/{tenant_ref}/audit-logs/stats`：审计聚合统计（仅 `owner/admin`）
- `GET /_platform/tenants/{tenant_ref}/audit-logs/export`：导出审计日志 CSV（仅 `owner/admin`）

## 角色权限矩阵

- `owner/admin`：可读写租户、项目、assistant profile、membership。
- `member`：只读（可看租户、项目、assistant profile），不可写。

## 分页与排序规范

列表接口统一支持：

- `limit`（默认 50，最大 200）
- `offset`（默认 0）
- `sort_by`（按接口支持字段）
- `sort_order=asc|desc`

列表接口会在响应头返回总数：`x-total-count`。

## 示例

### 1) 获取 token

```bash
TOKEN=$(curl -sS \
  -X POST "http://127.0.0.1:18080/realms/agent-platform/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=agent-proxy" \
  -d "username=demo_user" \
  -d "password=Demo@123456" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))')
```

### 2) 创建租户

```bash
curl -sS -X POST "http://127.0.0.1:2024/_platform/tenants" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Tenant A","slug":"tenant-a"}'
```

### 3) 查询我可见租户

```bash
curl -sS "http://127.0.0.1:2024/_platform/tenants" \
  -H "Authorization: Bearer $TOKEN"
```

### 4) 给租户添加成员

```bash
curl -sS -X POST "http://127.0.0.1:2024/_platform/tenants/<tenant-id-or-slug>/memberships" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"external_subject":"external-user-1","email":"external1@example.com","role":"member"}'
```

### 5) 创建项目（owner/admin）

```bash
curl -sS -X POST "http://127.0.0.1:2024/_platform/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"<tenant-id>","name":"Project A"}'
```

### 6) 创建 assistant profile（owner/admin）

```bash
curl -sS -X POST "http://127.0.0.1:2024/_platform/assistants" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<project-id>","name":"Agent A","graph_id":"graph-agent-a","runtime_base_url":"http://127.0.0.1:8123","description":"demo"}'
```

### 7) 查询审计日志（owner/admin）

```bash
curl -sS "http://127.0.0.1:2024/_platform/tenants/<tenant-id-or-slug>/audit-logs?limit=50&offset=0&plane=runtime_proxy" \
  -H "Authorization: Bearer $TOKEN"
```

支持过滤参数：

- `plane=control_plane|runtime_proxy|internal`
- `method=GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS`
- `path_prefix=/info`
- `status_code=200`
- `user_id=<uuid>`
- `from_time=<ISO8601>`
- `to_time=<ISO8601>`

### 8) 查询审计聚合统计（owner/admin）

```bash
curl -sS "http://127.0.0.1:2024/_platform/tenants/<tenant-id-or-slug>/audit-logs/stats?by=path&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

支持维度：

- `by=path`
- `by=status_code`
- `by=user_id`
- `by=plane`

### 9) 导出审计日志 CSV（owner/admin）

```bash
curl -sS "http://127.0.0.1:2024/_platform/tenants/<tenant-id-or-slug>/audit-logs/export?max_rows=5000" \
  -H "Authorization: Bearer $TOKEN"
```

支持过滤参数与审计查询一致：`plane/method/path_prefix/status_code/user_id/from_time/to_time`。

## 与透传链路的关系

- 请求带 `x-tenant-id` 时会触发 membership 校验。
- 没有 membership 返回 `403 tenant_access_denied`。
- 有 membership 才允许继续透传到 LangGraph。
- 浏览器 CORS 预检 `OPTIONS` 已统一放行，不走认证拦截。
- 如果请求带 `x-agent-id`，会校验该 agent 是否归属于 `x-tenant-id`，不一致返回 `403`。

如果启用 `RUNTIME_ROLE_ENFORCEMENT_ENABLED=true`：

- `member` 角色在透传链路下不能执行写方法（`POST/PUT/PATCH/DELETE`），会返回 `403 runtime_policy_denied`。
- `owner/admin` 不受此限制。

如果同时启用 `OPENFGA_AUTHZ_ENABLED=true`：

- 透传链路会按请求方法映射到 `can_read/can_write`，对 `tenant:<id>` 执行 OpenFGA `check`。
- 如果传了 `x-agent-id`，还会对 `agent:<id>` 做同样的 `check`。
- check 不通过同样返回 `403 runtime_policy_denied`。

## 审计日志

- 所有请求统一写入 `audit_logs`，无需预先知道 LangGraph 端点清单。
- `plane` 字段区分流量类型：
  - `control_plane`：`/_platform/*`
  - `runtime_proxy`：透传到 LangGraph 的请求
  - `internal`：`/_proxy/*` 内部接口
- 关键字段：`request_id/method/path/status_code/duration_ms/tenant_id/user_id/user_subject`。
