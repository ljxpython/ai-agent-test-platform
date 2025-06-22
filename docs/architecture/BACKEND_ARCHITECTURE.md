# 后端架构详细文档

## 概述

本项目后端采用现代化的Python技术栈，基于FastAPI框架构建高性能异步Web服务，使用工厂模式进行应用初始化，采用分层架构设计，支持AI智能体集成和企业级权限管理。

## 技术栈

### 核心框架
- **FastAPI 0.104+**: 高性能异步Web框架，支持自动API文档生成
- **Tortoise ORM**: 异步数据库ORM，类似Django ORM的异步版本
- **多数据库支持**: 支持MySQL、PostgreSQL、SQLite等主流关系数据库
- **Aerich**: Tortoise ORM的数据库迁移工具
- **Poetry**: Python依赖管理和虚拟环境工具

### AI集成
- **AutoGen 0.5.7**: Microsoft开源的多智能体对话框架
- **LlamaIndex**: 文档解析和RAG（检索增强生成）框架
- **OpenAI API**: 支持多种大语言模型（GPT、DeepSeek等）

### 安全认证
- **JWT (JSON Web Tokens)**: 无状态用户认证
- **bcrypt**: 密码哈希加密
- **RBAC**: 基于角色的访问控制

### 工具库
- **Loguru**: 现代化日志记录库
- **Pydantic**: 数据验证和序列化
- **python-multipart**: 文件上传支持
- **python-jose**: JWT令牌处理

## 项目结构

```
backend/
├── __init__.py                 # 工厂模式应用创建入口
├── api/                        # API路由层
│   ├── __init__.py
│   └── v1/                     # API版本1
│       ├── __init__.py         # 路由注册和权限配置
│       ├── auth.py             # 认证相关API
│       ├── chat.py             # AI对话API
│       ├── testcase.py         # 测试用例生成API
│       ├── midscene.py         # Midscene智能体API
│       └── system.py           # 系统管理API
├── controllers/                # 控制器层
│   ├── __init__.py
│   ├── auth_controller.py      # 认证控制器
│   ├── chat_controller.py      # 对话控制器
│   ├── testcase_controller.py  # 测试用例控制器
│   └── system_controller.py    # 系统管理控制器
├── services/                   # 业务服务层
│   ├── __init__.py
│   ├── auth_service.py         # 认证服务
│   ├── autogen_service.py      # AutoGen智能体服务
│   ├── testcase_service.py     # 测试用例生成服务
│   ├── midscene_service.py     # Midscene智能体服务
│   ├── document_service.py     # 文档处理服务
│   ├── file_processor.py       # 文件处理器
│   ├── image_analyzer.py       # 图像分析服务
│   └── permission_service.py   # 权限管理服务
├── models/                     # 数据模型层
│   ├── __init__.py
│   ├── base.py                 # 基础模型类
│   ├── user.py                 # 用户模型
│   ├── auth.py                 # 认证相关模型
│   ├── chat.py                 # 对话消息模型
│   ├── testcase.py             # 测试用例模型
│   ├── midscene.py             # Midscene相关模型
│   ├── role.py                 # 角色模型
│   ├── department.py           # 部门模型
│   └── api.py                  # API权限模型
├── schemas/                    # 数据模式定义
│   ├── __init__.py
│   ├── base.py                 # 基础模式类
│   └── system.py               # 系统相关模式
├── core/                       # 核心功能模块
│   ├── __init__.py
│   ├── init_app.py             # 应用初始化（工厂模式）
│   ├── database.py             # 数据库配置和初始化
│   ├── security.py             # 安全工具（密码哈希、JWT）
│   ├── dependency.py           # 权限依赖注入
│   ├── deps.py                 # 通用依赖注入
│   ├── exceptions.py           # 自定义异常类
│   ├── logger.py               # 日志配置
│   ├── llm.py                  # LLM客户端管理
│   ├── crud.py                 # 通用CRUD操作
│   ├── ctx.py                  # 上下文管理
│   └── config_validator.py     # 配置验证
├── conf/                       # 配置文件
│   ├── __init__.py
│   ├── config.py               # 配置类定义
│   ├── constants.py            # 常量定义
│   ├── settings.yaml           # 主配置文件
│   ├── settings.local.yaml     # 本地配置文件
│   └── file_extractor_config.py # 文件提取配置
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── jwt_utils.py            # JWT工具函数
│   └── password.py             # 密码处理工具
├── data/                       # 数据存储
│   └── aitestlab.db            # SQLite数据库文件
└── migrations/                 # 数据库迁移文件
    └── models/                 # 迁移模型
```

## 架构设计模式

### 1. 工厂模式 (Factory Pattern)

**位置**: `backend/core/init_app.py` 和 `backend/__init__.py`

**作用**: 统一管理应用的创建和初始化过程

**核心函数**:
```python
# backend/__init__.py
def create_app() -> FastAPI:
    """工厂函数：创建FastAPI应用实例"""

# backend/core/init_app.py
async def init_data(app=None):
    """初始化应用数据"""

def make_middlewares() -> List[Middleware]:
    """创建和配置中间件"""

def register_exceptions(app: FastAPI):
    """注册异常处理器"""

def register_routers(app: FastAPI, prefix: str = "/api"):
    """注册应用路由"""
```

**使用方式**:
```python
# main.py
from backend import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. 分层架构 (Layered Architecture)

**API层 → 控制器层 → 服务层 → 模型层**

**API层** (`backend/api/v1/`):
- 处理HTTP请求和响应
- 参数验证和序列化
- 路由定义和权限控制

**控制器层** (`backend/controllers/`):
- 业务逻辑协调
- 调用服务层方法
- 异常处理

**服务层** (`backend/services/`):
- 核心业务逻辑实现
- 数据处理和转换
- 外部服务集成

**模型层** (`backend/models/`):
- 数据库模型定义
- 数据关系映射
- 数据验证规则

### 3. 依赖注入 (Dependency Injection)

**位置**: `backend/core/dependency.py` 和 `backend/core/deps.py`

**权限依赖**:
```python
# backend/core/dependency.py
DependAuth = Depends(verify_token)           # 仅认证
DependPermission = Depends(check_permission) # 权限检查
DependAdmin = Depends(check_admin)           # 管理员权限
```

**使用示例**:
```python
# backend/api/v1/system.py
@router.get("/users", dependencies=[DependPermission])
async def get_users():
    """获取用户列表 - 需要权限检查"""

@router.post("/users", dependencies=[DependAdmin])
async def create_user():
    """创建用户 - 需要管理员权限"""
```

## 数据库设计

### 数据库配置

**位置**: `backend/core/database.py`

**多数据库支持**:
项目基于Tortoise ORM，支持多种主流关系数据库：

**SQLite配置** (默认，适合开发和小型部署):
```python
DATABASE_URL = f"sqlite://{db_file}"
```

**MySQL配置** (适合生产环境):
```python
DATABASE_URL = "mysql://user:password@localhost:3306/aitestlab"
```

**PostgreSQL配置** (适合大型应用):
```python
DATABASE_URL = "postgres://user:password@localhost:5432/aitestlab"
```

**Tortoise ORM统一配置**:
```python
TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "backend.models.user",
                "backend.models.chat",
                "backend.models.testcase",
                "backend.models.midscene",
                "backend.models.role",
                "backend.models.department",
                "backend.models.api",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
```

### 核心数据模型

**基础模型** (`backend/models/base.py`):
```python
class BaseModel(models.Model):
    """基础模型类，提供通用字段和方法"""
    id = fields.BigIntField(pk=True, index=True)

    async def to_dict(self, m2m: bool = False, exclude_fields: list[str] | None = None):
        """转换为字典格式"""

class TimestampMixin:
    """时间戳混入类"""
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True, index=True)
```

**用户模型** (`backend/models/user.py`):
```python
class User(BaseModel, TimestampMixin):
    """用户模型"""
    username = fields.CharField(max_length=50, unique=True, index=True)
    email = fields.CharField(max_length=100, unique=True, index=True)
    password_hash = fields.CharField(max_length=255)
    full_name = fields.CharField(max_length=100, null=True)
    is_active = fields.BooleanField(default=True)
    is_superuser = fields.BooleanField(default=False)

    # 关联关系
    dept = fields.ForeignKeyField("models.Department", related_name="users")
    roles = fields.ManyToManyField("models.Role", related_name="users")
```

### 数据库迁移

**工具**: Aerich (Tortoise ORM的迁移工具，支持所有数据库)

**配置**: `pyproject.toml`
```toml
[tool.aerich]
tortoise_orm = "backend.core.database.TORTOISE_ORM"
location = "./migrations"
src_folder = "./."
```

**常用命令** (适用于所有支持的数据库):
```bash
# 初始化迁移
aerich init -t backend.core.database.TORTOISE_ORM

# 生成迁移文件
aerich migrate

# 应用迁移
aerich upgrade

# 查看迁移历史
aerich history

# 回滚迁移
aerich downgrade
```

### 数据库选择指南

**SQLite** (默认):
- ✅ 适合: 开发环境、小型应用、单机部署
- ✅ 优势: 零配置、文件存储、轻量级
- ❌ 限制: 并发写入有限、不适合大型应用

**MySQL**:
- ✅ 适合: 生产环境、中大型应用、高并发场景
- ✅ 优势: 成熟稳定、性能优秀、生态丰富
- ⚙️ 配置: 需要安装MySQL服务器和客户端库

**PostgreSQL**:
- ✅ 适合: 复杂查询、大数据量、企业级应用
- ✅ 优势: 功能强大、标准兼容、扩展性好
- ⚙️ 配置: 需要安装PostgreSQL服务器和客户端库

**数据库切换**:
```python
# 环境变量方式配置
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://./data/aitestlab.db")

# 配置文件方式
# backend/conf/settings.yaml
database:
  url: "mysql://user:password@localhost:3306/aitestlab"
  # 或
  url: "postgres://user:password@localhost:5432/aitestlab"
  # 或
  url: "sqlite://./data/aitestlab.db"
```

## AI智能体集成

### AutoGen服务

**位置**: `backend/services/autogen_service.py`

**核心功能**:
- 多智能体对话管理
- 流式响应处理
- 智能体生命周期管理

**使用示例**:
```python
# 创建智能体服务
service = AutoGenService()

# 流式对话
async for chunk in service.run_stream(conversation_id, message):
    if chunk.type == "streaming_chunk":
        # 处理流式数据
        yield chunk.data
    elif chunk.type == "text_message":
        # 处理完整消息
        yield chunk.content
```

### 测试用例生成服务

**位置**: `backend/services/testcase_service.py`

**智能体协作流程**:
1. **需求分析智能体**: 解析用户需求和文档
2. **测试用例生成智能体**: 生成初始测试用例
3. **用户反馈处理**: 收集用户反馈意见
4. **质量评审智能体**: 根据反馈优化用例

**使用示例**:
```python
# 生成测试用例
async for chunk in testcase_service.generate_testcase_stream(
    conversation_id=conversation_id,
    user_input=user_input,
    uploaded_files=files
):
    yield chunk
```

### Midscene智能体服务

**位置**: `backend/services/midscene_service.py`

**四智能体协作**:
1. **UI分析智能体**: 分析界面截图
2. **交互分析智能体**: 设计交互流程
3. **Midscene生成智能体**: 生成YAML配置
4. **脚本生成智能体**: 生成Playwright脚本

**并行处理**:
```python
# UI分析和交互分析并行执行
ui_task = asyncio.create_task(ui_agent.analyze(image))
interaction_task = asyncio.create_task(interaction_agent.analyze(requirements))

ui_result, interaction_result = await asyncio.gather(ui_task, interaction_task)
```

## 安全认证系统

### JWT认证

**位置**: `backend/core/security.py`

**核心功能**:
```python
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """创建访问令牌"""

def verify_token(token: str) -> dict:
    """验证令牌"""

def hash_password(password: str) -> str:
    """密码哈希"""

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
```

### 权限管理

**三级权限控制**:
1. **仅认证** (`DependAuth`): 只需要有效的JWT令牌
2. **权限检查** (`DependPermission`): 检查用户是否有访问特定API的权限
3. **管理员权限** (`DependAdmin`): 需要管理员角色

**权限检查流程**:
```python
async def check_permission(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    """检查用户权限"""
    # 1. 获取请求的API路径和方法
    # 2. 查询用户角色权限
    # 3. 验证是否有访问权限
    # 4. 记录权限检查日志
```

## 配置管理

### 配置文件结构

**主配置**: `backend/conf/settings.yaml`
```yaml
test:
  # AI模型配置
  aimodel:
    model: "deepseek-chat"
    base_url: "https://api.deepseek.com/v1"
    api_key: "your-api-key"

  # AutoGen配置
  autogen:
    max_agents: 100
    cleanup_interval: 3600
    agent_ttl: 7200
```

**本地配置**: `backend/conf/settings.local.yaml`
```yaml
# 本地开发环境配置
test:
  aimodel:
    api_key: "local-dev-key"
```

### 配置类

**位置**: `backend/conf/config.py`

**使用示例**:
```python
from backend.conf.config import settings

# 获取AI模型配置
model_config = settings.test.aimodel
api_key = model_config.api_key
base_url = model_config.base_url
```

## 日志系统

### 日志配置

**位置**: `backend/core/logger.py`

**特性**:
- 基于Loguru的现代化日志系统
- 支持文件轮转和压缩
- 结构化日志输出
- 多级别日志记录

**使用示例**:
```python
from loguru import logger

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.success("成功信息")
```

## API设计规范

### RESTful API设计

**路由前缀**: `/api/v1`

**认证相关** (`/api/v1/auth`):
- `POST /login` - 用户登录
- `POST /logout` - 用户登出
- `GET /me` - 获取当前用户信息

**AI对话** (`/api/v1/chat`):
- `POST /stream` - 流式对话
- `GET /conversations` - 获取对话列表
- `DELETE /conversations/{id}` - 删除对话

**测试用例生成** (`/api/v1/testcase`):
- `POST /generate/stream` - 流式生成测试用例
- `POST /feedback` - 提交用户反馈
- `POST /upload` - 上传文档文件

**系统管理** (`/api/v1/system`):
- `GET /users` - 获取用户列表
- `POST /users` - 创建用户
- `GET /roles` - 获取角色列表
- `GET /apis` - 获取API权限列表

### 响应格式

**成功响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {...}
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "error message",
  "detail": "detailed error info"
}
```

**流式响应** (SSE):
```
data: {"type": "streaming_chunk", "content": "partial text"}

data: {"type": "text_message", "content": "complete message"}

data: {"type": "task_result", "result": {...}}
```

## 部署和运维

### 启动方式

**开发环境**:
```bash
# 使用Poetry
poetry install
poetry run python main.py

# 使用Makefile
make install
make start
```

**生产环境**:
```bash
# 使用Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 使用Gunicorn + Uvicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 环境变量

**必需环境变量**:
```bash
# AI模型配置
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# 数据库配置 (选择其中一种)
DATABASE_URL=sqlite:///./data/aitestlab.db                    # SQLite
# DATABASE_URL=mysql://user:password@localhost:3306/aitestlab   # MySQL
# DATABASE_URL=postgres://user:password@localhost:5432/aitestlab # PostgreSQL

# JWT配置
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 性能优化

**数据库优化**:
- 合理使用索引 (适用于所有数据库)
- 异步查询操作 (Tortoise ORM原生支持)
- 连接池管理 (MySQL/PostgreSQL自动管理)
- 查询优化 (根据具体数据库特性优化)

**缓存策略**:
- 用户权限缓存
- API权限缓存
- 智能体实例缓存

**并发处理**:
- FastAPI异步支持
- 智能体并行处理
- 流式响应优化

## 扩展指南

### 添加新的API模块

1. **创建模型** (`backend/models/new_module.py`)
2. **创建服务** (`backend/services/new_service.py`)
3. **创建控制器** (`backend/controllers/new_controller.py`)
4. **创建API路由** (`backend/api/v1/new_api.py`)
5. **注册路由** (`backend/api/v1/__init__.py`)

### 集成新的AI模型

1. **更新配置** (`backend/conf/settings.yaml`)
2. **扩展LLM客户端** (`backend/core/llm.py`)
3. **创建智能体服务** (`backend/services/new_agent_service.py`)
4. **添加API接口** (`backend/api/v1/new_agent.py`)

### 添加新的权限级别

1. **定义权限依赖** (`backend/core/dependency.py`)
2. **更新权限检查逻辑** (`backend/services/permission_service.py`)
3. **添加权限数据** (`backend/core/database.py`)
4. **应用到API路由** (`backend/api/v1/`)

这个后端架构文档为开发者提供了完整的技术指南，帮助理解项目结构、设计模式和扩展方法。
