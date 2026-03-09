# CI 失败排查（当前版本）

## 1. 适用范围

本文件用于排查“当前代码基线”下的构建/测试失败，基线为：

- 自建认证
- `/_management/*` 管理接口
- `agent-chat-ui` 管理界面

## 2. 当前建议流水线

按顺序执行本地同等命令：

```bash
PYTHONPATH=. pytest tests/test_self_hosted_auth_basics.py
cd agent-chat-ui && pnpm build
```

如果以上命令本地都通过，CI 失败通常是环境差异。

## 3. 常见失败与处理

### 3.1 Python 导入失败（`ModuleNotFoundError: app`）

原因：未设置项目根路径。

处理：

```bash
PYTHONPATH=. pytest tests/test_self_hosted_auth_basics.py
```

### 3.2 前端依赖或锁文件不一致

原因：`pnpm-lock.yaml` 与安装环境不一致。

处理：

```bash
cd agent-chat-ui
pnpm install --frozen-lockfile
pnpm build
```

### 3.3 前端构建通过但有 ESLint warning

说明：当前仓库存在历史 warning；若非本次改动引入，可记录为非阻断。

### 3.4 环境变量导致行为差异

建议最小化环境变量，只保留必要项。

后端至少保证：

- `AUTH_REQUIRED`（按环境）
- `JWT_ACCESS_SECRET`
- `JWT_REFRESH_SECRET`
- `DATABASE_URL`（启用 DB 时）

前端至少保证：

- `NEXT_PUBLIC_API_URL`

## 4. 排查顺序（推荐）

1. 先跑后端测试（定位接口层问题）
2. 再跑前端构建（定位类型/页面问题）
3. 最后对比 CI 环境变量与本地差异

## 5. 已废弃说明

以下内容不再作为当前 CI 主流程参考：

- Keycloak/OpenFGA 初始化链路
- `smoke-e2e.yml` 工作流
