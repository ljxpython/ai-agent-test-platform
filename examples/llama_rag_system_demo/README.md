# LlamaIndex RAG系统   代码如下,不过我已经将自己封装的比较好的代码放在了backend/rag_core中,所以这里就不重复了

基于LlamaIndex框架的RAG（检索增强生成）系统，使用Milvus向量数据库和DeepSeek大模型。

## 🚀 快速开始

```python
import asyncio
from examples.llama_rag_system_demo.rag import RAGSystem

async def main():
    async with RAGSystem() as rag:
        # 设置向量集合
        await rag.setup_collection(overwrite=True)

        # 添加知识
        await rag.add_text("人工智能是计算机科学的一个分支...")

        # 问答
        answer = await rag.chat("什么是人工智能？")
        print(answer)

asyncio.run(main())
```

## 📁 核心模块

- `rag.py` - 主入口文件
- `data_loader.py` - 数据加载
- `embedding_generator.py` - 嵌入生成
- `vector_store.py` - 向量数据库
- `llm_service.py` - LLM服务
- `query_engine.py` - 查询引擎

## 🧪 测试和示例

所有测试文件、演示案例和详细文档都在 `tests/` 目录中：

```bash
# 快速测试
python3 tests/quick_test.py

# 快速开始示例
python3 tests/quick_start.py

# 完整演示
python3 tests/demo.py

# 简单示例
python3 tests/simple_example.py
```

## ⚙️ 配置

配置文件位于 `examples/conf/rag_config/config.py`

## 📚 详细文档

查看 `tests/README_detailed.md` 获取完整文档。
