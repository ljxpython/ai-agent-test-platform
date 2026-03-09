# Keycloak 集成说明（一次性通过版）

## 目标

用最少步骤完成本地联调：拿到 Keycloak token，并成功调用 `http://127.0.0.1:2024/info` 返回 `200`。

## 前置约定（关键）

- Keycloak 端口固定用 `18080`（避免与本机 8080 冲突）
- `KEYCLOAK_AUDIENCE` 本地联调用 `account`（避免 `aud` 不匹配）
- 用户必须有：`email`、`first name`、`last name`，且 `Temporary password` 关闭

## 一次性流程

### 1) 启动 Keycloak

```bash
docker rm -f agent-keycloak 2>/dev/null || true
docker run -d \
  --name agent-keycloak \
  -p 18080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin123 \
  quay.io/keycloak/keycloak:26.0 \
  start-dev
```

后台地址：`http://127.0.0.1:18080`

### 2) Keycloak 后台配置

1. 登录 `admin/admin123`
2. 创建 Realm：`agent-platform`
3. 创建 Client：`agent-proxy`
4. Client 设置：
   - `Client authentication = Off`
   - `Direct access grants = On`
5. 创建用户 `demo_user`
6. 用户字段必须补齐：
   - `Email = demo_user@example.com`
   - `First name = Demo`
   - `Last name = User`
   - `Enabled = On`
   - `Email verified = On`
7. 用户密码：`Demo@123456`，且 `Temporary = Off`

> 如果你看到 `Account is not fully set up`，99% 是第 6/7 步没配完整。

### 3) 配置项目 `.env`

```env
KEYCLOAK_AUTH_ENABLED=true
KEYCLOAK_AUTH_REQUIRED=true
KEYCLOAK_ISSUER=http://127.0.0.1:18080/realms/agent-platform
KEYCLOAK_AUDIENCE=account
KEYCLOAK_JWKS_URL=
KEYCLOAK_JWKS_CACHE_TTL_SECONDS=300
```

本地开发如果需要“无登录也能调平台接口”，开启以下开关：

```env
DEV_AUTH_BYPASS_ENABLED=true
DEV_AUTH_BYPASS_MODE=fixed
DEV_AUTH_BYPASS_SUBJECT=dev-local-user
DEV_AUTH_BYPASS_EMAIL=dev-local@example.com
DEV_AUTH_BYPASS_ROLE=owner
DEV_AUTH_BYPASS_MEMBERSHIP_ENABLED=true
```

说明：

- `fixed`：注入固定开发用户（推荐，行为稳定）。
- `anonymous`：注入匿名开发用户（`sub=dev-anonymous`）。
- 该模式仅用于本地开发；staging/prod 必须关闭。

### 4) 启动代理服务

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 2024 --reload
```

### 5) 验证未登录拦截

```bash
curl -i http://127.0.0.1:2024/info
```

预期：`401`，并带 `WWW-Authenticate: Bearer`

### 6) 获取 token（推荐先看原始响应，再提取）

```bash
RESP=$(curl -sS \
  -X POST "http://127.0.0.1:18080/realms/agent-platform/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=agent-proxy" \
  -d "username=demo_user" \
  -d "password=Demo@123456")

echo "$RESP"

TOKEN=$(echo "$RESP" | python3 -c 'import sys,json; obj=json.load(sys.stdin); print(obj.get("access_token",""))')

echo "TOKEN_LENGTH=${#TOKEN}"
```

> 注意变量名是 `TOKEN`，不是 `TTOKEN`。

### 7) 带 token 调用

```bash
curl -i -H "Authorization: Bearer $TOKEN" http://127.0.0.1:2024/info
```

预期：`200`，响应头包含 `x-user-subject`

## 免重复输入：自动获取并缓存 token（推荐）

如果你不想每次都手写 `curl`，可以直接使用脚本：`scripts/keycloak_token.py`。

### 1) 一次性配置凭据（写入本地 shell 配置）

```bash
export KEYCLOAK_TOKEN_USERNAME=demo_user
export KEYCLOAK_TOKEN_PASSWORD=Demo@123456
```

可选覆盖项（不配也能用默认值）：

```bash
export KEYCLOAK_CLIENT_ID=agent-proxy
export KEYCLOAK_TOKEN_URL="http://127.0.0.1:18080/realms/agent-platform/protocol/openid-connect/token"
```

### 2) 获取 token（自动缓存，默认缓存到 `.cache/keycloak_token.json`）

```bash
TOKEN=$(uv run python scripts/keycloak_token.py)
```

然后照常调用：

```bash
curl -i -H "Authorization: Bearer $TOKEN" http://127.0.0.1:2024/info
```

### 3) 一行调用（不落 TOKEN 变量）

```bash
curl -i -H "$(uv run python scripts/keycloak_token.py --auth-header)" http://127.0.0.1:2024/info
```

说明：

- 脚本会优先使用未过期缓存 token。
- token 临近过期（默认 30 秒）会自动刷新。
- 可以用 `KEYCLOAK_TOKEN_CACHE_FILE` 自定义缓存文件路径。

## 前端免手填 token（agent-chat-ui）

如果希望前端页面也不需要每次输入 token，可启用前端内置 token 代理：

### 1) 在 `agent-chat-ui/.env` 配置

```env
NEXT_PUBLIC_AUTO_KEYCLOAK_TOKEN=true
KEYCLOAK_TOKEN_PROXY_ENABLED=true

# 下面几项用于服务端路由向 Keycloak 换取 token
KEYCLOAK_TOKEN_URL=http://127.0.0.1:18080/realms/agent-platform/protocol/openid-connect/token
KEYCLOAK_CLIENT_ID=agent-proxy
KEYCLOAK_TOKEN_USERNAME=demo_user
KEYCLOAK_TOKEN_PASSWORD=Demo@123456
```

### 2) 启动前端

```bash
cd agent-chat-ui
pnpm dev
```

效果：

- 前端会调用 `/api/keycloak-token` 自动获取并缓存 token。
- `StreamProvider/ThreadProvider` 会自动复用该 token，无需手工填 API Key。
- token 临近过期会自动刷新。
- 自动模式会在页面启动时覆盖旧缓存 token，避免因历史无效 token 导致持续 `401 invalid_token`。

> 提醒：该模式适合本地开发或内网环境。生产建议改为标准 OIDC 登录态（避免在前端服务配置固定用户名密码）。

### 前端仍然出现 `401 invalid_token` 的快速排查

1. 检查后端 `.env`：`KEYCLOAK_AUDIENCE=agent-proxy`。
2. 检查前端 `.env`：`NEXT_PUBLIC_AUTO_KEYCLOAK_TOKEN=true` 且 `KEYCLOAK_TOKEN_PROXY_ENABLED=true`。
3. 打开浏览器访问 `http://localhost:3000/api/keycloak-token`，确认能拿到 `access_token`。
4. 若仍失败，清一次浏览器 localStorage 键：`lg:chat:apiKey` 后刷新页面。
5. 用命令行验证同一 token 能过后端：

```bash
TOKEN=$(uv run python scripts/keycloak_token.py)
curl -i -H "Authorization: Bearer $TOKEN" http://127.0.0.1:2024/info
```

如果第 5 步是 `200`，但前端仍 `401`，通常是前端环境变量未生效（需要重启 `pnpm dev`）。

## 已确认的后续计划（暂不在本轮实施）

我们已确认：

1. 当前保留“自动获取 token”模式用于本地开发提效。
2. 后续版本会移除固定 `username/password` 方案，改为标准 Keycloak 浏览器登录流（OIDC Authorization Code + PKCE）。
3. 浏览器登录流落地后，前端不再依赖 `KEYCLOAK_TOKEN_USERNAME/KEYCLOAK_TOKEN_PASSWORD`。

本章节用于记录决策，避免后续重复讨论。

## 前端标准登录流（OIDC Code + PKCE，已落地）

已新增前端浏览器登录流，不再依赖固定用户名/密码换 token：

- 登录页：`/auth/login`
- 回调页：`/auth/callback`
- code->token 交换接口：`/api/auth/oidc/token`

### 前端环境变量

在 `agent-chat-ui/.env` 配置：

```env
NEXT_PUBLIC_OIDC_ENABLED=true
NEXT_PUBLIC_KEYCLOAK_ISSUER=http://127.0.0.1:18080/realms/agent-platform
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=agent-proxy

# 服务端 token 交换使用（route handler）
KEYCLOAK_CLIENT_ID=agent-proxy
KEYCLOAK_ISSUER=http://127.0.0.1:18080/realms/agent-platform
```

### Keycloak Client 必需设置

- `Client authentication = Off`（public client）
- `Standard flow = On`
- `Valid redirect URIs` 包含：`http://127.0.0.1:3000/auth/callback`
- `Web origins` 包含：`http://127.0.0.1:3000`

### 使用方式

1. 打开 `http://127.0.0.1:3000/auth/login`
2. 可选两种登录方式：
   - 浏览器跳转：点击 `Continue with Keycloak`
   - 账户密码直登：填写 `username/password`，点击 `Sign in with account`
3. 登录后回到 `workspace`，token 自动写入浏览器存储并用于 API 调用

> 兼容说明：原 `/api/keycloak-token` 自动模式仍可保留作本地兜底，但推荐默认使用 OIDC 浏览器登录流。

### Chat CORS 快速规则（本地）

- 浏览器端 Chat 请求建议走 `http://localhost:2024`（或同源 `/api` 代理）。
- 不要让浏览器直接请求 `http://127.0.0.1:8123`，否则容易出现 `Access-Control-Allow-Origin` 与 `http://localhost:3000` 不一致。
- 如果看到 `/threads/search` 或 `/info` CORS 报错，先检查 URL 参数 `apiUrl` 是否被写成了 `127.0.0.1:8123`。

## 重要：两条“必须重做”

1. 你修改了 Keycloak 的 Audience Mapper 后，**必须重新获取一枚新 token**（旧 token 不会自动更新 `aud`）。
2. 你修改了 `.env`（如 `KEYCLOAK_AUDIENCE`）后，**必须重启 FastAPI 服务**（热更新不保证重载环境变量）。

## 典型错误对照

- `invalid_client`
  - client 没设成 public，或 `client_id` 错，或 realm 用错
- `invalid_grant: Account is not fully set up`
  - 用户资料不完整（email/first/last）或密码仍是 temporary
- `401 invalid_token`（调用代理时）
  - `KEYCLOAK_ISSUER` 或 `KEYCLOAK_AUDIENCE` 不匹配（本地先用 `account`）

## 把 token 的受众配置为 `agent-proxy`（生产推荐）

当你准备把 `.env` 切回 `KEYCLOAK_AUDIENCE=agent-proxy` 时，先在 Keycloak 配置 audience mapper。

### UI 操作步骤

1. 进入 Realm：`agent-platform`
2. `Client scopes` -> `Create client scope`
   - Name: `agent-proxy-audience`
   - Type: `Default`
   - Protocol: `openid-connect`
3. 进入该 scope -> `Mappers` -> `Add mapper` -> 选择 `Audience`
   - Name: `aud-agent-proxy`
   - Included Client Audience: `agent-proxy`
   - Add to access token: `ON`
   - Add to ID token: `OFF`（可选）
4. 进入 `Clients` -> `agent-proxy` -> `Client scopes`
   - 把 `agent-proxy-audience` 加到 `Assigned default client scopes`
5. 重新获取新 token（旧 token 不会自动更新 `aud`）

### 验证 `aud` 是否包含 `agent-proxy`

```bash
curl -sS \
  -X POST "http://127.0.0.1:18080/realms/agent-platform/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=agent-proxy" \
  -d "username=demo_user" \
  -d "password=Demo@123456" | \
python3 -c 'import sys,json,base64; obj=json.load(sys.stdin); tok=obj.get("access_token",""); p=tok.split(".")[1]; p += "=" * (-len(p)%4); payload=json.loads(base64.urlsafe_b64decode(p)); print("aud=", payload.get("aud"))'
```

预期输出包含：`agent-proxy`。

## 端口冲突排查

如果打开浏览器出现 VSCode Web，而不是 Keycloak：

```bash
lsof -i :8080 -n -P
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

保持 Keycloak 在 `18080` 即可规避。

## 开发环境与生产环境访问约定

- 开发环境（推荐）：服务器仅开放 `22`，通过 SSH 隧道访问 Keycloak。
- 开发环境示例：`KEYCLOAK_ISSUER=http://127.0.0.1:18080/realms/agent-platform`（本机转发端口）。
- 生产环境建议：Keycloak 优先走内网与统一反向代理，对外访问按需开放并强制 TLS。
- 生产环境不要直接公网暴露 PostgreSQL；数据库只保留私网访问。
- 详细网络边界与端口策略见：`docs/server-migration-guide.md`。
