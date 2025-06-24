

## UI框架改动



```
请仔细熟悉我的智能体发开框架及步骤,代码及说明在backend/ai_core中,应用范例:接口层:backend/api/v1/testcase.py,服务层:backend/services/testcase
现在我想在对外接口不变化的前提下将UI智能体系统的代码按照该框架实现,UI的接口代码:backend/api/v1/midscene.py,服务层代码:backend/services/ui_testing
```





1. **模块化设计**：`backend/ai_core/` 提供统一的LLM客户端、智能体工厂、内存管理、运行时管理、消息队列
2. ujn业务解耦**：通用组件与业务逻辑分离，提高复用性
3. **健壮性优先**：完整的错误处理和容错机制
4. **工程化友好**：简化业务代码开发，提高开发效率



- **接口层**：`backend/api/v1/testcase.py` - 使用SSE流式输出
- **服务层**：`backend/services/testcase/` - 基于AI核心框架的业务封装
- **智能体实现**：使用`create_assistant_agent`、消息队列、内存管理
- **运行时管理**：专用运行时`TestCaseRuntime`继承`BaseRuntime`



## RAG服务搭建



```
我想搭建一个RAG服务:
技术: LlamaIndex Ollama Milvus

```



现在deepseek上寻求帮助

```
我想llama_index 怎么和ollama及Milvus结合在一起,请做一个demo,框架化一点,我已经远程部署好ollama及Milvus了,我想做一个RAG系统
```

![image-20250624235702179](./assets/image-20250624235702179.png)



deepseek帮我生成了相应的代码,从这份代码学习,将该代码跑通,之后融合到我现在的服务框架中

后续我发现demo还不算太难,但是在这个过程中遇到了很多的报错,需要自己从deepseek的文档中学习查找





```
帮我完成一个RAG系统demo的开发,代码放在
examples/llama_rag_system_demo中
使用Milvus向量数据库,Ollama大模型服务,llama_index
框架如下:
RAG System
├── 数据加载模块 (Data Loader)
├── 嵌入生成模块 (Embedding Generator)
├── Milvus向量数据库 (Vector DB)
├── Ollama大模型服务 (LLM Service)
└── 查询引擎 (Query Engine)

环境的配置在examples/conf/constants.py的settings,具体值在examples/conf/settings.yaml中
嵌入模型: "nomic-embed-text"
大语言模deepseek
大语言开发框架: llama_index
llama_index的文档:https://docs.llamaindex.ai/en/stable/api_reference/
最后给出一个小的案例来进行展示

```



```
1. 关于你刚才遇到的llm导入问题:
可以从这个页面得到答案:https://docs.llamaindex.ai/en/stable/examples/llm/deepseek/
from llama_index.llms.deepseek import DeepSeek
# you can also set DEEPSEEK_API_KEY in your environment variables
llm = DeepSeek(model="deepseek-reasoner", api_key="you_api_key")
2. examples/llama_rag_system_demo/config.py中配置可以放到examples/conf创建一个名为rag_config的目录
2. examples/llama_rag_system_demo目录下,文件太多,删除掉多余的文件,测试文件放在test目录下,让我可以更快的上手这个服务,框架更加清晰明了


```



```
examples/llama_rag_system_demo 这个目录下非服务核心部分的代码全部放到tests目录下
```





**核心服务文件（保留在主目录）**：

- `__init__.py` - 包初始化
- `utils.py` - 工具模块
- `rag.py` - 主入口文件
- `data_loader.py` - 数据加载模块
- `embedding_generator.py` - 嵌入生成模块
- `vector_store.py` - 向量数据库模块
- `llm_service.py` - LLM服务模块
- `query_engine.py` - 查询引擎模块

**非核心文件（移动到tests目录）**：

- `demo.py` - 演示案例
- `quick_start.py` - 快速开始示例
- `simple_example.py` - 简单示例
- `rag_system.py` - 完整版RAG系统（可选保留或移动）
- `README.md` - 文档





```
人工智能AI是计算机科学的一个分支致力于创建能够执行通常需要人类智能的任务的系统 机器学习是人工智能的一个子集它使计算机能够从数据中学习而无需明确编程 深度学习是机器学习的一个子集使用神经网络来模拟人脑的工作方式
```
