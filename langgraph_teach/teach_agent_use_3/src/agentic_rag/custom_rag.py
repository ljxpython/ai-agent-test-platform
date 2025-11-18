import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Literal

from langchain.chat_models import init_chat_model

# 1、解析并加载文档
from langchain_community.document_loaders.parsers import LLMImageBlobParser
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from langchain_milvus import Milvus
from langchain_openai import ChatOpenAI
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.constants import END, START
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from loguru import logger

# 智能导入处理 - 支持直接运行和包导入两种方式
try:
    # 尝试相对导入（包导入方式）
    from .settings import settings
except ImportError:
    try:
        # 尝试绝对导入（直接运行方式）
        from settings import settings
    except ImportError:
        # 如果都失败，添加当前目录到路径再尝试
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from settings import settings


@dataclass
class GradeDocuments:
    """文档评分模型"""

    binary_score: Literal["yes", "no"]


class ThreadSafeVectorStoreRetriever(BaseRetriever):
    """Custom retriever that keeps Milvus calls on synchronous client.

    LangGraph always awaits tools which triggers retriever ``ainvoke``.
    LangChain's default vector store retriever forwards this to Milvus'
    asyncio client, which binds futures to the event loop used during
    initialization.  Since ``custom_rag`` builds the engine via
    ``asyncio.run`` at import time, later LangGraph worker loops differ and
    Milvus raises ``Future attached to a different loop``.  By overriding the
    retriever we delegate async calls to ``asyncio.to_thread`` so Milvus uses
    its blocking search API and stays loop-agnostic.
    """

    vectorstore: VectorStore
    search_kwargs: dict | None = None

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> list[Document]:
        kwargs = self.search_kwargs or {}
        return self.vectorstore.similarity_search(query, **kwargs)

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun | None = None,
    ) -> list[Document]:
        kwargs = self.search_kwargs or {}
        return await asyncio.to_thread(
            self.vectorstore.similarity_search,
            query,
            **kwargs,
        )


# ===== 提示词模板 =====

GRADE_PROMPT = (
    "你是一个文档相关性评估专家，负责评估检索到的文档与用户问题的相关性。\n\n"
    "【检索到的文档】：\n{context}\n\n"
    "【用户问题】：\n{question}\n\n"
    "【评估标准】：\n"
    "- 如果文档包含与用户问题相关的关键词、概念或语义信息，则判定为相关\n"
    "- 如果文档内容能够帮助回答用户问题，则判定为相关\n"
    "- 如果文档与问题完全无关或信息不足，则判定为不相关\n\n"
    "【输出要求】：\n"
    "请给出二元评分：'yes'（相关）或 'no'（不相关）"
)

REWRITE_PROMPT = (
    "你是一个问题优化专家，擅长理解用户问题的深层语义意图并重新表述问题。\n\n"
    "【原始问题】：\n"
    "-------------------\n"
    "{question}\n"
    "-------------------\n\n"
    "【任务要求】：\n"
    "1. 分析问题的核心语义和潜在意图\n"
    "2. 识别问题中的关键概念和隐含需求\n"
    "3. 将问题重新表述得更加清晰、具体和易于检索\n"
    "4. 保持原问题的核心意图不变\n\n"
    "【优化后的问题】："
)

GENERATE_PROMPT = (
    "你是一个专业的问答助手，擅长基于检索到的上下文信息回答用户问题。\n\n"
    "【用户问题】：\n{question}\n\n"
    "【检索到的上下文】：\n{context}\n\n"
    "【回答要求】：\n"
    "1. 仔细阅读上下文信息，基于事实进行回答\n"
    "2. 如果上下文中包含答案，请准确提取并组织成连贯的回答\n"
    '3. 如果上下文信息不足以回答问题，请明确说明"根据现有信息无法回答"\n'
    "4. 回答要简洁明了，控制在3-5句话以内\n"
    "5. 使用专业、友好的语气\n"
    "6. 不要编造或推测上下文中没有的信息\n\n"
    "【你的回答】："
)


class AgenticRAGEngine:
    """Agentic RAG 引擎"""

    def __init__(self, knowledge_base: str = None, vector_store=None):
        self.knowledge_base = knowledge_base or settings.DEFAULT_KNOWLEDGE_BASE
        self.vector_store = vector_store
        self.retriever = None
        self.retriever_tool = None
        self.response_model = None
        self.grader_model = None
        self.graph = None
        self._initialized = False

    async def initialize(self):
        """初始化引擎"""
        if self._initialized:
            return

        try:
            # 创建嵌入模型 - 使用与sematic_study.py相同的方式
            from langchain_ollama import OllamaEmbeddings

            embedding = OllamaEmbeddings(
                model=settings.EMBEDDING_MODEL,
                base_url=settings.EMBEDDING_BASE_URL,
                temperature=settings.EMBEDDING_TEMPERATURE,
            )

            # 创建Milvus客户端 - 使用与sematic_study.py相同的方式
            from langchain_milvus import Milvus

            self.vector_store = Milvus(
                embedding_function=embedding,
                connection_args={"uri": settings.MILVUS_URI},
                index_params={"index_type": "FLAT", "metric_type": "L2"},
            )

            # 创建检索器，使用线程安全的同步Milvus调用
            self.retriever = ThreadSafeVectorStoreRetriever(
                vectorstore=self.vector_store,
                search_kwargs={"k": settings.RAG_RETRIEVER_K},
            )

            # 创建检索工具
            from langchain_classic.tools.retriever import create_retriever_tool

            self.retriever_tool = create_retriever_tool(
                self.retriever,
                "retrieve_documents",
                f"Search and return information from {self.knowledge_base} knowledge base.",
            )

            # 初始化LLM模型 - 使用DeepSeek原生格式支持结构化输出
            from langchain_deepseek import ChatDeepSeek

            self.response_model = ChatDeepSeek(
                model=settings.LLM_MODEL,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_BASE,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            self.grader_model = self.response_model

            # 构建图
            await self._build_graph()

            self._initialized = True
            logger.info(
                f"Agentic RAG engine initialized for knowledge base: {self.knowledge_base}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Agentic RAG engine: {str(e)}")
            raise

    async def _build_graph(self):
        """构建LangGraph工作流"""
        workflow = StateGraph(MessagesState)

        # 添加节点
        workflow.add_node("generate_query_or_respond", self._generate_query_or_respond)
        workflow.add_node("retrieve", ToolNode([self.retriever_tool]))
        workflow.add_node("grade_documents", self._grade_documents)
        workflow.add_node("rewrite_question", self._rewrite_question)
        workflow.add_node("generate_answer", self._generate_answer)

        # 添加边
        workflow.add_edge(START, "generate_query_or_respond")

        # 决定是否检索
        workflow.add_conditional_edges(
            "generate_query_or_respond",
            tools_condition,
            {
                "tools": "retrieve",
                END: END,
            },
        )

        # 检索后的条件边
        workflow.add_conditional_edges(
            "retrieve",
            self._grade_documents,
        )

        workflow.add_edge("generate_answer", END)
        workflow.add_edge("rewrite_question", "generate_query_or_respond")

        # 编译图
        self.graph = workflow.compile()

    def extract_pdf_text_with_images(self, pdf_file: str) -> list:
        """
        提取pdf中的文本信息，如果包含图片，也同步解析成文本
        """
        _PROMPT_IMAGES_TO_DESCRIPTION: str = (
            "您是一名负责为图像检索任务生成摘要的助手。"
            "1. 这些摘要将被嵌入并用于检索原始图像。"
            "请提供简洁的图像摘要，确保其高度优化以利于检索\n"
            "2. 提取图像中的所有文本内容。"
            "不得遗漏页面上的任何信息。\n"
            "3. 不要凭空捏造不存在的信息\n"
            "请使用Markdown格式直接输出答案，"
            "无需解释性文字，且开头不要使用Markdown分隔符```。"
        )

        llm_parser = LLMImageBlobParser(
            model=ChatOpenAI(
                base_url=settings.IMAGE_PARSER_API_BASE,
                api_key=settings.IMAGE_PARSER_API_KEY,
                model=settings.IMAGE_PARSER_MODEL,
                max_tokens=settings.IMAGE_PARSER_MAX_TOKENS,
            ),
            prompt=_PROMPT_IMAGES_TO_DESCRIPTION,
        )

        loader = PyMuPDF4LLMLoader(
            pdf_file,
            mode=settings.PDF_LOADER_MODE,
            extract_images=settings.PDF_EXTRACT_IMAGES,
            table_strategy=settings.PDF_TABLE_STRATEGY,
            images_parser=llm_parser,
        )
        documents = loader.load()
        return documents

    def spill_pdf_text(self, documents) -> list:
        """
        将PDF文件拆分为多个小文件
        """
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
        )
        doc_splits = text_splitter.split_documents(documents)
        return doc_splits

    def add_document_to_vectorstore_pdf(self, pdf_file: str):
        """将PDF文档添加到向量存储"""
        docs = self.extract_pdf_text_with_images(pdf_file)
        doc_splits = self.spill_pdf_text(docs)

        # 将文档添加到Milvus
        if self.milvus_service:
            self.milvus_service.client.add_documents(documents=doc_splits)
            logger.info(f"Added {len(doc_splits)} document chunks to vector store")

    def _generate_query_or_respond(self, state):
        """生成查询或直接回答"""
        if self.response_model is None:
            return {
                "messages": [
                    {"role": "assistant", "content": "LLM model not available"}
                ]
            }

        try:
            response = self.response_model.bind_tools([self.retriever_tool]).invoke(
                state["messages"]
            )
            return {"messages": [response]}
        except Exception as e:
            return {"messages": [{"role": "assistant", "content": f"Error: {str(e)}"}]}

    def _grade_documents(self, state) -> Literal["generate_answer", "rewrite_question"]:
        """评估检索文档的相关性"""
        if not settings.RAG_ENABLE_GRADING:
            return "generate_answer"

        if self.grader_model is None:
            return "generate_answer"

        try:
            question = state["messages"][0].content
            context = state["messages"][-1].content

            prompt = GRADE_PROMPT.format(question=question, context=context)
            response = self.grader_model.with_structured_output(GradeDocuments).invoke(
                [{"role": "user", "content": prompt}]
            )

            # 处理不同的返回格式
            if isinstance(response, dict):
                score = response.get("binary_score", "yes")
            else:
                score = response.binary_score

            if score == "yes":
                return "generate_answer"
            else:
                # 检查迭代次数
                iteration_count = getattr(state, "iteration_count", 0)
                if iteration_count >= settings.RAG_MAX_ITERATIONS:
                    return "generate_answer"
                return "rewrite_question"

        except Exception as e:
            logger.error(f"Error in grade_documents: {str(e)}")
            return "generate_answer"

    def _rewrite_question(self, state):
        """重写问题"""
        if not settings.RAG_ENABLE_REWRITE:
            return {"messages": state["messages"]}

        if self.response_model is None:
            return {"messages": state["messages"]}

        try:
            messages = state["messages"]
            question = messages[0].content
            prompt = REWRITE_PROMPT.format(question=question)
            response = self.response_model.invoke([{"role": "user", "content": prompt}])

            # 增加迭代计数
            iteration_count = getattr(state, "iteration_count", 0) + 1

            return {
                "messages": [{"role": "user", "content": response.content}],
                "iteration_count": iteration_count,
            }
        except Exception as e:
            logger.error(f"Error in rewrite_question: {str(e)}")
            return {"messages": state["messages"]}

    def _generate_answer(self, state):
        """生成最终答案"""
        if self.response_model is None:
            return {
                "messages": [
                    {"role": "assistant", "content": "LLM model not available"}
                ]
            }

        try:
            question = state["messages"][0].content
            context = state["messages"][-1].content
            prompt = GENERATE_PROMPT.format(question=question, context=context)
            response = self.response_model.invoke([{"role": "user", "content": prompt}])
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"Error in generate_answer: {str(e)}")
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"Error generating answer: {str(e)}",
                    }
                ]
            }


class AgenticRAGEngineFactory:
    """Agentic RAG引擎工厂类"""

    _instances = {}

    @classmethod
    async def create_engine(cls, knowledge_base: str = None) -> AgenticRAGEngine:
        """创建或获取引擎实例"""
        knowledge_base = knowledge_base or settings.DEFAULT_KNOWLEDGE_BASE

        if knowledge_base not in cls._instances:
            engine = AgenticRAGEngine(knowledge_base=knowledge_base)
            await engine.initialize()
            cls._instances[knowledge_base] = engine
            logger.info(
                f"Created new Agentic RAG engine for knowledge base: {knowledge_base}"
            )

        return cls._instances[knowledge_base]

    @classmethod
    async def get_default_engine(cls) -> AgenticRAGEngine:
        """获取默认引擎"""
        return await cls.create_engine()

    @classmethod
    def clear_instances(cls):
        """清理所有实例"""
        cls._instances.clear()
        logger.info("Cleared all Agentic RAG engine instances")


# 创建全局引擎实例供测试使用
try:
    engine = asyncio.run(AgenticRAGEngineFactory.create_engine())
    graph = engine.graph
except Exception as e:
    logger.error(f"创建全局引擎实例失败: {str(e)}")
    engine = None
    graph = None


# 添加一个简化版的函数，用于快速测试
def create_simple_rag_engine():
    """创建一个简单的RAG引擎用于测试"""
    from langchain_milvus import Milvus
    from langchain_ollama import OllamaEmbeddings

    # 创建嵌入模型
    embedding = OllamaEmbeddings(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.EMBEDDING_BASE_URL,
        temperature=settings.EMBEDDING_TEMPERATURE,
    )

    # 创建Milvus客户端
    vector_store = Milvus(
        embedding_function=embedding,
        connection_args={"uri": settings.MILVUS_URI},
        index_params={"index_type": "FLAT", "metric_type": "L2"},
    )

    # 创建检索器工具
    retriever = ThreadSafeVectorStoreRetriever(
        vectorstore=vector_store,
        search_kwargs={"k": settings.RAG_RETRIEVER_K},
    )

    try:
        from langchain.tools.retriever import create_retriever_tool

        retriever_tool = create_retriever_tool(
            retriever, "retrieve_documents", "搜索并返回文档信息"
        )
    except ImportError:
        # 如果导入失败，返回None
        retriever_tool = None

    return vector_store, retriever_tool


# 为langgraph_api创建全局graph实例
# def create_graph():
#     """创建用于langgraph_api的图实例"""
#     try:
#         # 创建简单的向量存储和检索器
#         from langchain_ollama import OllamaEmbeddings
#         from langchain_milvus import Milvus
#         from langchain_core.tools import Tool
#
#         # 创建嵌入模型
#         embedding = OllamaEmbeddings(
#             model=settings.EMBEDDING_MODEL,
#             base_url=settings.EMBEDDING_BASE_URL,
#             temperature=settings.EMBEDDING_TEMPERATURE
#         )
#
#         # 创建Milvus客户端
#         vector_store = Milvus(
#             embedding_function=embedding,
#             connection_args={"uri": settings.MILVUS_URI},
#             index_params={"index_type": "FLAT", "metric_type": "L2"},
#         )
#
#         # 创建检索器
#         retriever = vector_store.as_retriever(
#             search_type="similarity",
#             search_kwargs={"k": settings.RAG_RETRIEVER_K}
#         )
#
#         # 创建检索工具
#         def retrieve_documents(query: str):
#             """检索文档"""
#             return retriever.invoke(query)
#
#         retrieval_tool = Tool(
#             name="retrieve_documents",
#             description="搜索并返回文档信息",
#             func=retrieve_documents
#         )
#
#         # 创建LLM模型
#         llm = init_chat_model(
#             f"deepseek:{settings.LLM_MODEL}",
#             temperature=settings.LLM_TEMPERATURE,
#             max_tokens=settings.LLM_MAX_TOKENS,
#             api_key=settings.LLM_API_KEY,
#             base_url=settings.LLM_API_BASE
#         )
#
#         # 创建简单的图
#         from langgraph.graph import StateGraph, MessagesState
#         from langgraph.prebuilt import ToolNode, tools_condition
#         from langgraph.constants import START, END
#
#         workflow = StateGraph(MessagesState)
#
#         def agent_node(state):
#             """代理节点"""
#             messages = state["messages"]
#             llm_with_tools = llm.bind_tools([retrieval_tool])
#             response = llm_with_tools.invoke(messages)
#             return {"messages": [response]}
#
#         def retrieve_node(state):
#             """检索节点"""
#             messages = state["messages"]
#             last_message = messages[-1]
#
#             if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
#                 # 执行工具调用
#                 tool_call = last_message.tool_calls[0]
#                 query = tool_call['args']['query']
#                 docs = retrieval_tool.func(query)
#
#                 # 格式化文档内容
#                 context = "\n\n".join([doc.page_content for doc in docs])
#
#                 return {"messages": [{"role": "system", "content": f"检索到的上下文:\n{context}"}]}
#
#             return {"messages": []}
#
#         # 添加节点
#         workflow.add_node("agent", agent_node)
#         workflow.add_node("retrieve", retrieve_node)
#
#         # 添加边
#         workflow.add_edge(START, "agent")
#         workflow.add_conditional_edges(
#             "agent",
#             tools_condition,
#             {
#                 "tools": "retrieve",
#                 END: END,
#             },
#         )
#         workflow.add_edge("retrieve", END)
#
#         return workflow.compile()
#
#     except Exception as e:
#         logger.error(f"创建图失败: {str(e)}")
#         # 返回一个简单的图作为备选
#         from langgraph.graph import StateGraph, MessagesState
#
#         workflow = StateGraph(MessagesState)
#
#         def simple_agent(state):
#             messages = state["messages"]
#             return {"messages": [{"role": "assistant", "content": "系统初始化中，请稍后..."}]}
#
#         workflow.add_node("agent", simple_agent)
#         workflow.add_edge(START, "agent")
#         workflow.add_edge("agent", END)
#
#         return workflow.compile()

# engine = asyncio.run(AgenticRAGEngineFactory.create_engine())
#
# graph = engine.graph

if __name__ == "__main__":
    from langchain.messages import HumanMessage

    # question = HumanMessage(content="如何保持多轮对话")
    question = HumanMessage(content="如何处理速冻食品")
    resp = graph.invoke({"messages": question})
    for i in resp["messages"]:
        i.pretty_print()
