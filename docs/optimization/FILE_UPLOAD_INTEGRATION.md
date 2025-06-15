# 文件上传与需求分析集成优化文档

## 优化概述

根据用户要求，优化了文件上传和需求分析的集成流程，确保 `session_id` 和 `conversation_id` 一致，并且在需求分析时能够根据 `conversation_id` 自动获取之前上传的文件内容，传递给智能体进行分析。

## 主要优化内容

### 1. 统一ID管理

#### 修改前
```python
# upload接口使用独立的session_id
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form("default")  # 独立的session_id
):
```

#### 修改后
```python
# upload接口使用conversation_id
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: str = Form(..., description="对话ID，与测试用例生成的conversation_id保持一致")
):
```

### 2. 新增文件内容获取方法

在 `TestCaseService` 中新增了两个方法来获取上传的文件：

#### `get_uploaded_files_content()`
```python
def get_uploaded_files_content(self, conversation_id: str) -> str:
    """
    根据conversation_id获取上传的文件内容

    Args:
        conversation_id: 对话ID，与session_id一致

    Returns:
        str: 合并的文件内容，如果没有文件则返回空字符串
    """
    from backend.services.document_service import document_service
    content = document_service.get_session_content(conversation_id)
    return content
```

#### `get_uploaded_files_info()`
```python
def get_uploaded_files_info(self, conversation_id: str) -> List[Dict]:
    """
    根据conversation_id获取上传的文件信息

    Args:
        conversation_id: 对话ID，与session_id一致

    Returns:
        List[Dict]: 文件信息列表
    """
    from backend.services.document_service import document_service
    files_info = document_service.get_session_files(conversation_id)
    return files_info
```

### 3. 优化需求分析智能体

#### 步骤1: 文件信息展示优化

**修改前**:
```python
# 只处理message中的file_paths或files
if message.file_paths:
    # 处理文件路径
elif message.files:
    # 处理文件对象
else:
    # 无文件
```

**修改后**:
```python
# 优先从document_service获取上传的文件信息
uploaded_files_info = testcase_service.get_uploaded_files_info(conversation_id)

if uploaded_files_info:
    # 使用document_service的高质量文件信息
    for file_info in uploaded_files_info:
        user_requirements_display += f"**{file_info['filename']}**\n"
        user_requirements_display += f"   - 文件ID: {file_info['file_id']}\n"
        user_requirements_display += f"   - 文件类型: {file_info['file_type']}\n"
        user_requirements_display += f"   - 文件大小: {file_info['file_size']} bytes\n"
        user_requirements_display += f"   - 上传时间: {file_info['upload_time']}\n\n"
elif message.file_paths:
    # 回退到原有的文件路径处理
elif message.files:
    # 回退到原有的文件对象处理
```

#### 步骤2: 文件内容获取优化

**修改前**:
```python
# 复杂的文件路径和文件对象处理逻辑
if message.file_paths:
    file_content = await self.get_document_from_file_paths(message.file_paths)
elif message.files:
    file_content = await self.get_document_from_files(message.files)
```

**修改后**:
```python
# 优先从document_service获取文件内容
uploaded_file_content = testcase_service.get_uploaded_files_content(conversation_id)

if uploaded_file_content:
    # 使用document_service的高质量解析内容
    analysis_content += f"\n\n📎 附件文件内容:\n{uploaded_file_content}"
    # 构建展示内容...
elif message.file_paths:
    # 回退到原有的文件路径处理
elif message.files:
    # 回退到原有的文件对象处理
```

## 工作流程

### 优化后的完整流程

1. **用户上传文件**
   ```python
   POST /api/testcase/upload
   {
       "file": <文件>,
       "conversation_id": "conv_123"
   }
   ```

2. **文件处理和存储**
   ```python
   # document_service使用conversation_id作为session_id
   result = await document_service.save_and_extract_file(file, conversation_id)
   ```

3. **用户发起需求分析**
   ```python
   POST /api/testcase/generate/streaming
   {
       "text_content": "用户需求",
       "conversation_id": "conv_123"  # 相同的conversation_id
   }
   ```

4. **智能体自动获取文件内容**
   ```python
   # 需求分析智能体自动获取上传的文件
   uploaded_file_content = testcase_service.get_uploaded_files_content(conversation_id)
   uploaded_files_info = testcase_service.get_uploaded_files_info(conversation_id)

   # 将文件内容传递给AI进行分析
   analysis_content = message.text_content + "\n\n📎 附件文件内容:\n" + uploaded_file_content
   ```

## 技术优势

### 1. 统一的ID管理
- **一致性**: `conversation_id` 贯穿整个流程
- **简化**: 用户无需管理多个ID
- **可追溯**: 文件和对话完全关联

### 2. 高质量文件处理
- **专业解析**: 使用marker进行高质量文档转换
- **图片分析**: 支持LLM图片描述
- **缓存机制**: 避免重复解析相同文件

### 3. 智能回退机制
- **优先级**: document_service > file_paths > files
- **兼容性**: 保持对原有接口的完全兼容
- **稳定性**: 任何一层失败都有回退方案

### 4. 详细的信息展示
- **文件信息**: 显示文件ID、类型、大小、上传时间
- **解析统计**: 显示字符数、词数、表格数、图片数
- **处理配置**: 显示LLM启用状态、格式增强等

## 使用示例

### 1. 完整的文件上传和分析流程

```bash
# 步骤1: 上传文件
curl -X POST "http://localhost:8000/api/testcase/upload" \
  -F "file=@requirements.pdf" \
  -F "conversation_id=conv_123"

# 步骤2: 发起需求分析（自动包含文件内容）
curl -X POST "http://localhost:8000/api/testcase/generate/streaming" \
  -H "Content-Type: application/json" \
  -d '{
    "text_content": "请分析这个需求文档",
    "conversation_id": "conv_123"
  }'
```

### 2. 前端集成示例

```javascript
// 上传文件
const uploadFile = async (file, conversationId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('conversation_id', conversationId);

  const response = await fetch('/api/testcase/upload', {
    method: 'POST',
    body: formData
  });

  return response.json();
};

// 发起需求分析（自动包含文件内容）
const generateTestCase = async (textContent, conversationId) => {
  const response = await fetch('/api/testcase/generate/streaming', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text_content: textContent,
      conversation_id: conversationId  // 相同的conversation_id
    })
  });

  // 处理SSE流式响应...
};
```

## 兼容性保证

### 1. 向后兼容
- 原有的 `file_paths` 和 `files` 参数仍然支持
- 如果没有通过document_service上传文件，会回退到原有逻辑
- 所有原有功能保持不变

### 2. 渐进式增强
- 新功能是在原有基础上的增强
- 不会破坏现有的工作流程
- 用户可以选择使用新的集成方式或继续使用原有方式

## 错误处理

### 1. 文件获取失败
```python
try:
    uploaded_file_content = testcase_service.get_uploaded_files_content(conversation_id)
except Exception as e:
    logger.error(f"获取文件内容失败: {e}")
    # 回退到原有的文件处理逻辑
```

### 2. 文件信息获取失败
```python
try:
    uploaded_files_info = testcase_service.get_uploaded_files_info(conversation_id)
except Exception as e:
    logger.error(f"获取文件信息失败: {e}")
    # 回退到原有的文件信息显示
```

## 总结

通过这次优化，成功实现了文件上传与需求分析的深度集成：

1. **统一ID管理**: `conversation_id` 贯穿整个流程
2. **自动文件获取**: 智能体自动获取上传的文件内容
3. **高质量解析**: 使用marker提供专业级文档处理
4. **完全兼容**: 保持对原有接口的完全兼容性
5. **智能回退**: 多层回退机制确保系统稳定性

现在用户只需要：
1. 使用相同的 `conversation_id` 上传文件
2. 使用相同的 `conversation_id` 发起需求分析
3. 智能体会自动获取并分析上传的文件内容

这大大简化了用户的使用流程，同时提供了更高质量的文档理解和分析能力。
