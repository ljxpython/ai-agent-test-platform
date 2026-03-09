# LangGraph Transparent Proxy (FastAPI)

This service is a transparent proxy in front of a LangGraph API server.

The goal is full API passthrough so `agent-chat-ui` can point to this service
without changing its request paths.

## Environment variables

- `LANGGRAPH_UPSTREAM_URL` (default: `http://127.0.0.1:8123`)
- `LANGGRAPH_UPSTREAM_API_KEY` (optional, injected as `x-api-key` to upstream)
- `PROXY_TIMEOUT_SECONDS` (default: `300`)
- `PROXY_CORS_ALLOW_ORIGINS` (default: `*`, comma-separated)
- `PROXY_UPSTREAM_RETRIES` (default: `1`)
- `PROXY_LOG_LEVEL` (default: `INFO`)
- `PLATFORM_DB_ENABLED` (default: `false`)
- `PLATFORM_DB_AUTO_CREATE` (default: `false`)
- `DATABASE_URL` (required when `PLATFORM_DB_ENABLED=true`)
- `AUTH_REQUIRED` (default: `true`, protects non-public routes)
- `LANGGRAPH_AUTH_REQUIRED` (default: `false`, protects `/api/langgraph/*` routes)
- `LANGGRAPH_SCOPE_GUARD_ENABLED` (default: `false`, enforces `x-project-id` boundary checks on LangGraph resources)
- `JWT_ACCESS_SECRET` (default: insecure dev fallback; set explicitly outside local throwaway envs)
- `JWT_REFRESH_SECRET` (default: insecure dev fallback; set explicitly outside local throwaway envs)
- `JWT_ACCESS_TTL_SECONDS` (default: `1800`)
- `JWT_REFRESH_TTL_SECONDS` (default: `604800`)
- `BOOTSTRAP_ADMIN_USERNAME` (default: `admin`)
- `BOOTSTRAP_ADMIN_PASSWORD` (default: `admin123456`)
- `API_DOCS_ENABLED` (default: `false`, exposes `/docs`, `/redoc`, `/openapi.json`)
- `LOGS_DIR` (default: `logs`)
- `BACKEND_LOG_FILE` (default: `backend.log`)
- `BACKEND_LOG_MAX_BYTES` (default: `10485760`)
- `BACKEND_LOG_BACKUP_COUNT` (default: `5`)
- `LANGGRAPH_GRAPH_SOURCE_ROOT` (optional, overrides dynamic graph schema source discovery)

## Notes on old variables

- Current backend uses self-hosted auth and project RBAC.
- Old `KEYCLOAK_*`, `OPENFGA_*`, `DEV_AUTH_BYPASS_*`, `RUNTIME_ROLE_ENFORCEMENT_ENABLED`, and `REQUIRE_TENANT_CONTEXT` variables are no longer part of the active backend config path.

## Run

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 2024 --reload
```

## Environment loading

- Runtime only reads the repo-root `.env` file.
- The loading path is `main.py -> app/factory.py -> load_dotenv() -> app/config.py`.
- `config/environments/*.example` are profile templates for humans to copy into the repo-root `.env` when switching environments.

### Recommended switching workflow

```bash
# Minimal local runnable setup
cp .env.example .env

# Local code + local PostgreSQL
cp config/environments/.env.dev.example .env

# Local code + remote infra over SSH tunnel
cp config/environments/.env.dev.tunnel.example .env

# Staging / production-like profile
cp config/environments/.env.staging.example .env
```

## Recommended profiles

### Local development (no login required)

```env
PLATFORM_DB_ENABLED=true
PLATFORM_DB_AUTO_CREATE=true
DATABASE_URL=postgresql+psycopg://agent:<pg-password>@127.0.0.1:5432/agent_platform

AUTH_REQUIRED=false
LANGGRAPH_AUTH_REQUIRED=false
LANGGRAPH_SCOPE_GUARD_ENABLED=false

API_DOCS_ENABLED=true

JWT_ACCESS_SECRET=local-access-secret-change-me
JWT_REFRESH_SECRET=local-refresh-secret-change-me
JWT_ACCESS_TTL_SECONDS=1800
JWT_REFRESH_TTL_SECONDS=604800

BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=admin123456
```

### Staging/Production (strict auth)

```env
API_DOCS_ENABLED=false

AUTH_REQUIRED=true
LANGGRAPH_AUTH_REQUIRED=true
LANGGRAPH_SCOPE_GUARD_ENABLED=true

JWT_ACCESS_SECRET=<set-a-strong-secret>
JWT_REFRESH_SECRET=<set-a-strong-secret>

BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=<set-a-strong-password>
```

## Health check

```bash
curl http://127.0.0.1:2024/_proxy/health
```

## Notes

- All incoming paths and methods are forwarded as-is.
- Status code and response headers are preserved (except hop-by-hop headers).
- SSE and long responses are streamed through directly.

## Docs

- `docs/README.md`
- `docs/dev-tunnel-guide.md`
- `docs/langgraph-passthrough-guide.md`
- `docs/chat-file-upload-guide.md`
- `docs/management-console-overview.md`
- `docs/self-hosted-auth-rbac-mvp.md`
- `docs/postgres-operations.md`
- `docs/code-architecture.md`
- `docs/error-playbook.md`
- `docs/testing.md`
- `docs/ci-troubleshooting.md`
- `docs/logging-system.md`
- `docs/archive/`（历史文档）

## Data migration status

- 平台库已经统一切到 PostgreSQL。
- 旧的本地 SQLite 数据已迁入远端 PostgreSQL，并不再作为运行时数据源。
- 如需再次导入历史 SQLite，请使用 `scripts/migrate_sqlite_to_postgres.py`。
- 迁移前备份位于 `backups/agent_platform_pre_schema_align.dump` 与 `backups/agent_platform_pre_data_migration.dump`。
- 历史遗留表 `memberships`、`runtime_bindings` 已从远端 PostgreSQL 清理。

## Environment templates

- `.env.example`: 最小可运行模板，适合快速本地启动。
- `config/environments/.env.dev.example`：本地代码 + 本地 PostgreSQL（通常 `127.0.0.1:5432`）
- `config/environments/.env.dev.tunnel.example`：本地代码 + SSH 隧道远端 PostgreSQL（通常 `127.0.0.1:15432`）
- `config/environments/.env.staging.example`
- `config/environments/.env.prod.example`

这些文件不会被程序直接自动读取；真正生效的是你复制出来的根目录 `.env`。
