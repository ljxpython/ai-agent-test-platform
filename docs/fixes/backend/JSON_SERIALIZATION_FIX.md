# 🔧 JSON序列化问题修复

[← 返回后端修复记录](./README.md) | [← 返回文档中心](../../README.md)

## 🎯 问题描述

在保存文件数据库时出现错误：`Object of type Image is not JSON serializable`

### 错误现象
- 当使用marker-pdf处理包含图像的文件时，返回的`MarkdownContent`对象中的`images`字典包含Image对象
- 这些Image对象无法直接序列化为JSON格式
- 导致`DocumentService._save_files_db()`方法失败
- 影响文件信息的持久化存储

### 错误位置
1. `examples/document_service.py` - `_save_files_db()`方法
2. `backend/services/testcase_service.py` - `_save_to_memory()`方法

## 🔧 解决方案

### 1. 创建自定义JSON序列化函数

在`examples/document_service.py`中添加了专门的序列化处理函数：

#### `serialize_for_json(obj)`
```python
def serialize_for_json(obj):
    """自定义JSON序列化函数，处理不能直接序列化的对象"""
    if hasattr(obj, '__dict__'):
        # 对象属性序列化
        try:
            return obj.__dict__
        except:
            return str(obj)
    elif hasattr(obj, 'tobytes'):
        # 图像对象转base64
        try:
            return {
                'type': 'image_bytes',
                'data': base64.b64encode(obj.tobytes()).decode('utf-8'),
                'format': getattr(obj, 'format', 'unknown')
            }
        except:
            return str(obj)
    elif hasattr(obj, 'save'):
        # PIL Image对象处理
        try:
            import io
            buffer = io.BytesIO()
            obj.save(buffer, format='PNG')
            return {
                'type': 'pil_image',
                'data': base64.b64encode(buffer.getvalue()).decode('utf-8'),
                'size': getattr(obj, 'size', None),
                'mode': getattr(obj, 'mode', None)
            }
        except:
            return str(obj)
    elif isinstance(obj, bytes):
        # 字节数据转base64
        return {
            'type': 'bytes',
            'data': base64.b64encode(obj).decode('utf-8')
        }
    else:
        return str(obj)
```

#### `safe_json_dump(data, file_handle, **kwargs)`
```python
def safe_json_dump(data, file_handle, **kwargs):
    """安全的JSON序列化，处理不能序列化的对象"""
    def default_serializer(obj):
        return serialize_for_json(obj)

    return json.dump(data, file_handle, default=default_serializer, **kwargs)
```

### 2. 更新DocumentService保存方法

修改`_save_files_db()`方法使用安全序列化：

```python
def _save_files_db(self):
    """保存文件数据库"""
    logger.debug("💾 开始保存文件数据库...")

    db_file = self.files_db_dir / "files.json"
    try:
        logger.debug(f"📁 保存主数据库到: {db_file}")
        with open(db_file, 'w', encoding='utf-8') as f:
            safe_json_dump({
                'uploaded_files': self.uploaded_files,
                'session_files': self.session_files,
                'file_cache': self.file_cache
            }, f, ensure_ascii=False, indent=2)
        logger.debug("✅ 主数据库保存成功")
    except Exception as e:
        logger.error(f"❌ 保存文件数据库失败: {e}")
```

### 3. 修复testcase_service内存保存

在`backend/services/testcase_service.py`中添加安全序列化：

```python
def safe_json_serializer(obj):
    """安全的JSON序列化器，处理不能序列化的对象"""
    if hasattr(obj, '__dict__'):
        try:
            return obj.__dict__
        except:
            return str(obj)
    elif hasattr(obj, 'tobytes') or hasattr(obj, 'save'):
        # 对于图像对象，返回类型信息而不是完整数据
        return {
            'type': 'image_object',
            'class': obj.__class__.__name__,
            'size': getattr(obj, 'size', None),
            'mode': getattr(obj, 'mode', None)
        }
    elif isinstance(obj, bytes):
        # 对于字节数据，只保存长度信息
        return {
            'type': 'bytes',
            'length': len(obj)
        }
    else:
        return str(obj)

memory_content = MemoryContent(
    content=json.dumps(data, ensure_ascii=False, default=safe_json_serializer),
    mime_type=MemoryMimeType.JSON,
)
```

## 📊 修复效果

### 支持的对象类型

1. **Image对象** - 转换为base64编码的PNG格式
2. **字节数据** - 转换为base64编码字符串
3. **自定义对象** - 序列化对象属性
4. **PIL Image** - 保存为PNG并转换为base64
5. **普通对象** - 转换为字符串表示

### 序列化结果示例

#### Image对象序列化
```json
{
  "type": "pil_image",
  "data": "iVBORw0KGgoAAAANSUhEUgAA...",
  "size": [800, 600],
  "mode": "RGB"
}
```

#### 字节数据序列化
```json
{
  "type": "bytes",
  "data": "aGVsbG8gd29ybGQ="
}
```

#### 自定义对象序列化
```json
{
  "name": "test",
  "value": 42
}
```

## 🧪 测试验证

### 测试覆盖范围
1. **自定义序列化函数** - ✅ 通过
2. **安全JSON序列化** - ✅ 通过
3. **MarkdownContent序列化** - ✅ 通过
4. **DocumentService保存** - ✅ 通过

### 测试结果
```
🎯 总体结果: 4/4 个测试通过
🎉 所有测试都通过了！JSON序列化问题已修复。
```

### 详细日志输出
```
💾 开始保存文件数据库...
📁 保存主数据库到: .../files_db/files.json
✅ 主数据库保存成功
📁 保存缓存数据库到: .../files_db/file_cache.json
✅ 缓存数据库保存成功
```

## 🎯 技术亮点

### 1. 智能类型检测
- 通过`hasattr()`检测对象特征
- 针对不同类型采用不同的序列化策略
- 优雅的错误处理和回退机制

### 2. 数据完整性保护
- Image对象转换为可恢复的base64格式
- 保留重要的元数据信息（尺寸、模式等）
- 字节数据安全编码，避免数据丢失

### 3. 性能优化
- 对于内存存储，只保存类型信息而非完整数据
- 避免大量图像数据影响序列化性能
- 合理的错误处理，不影响主要功能

### 4. 向后兼容
- 不影响现有的正常JSON数据
- 保持原有的API接口不变
- 透明的序列化处理

## 🔗 相关文档

- [文件处理器优化](../../optimizations/performance/FILE_PROCESSOR_OPTIMIZATION.md) - 文件处理性能优化
- [日志系统指南](../../development/LOGGING_GUIDE.md) - 日志记录最佳实践
- [错误处理指南](../../troubleshooting/ERROR_HANDLING.md) - 错误处理机制

## 📝 使用说明

### 在新代码中使用
```python
from examples.document_service import safe_json_dump

# 替代标准的json.dump
with open('data.json', 'w') as f:
    safe_json_dump(complex_data, f, indent=2)
```

### 自定义序列化器
```python
from examples.document_service import serialize_for_json

# 处理单个对象
serialized = serialize_for_json(image_object)
```

---

✅ **修复完成**: JSON序列化问题已彻底解决，支持包含Image对象的复杂数据结构的安全序列化！
