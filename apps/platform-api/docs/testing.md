# 测试与验证（当前版本）

## 1. 目标

本文件只记录当前仓库可执行、可复现的验证方式。

## 2. 后端测试

### 2.1 快速回归（推荐）

```bash
PYTHONPATH=. pytest tests/test_self_hosted_auth_basics.py
```

用途：验证自建认证与管理面基础链路（`/_management/*`）是否可用。

### 2.2 额外集成测试（按需）

```bash
PYTHONPATH=. pytest tests/test_langgraph_sdk_real_integration.py
```

说明：该用例依赖真实上游/环境准备，不作为每次改动的必跑项。

## 3. 前端验证

目录：`agent-chat-ui`

### 3.1 构建验证（推荐）

```bash
cd agent-chat-ui
pnpm build
```

用途：检查类型与构建是否通过。

### 3.2 本地运行验证

```bash
cd agent-chat-ui
pnpm dev
```

然后手工验证以下页面：

- `/workspace/projects`
- `/workspace/users`
- `/workspace/audit`
- `/workspace/me`

## 4. 变更后最小验收清单

每次涉及管理面改动，至少执行：

1. 后端：`PYTHONPATH=. pytest tests/test_self_hosted_auth_basics.py`
2. 前端：`cd agent-chat-ui && pnpm build`
3. 手工：登录后进入 `workspace`，验证关键页面可访问

## 5. 已废弃说明

以下旧路径/流程不再作为当前测试基线：

- `scripts/smoke_e2e.py`
- `.github/workflows/smoke-e2e.yml`
- 依赖 Keycloak/OpenFGA 的旧联调链路
