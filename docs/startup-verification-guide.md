# 启动与本地验证指南（当前可执行版本）

本文只记录当前 `AITestLab` 新结构下，已经在本机验证过的启动方式。

## 1. 当前目录结构

```text
AITestLab/
├── apps/platform-api
├── apps/platform-web
├── apps/runtime-service
└── apps/runtime-web
```

## 2. 当前已确认的本地依赖前提

### 2.1 本机 PostgreSQL

当前验证使用的是本机 PostgreSQL，连接信息已经写入：

- `apps/platform-api/.env`

当前有效库连接为：

```text
postgresql+psycopg://agent:AgentPg_2026!migrate@127.0.0.1:5432/agent_platform
```

### 2.2 runtime-service 上游地址

当前平台配置已指向：

```text
http://127.0.0.1:8123
```

即：

- `apps/runtime-service` 跑在 `8123`
- `apps/platform-api` 通过 `LANGGRAPH_UPSTREAM_URL=http://127.0.0.1:8123` 调它

## 3. 推荐启动顺序

推荐顺序：

1. `runtime-service`
2. `platform-api`
3. `platform-web`
4. `runtime-web`（按需）

## 4. 逐个启动命令

### 4.1 启动 runtime-service

```bash
cd apps/runtime-service
uv run langgraph dev --config graph_src_v2/langgraph.json --port 8123 --no-browser
```

启动后自检：

```bash
curl http://127.0.0.1:8123/info
curl http://127.0.0.1:8123/internal/capabilities/models
curl http://127.0.0.1:8123/internal/capabilities/tools
```

### 4.2 启动 platform-api

```bash
cd apps/platform-api
uv run uvicorn main:app --host 0.0.0.0 --port 2024 --reload
```

启动后自检：

```bash
curl http://127.0.0.1:2024/api/langgraph/info
```

## 5. 平台联调 runtime 的关键验证

确认 `runtime-service` 和 `platform-api` 都启动后，可以验证：

```bash
curl http://127.0.0.1:2024/api/langgraph/info
```

预期：返回 `200`

## 6. platform-web 启动

```bash
cd apps/platform-web
pnpm dev
```

默认访问：

```text
http://127.0.0.1:3000
```

当前 `.env` 已配置：

```text
NEXT_PUBLIC_API_URL=http://localhost:2024
```

## 7. runtime-web 启动

```bash
cd apps/runtime-web
PORT=3001 pnpm dev
```

默认访问：

```text
http://127.0.0.1:3001
```

当前 `.env` 已配置：

```text
NEXT_PUBLIC_API_URL=http://localhost:8124
NEXT_PUBLIC_ASSISTANT_ID=assistant_entrypoint
```

注意：

- 如果你当前 runtime 实际跑在 `8123`，那这里的 `.env` 需要改成 `8123`
- 否则 `runtime-web` 会连错端口

如果你想直接用当前已验证的端口，请改成：

```text
NEXT_PUBLIC_API_URL=http://localhost:8123
```

## 8. 当前已经验证通过的接口

以下接口已经在新目录结构下验证通过：

```bash
curl http://127.0.0.1:8123/info
curl http://127.0.0.1:8123/internal/capabilities/models
curl http://127.0.0.1:8123/internal/capabilities/tools
curl http://127.0.0.1:2024/api/langgraph/info
```

以及平台到 runtime 的管理链路：

- `POST /_management/catalog/models/refresh`
- `GET /_management/runtime/models`
- `POST /_management/catalog/tools/refresh`
- `GET /_management/runtime/tools`

## 9. 一键脚本（可选）

根目录已提供脚本：

```bash
scripts/dev-up.sh
scripts/dev-down.sh
scripts/check-health.sh
```

但当前最推荐你先按本文手工逐步启动，这样排查最直观。

## 10. 停止方式

如果你是手工在前台启动：

- 直接 `Ctrl + C`

如果你是通过根脚本启动：

```bash
scripts/dev-down.sh
```
