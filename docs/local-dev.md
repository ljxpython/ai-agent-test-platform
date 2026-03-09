# 本地开发与联调说明

## 1. 推荐启动顺序

推荐顺序：

1. 启动 `runtime-service`
2. 启动 `platform-api`
3. 启动 `platform-web`
4. 按需启动 `runtime-web`

## 2. 各应用启动命令

### 2.1 `apps/runtime-service`

```bash
cd apps/runtime-service
uv run langgraph dev --config graph_src_v2/langgraph.json --port 8123 --no-browser
```

### 2.2 `apps/platform-api`

```bash
cd apps/platform-api
uv run uvicorn main:app --host 0.0.0.0 --port 2024 --reload
```

### 2.3 `apps/platform-web`

```bash
cd apps/platform-web
pnpm dev
```

### 2.4 `apps/runtime-web`

```bash
cd apps/runtime-web
pnpm dev
```

## 3. 常用访问地址

- platform api: `http://127.0.0.1:2024`
- platform web: `http://127.0.0.1:3000`
- runtime service: `http://127.0.0.1:8123`
- runtime web: 建议本地使用单独端口，例如 `http://127.0.0.1:3001`

## 4. 建议联调关系

- `platform-web` -> `platform-api`
- `platform-api` -> `runtime-service`
- `runtime-web` -> `runtime-service`

## 5. 第一阶段原则

- 不共享 `.venv`
- 不共享 Node 依赖
- 不共享 `.env`
- 先保证独立运行和联调成功
