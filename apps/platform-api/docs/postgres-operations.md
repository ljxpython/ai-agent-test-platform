# PostgreSQL 容器运行手册

## 目标

提供可直接执行的 PostgreSQL Docker 方案，支持：启动、停止、备份、恢复、迁移。

## 一次性创建并启动容器

先约定两个变量，后面命令都用它们：

```bash
export PG_CONTAINER=agent-postgres
export PG_PASSWORD='<set-a-strong-password>'
```

```bash
docker run -d \
  --name "$PG_CONTAINER" \
  -e POSTGRES_USER=agent \
  -e POSTGRES_PASSWORD="$PG_PASSWORD" \
  -e POSTGRES_DB=agent_platform \
  -p 5432:5432 \
  -v agent_platform_pgdata:/var/lib/postgresql/data \
  -v $(pwd)/backups:/backups \
  postgres:16
```

或使用你当前目录无关的备份路径（推荐）：

```bash
docker run -d \
  --name "$PG_CONTAINER" \
  -e POSTGRES_USER=agent \
  -e POSTGRES_PASSWORD="$PG_PASSWORD" \
  -e POSTGRES_DB=agent_platform \
  -p 5432:5432 \
  -v agent_platform_pgdata:/var/lib/postgresql/data \
  -v "$HOME/pg_data/backups":/backups \
  postgres:16
```

说明：
- `agent_platform_pgdata` 是持久化卷，容器重建数据不丢。
- `$(pwd)/backups` 挂载到容器 `/backups`，用于导出备份文件。

## 启动与停止

```bash
# 启动
docker start "$PG_CONTAINER"

# 停止
docker stop "$PG_CONTAINER"

# 重启
docker restart "$PG_CONTAINER"

# 查看日志
docker logs -f "$PG_CONTAINER"
```

## 连接测试

```bash
docker exec -it "$PG_CONTAINER" psql -U agent -d agent_platform -c "SELECT version();"
```

## 备份（逻辑备份）

```bash
docker exec "$PG_CONTAINER" \
  pg_dump -U agent -d agent_platform -F c -f /backups/agent_platform_$(date +%F_%H%M%S).dump
```

说明：
- `-F c` 为自定义格式，适合 `pg_restore`。
- 备份文件会出现在宿主机 `./backups` 目录。

## 恢复（从 dump 恢复）

```bash
# 先清空并重建 public schema（谨慎执行）
docker exec "$PG_CONTAINER" psql -U agent -d agent_platform -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# 执行恢复
docker exec "$PG_CONTAINER" \
  pg_restore -U agent -d agent_platform /backups/<your_dump_file>.dump
```

## 迁移方案（Alembic）

推荐在应用侧执行迁移，不直接手工改表。

```bash
# 安装（若后续引入）
uv add alembic sqlalchemy psycopg[binary]

# 初始化迁移目录（只执行一次）
uv run alembic init migrations

# 设置连接串（示例）
export DATABASE_URL="postgresql+psycopg://agent:${PG_PASSWORD}@127.0.0.1:5432/agent_platform"

# 生成迁移文件
uv run alembic revision -m "create core platform tables"

# 执行迁移
uv run alembic upgrade head

# 回滚一步
uv run alembic downgrade -1
```

## 建议的最小运维策略

- 每天至少一次逻辑备份，保留最近 7 天。
- 每次迁移前先执行一次手动备份。
- 所有 schema 变更必须走迁移脚本，禁止手工直改生产库。

## 本地 / 隧道 两种连接口径

- 本地直接连 PostgreSQL：`127.0.0.1:5432`
- SSH 隧道连远端 PostgreSQL：`127.0.0.1:15432`
- 对应用来说，两者都只是不同的 `DATABASE_URL`；项目已经统一按 PostgreSQL 使用。

## SQLite 历史数据迁移到 PostgreSQL

如果你手头还有历史 SQLite 文件，可以用仓库自带脚本重新导入到当前 PostgreSQL。

```bash
# 先确认当前 .env / DATABASE_URL 指向目标 PostgreSQL
PYTHONPATH=. uv run python scripts/migrate_sqlite_to_postgres.py --dry-run

# 真正执行迁移
PYTHONPATH=. uv run python scripts/migrate_sqlite_to_postgres.py
```

说明：

- 默认源库路径是 `data/archive/agent_platform_v3_migrated_20260307.db`
- 脚本会按依赖顺序整表覆盖导入：`tenants -> users -> projects -> project_members -> refresh_tokens -> agents -> assistant_profiles -> audit_logs`
- 执行前应先做 PostgreSQL 逻辑备份
- 当前仓库已经完成过一次正式迁移，备份文件位于 `backups/agent_platform_pre_schema_align.dump` 和 `backups/agent_platform_pre_data_migration.dump`

## RBAC 回滚说明（当前版本）

旧的 `scripts/rbac_membership_rollback.py` 已不在当前仓库中维护。

当前版本采用自建认证与项目级 RBAC，成员角色回滚应通过：

- 管理接口直接修正成员角色
- 数据库备份/恢复流程回退错误变更
- 必要时结合 Alembic 迁移回滚数据库结构变更

如果后续需要“一键回滚成员角色”的运维能力，建议以当前 `/_management/*` 接口和自建 RBAC 模型为基础重新实现，而不是恢复旧的 Keycloak/OpenFGA 时代脚本。
