# 本地开发说明

## 1. 目标

这份文档只记录当前有效的本地开发路径：

- 本地 PostgreSQL
- 可选的 SSH 隧道 PostgreSQL
- 本地运行 `platform-api`
- 本地验证健康检查、bootstrap admin、最小测试

## 2. 环境文件选择

当前程序默认读取 `apps/platform-api` 目录下的 `.env`。

推荐模板：

- `.env.example`：最小可运行模板
- `config/environments/.env.dev.example`：本地代码 + 本地 PostgreSQL
- `config/environments/.env.dev.tunnel.example`：本地代码 + 远端 PostgreSQL（通过 SSH 隧道）

常见起步方式：

```bash
cp .env.example .env
```

如果你已经有本地 PostgreSQL：

```bash
cp config/environments/.env.dev.example .env
```

如果你走远端 PostgreSQL 隧道：

```bash
cp config/environments/.env.dev.tunnel.example .env
```

## 3. 最小必填项

至少确认这些值是正确的：

- `LANGGRAPH_UPSTREAM_URL`
- `PLATFORM_DB_ENABLED`
- `PLATFORM_DB_AUTO_CREATE`
- `DATABASE_URL`
- `JWT_ACCESS_SECRET`
- `JWT_REFRESH_SECRET`
- `BOOTSTRAP_ADMIN_USERNAME`
- `BOOTSTRAP_ADMIN_PASSWORD`

## 4. 数据库口径

### 本地 PostgreSQL

- 常见地址：`127.0.0.1:5432`
- 典型 `DATABASE_URL`：

```env
DATABASE_URL=postgresql+psycopg://agent:<pg-password>@127.0.0.1:5432/agent_platform
```

### SSH 隧道 PostgreSQL

- 常见地址：`127.0.0.1:15432`
- 典型 `DATABASE_URL`：

```env
DATABASE_URL=postgresql+psycopg://agent:<pg-password>@127.0.0.1:15432/agent_platform
```

## 5. `PLATFORM_DB_AUTO_CREATE` 当前含义

当前代码在 `app/bootstrap/lifespan.py` 中通过 `create_core_tables()` 创建核心表。

建议：

- 本地首次启动：`PLATFORM_DB_AUTO_CREATE=true`
- 已经准备好现有库结构时：`PLATFORM_DB_AUTO_CREATE=false`

注意：

- 当前仓库已安装 Alembic 依赖，但日常本地启动的真实基线仍然是 `create_core_tables()`
- 如果后续迁移体系完全切换到 Alembic，应再单独更新本文档

## 6. 启动服务

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 2024 --reload
```

## 7. 启动后最小检查

### 健康检查

```bash
curl http://127.0.0.1:2024/_proxy/health
```

### API docs（如果启用）

```bash
open http://127.0.0.1:2024/docs
```

### bootstrap admin

当满足以下条件时，启动过程会自动确保 bootstrap admin 存在：

- `PLATFORM_DB_ENABLED=true`
- `DATABASE_URL` 可连接

它会：

- 创建缺失的管理员账号
- 或修复已有 bootstrap admin 的 `active/super_admin/password_hash`

## 8. 推荐日常工作流

1. 复制/更新 `.env`
2. 准备 PostgreSQL
3. 启动 `platform-api`
4. 跑后端最小测试
5. 再联调 `platform-web` 或 `runtime-service`

## 9. 当前不再作为开发基线的内容

以下历史链路已不再是当前本地开发基线：

- Keycloak
- OpenFGA
- retired passthrough routes
- 旧 `agent-chat-ui` 命名下的说明文档
