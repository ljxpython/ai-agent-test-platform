# 日志系统说明（前后端）

## 目标

- 后端与前端分别输出日志文件。
- 日志统一落在仓库根目录 `logs/`。
- 关键链路可追踪：请求入口、鉴权、租户校验、透传、前端 API 路由、前端运行时错误。

## 文件结构

- 后端日志：`logs/backend.log`
- 前端服务端日志：`logs/frontend-server.log`
- 前端浏览器上报日志：`logs/frontend-client.log`

## 后端日志

### 启用方式

默认启动即启用，无需额外代码改动。

可选环境变量：

```env
LOGS_DIR=logs
BACKEND_LOG_FILE=backend.log
BACKEND_LOG_MAX_BYTES=10485760
BACKEND_LOG_BACKUP_COUNT=5
```

### 已覆盖关键点

- 服务启动/关闭（Keycloak/OpenFGA/DB 初始化状态）
- 请求开始/完成（`request_id/method/path/status/duration`）
- 鉴权链路（token 来源、验签成功/失败）
- 租户上下文链路（tenant 解析、membership 结果）
- 运行时策略拒绝（role policy、agent mapping、OpenFGA check）
- 上游透传（upstream URL、重试、超时、返回码）
- 平台 API 关键操作（tenant/project/agent/binding/audit）

## 前端日志

### 服务端日志（Next Route）

由 `agent-chat-ui/src/lib/server-logger.ts` 负责写文件。

可选环境变量：

```env
FRONTEND_LOGS_DIR=../logs
FRONTEND_SERVER_LOG_FILE=frontend-server.log
FRONTEND_CLIENT_LOG_FILE=frontend-client.log
```

### 浏览器日志上报

- 浏览器通过 `logClient(...)` 上报到 `POST /api/client-logs`
- `LogBootstrap` 会自动上报全局 `window error` 与 `unhandledrejection`
- `StreamProvider/ThreadProvider/WorkspaceContext/platform-api client` 已加入关键日志埋点

## 快速验证

### 后端

```bash
uv run uvicorn main:app --host 127.0.0.1 --port 2024
curl http://127.0.0.1:2024/_proxy/health
```

确认 `logs/backend.log` 有新增行。

### 前端

```bash
cd agent-chat-ui
pnpm dev
curl -X POST http://127.0.0.1:3000/api/client-logs \
  -H "Content-Type: application/json" \
  -d '{"level":"info","event":"manual_test","message":"frontend log test"}'
```

确认：

- `logs/frontend-client.log` 有 `manual_test`
- `logs/frontend-server.log` 有 `client_log_received`

## 注意事项

- 日志可能包含业务上下文，请勿写入敏感明文（密码、密钥、完整 token）。
- 当前前端 client log 接口限制了 payload 大小（32KB），避免滥用。
- 生产环境建议继续叠加集中式日志平台（ELK/OpenSearch/Loki）与告警。
