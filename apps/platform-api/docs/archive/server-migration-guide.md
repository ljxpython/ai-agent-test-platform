# 服务器迁移手册（PostgreSQL + Keycloak + OpenFGA）

## 目标

把本地已跑通的平台能力迁移到服务器，并尽量做到：

- 迁移后业务数据可直接用（租户/项目/智能体/审计不丢）
- 认证与授权可直接用（Keycloak + OpenFGA）
- 除必要环境差异（域名、端口、证书）外，不需要重复手工配置

---

## 迁移策略（推荐顺序）

1. 先迁 PostgreSQL（业务主数据）。
2. 再迁 Keycloak（Realm/Client/User）。
3. 再迁 OpenFGA（模型 + tuple）。
4. 最后切换代理服务 `.env` 并做冒烟验证。

> 关键原则：**ID 稳定优先**。如果 tenant/project/agent/user subject 不变，迁移会最省心。

---

## 一次性准备（现在就做，未来最省事）

### 1) 固化关键命名

- Keycloak Realm：`agent-platform`
- Keycloak Client：`agent-proxy`
- OpenFGA 模型文件：`config/openfga-models/v1.json`

不要随意改这些标识，后续迁移和回放会更稳定。

### 2) 保留一份“生产环境模板”

建议新增并长期维护：

- `.env.server.template`（仅模板，不放密钥）
- 迁移时只替换：域名、端口、密码、证书路径

### 3) 明确哪些是“必须手工”的

- 域名与 TLS 证书
- 服务器防火墙/安全组
- DNS 切换

其余（数据库恢复、模型写入、应用迁移）可脚本化。

---

## 第 0 步：迁移前冻结窗口

在切换窗口内，暂停写操作（至少暂停平台管理写操作），避免导出期间数据继续变化。

---

## 第 1 步：导出本地数据

## 1.1 导出 PostgreSQL（强制）

使用 `docs/postgres-operations.md` 的逻辑备份流程：

```bash
docker exec agent-platform-pg \
  pg_dump -U agent -d agent_platform -F c -f /backups/agent_platform_migrate.dump
```

导出后把 dump 文件拷贝到服务器。

## 1.2 导出 Keycloak（推荐强制）

你有两种方式：

- 方式 A（推荐）：Keycloak 后台导出 Realm（包含 client/roles/users）
- 方式 B：在容器内用 `kc.sh export` 导出到文件

目标产物：`realm-agent-platform.json`

> 注意：如果只迁移配置不迁移用户，你之后仍需手动创建用户。

## 1.3 记录 OpenFGA 当前状态（最少记录）

记录当前 `.env`：

- `OPENFGA_URL`
- `OPENFGA_STORE_ID`
- `OPENFGA_MODEL_ID`
- `OPENFGA_MODEL_FILE`

以及当前模型文件版本（默认 `config/openfga-models/v1.json`）。

---

## 第 2 步：部署服务器基础组件

## 2.1 PostgreSQL

- 启动服务器 PostgreSQL（推荐独立实例/托管服务）
- 创建目标库
- 恢复 dump：

```bash
pg_restore -U <user> -d <db_name> /path/to/agent_platform_migrate.dump
```

然后执行：

```bash
uv run alembic upgrade head
```

保证目标库 schema 与当前代码一致。

## 2.2 Keycloak

- 服务器启动 Keycloak（生产建议接 PostgreSQL，不用内置 H2）
- 导入 `realm-agent-platform.json`
- 检查：
  - Realm = `agent-platform`
  - Client = `agent-proxy`
  - audience 配置仍满足当前服务端配置

## 2.3 OpenFGA

- 生产建议 OpenFGA 使用 PostgreSQL datastore（避免内存/临时存储）
- 确保 OpenFGA 服务可达

## 开发环境与生产环境网络边界（必须明确）

### 端口公开策略

- 开发环境（远程服务器联调）：公网只开放 `22`（SSH）。
- 开发环境（远程服务器联调）：`18080`（Keycloak）、`18081`（OpenFGA）、`5432`（PostgreSQL）、`11434`（Ollama）不对公网开放，仅允许 `127.0.0.1` 或内网访问。
- 生产环境：`5432`（PostgreSQL）与 `11434`（Ollama）不对公网开放。
- 生产环境：`18080`/`18081` 默认也不对公网开放，如确需外部访问，只通过统一 Ingress/反向代理暴露 Keycloak/OpenFGA，并配 TLS 与访问控制。

### 开发环境推荐模式：只开 SSH + 本地端口转发

在本机建立一次性多端口 SSH 隧道：

```bash
ssh -N \
  -L 18080:127.0.0.1:18080 \
  -L 18081:127.0.0.1:18081 \
  -L 5432:127.0.0.1:5432 \
  -L 11434:127.0.0.1:11434 \
  <user>@<server>
```

使用方式：

- 本机访问 `http://127.0.0.1:18080` 等价访问服务器 Keycloak。
- 本机访问 `http://127.0.0.1:18081` 等价访问服务器 OpenFGA。
- 本机连接 `127.0.0.1:5432` 等价连接服务器 PostgreSQL。
- 本机访问 `http://127.0.0.1:11434` 等价访问服务器 Ollama。

停止隧道：

- 前台运行时，直接 `Ctrl+C`。
- 后台运行时，结束对应 `ssh -N` 进程。

### 如何区分开发环境/预发环境/生产环境（使用现有模板）

固定使用环境模板，不在同一个 `.env` 上反复手改：

- `config/environments/.env.dev.example`
- `config/environments/.env.dev.tunnel.example`
- `config/environments/.env.staging.example`
- `config/environments/.env.prod.example`

建议流程：

1. 开发环境：
   - 本地单机调试可从 `.env.dev.example` 复制。
   - 远程基础设施联调（SSH 隧道）建议从 `.env.dev.tunnel.example` 复制。
2. 预发环境：从 `.env.staging.example` 复制，使用预发域名或内网地址。
3. 生产环境：从 `.env.prod.example` 复制，使用生产域名或私网地址。

关键变量示例：

```env
# 开发环境（SSH 隧道）
KEYCLOAK_ISSUER=http://127.0.0.1:28080/realms/agent-platform
OPENFGA_URL=http://127.0.0.1:28081

# 生产环境（示例）
KEYCLOAK_ISSUER=https://<auth-domain>/realms/agent-platform
OPENFGA_URL=http://openfga.internal:8080
```

### 环境选择与上线前快速检查清单

- [ ] 当前 `.env` 来源模板正确（dev/staging/prod 之一）。
- [ ] 开发环境仅开放 `22`，业务端口通过 SSH 隧道访问。
- [ ] 生产环境未公网暴露 PostgreSQL `5432` 与 Ollama `11434`。
- [ ] `KEYCLOAK_ISSUER` 与目标环境一致（开发为本机转发，生产为正式域名）。
- [ ] `OPENFGA_URL` 与目标环境一致（开发为本机转发，生产为私网或受控入口）。
- [ ] 服务重启后，`/_proxy/health` 与鉴权冒烟验证通过。

---

## 第 3 步：迁移 OpenFGA 数据（模型 + tuple）

OpenFGA 有两种迁移路径：

### 路径 A（最佳）：连 OpenFGA 的底层持久化库一起迁移

- 优点：store/model/tuple 全保留，几乎零额外动作。
- 结果：可继续使用原 `OPENFGA_STORE_ID` / `OPENFGA_MODEL_ID`。

### 路径 B（常见）：只在新 OpenFGA 上重建模型

1. 在服务器写入模型并拿到新的 store/model id：

```bash
PYTHONPATH=. OPENFGA_URL=http://<server-openfga-host>:<port> \
OPENFGA_MODEL_FILE=config/openfga-models/v1.json \
uv run python scripts/setup_openfga.py
```

2. 把输出写入服务器 `.env`：

- `OPENFGA_STORE_ID=<new-store-id>`
- `OPENFGA_MODEL_ID=<new-model-id>`

3. 回填 tuple（必须）

当前代码会在“新增/删除”时同步 tuple，但**历史数据不会自动回填**。
因此路径 B 需要执行一次全量回填（脚本化或一次性批处理）。

回填关系最小集合：

- `user:<subject> --(owner/admin/member)--> tenant:<tenant_id>`
- `tenant:<tenant_id> --(tenant)--> project:<project_id>`
- `project:<project_id> --(project)--> agent:<agent_id>`

---

## 第 4 步：切换应用配置（服务器 `.env`）

重点确认：

```env
DATABASE_URL=postgresql+psycopg://<user>:<pwd>@<host>:5432/<db>

API_DOCS_ENABLED=false
DEV_AUTH_BYPASS_ENABLED=false
DEV_AUTH_BYPASS_MODE=fixed
DEV_AUTH_BYPASS_SUBJECT=dev-local-user
DEV_AUTH_BYPASS_EMAIL=
DEV_AUTH_BYPASS_ROLE=owner
DEV_AUTH_BYPASS_MEMBERSHIP_ENABLED=false

KEYCLOAK_AUTH_ENABLED=true
KEYCLOAK_AUTH_REQUIRED=true
KEYCLOAK_ISSUER=https://<your-keycloak-host>/realms/agent-platform
KEYCLOAK_AUDIENCE=agent-proxy
KEYCLOAK_JWKS_URL=

OPENFGA_ENABLED=true
OPENFGA_AUTHZ_ENABLED=true
OPENFGA_URL=http://<your-openfga-host>:8080
OPENFGA_STORE_ID=<id>
OPENFGA_MODEL_ID=<id>
OPENFGA_MODEL_FILE=config/openfga-models/v1.json
```

修改后重启服务。

---

## 第 5 步：迁移后验收（必须全通过）

1. 健康检查：`/_proxy/health` 返回 `200`
2. Keycloak：拿 token 后请求 `/info` 返回 `200`
3. 平台数据：能读到既有 tenant/project/agent
4. OpenFGA：
   - member 读请求通过
   - member 写请求被 `403`
5. 冒烟脚本：运行 `scripts/smoke_e2e.py`

---

## 最小停机切换方案（推荐）

1. 旧环境只读（冻结写）
2. 导出 PG + Keycloak
3. 服务器导入并启动
4. 完成 OpenFGA 模型/tuple 就绪
5. 执行冒烟
6. 切 DNS/网关到新环境

---

## 回滚预案（必须提前准备）

- 保留切换前 PostgreSQL dump
- 保留 Keycloak realm 导出文件
- 保留旧环境运行至少 24h（不立刻销毁）
- 新环境失败时，DNS/网关回指旧环境

---

## 你未来“几乎不用重新配置”的关键条件

只要满足以下 4 条，迁移就接近一次完成：

1. Keycloak realm/client 命名保持不变
2. PostgreSQL 主数据完整恢复
3. OpenFGA tuple 也完成迁移（或已全量回填）
4. `.env.server.template` 只改主机与密钥，不改业务标识

否则就会出现“服务起来了但权限不对/用户失效/数据不一致”的情况。

---

## 本次实战经验记录（2026-03）

### 1) 端口与网络边界

- 远程服务器已落地为 localhost 绑定：`127.0.0.1:18080/18081/5432/11434/8123`。
- 验证方式：`docker ps` + `ss -lntp` 双重确认，避免“容器配置改了但监听还在公网”。
- 对外探测验证：从服务器本机对公网 IP 探测 `18080/18081/5432/11434/8123` 均应 `closed`。

### 2) 本地开发连接方式（推荐固定）

- 使用单条 SSH 隧道命令统一转发：

```bash
ssh -p 10526 -N \
  -L 28080:127.0.0.1:18080 \
  -L 28081:127.0.0.1:18081 \
  -L 15432:127.0.0.1:5432 \
  -L 11143:127.0.0.1:11434 \
  -L 8123:127.0.0.1:8123 \
  root@61.147.247.83
```

- 说明：本地若已占用 `18080/18081`，建议使用 `28080/28081`，避免和本机现有服务冲突。

### 2.1 原理说明（为什么本地能调远端）

SSH 隧道本质是把你本机端口“映射”到远端服务器的本机端口：

- `-L 28080:127.0.0.1:18080` 表示：访问本机 `127.0.0.1:28080`，实际转发到远端 `127.0.0.1:18080`（Keycloak）。
- `-L 28081:127.0.0.1:18081` 表示：本机 OpenFGA 请求转发到远端 OpenFGA。
- `-L 15432:127.0.0.1:5432` 表示：本机数据库连接转发到远端 PostgreSQL。
- `-L 8123:127.0.0.1:8123` 表示：本机 runtime 请求转发到远端 runtime。

因此：

- 你的应用仍然只连本机 `127.0.0.1:*`。
- 远端业务端口不需要暴露公网，只保留 SSH 端口即可。
- 隧道断开后，这些“本地可访问远端”的通道会立即失效。

可选一键脚本（在仓库根目录执行）：

```bash
bash scripts/dev_tunnel_up.sh
bash scripts/dev_tunnel_down.sh
```

或使用 Makefile：

```bash
make dev-up
make dev-down
```

### 3) 本地后端联调关键配置

- `DATABASE_URL=postgresql+psycopg://agent:<pwd>@127.0.0.1:15432/agent_platform`
- `KEYCLOAK_ISSUER=http://127.0.0.1:28080/realms/agent-platform`
- `OPENFGA_URL=http://127.0.0.1:28081`
- `LANGGRAPH_UPSTREAM_URL=http://127.0.0.1:8123`
- `OPENFGA_STORE_ID` / `OPENFGA_MODEL_ID` 必须与远端现网一致。

### 4) 验收顺序（先连通，再鉴权，再授权）

1. `curl http://127.0.0.1:2024/_proxy/health` => `200`
2. `curl http://127.0.0.1:2024/info`（无 token）=> `401`
3. 从 Keycloak 取 token 后请求 `/info` => `200`
4. OpenFGA `check`：member `can_read=true`、`can_write=false`

### 5) 常见坑

- 只改了 `.env` 但没重启后端，配置不会生效。
- `DEV_AUTH_BYPASS_ENABLED=true` 会掩盖真实鉴权问题，联调阶段应关闭。
- `OPENFGA_AUTHZ_ENABLED=false` 会让授权失效，验权前必须打开。

### 6) 重启后 30 秒自检

```bash
curl -sS -o /dev/null -w 'health:%{http_code}\n' http://127.0.0.1:2024/_proxy/health
curl -sS -o /dev/null -w 'openfga:%{http_code}\n' http://127.0.0.1:28081/healthz
TOKEN=$(curl -sS -X POST 'http://127.0.0.1:28080/realms/agent-platform/protocol/openid-connect/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password' -d 'client_id=agent-proxy' \
  -d 'username=demo_user' -d 'password=Demo@123456' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")
curl -sS -o /dev/null -w 'info_with_token:%{http_code}\n' -H "Authorization: Bearer $TOKEN" http://127.0.0.1:2024/info
```

预期输出：`health:200`、`openfga:200`、`info_with_token:200`。
