# 管理界面功能总览（Project / User / Audit）

## 1. 文档目标

本文件用于统一说明当前管理界面的功能、页面入口、权限边界与交互约定，作为日常开发与测试的主参考文档。

## 2. 管理界面入口

- `workspace/projects`：项目列表与项目管理入口
- `workspace/projects/new`：创建项目
- `workspace/projects/[projectId]`：项目详情
- `workspace/projects/[projectId]/members`：项目成员管理
- `workspace/users`：用户列表与编辑入口
- `workspace/users/new`：创建用户
- `workspace/users/[userId]`：管理员视角用户详情
- `workspace/audit`：审计日志
- `workspace/me`：当前登录用户资料页（My Profile）
- `workspace/security`：安全相关页面（保留）
- `workspace/runtime`：LangGraph runtime 能力总览（模型与工具）

## 3. 功能清单（按模块）

### 3.1 Projects（项目）

- 列表展示：名称、描述、状态、操作
- 支持分页、页大小切换、`Go` 跳转指定页
- 支持关键字搜索（项目名 / 描述）
- 支持删除项目（统一确认弹窗）
- 创建项目后返回项目列表

### 3.2 Project Members（项目成员）

- 展示：用户 ID、用户名、角色、操作
- 支持按用户名搜索成员
- 支持成员新增（按用户名搜索候选并排除已加入成员）
- 支持角色设置（`admin/editor/executor`）
- 支持成员移除（统一确认弹窗）
- 最后一个 `admin` 保护（不可移除/降权）

### 3.3 Users（用户）

- 列表展示：用户名、状态、是否超级管理员、操作
- 支持分页、页大小切换、`Go` 跳转指定页
- 支持按用户名搜索
- 创建用户与编辑用户分离
- 创建用户页面默认无预填（避免默认用户名/密码）

### 3.4 User Detail（管理员视角）

- 基本资料：用户名、状态、超级管理员标识、创建/更新时间
- 安全：可更新目标用户密码
- 项目权限：展示该用户的项目角色关系
- 审计摘要：展示近期相关审计
- 支持启用/禁用账号（统一确认弹窗）

### 3.5 Audit（审计）

- 展示：时间、方法、路径、状态、动作、目标
- 支持筛选：`action/target_type/target_id/method/status_code`
- 支持分页、页大小切换、`Go` 跳转指定页

### 3.6 My Profile（当前用户）

- 展示和编辑当前登录用户资料（用户名、邮箱）
- 头像与签名编辑（当前版本使用本地持久化）
- 修改密码（旧密码校验 + 新密码确认）
- 退出登录（统一确认弹窗）

## 4. 通用交互能力

### 4.1 列表通用能力

- 所有列表均包含左侧序号列 `#`
- 所有核心列表支持搜索
- 所有核心列表支持分页与指定页跳转

### 4.2 表格列拖拽

- 所有核心列表支持列宽左右拖拽
- 每列宽度独立保存（localStorage）
- 双击分隔条可恢复该列默认宽度
- 拖拽中具备高亮与鼠标 `col-resize` 交互反馈
- 表格宽度策略：`max(100%, 列宽总和)`，保证铺满容器

### 4.3 确认弹窗统一

- 删除/危险操作统一使用站内确认弹窗
- 不再使用浏览器原生 `window.confirm`

## 5. 权限边界（当前实现）

- 普通用户仅可见自己加入的项目
- `super_admin` 可管理全部项目
- 项目内角色固定：`admin/editor/executor`
- 项目管理关键写操作以后端鉴权为准，前端只做体验提示

## 6. 相关后端接口（管理面）

- `/_management/auth/*`
- `/_management/users/*`
- `/_management/projects/*`
- `/_management/projects/{project_id}/members/*`
- `/_management/audit`

## 7. 后续建议（可选）

- 将头像/签名从本地持久化升级为数据库字段持久化
- 为列拖拽增加“显示参考线”视觉反馈
- 将列表搜索与分页条进一步组件化到统一 Table 工具层
