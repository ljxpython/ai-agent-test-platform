# 常见错误与排查手册（当前栈）

## 1. 目标

记录当前实现（自建认证 + `/_management/*` + 管理界面）下的高频问题与修复方式。

## 2. 常见问题

### 2.1 `401 unauthorized`（访问管理接口）

现象：调用 `/_management/*` 返回 401。

原因：本地 token 缺失或过期。

处理：

1. 重新登录前端
2. 检查浏览器 `localStorage` 的 `oidc:token_set`
3. 确认请求头带 `Authorization: Bearer ...`

### 2.2 `403 admin_required`

现象：访问用户/项目管理接口返回 403。

原因：当前用户不具备管理员能力（非 super_admin 且无项目 admin 角色）。

处理：

1. 用管理员账号登录
2. 或在项目成员里授予 `admin`

### 2.3 `403 insufficient_project_role`

现象：项目成员管理、项目删除等操作被拒绝。

原因：当前用户在该项目角色不足。

处理：

1. 检查该项目内角色（`admin/editor/executor`）
2. 改为 `admin` 后重试

### 2.4 `409 username_already_exists`

现象：创建用户或修改用户名时报冲突。

原因：用户名唯一约束冲突。

处理：

1. 使用新用户名
2. 检查历史账号是否占用

### 2.5 项目成员删除失败（最后管理员）

现象：删除/降权最后一个项目管理员被阻止。

原因：后端保护规则生效。

处理：

1. 先补充另一个 `admin`
2. 再执行删除或降权

### 2.6 列表分页 `Go` 跳页异常

现象：输入页码后跳转不符合预期。

原因：总数变化导致偏移超出范围。

处理：

1. 使用搜索后先回到第 1 页再跳转
2. 若仍异常，清空筛选后重试

### 2.7 前端构建失败

现象：`pnpm build` 失败。

处理：

```bash
cd agent-chat-ui
pnpm install --frozen-lockfile
pnpm build
```

### 2.8 后端测试导入失败

现象：`ModuleNotFoundError: app`。

处理：

```bash
PYTHONPATH=. pytest tests/test_self_hosted_auth_basics.py
```

## 3. 推荐最小排查命令

```bash
PYTHONPATH=. pytest tests/test_self_hosted_auth_basics.py
cd agent-chat-ui && pnpm build
```

## 4. 已废弃说明

本手册不再包含 Keycloak/OpenFGA 专项故障条目；相关历史内容已归档到 `docs/archive/`。
