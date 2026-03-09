# Auth / Tenant / Project 流程与架构（Mermaid）

这份文档回答三个核心问题：

1. 前端是否是先登录再选租户？
2. 租户和项目是什么关系？
3. 请求从前端到后端是如何做鉴权与租户隔离的？


## 结论先看

- 是的，正常流程是：登录 -> 选择租户 -> 选择项目。
- 一个租户可以有多个项目。
- 一个项目只属于一个租户（不是多租户共享项目）。
- 用户与租户是多对多关系，通过 membership 绑定角色（owner/admin/member）。


## 1) 前端操作流程图

```mermaid
flowchart TD
    A[打开前端 /workspace] --> B{是否已有有效 token}
    B -- 否 --> C[登录 /auth/login 或 OIDC 回调]
    C --> D[写入 lg:chat:apiKey]
    B -- 是 --> E[加载 WorkspaceContext]
    D --> E
    E --> F[调用 GET /_platform/tenants]
    F --> G{当前 tenantId 是否有效}
    G -- 否 --> H[默认选择第一个 tenant]
    G -- 是 --> I[沿用当前 tenant]
    H --> J["调用 GET /_platform/tenants/{tenant_ref}/projects"]
    I --> J
    J --> K{当前 projectId 是否有效}
    K -- 否 --> L[默认选择第一个 project]
    K -- 是 --> M[沿用当前 project]
    L --> N[进入 agents/chat/audit 等页面]
    M --> N
```


## 2) 后端鉴权与租户隔离流程图

```mermaid
sequenceDiagram
    participant UI as Frontend UI
    participant API as FastAPI
    participant Auth as auth_context
    participant Tenant as tenant_context
    participant SVC as platform services
    participant DB as PostgreSQL

    UI->>API: 请求 /_platform/* + Authorization
    API->>Auth: 验证 token, 设置 user_subject/user_id
    Auth-->>API: 通过或 401
    API->>Tenant: 解析 x-tenant-id, 校验 membership
    Tenant-->>API: 通过或 403
    API->>SVC: 执行业务（tenant/project/agent/audit）
    SVC->>DB: 读写 tenant-scoped 数据
    DB-->>SVC: 返回结果
    SVC-->>UI: JSON 响应
```


## 3) 实体关系图（ER）

```mermaid
erDiagram
    USER ||--o{ MEMBERSHIP : has
    TENANT ||--o{ MEMBERSHIP : contains
    TENANT ||--o{ PROJECT : owns
    PROJECT ||--o{ AGENT : contains
    AGENT ||--o{ RUNTIME_BINDING : has

    USER {
      uuid id
      string external_subject
      string email
    }

    TENANT {
      uuid id
      string name
      string slug
      string status
    }

    MEMBERSHIP {
      uuid id
      uuid tenant_id
      uuid user_id
      string role
    }

    PROJECT {
      uuid id
      uuid tenant_id
      string name
    }

    AGENT {
      uuid id
      uuid project_id
      string name
      string graph_id
      string runtime_base_url
    }

    RUNTIME_BINDING {
      uuid id
      uuid agent_id
      string environment
    }
```


## 4) 你问的关系是否正确

- 账号（登录身份）= 你是谁。
- 租户（tenant）= 你的组织空间。
- membership（角色）= 你在该租户里的权限。
- 项目（project）是租户下资源，`project.tenant_id` 是单值外键。

因此：

- 一个租户可以有多个项目（正确）。
- 一个项目不能属于多个租户（当前架构下不支持）。


## 5) 对应代码锚点

- 前端加载租户/项目上下文：`agent-chat-ui/src/providers/WorkspaceContext.tsx`
- 后端认证中间件：`app/middleware/auth_context.py`
- 后端租户上下文与 membership 校验：`app/middleware/tenant_context.py`
- 项目服务（租户级授权）：`app/services/project_service.py`
- 数据模型（tenant_id 外键）：`app/db/models.py`
