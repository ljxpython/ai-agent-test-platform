# 数据库管理系统

## 概述

本项目实现了完整的数据库管理系统，支持SQLite和MySQL两种数据库的动态切换和数据迁移。通过配置文件和命令行工具，可以轻松在不同数据库之间切换，满足开发和生产环境的不同需求。

## 功能特性

### ✅ 已实现功能

1. **多数据库支持**
   - SQLite：适用于开发环境和小型部署
   - MySQL：适用于生产环境和高并发场景

2. **动态配置切换**
   - 通过配置文件控制数据库类型
   - 支持运行时切换数据库配置
   - 自动生成对应的数据库连接URL

3. **数据迁移工具**
   - 从SQLite迁移到MySQL
   - 保持数据完整性和一致性
   - 支持所有表的数据迁移

4. **命令行工具**
   - 数据库状态查看
   - 连接测试
   - 配置切换
   - 数据迁移

5. **MySQL管理**
   - 自动创建数据库和用户
   - 权限配置
   - 连接测试

## 文件结构

```
backend/
├── conf/
│   ├── settings.yaml          # 数据库配置文件
│   └── config.py              # Dynaconf配置管理
├── api_core/
│   └── database.py            # 数据库初始化和连接管理
scripts/
├── migrate_database.py        # 数据库迁移脚本
├── switch_database.py         # 数据库切换脚本
└── setup_mysql.py            # MySQL设置脚本
docs/database/
├── README.md                  # 本文件
├── DATABASE_MIGRATION.md     # 详细迁移指南
└── USAGE_EXAMPLES.md         # 使用示例
Makefile                       # 包含数据库管理命令
```

## 快速开始

### 1. 查看当前配置

```bash
make db-status
```

### 2. 测试数据库连接

```bash
make test-db
```

### 3. 切换数据库类型

```bash
# 切换到SQLite
make switch-to-sqlite

# 切换到MySQL
make switch-to-mysql
```

## 配置说明

### 数据库配置结构

```yaml
test:
  database:
    # 数据库类型: sqlite, mysql
    type: "sqlite"

    # SQLite配置
    sqlite:
      path: "./data/aitestlab.db"

    # MySQL配置
    mysql:
      host: "101.126.90.71"
      port: 3306
      user: "aitestlab"
      password: "sRhSjiyhnpGz3Emr"
      database: "aitestlab"
      charset: "utf8mb4"
      # 连接池配置
      pool_size: 10
      max_overflow: 20
      pool_timeout: 30
      pool_recycle: 3600
```

### 动态URL生成

系统会根据配置自动生成对应的数据库连接URL：

- **SQLite**: `sqlite:///path/to/database.db`
- **MySQL**: `mysql://user:password@host:port/database?charset=utf8mb4`

## 可用命令

### 基础数据库管理

```bash
make init-db              # 初始化数据库
make migrate              # 运行数据库迁移
make makemigrations       # 创建新的迁移文件
make reset-db             # 重置数据库
```

### 数据库切换

```bash
make switch-to-sqlite     # 切换到SQLite数据库
make switch-to-mysql      # 切换到MySQL数据库
make db-status            # 查看当前数据库配置
make test-db              # 测试数据库连接
```

### MySQL管理

```bash
make setup-mysql          # 设置MySQL数据库
make check-mysql          # 检查MySQL连接
make migrate-sqlite-to-mysql # 从SQLite迁移到MySQL
```

## 使用场景

### 开发环境

```bash
# 使用SQLite进行快速开发
make switch-to-sqlite
make init-db
make start
```

### 生产环境

```bash
# 使用MySQL支持高并发
make setup-mysql
make switch-to-mysql
make migrate-sqlite-to-mysql  # 如果需要迁移现有数据
make start
```

### 数据迁移

```bash
# 完整的迁移流程
make setup-mysql                # 设置MySQL
make migrate-sqlite-to-mysql    # 迁移数据
make switch-to-mysql            # 切换配置
make stop && make start         # 重启应用
```

## 技术实现

### 1. 配置管理

使用Dynaconf库管理配置，支持：
- 多环境配置
- 配置文件热重载
- 环境变量覆盖

### 2. 数据库抽象

通过Tortoise ORM实现数据库抽象：
- 统一的模型定义
- 自动迁移管理
- 多数据库支持

### 3. 连接管理

动态生成数据库连接：
- 根据配置类型选择驱动
- 自动处理连接参数
- 连接池优化

### 4. 数据迁移

完整的数据迁移流程：
- 模型序列化/反序列化
- 依赖关系处理
- 错误处理和回滚

## 最佳实践

1. **开发环境使用SQLite**
   - 快速启动，无需额外配置
   - 便于调试和测试

2. **生产环境使用MySQL**
   - 更好的性能和并发支持
   - 支持集群和高可用

3. **定期备份数据**
   - SQLite：文件备份
   - MySQL：mysqldump备份

4. **测试迁移流程**
   - 在测试环境验证迁移
   - 确保数据完整性

5. **监控数据库性能**
   - 使用合适的连接池配置
   - 监控查询性能

## 故障排除

### 常见问题

1. **MySQL连接失败**
   - 检查MySQL服务状态
   - 验证用户权限
   - 确认网络连接

2. **迁移数据丢失**
   - 检查源数据库状态
   - 验证目标数据库权限
   - 查看迁移日志

3. **配置不生效**
   - 重启应用
   - 检查配置文件语法
   - 验证环境变量

### 调试技巧

1. **启用详细日志**
   ```yaml
   test:
     LOG_LEVEL: "DEBUG"
   ```

2. **手动测试连接**
   ```bash
   make test-db
   ```

3. **查看配置状态**
   ```bash
   make db-status
   ```

## 扩展计划

### 未来可能添加的功能

1. **更多数据库支持**
   - PostgreSQL
   - MongoDB
   - Redis

2. **高级迁移功能**
   - 增量迁移
   - 数据验证
   - 回滚机制

3. **性能优化**
   - 连接池监控
   - 查询优化建议
   - 自动索引建议

4. **管理界面**
   - Web管理界面
   - 可视化迁移工具
   - 性能监控面板

## 贡献指南

如果您想为数据库管理系统贡献代码：

1. Fork项目
2. 创建功能分支
3. 编写测试用例
4. 提交Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。
