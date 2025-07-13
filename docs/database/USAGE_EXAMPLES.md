# 数据库使用示例

## 完整的数据库迁移流程示例

### 场景：从SQLite迁移到MySQL

假设您当前使用SQLite数据库，现在需要迁移到MySQL以支持更高的并发和更好的性能。

#### 步骤1：检查当前状态

```bash
# 查看当前数据库配置
make db-status
```

输出示例：
```
📊 当前数据库配置:
🔧 类型: SQLITE
📁 路径: ./data/aitestlab.db
```

#### 步骤2：备份当前数据

```bash
# 备份SQLite数据库文件
cp backend/data/aitestlab.db backend/data/aitestlab_backup_$(date +%Y%m%d).db
```

#### 步骤3：设置MySQL数据库

```bash
# 设置MySQL数据库（需要root密码）
make setup-mysql
```

输出示例：
```
🛠️ 设置MySQL数据库...
请输入MySQL root密码: ********
🏠 MySQL主机: 101.126.90.71:3306
🗄️ 目标数据库: aitestlab
👤 目标用户: aitestlab
📝 创建数据库: aitestlab
👤 创建用户: aitestlab
🔑 授予权限...
✅ MySQL数据库设置完成
🔍 测试新用户连接...
✅ 用户连接测试成功
```

#### 步骤4：验证MySQL连接

```bash
# 检查MySQL连接
make check-mysql
```

输出示例：
```
🔍 检查MySQL连接...
✅ MySQL连接成功 - 版本: 8.0.35
```

#### 步骤5：执行数据迁移

```bash
# 从SQLite迁移到MySQL
make migrate-sqlite-to-mysql
```

输出示例：
```
🚀 从SQLite迁移到MySQL...
🚀 开始从SQLite迁移到MySQL...
源数据库 (SQLite): sqlite:///Users/.../aitestlab.db
目标数据库 (MySQL): mysql://aitestlab:***@101.126.90.71:3306/aitestlab?charset=utf8mb4
📤 导出SQLite数据...
📊 数据导出统计:
  departments: 1 条记录
  roles: 1 条记录
  users: 1 条记录
  projects: 1 条记录
  rag_collections: 4 条记录
  rag_files: 0 条记录
  chat_sessions: 0 条记录
  chat_messages: 0 条记录
  test_cases: 0 条记录
  api_permissions: 25 条记录
✅ SQLite数据导出完成，共 10 个表
📥 导入数据到MySQL...
✅ MySQL表结构创建完成
✅ departments: 1 条记录导入完成
✅ roles: 1 条记录导入完成
✅ users: 1 条记录导入完成
✅ projects: 1 条记录导入完成
✅ rag_collections: 4 条记录导入完成
✅ rag_files: 0 条记录导入完成
✅ chat_sessions: 0 条记录导入完成
✅ chat_messages: 0 条记录导入完成
✅ test_cases: 0 条记录导入完成
✅ api_permissions: 25 条记录导入完成
✅ 数据迁移到MySQL完成
🎉 数据库迁移完成！
💡 请更新 backend/conf/settings.yaml 中的数据库类型为 'mysql'
```

#### 步骤6：切换到MySQL

```bash
# 切换数据库配置到MySQL
make switch-to-mysql
```

输出示例：
```
🔄 切换到MySQL数据库...
🔄 切换到MySQL数据库...
✅ 已切换到MySQL数据库
🏠 主机: 101.126.90.71
🔌 端口: 3306
👤 用户: aitestlab
🗄️ 数据库: aitestlab
💡 请重启应用以使配置生效
```

#### 步骤7：验证切换结果

```bash
# 查看新的数据库配置
make db-status
```

输出示例：
```
📊 当前数据库配置:
🔧 类型: MYSQL
🏠 主机: 101.126.90.71
🔌 端口: 3306
👤 用户: aitestlab
🗄️ 数据库: aitestlab
```

```bash
# 测试MySQL连接
make test-db
```

#### 步骤8：重启应用

```bash
# 停止当前服务
make stop

# 启动服务
make start
```

### 场景：从MySQL切换回SQLite

如果需要从MySQL切换回SQLite（比如在开发环境中）：

#### 步骤1：切换配置

```bash
# 切换到SQLite
make switch-to-sqlite
```

#### 步骤2：验证配置

```bash
# 查看配置
make db-status

# 测试连接
make test-db
```

#### 步骤3：重启应用

```bash
make stop
make start
```

## 配置文件示例

### SQLite配置

```yaml
test:
  database:
    type: "sqlite"
    sqlite:
      path: "./data/aitestlab.db"
```

### MySQL配置

```yaml
test:
  database:
    type: "mysql"
    mysql:
      host: "101.126.90.71"
      port: 3306
      user: "aitestlab"
      password: "sRhSjiyhnpGz3Emr"
      database: "aitestlab"
      charset: "utf8mb4"
      pool_size: 10
      max_overflow: 20
      pool_timeout: 30
      pool_recycle: 3600
```

## 常见使用场景

### 开发环境设置

```bash
# 开发环境通常使用SQLite
make switch-to-sqlite
make init-db
make start
```

### 生产环境部署

```bash
# 生产环境使用MySQL
make setup-mysql
make switch-to-mysql
make init-db
make start
```

### 数据备份

```bash
# SQLite备份
cp backend/data/aitestlab.db backup/

# MySQL备份
mysqldump -u aitestlab -p aitestlab > backup/aitestlab_$(date +%Y%m%d).sql
```

### 性能测试

```bash
# 在不同数据库间切换进行性能对比
make switch-to-sqlite
make test-db

make switch-to-mysql
make test-db
```

## 故障恢复

### SQLite文件损坏

```bash
# 使用备份恢复
cp backend/data/aitestlab_backup_20241201.db backend/data/aitestlab.db

# 或重新初始化
make reset-db
```

### MySQL连接问题

```bash
# 重新设置MySQL
make setup-mysql

# 检查连接
make check-mysql

# 如果仍有问题，切换回SQLite
make switch-to-sqlite
```

## 自动化脚本示例

### 自动迁移脚本

```bash
#!/bin/bash
# auto_migrate.sh

echo "🚀 开始自动迁移流程..."

# 备份当前数据
if [ -f "backend/data/aitestlab.db" ]; then
    cp backend/data/aitestlab.db backend/data/aitestlab_backup_$(date +%Y%m%d_%H%M%S).db
    echo "✅ SQLite数据已备份"
fi

# 设置MySQL
make setup-mysql
if [ $? -ne 0 ]; then
    echo "❌ MySQL设置失败"
    exit 1
fi

# 执行迁移
make migrate-sqlite-to-mysql
if [ $? -ne 0 ]; then
    echo "❌ 数据迁移失败"
    exit 1
fi

# 切换到MySQL
make switch-to-mysql
if [ $? -ne 0 ]; then
    echo "❌ 数据库切换失败"
    exit 1
fi

echo "🎉 迁移完成！请重启应用。"
```

### 环境切换脚本

```bash
#!/bin/bash
# switch_env.sh

ENV=${1:-dev}

if [ "$ENV" = "dev" ]; then
    echo "🔧 切换到开发环境 (SQLite)"
    make switch-to-sqlite
elif [ "$ENV" = "prod" ]; then
    echo "🚀 切换到生产环境 (MySQL)"
    make switch-to-mysql
else
    echo "❌ 未知环境: $ENV"
    echo "用法: $0 [dev|prod]"
    exit 1
fi

make db-status
echo "💡 请重启应用以使配置生效"
```

使用方法：
```bash
# 切换到开发环境
./switch_env.sh dev

# 切换到生产环境
./switch_env.sh prod
```
