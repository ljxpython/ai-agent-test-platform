# SSH 开发隧道教学文档

## 1. 这份文档解决什么问题

如果你之前不熟悉 SSH 隧道，这两个脚本可以把“远程开发环境里的基础设施服务”安全地映射到你本机端口上，让你在本地开发时，像连本机服务一样去连远端服务。

对应脚本：

- `scripts/dev_tunnel_up.sh`：启动 SSH 隧道。
- `scripts/dev_tunnel_down.sh`：关闭 SSH 隧道。

适用场景：

- 前端、本地后端，需要联调远端 Keycloak / OpenFGA / PostgreSQL / Ollama / Runtime。
- 远端开发机只开放 SSH，不希望把业务端口直接暴露到公网。
- 你希望本地保留真实认证与授权链路，而不是走本地绕过模式。

---

## 2. 先用一句人话理解 SSH 隧道

你可以把 SSH 隧道理解成：

> 在你本机和远程服务器之间，临时拉了一根“只给你自己用的专线”。

比如：

- 你访问本机 `127.0.0.1:28080`
- 实际会被 SSH 转发到远程服务器的 `127.0.0.1:18080`

所以对你本地程序来说，它看到的仍然是本机地址；但真正提供服务的，是远端机器上的 Keycloak / OpenFGA / PostgreSQL 等服务。

这个方案的好处是：

- 远端业务端口不需要暴露公网。
- 本地应用配置简单，统一指向 `127.0.0.1`。
- 认证、权限、数据库这些联调链路更接近真实环境。

### 2.1 图解：请求是怎么被转发的

```text
+---------------------+          SSH Tunnel           +----------------------+
| 你的本地开发机       | ============================> | 远程开发服务器        |
|                     |                               |                      |
| 前端 / 本地后端      | ---- http://127.0.0.1:28080 -> Keycloak :18080 |
|                     | ---- http://127.0.0.1:28081 -> OpenFGA  :18081 |
| .env 里配置的是本机  | ----      127.0.0.1:15432 -> Postgres :5432  |
| 127.0.0.1:*         | ---- http://127.0.0.1:11143 -> Ollama   :11434 |
|                     | ---- http://127.0.0.1:8123  -> Runtime  :8123  |
+---------------------+                               +----------------------+

你看到的是本机端口。
SSH 做的是把这些本机端口，安全转发到远端机器自己的服务端口。
```

---

## 3. 这两个脚本到底做了什么

### 3.1 `scripts/dev_tunnel_up.sh`

这个脚本负责启动一个后台 SSH 进程，并建立多组本地端口转发。

默认转发关系如下：

| 本地访问地址 | 远端实际地址 | 服务 |
| --- | --- | --- |
| `127.0.0.1:28080` | `127.0.0.1:18080` | Keycloak |
| `127.0.0.1:28081` | `127.0.0.1:18081` | OpenFGA |
| `127.0.0.1:15432` | `127.0.0.1:5432` | PostgreSQL |
| `127.0.0.1:11143` | `127.0.0.1:11434` | Ollama |
| `127.0.0.1:8123` | `127.0.0.1:8123` | Runtime |

它还做了 4 件很重要的事：

1. 检查 PID 文件 ` .cache/dev_tunnel_ssh.pid ` 是否已记录运行中的隧道。
2. 检查本地 `LOCAL_KEYCLOAK_PORT` 默认端口 `28080` 是否已被监听。
3. 如果监听这个端口的本来就是 `ssh` 进程，则认为隧道已经存在，不重复启动。
4. 启动成功后，把实际 SSH 进程 PID 写回 `.cache/dev_tunnel_ssh.pid`，方便后续关闭。

这说明脚本是**幂等**的：

- 重复执行 `up`，不会无限创建新的 SSH 隧道。
- 但如果本地端口被别的非 SSH 程序占用，它会直接报错退出。

### 3.2 `scripts/dev_tunnel_down.sh`

这个脚本负责停止之前的 SSH 隧道。

它的停止逻辑分两层：

1. 先读 `.cache/dev_tunnel_ssh.pid`，如果 PID 存在且进程还活着，就直接 `kill`。
2. 如果 PID 文件失效，再通过本地 `LOCAL_KEYCLOAK_PORT` 默认端口 `28080` 去查监听进程，确认它是目标 SSH 命令后再停止。

这说明即使你误删了 PID 文件，或者 PID 文件和真实进程不同步，它仍然有一定的兜底能力。

---

## 4. 前置条件

在使用前，请确认下面几件事：

### 4.1 你能登录远程机器

脚本默认使用以下 SSH 连接参数：

- `SSH_HOST=61.147.247.83`
- `SSH_PORT=10526`
- `SSH_USER=root`

也就是说，脚本最终会执行类似：

```bash
ssh -p 10526 root@61.147.247.83
```

如果你连基础 SSH 登录都不通，隧道自然也起不来。

### 4.2 本机要有 `ssh` 和 `lsof`

脚本依赖：

- `ssh`：建立隧道
- `lsof`：检查端口占用、反查监听进程 PID

### 4.3 远端服务本身要已经启动

脚本只负责“打通通道”，不负责“启动服务”。

也就是说，远端这些服务需要先在服务器上正常运行：

- Keycloak
- OpenFGA
- PostgreSQL
- Ollama
- Runtime

如果远端服务没启动，隧道可以建立，但你访问过去仍然会失败。

---

## 5. 最快上手：第一次怎么用

### 5.1 启动隧道

推荐方式：

```bash
make dev-up
```

等价命令：

```bash
bash scripts/dev_tunnel_up.sh
```

成功后你会看到类似输出：

```bash
Tunnel started: pid=12345
Keycloak: http://127.0.0.1:28080
OpenFGA:  http://127.0.0.1:28081
Postgres: 127.0.0.1:15432
Ollama:   http://127.0.0.1:11143
Runtime:  http://127.0.0.1:8123
```

这时表示：你的本机端口已经能代表远端服务端口。

### 5.2 检查隧道和服务是否通

仓库已经提供了一个最小检查命令：

```bash
make dev-check
```

它会检查：

- `http://127.0.0.1:2024/_proxy/health`
- `http://127.0.0.1:8123/info`

注意：

- `dev-check` 默认假设你的本地代理服务已经跑在 `127.0.0.1:2024`。
- 如果你还没启动本地后端，`health` 检查会失败，但 Runtime 可能仍然是通的。

### 5.3 关闭隧道

```bash
make dev-down
```

等价命令：

```bash
bash scripts/dev_tunnel_down.sh
```

---

## 6. 你本地应该怎么配 `.env`

先记住一个关键事实：

- 服务启动时只会读取仓库根目录的 `.env`
- `config/environments/.env.dev.tunnel.example` 只是“tunnel 联调模板”
- 切换环境的本质不是让程序自动读不同文件，而是把目标模板复制成根目录 `.env`

如果你是“本地代码 + 远端基础设施联调”，应该优先使用：

- `config/environments/.env.dev.tunnel.example`

这个模板的核心思想是：

- 当前后端真正使用的远端依赖，主要是 Runtime 和数据库。
- 认证改为仓库内自建 JWT，不再依赖 Keycloak / OpenFGA 配置项。
- 隧道仍然会额外暴露 Keycloak / OpenFGA / Ollama 端口，但它们现在属于可选联调能力，不是当前后端主链路必填项。

### 6.1 推荐起步方式

```bash
cp config/environments/.env.dev.tunnel.example .env
```

然后按你的真实环境补齐敏感值，例如：

- `DATABASE_URL` 里的 PostgreSQL 密码
- `JWT_ACCESS_SECRET`
- `JWT_REFRESH_SECRET`
- `BOOTSTRAP_ADMIN_PASSWORD`

### 6.2 关键配置解释

`config/environments/.env.dev.tunnel.example` 里最关键的是这些项：

```env
LANGGRAPH_UPSTREAM_URL=http://127.0.0.1:8123

AUTH_REQUIRED=true
LANGGRAPH_AUTH_REQUIRED=true
LANGGRAPH_SCOPE_GUARD_ENABLED=true

PLATFORM_DB_ENABLED=true
PLATFORM_DB_AUTO_CREATE=false
DATABASE_URL=postgresql+psycopg://agent:<pg-password>@127.0.0.1:15432/agent_platform

JWT_ACCESS_SECRET=<set-a-local-dev-secret>
JWT_REFRESH_SECRET=<set-a-local-dev-secret>

BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=<set-a-local-dev-password>
```

你可以这样理解：

- `127.0.0.1:15432` 其实是远端 PostgreSQL
- `127.0.0.1:8123` 其实是远端 Runtime
- `127.0.0.1:28080` / `127.0.0.1:28081` / `127.0.0.1:11143` 是脚本顺带暴露出来的可选远端服务端口

所以 `.env` 看起来像在连本机，实际上是在借 SSH 隧道连远端。

如果你要在不同环境之间切换，推荐直接覆盖根目录 `.env`：

```bash
# 最小本地启动模板
cp .env.example .env

# 本地代码 + 本地 PostgreSQL
cp config/environments/.env.dev.example .env

# 本地代码 + SSH 隧道联调远端基础设施
cp config/environments/.env.dev.tunnel.example .env

# 预发配置模板
cp config/environments/.env.staging.example .env

# 生产配置模板
cp config/environments/.env.prod.example .env
```

复制之后，再按真实环境补齐密码、密钥等敏感值。

---

## 7. 脚本里可覆盖的环境变量

如果默认值不适合你，可以在执行时覆盖。

### 7.1 SSH 连接相关

```bash
SSH_HOST=your-server \
SSH_PORT=22 \
SSH_USER=ubuntu \
bash scripts/dev_tunnel_up.sh
```

可覆盖项：

- `SSH_HOST`
- `SSH_PORT`
- `SSH_USER`

### 7.2 本地端口相关

如果你本机端口冲突，也可以改本地监听端口：

```bash
LOCAL_KEYCLOAK_PORT=38080 \
LOCAL_OPENFGA_PORT=38081 \
LOCAL_PG_PORT=25432 \
LOCAL_OLLAMA_PORT=21143 \
LOCAL_RUNTIME_PORT=9123 \
bash scripts/dev_tunnel_up.sh
```

可覆盖项：

- `LOCAL_KEYCLOAK_PORT`，默认 `28080`
- `LOCAL_OPENFGA_PORT`，默认 `28081`
- `LOCAL_PG_PORT`，默认 `15432`
- `LOCAL_OLLAMA_PORT`，默认 `11143`
- `LOCAL_RUNTIME_PORT`，默认 `8123`

### 7.3 远端端口相关

如果服务器实际服务端口和默认值不一样，也可以覆盖：

- `REMOTE_KEYCLOAK_PORT`，默认 `18080`
- `REMOTE_OPENFGA_PORT`，默认 `18081`
- `REMOTE_PG_PORT`，默认 `5432`
- `REMOTE_OLLAMA_PORT`，默认 `11434`
- `REMOTE_RUNTIME_PORT`，默认 `8123`

例如：

```bash
REMOTE_PG_PORT=6543 bash scripts/dev_tunnel_up.sh
```

### 7.4 PID 文件位置

默认 PID 文件是：

- `.cache/dev_tunnel_ssh.pid`

如果你想做多套并行隧道，理论上可以覆盖：

```bash
PID_FILE=.cache/dev_tunnel_ssh.staging.pid bash scripts/dev_tunnel_up.sh
```

但要注意：如果你做了这种覆盖，本地端口也最好一起改，避免多条隧道互相冲突。

---

## 8. 建议的日常开发流程

如果你是第一次接触这套方式，可以按下面顺序执行。

### 8.1 每天开始开发时

```bash
make dev-up
cp config/environments/.env.dev.tunnel.example .env
```

然后补齐 `.env` 中的敏感值，再启动本地后端：

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 2024 --reload
```

### 8.2 做联调验证

```bash
make dev-check
```

如果需要人工验证，也可以直接访问：

- `http://127.0.0.1:28080`：Keycloak
- `http://127.0.0.1:28081/healthz`：OpenFGA 健康检查
- `http://127.0.0.1:8123/info`：Runtime 信息
- `127.0.0.1:15432`：PostgreSQL 连接入口

### 8.3 开发结束后

```bash
make dev-down
```

这是个好习惯：

- 不留多余 SSH 进程
- 不占着本地端口
- 下次启动更容易判断当前状态

---

## 9. 常见问题与排查

### 9.1 执行 `make dev-up`，提示隧道已经在运行

可能输出：

```bash
Tunnel already running (pid=12345).
```

或者：

```bash
Tunnel already listening on 28080 (pid=12345).
```

这通常不是错误，而是说明已有 SSH 隧道存在。

你可以直接继续使用，或者先执行：

```bash
make dev-down
```

再重新启动。

### 9.2 提示端口被占用

可能输出：

```bash
Port 28080 is already in use by non-ssh process (pid=xxxx).
```

这表示本地 `28080` 已经被别的程序占用了，而不是 SSH 隧道。

处理方式有两种：

1. 关掉占用该端口的本地程序。
2. 换一个本地端口重新启动隧道。

例如：

```bash
LOCAL_KEYCLOAK_PORT=38080 bash scripts/dev_tunnel_up.sh
```

但注意：只要你改了本地端口，`.env` 里对应地址也必须一起改。

### 9.3 隧道起成功了，但服务访问失败

这通常不是 SSH 本身的问题，而是下面几类原因：

1. 远端服务没启动。
2. 远端服务虽然启动了，但并没有监听脚本假定的端口。
3. 你的 `.env` 仍然指向旧地址，而不是新的本地隧道端口。
4. 本地代理服务没启动，所以 `make dev-check` 里的 `health` 项失败。

### 9.4 `make dev-down` 没找到进程

可能输出：

```bash
No matching tunnel process found.
```

这一般表示：

- 隧道本来就没启动
- PID 文件已经失效
- 当前监听 `28080` 的不是目标 SSH 进程

如果你的隧道是通过自定义端口、用户、主机或 PID 文件启动的，关闭时最好带上同样的环境变量，确保匹配到正确进程。

### 9.5 为什么 `dev-check` 没检查 Keycloak / PostgreSQL

当前 `Makefile` 里的 `dev-check` 只检查：

- 本地代理健康接口
- Runtime 信息接口

这意味着它是一个“最小可用检查”，不是“所有隧道端口的完整巡检”。

所以：

- `dev-check` 成功，说明关键链路大概率可用。
- `dev-check` 失败，不代表所有隧道都失败，需要结合具体服务逐项判断。

---

## 10. 为什么这套方式更安全

这套方案的重点不是“方便”，而是“在方便的同时不把远端服务裸露到公网”。

因为这里的设计思路是：

- 远端服务器只开放 SSH 端口。
- Keycloak / OpenFGA / PostgreSQL / Ollama / Runtime 这些服务只绑定在远端本机或内网。
- 真正需要访问时，由开发者自己从本地临时建立 SSH 隧道。

这样做的价值是：

- 暴露面更小
- 联调环境更接近真实生产边界
- 数据库和鉴权服务不容易被公网直接扫到

一句话总结：

> 不是把服务“开放出来”，而是把访问“临时带进去”。

---

## 11. 新同学可以直接照抄的最小流程

```bash
# 1) 建立 SSH 隧道
make dev-up

# 2) 准备 tunnel 模式环境变量
cp config/environments/.env.dev.tunnel.example .env

# 3) 修改 .env 中的真实密码 / store id / model id

# 4) 启动本地后端
uv run uvicorn main:app --host 0.0.0.0 --port 2024 --reload

# 5) 做最小检查
make dev-check

# 6) 结束开发后关闭隧道
make dev-down
```

如果你只记住一件事，请记住这句：

> `dev_tunnel_up.sh` 不是在启动远端服务，而是在把远端服务安全地映射到你的本机端口。
