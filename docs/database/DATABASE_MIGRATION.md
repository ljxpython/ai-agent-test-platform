# 数据库迁移指南

## 概述

本项目支持SQLite和MySQL两种数据库，可以通过配置文件动态切换，并提供了完整的数据迁移工具。

## 支持的数据库

### SQLite
- **适用场景**: 开发环境、小型部署、单机应用
- **优点**: 无需额外安装、配置简单、文件存储
- **缺点**: 并发性能有限、不支持分布式

### MySQL
- **适用场景**: 生产环境、大型应用、高并发场景
- **优点**: 高性能、支持集群、成熟稳定
- **缺点**: 需要额外安装配置

## 配置文件

数据库配置位于 `backend/conf/settings.yaml`:

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
      host: "localhost"
      port: 3306
      user: "aitestlab"
      password: "your_password"
      database: "aitestlab"
      charset: "utf8mb4"
      # 连接池配置
      pool_size: 10
      max_overflow: 20
      pool_timeout: 30
      pool_recycle: 3600
```

## 快速开始

### 1. 查看当前数据库配置

```bash
make db-status
```

### 2. 测试数据库连接

```bash
make test-db
```

## SQLite 使用

### 切换到SQLite

```bash
make switch-to-sqlite
```

### 初始化SQLite数据库

```bash
make init-db
```

## MySQL 使用

### 1. 安装MySQL服务器

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

**CentOS/RHEL:**
```bash
sudo yum install mysql-server
sudo systemctl start mysqld
sudo mysql_secure_installation
```

**macOS:**
```bash
brew install mysql
brew services start mysql
```

### 2. 设置MySQL数据库

```bash
make setup-mysql
```

这个命令会：
- 创建数据库
- 创建用户
- 授予权限
- 测试连接

### 3. 检查MySQL连接

```bash
make check-mysql
```

### 4. 切换到MySQL

```bash
make switch-to-mysql
```

## 数据库迁移

### 从SQLite迁移到MySQL

1. **确保MySQL已设置**:
   ```bash
   make setup-mysql
   make check-mysql
   ```

2. **执行数据迁移**:
   ```bash
   make migrate-sqlite-to-mysql
   ```

3. **切换到MySQL**:
   ```bash
   make switch-to-mysql
   ```

4. **重启应用**:
   ```bash
   make stop
   make start
   ```

### 迁移过程说明

迁移脚本会：
1. 连接到SQLite数据库
2. 导出所有表数据
3. 连接到MySQL数据库
4. 创建表结构
5. 按依赖顺序导入数据
6. 验证数据完整性

## 常用命令

### 数据库管理
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

## 故障排除

### 常见问题

#### 1. MySQL连接失败

**错误**: `Can't connect to MySQL server`

**解决方案**:
```bash
# 检查MySQL服务状态
sudo systemctl status mysql

# 启动MySQL服务
sudo systemctl start mysql

# 检查端口是否开放
netstat -tlnp | grep 3306
```

#### 2. 权限不足

**错误**: `Access denied for user`

**解决方案**:
```bash
# 重新设置MySQL数据库
make setup-mysql

# 或手动授权
mysql -u root -p
GRANT ALL PRIVILEGES ON aitestlab.* TO 'aitestlab'@'%';
FLUSH PRIVILEGES;
```

#### 3. 字符集问题

**错误**: `Incorrect string value`

**解决方案**:
- 确保MySQL配置使用utf8mb4字符集
- 检查配置文件中的charset设置

#### 4. 迁移数据丢失

**解决方案**:
```bash
# 备份SQLite数据库
cp backend/data/aitestlab.db backend/data/aitestlab.db.backup

# 重新执行迁移
make migrate-sqlite-to-mysql
```

### 调试技巧

#### 1. 启用详细日志

在配置文件中设置:
```yaml
test:
  LOG_LEVEL: "DEBUG"
```

#### 2. 手动测试连接

```python
# 测试SQLite
python -c "
import asyncio
from backend.api_core.database import get_database_url
print(get_database_url())
"

# 测试MySQL
python scripts/setup_mysql.py check
```

#### 3. 查看迁移日志

迁移过程中的详细日志会显示：
- 导出的表和记录数
- 导入的进度
- 任何错误信息

## 性能优化

### SQLite优化

```sql
-- 启用WAL模式
PRAGMA journal_mode=WAL;

-- 设置缓存大小
PRAGMA cache_size=10000;

-- 启用外键约束
PRAGMA foreign_keys=ON;
```

### MySQL优化

```sql
-- 调整缓冲池大小
SET GLOBAL innodb_buffer_pool_size = 1073741824;

-- 优化连接数
SET GLOBAL max_connections = 200;

-- 启用查询缓存
SET GLOBAL query_cache_type = ON;
SET GLOBAL query_cache_size = 67108864;
```

## 备份策略

### SQLite备份

```bash
# 简单备份
cp backend/data/aitestlab.db backup/aitestlab_$(date +%Y%m%d).db

# 在线备份
sqlite3 backend/data/aitestlab.db ".backup backup/aitestlab_$(date +%Y%m%d).db"
```

### MySQL备份

```bash
# 完整备份
mysqldump -u aitestlab -p aitestlab > backup/aitestlab_$(date +%Y%m%d).sql

# 仅结构备份
mysqldump -u aitestlab -p --no-data aitestlab > backup/aitestlab_structure.sql

# 仅数据备份
mysqldump -u aitestlab -p --no-create-info aitestlab > backup/aitestlab_data.sql
```

## 最佳实践

1. **开发环境使用SQLite**: 简单快速，便于调试
2. **生产环境使用MySQL**: 性能更好，支持高并发
3. **定期备份数据**: 避免数据丢失
4. **测试迁移过程**: 在测试环境先验证迁移
5. **监控数据库性能**: 及时发现和解决问题
6. **使用连接池**: 提高数据库连接效率
7. **合理设置字符集**: 避免中文乱码问题
