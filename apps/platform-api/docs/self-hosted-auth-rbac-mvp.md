# 自建认证与权限系统（MVP 决策稿）

## 1. 目标与边界

- 目标：不使用 Keycloak 和 OpenFGA，采用项目内自建认证与权限体系。
- 适用范围：账号登录、项目成员与角色管理、项目删除控制、审计留痕。
- 版本定位：MVP（先做简单、可跑、可审计）。

## 2. 已确认决策（本次讨论结论）

- 身份认证：用户名 + 密码登录。
- 账号创建：由管理员创建账号（不做自助注册）。
- 密码修改：用户可自行重置/修改密码。
- 首次登录：不强制修改密码。
- 权限来源：管理员可给其他用户赋权。
- 审计：记录关键管理与安全行为（见第 6 节最小字段）。
- 项目删除：仅管理员可删除项目。
- 后端防越权：所有写操作以后端角色校验为准，前端只做体验层限制。

## 3. 角色模型（最简 RBAC）

> 说明：RBAC = 基于角色的权限控制。当前方案采用固定角色，不引入策略引擎。

- `admin`：最高权限。
- `editor`：可管理成员（按下述边界），可进行业务写操作。
- `executor`：执行与只读能力，不可管理成员与系统配置。

### 3.1 权限边界

- `admin`
  - 可删除项目。
  - 可管理成员与角色（含提升/降级角色）。
  - 可做项目配置变更与全部业务读写。
- `editor`
  - 可管理成员，但不能将成员提升为 `admin`。
  - 可新增/移除/调整 `executor`（不含项目删除）。
  - 可进行业务读写。
- `executor`
  - 可执行任务与查看结果。
  - 不可管理成员、不可改配置、不可删除项目。

## 4. 强约束（防事故与一致性）

- 最后一个项目 `admin` 不能被移除。
- 最后一个项目 `admin` 不能被降权。
- 以上检查必须在后端事务中完成，避免并发绕过。

## 5. 删除一致性方案（推荐）

采用“两阶段删除”，避免半删状态：

1. `admin` 发起删除后，先将项目状态置为 `deleting`，并拒绝新写请求。
2. 检查并处理运行中任务（停止或等待完成，按业务规则统一）。
3. 清理项目下级资源（成员关系、业务数据等）。
4. 完成删除（软删 `deleted_at` 或物理删除二选一）。

建议：

- 审计日志不物理删除，至少保留 `project_id` 与操作快照。
- 若采用软删，默认不在业务查询返回；管理员可在审计域查询历史记录。

## 6. 审计设计（最小可用）

### 6.1 必记字段

- `who`（操作者 user_id / username）
- `when`（时间戳）
- `project`（project_id）
- `action`（动作名）
- `target`（被操作对象类型 + id）
- `before`（变更前快照，可裁剪）
- `after`（变更后快照，可裁剪）
- `result`（success / failed + 错误码）
- `ip`（来源 IP）

### 6.2 首批必须审计的动作

- 登录成功/失败。
- 账号创建、密码修改/重置。
- 成员新增、移除、角色变更。
- 项目配置修改。
- 项目删除发起/完成/失败。

## 7. 登录安全方案（按本次确认）

### 7.1 保留项

- 密码仅存哈希（推荐 Argon2id，备选 bcrypt）。
- 会话采用 Access Token + Refresh Token（Refresh 支持失效/轮换）。
- 登出后使 Refresh Token 失效。
- 全链路 HTTPS（生产环境）。

### 7.2 明确不做（当前阶段）

- 不做登录限流（允许任意 IP/地址登录）。
- 不做密码复杂度策略（如长度/字符集强制规则）。

> 注：以上两项是当前业务决策，不是通用安全最佳实践；后续可按风险再补。

## 8. 数据模型建议（MVP）

- `users`
  - `id`, `username`(unique), `password_hash`, `status`, `created_at`, `updated_at`
- `projects`
  - `id`, `name`, `status`(active/deleting/deleted), `created_at`, `updated_at`, `deleted_at`(optional)
- `project_members`
  - `id`, `project_id`, `user_id`, `role`(admin/editor/executor), `created_at`, `updated_at`
  - unique(`project_id`, `user_id`)
- `audit_logs`
  - 按第 6 节最小字段落表

## 9. API 侧校验原则

- 所有写接口统一经过后端权限校验器。
- 成员管理相关接口必须附带“最后 admin 保护”检查。
- 项目删除接口只允许 `admin`。
- 审计写入与业务事务分离或异步化时，需要保证失败可追踪（至少错误日志 + 重试）。

## 10. 下一步讨论入口

本稿完成后，下一阶段讨论：

- 代码架构分层（API / Service / Repository / Auth / Audit）。
- 技术栈选择（密码库、Token 方案、中间件组织、迁移工具）。
- 与现有代码的迁移路径（逐步替换 vs 分支重建）。

## 11. 代码架构建议（可直接落地）

### 11.1 分层原则

- API 层：只做参数校验、鉴权入口、响应组装。
- Service 层：只放业务规则（角色判断、最后 admin 保护、删除编排）。
- Repository 层：只做数据库读写，不承载业务分支。
- Middleware 层：认证上下文注入、审计写入。

### 11.2 推荐目录（在现有项目内渐进演进）

```text
app/
  api/
    management/
      auth.py            # 登录、刷新、登出、改密
      users.py           # 管理员创建账号、禁用账号
      projects.py        # 项目 CRUD（删除仅 admin）
      members.py         # 成员增删改与角色调整
  services/
    auth_service.py
    user_service.py
    project_service.py
    member_service.py
    audit_service.py
  repositories/
    user_repo.py
    project_repo.py
    member_repo.py
    token_repo.py
    audit_repo.py
  middleware/
    auth_context.py      # 解析 access token 并注入 request.state.user
    audit_log.py         # 审计记录中间件
  security/
    password.py          # hash/verify
    token.py             # JWT 签发/验签
    permission.py        # RBAC 权限矩阵 + 统一校验器
```

### 11.3 关键设计点

- 权限校验统一入口：`permission.py` 暴露 `require_role(...)`，所有写接口复用。
- “最后一个 admin 保护”只在 Service 层实现，禁止散落到 API 层。
- 项目删除走统一编排函数（两阶段删除），避免各接口重复清理逻辑。

## 12. 技术栈建议（按当前仓库最佳复用）

### 12.1 后端基础

- Web 框架：FastAPI（沿用当前）。
- 数据库：PostgreSQL（沿用当前）。
- ORM：SQLAlchemy 2.x（沿用当前）。
- 迁移：Alembic（沿用当前 migrations 体系）。

### 12.2 认证与安全

- 密码哈希：Argon2id（`argon2-cffi`），备选 bcrypt。
- Token：JWT（`PyJWT`，当前仓库已使用）。
- 会话模型：
  - Access Token（短时效，如 15~30 分钟）
  - Refresh Token（长时效，如 7~30 天，服务端可失效）
- Refresh Token 建议落库：支持登出、手动失效、异常会话回收。

### 12.3 工程配套

- 数据校验：Pydantic（沿用当前）。
- 测试：pytest（接口测试 + 权限矩阵测试 + 最后 admin 保护测试）。
- 日志：沿用当前结构化日志方案，审计写入独立表。

## 13. 迁移实施方案（分步替换，风险最低）

### 13.1 第 0 步：冻结边界

- 新分支仅新增“自建认证/RBAC”路径，不再扩展 Keycloak/OpenFGA 新能力。
- 将 Keycloak/OpenFGA 相关配置视为兼容开关，准备后续下线。

### 13.2 第 1 步：数据层落地

- 新增/调整表：`users`、`project_members`、`refresh_tokens`、`audit_logs`。
- 为 `project_members(project_id, user_id)` 建唯一索引。

### 13.3 第 2 步：认证链路落地

- 实现登录、刷新、登出、改密接口。
- 新 `auth_context` 中间件改为解析自建 JWT，并注入 `request.state.user_id`。

### 13.4 第 3 步：权限链路落地

- 接入统一 RBAC 校验器。
- 全量替换写接口到后端角色校验。
- 加入“最后一个 admin 不可移除/降权”事务保护。

### 13.5 第 4 步：项目删除与审计

- 实现两阶段删除（`active -> deleting -> deleted`）。
- 审计覆盖登录、成员管理、角色变更、项目删除等关键动作。

### 13.6 第 5 步：移除旧依赖

- 下线 Keycloak/OpenFGA 代码路径与文档入口。
- 清理对应环境变量与启动依赖。

## 14. 本阶段交付定义（完成标准）

- 管理员可创建账号，用户可登录与改密。
- `admin/editor/executor` 权限行为与第 3 节一致。
- “最后一个 admin 保护”可通过测试验证。
- 项目删除仅 admin 可执行，且走两阶段流程。
- 审计字段满足第 6 节最小集合。

## 15. 重构策略（明确不做兼容）

- 本次采用“推倒重来”策略，不保留 Keycloak/OpenFGA/旧租户授权兼容层。
- 目标是快速收敛到自建认证 + 项目级 RBAC，不为历史接口保留过渡分支。
- 旧代码删除优先，避免新旧权限模型并存导致行为冲突。

### 15.1 后端可直接删除（delete-now）

- `app/auth/keycloak.py`
- `app/auth/openfga.py`
- `config/openfga-models/v1.json`
- `config/openfga-model.json`
- `scripts/keycloak_token.py`
- `scripts/setup_openfga.py`
- `scripts/openfga_model_migrate.py`
- `scripts/openfga_model_rollback.py`
- `scripts/rbac_membership_rollback.py`
- `docs/keycloak-integration.md`
- `docs/openfga-integration.md`

### 15.2 后端必须重写（refactor）

- `app/middleware/auth_context.py`
- `app/middleware/tenant_context.py`
- `app/services/platform_common.py`
- `app/api/platform/*.py`
- `app/db/models.py`
- `app/db/access.py`
- `app/config.py`
- `app/bootstrap/lifespan.py`
- `app/api/proxy/runtime_passthrough.py`

### 15.3 后端可保留（keep）

- `app/factory.py`（应用装配壳层）
- `main.py`（启动壳层）
- `app/middleware/request_context.py`（请求追踪）
- `app/middleware/audit_log.py`（审计中间件机制，按新字段适配）

## 16. 前端重构范围与页面方案

### 16.1 前端旧链路删除/替换范围

- Provider 与上下文
  - `agent-chat-ui/src/providers/WorkspaceContext.tsx`
- 平台 API 封装（租户/旧权限语义）
  - `agent-chat-ui/src/lib/platform-api/*.ts`
- 旧认证页面与接口
  - `agent-chat-ui/src/app/auth/*`
  - `agent-chat-ui/src/app/api/keycloak-token/route.ts`
  - `agent-chat-ui/src/app/api/auth/oidc/token/route.ts`
- 旧管理页面
  - `agent-chat-ui/src/app/workspace/tenants/*`
  - `agent-chat-ui/src/app/workspace/runtime-bindings/page.tsx`
  - `agent-chat-ui/src/components/platform/scope-switcher.tsx`

### 16.2 前端 MVP 页面清单（重建后）

- `/login`：用户名密码登录。
- `/workspace/projects`：项目列表与进入项目。
- `/workspace/projects/[projectId]/members`：成员管理与角色分配。
- `/workspace/users`：账号管理（管理员创建/禁用账号）。
- `/workspace/audit`：审计日志查询。
- `/workspace/security`：个人改密码。
- `/workspace/chat`：执行与查看结果。

### 16.3 前端改造原则

- 去掉 `tenantId/projectId/assistantId` 复合上下文，收敛为“当前用户 + 当前项目”。
- 前端只做权限体验（按钮可见性），真实权限以后端 `403` 为准。
- 新 API 分组收敛为：`auth/users/projects/members/audit`。

## 17. 实施顺序（后端+前端）

1. 删除旧认证授权代码与文档入口（第 15.1 / 16.1 中 delete-now 项）。
2. 落新数据库模型与迁移（`users/project_members/refresh_tokens/audit_logs`）。
3. 实现新认证中间件与 RBAC 校验器（含最后一个 admin 保护）。
4. 重写管理 API（`users/projects/members/audit`）。
5. 重建前端 7 个 MVP 页面并切换到新 API。
6. 统一回归：权限矩阵、删除流程、审计完整性、前端 403 行为一致性。

## 18. 统一权限模型与治理规则（最终版）

本节为当前系统的唯一权限基线，后续实现与测试均以本节为准。

### 18.1 角色与主体

- 项目创建者自动成为该项目 `admin`。
- 项目内权限采用固定三角色：`admin / editor / executor`。
- 项目 `admin` 权限：项目内增删改查、成员加入/移除、角色分配。
- `super_admin`（系统超级管理员）：可管理任何项目（跨项目最高权限）。

### 18.2 可见性与访问范围

- 普通用户只能看到自己加入的项目。
- `super_admin` 可看到全部项目。
- 用户被禁用后自动失去项目访问权限，但历史审计记录必须保留。

### 18.3 强约束规则

- 最后一个项目 `admin` 不能被移除。
- 最后一个项目 `admin` 不能被降权。
- 项目删除权限：仅项目 `admin` 或 `super_admin` 可执行。
- 角色授予边界：项目 `admin` 不能授予/变更 `super_admin`。
- `super_admin` 仅允许通过系统级用户管理能力调整，不走项目成员接口。

### 18.4 审计要求

- 审计必须覆盖：成员增删、角色变更、项目删除、账号状态变更（禁用/启用）。
- 审计记录应包含：操作者、目标对象、动作类型、前后快照、结果、时间、项目维度。
- 审计数据保留，不因离职/禁用而删除。

## 19. 当前实现状态（精简版）

### 19.1 后端

- 已切换到自建认证与管理路由：`/_management/*`。
- 已移除 Keycloak/OpenFGA 相关代码路径与脚本。
- 已落地最小链路：`auth/users/projects/members/audit`。

### 19.2 前端

- 已移除旧 `tenant`/`platform-api` 页面与依赖。
- 当前保留页面：
  - `/auth/login`
  - `/workspace/projects`
  - `/workspace/projects/[projectId]/members`
  - `/workspace/users`
  - `/workspace/audit`
  - `/workspace/security`
  - `/workspace/chat`

### 19.3 本地配置

- 后端使用自建认证配置。
- 本地数据库：统一使用 PostgreSQL，例如：`DATABASE_URL=postgresql+psycopg://agent:<pg-password>@127.0.0.1:5432/agent_platform`。
- 前端已关闭 OIDC/auto token，直接调用后端。

## 20. 下一阶段改造清单（不含代码）

### 20.1 后端

- 在成员管理接口统一落实“最后 admin 保护”。
- 在项目删除接口统一落实“admin/super_admin 才可删”。
- 严格限制项目接口不得修改 `is_super_admin`。
- 用户 `status != active` 时鉴权直接拒绝。
- 审计事件类型统一：`member_added/member_removed/role_changed/project_deleted/user_disabled`。

### 20.2 前端

- 用户页明确区分 `super_admin`（系统级）与 `project role`（项目级）。
- 最后 admin 场景下，删除/降权按钮置灰并给出原因提示。
- 审计页补齐事件与对象筛选能力。

### 20.3 数据库

- `users`：`status(active/disabled)` + `is_super_admin`。
- `project_members`：`role(admin/editor/executor)` + 唯一约束 `(project_id, user_id)`。
- `audit_logs`：可记录操作者、对象、动作、前后快照、结果、时间、项目维度，并长期保留。
