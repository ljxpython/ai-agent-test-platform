# 环境变量矩阵

## 1. `platform-api`

主要配置来源：

- `apps/platform-api/.env`
- `apps/platform-api/.env.example`

关键变量：

- `LANGGRAPH_UPSTREAM_URL`
- `DATABASE_URL`
- `PLATFORM_DB_ENABLED`
- `PLATFORM_DB_AUTO_CREATE`
- `AUTH_REQUIRED`
- `LANGGRAPH_AUTH_REQUIRED`
- `LANGGRAPH_SCOPE_GUARD_ENABLED`
- `JWT_ACCESS_SECRET`
- `JWT_REFRESH_SECRET`

## 2. `platform-web`

主要配置来源：

- `apps/platform-web/.env`
- `apps/platform-web/.env.example`

关键变量：

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_ASSISTANT_ID`
- 可选：`LANGGRAPH_API_URL`

## 3. `runtime-service`

主要配置来源：

- `apps/runtime-service/graph_src_v2/.env`
- `apps/runtime-service/graph_src_v2/.env.example`
- `apps/runtime-service/graph_src_v2/conf/settings.yaml`
- `apps/runtime-service/graph_src_v2/conf/settings.local.yaml`

关键变量：

- `APP_ENV`
- `MODEL_ID`
- `ENABLE_TOOLS`
- `TOOLS`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`

## 4. `runtime-web`

主要配置来源：

- `apps/runtime-web/.env`
- `apps/runtime-web/.env.example`

关键变量：

- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_ASSISTANT_ID`

## 5. 当前原则

- 四个应用的环境变量彼此独立维护
- 根目录暂不新增统一 `.env`
- 后续如果确实需要统一入口，再额外设计根级环境编排
