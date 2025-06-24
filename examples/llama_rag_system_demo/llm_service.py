"""
大语言模型服务模块
基于LlamaIndex官方DeepSeek LLM实现
"""

from typing import Any, Dict, List, Optional

# 设置项目路径
from llama_index.core.llms import LLM
from llama_index.llms.deepseek import DeepSeek
from loguru import logger

from examples.conf.rag_config import RAGConfig


class LLMService:
    """大语言模型服务"""

    def __init__(self, config: RAGConfig):
        """
        初始化LLM服务

        Args:
            config: RAG配置
        """
        self.config = config.deepseek
        self.llm: LLM = None
        self._initialized = False

        logger.info(f"🤖 LLM服务初始化 - 模型: {self.config.model}")

    def initialize(self):
        """初始化LLM模型"""
        if self._initialized:
            return

        logger.info("🚀 正在初始化DeepSeek LLM模型...")

        try:
            # 使用LlamaIndex官方DeepSeek实现
            self.llm = DeepSeek(
                model=self.config.model,
                api_key=self.config.api_key,
                temperature=0.1,
                max_tokens=2048,
            )

            # 测试模型是否可用
            test_response = self.llm.complete("请说'测试成功'")
            logger.debug(f"模型测试响应: {test_response.text[:50]}...")

            self._initialized = True
            logger.success("✅ DeepSeek LLM模型初始化成功")

        except Exception as e:
            logger.error(f"❌ DeepSeek LLM模型初始化失败: {e}")
            raise

    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        生成响应

        Args:
            prompt: 输入提示
            **kwargs: 其他参数

        Returns:
            str: 生成的响应
        """
        if not self._initialized:
            self.initialize()

        logger.info(f"💭 生成响应 - 提示长度: {len(prompt)}")

        try:
            # 生成响应
            response = self.llm.complete(prompt, **kwargs)

            logger.success(f"✅ 响应生成完成 - 长度: {len(response.text)}")
            return response.text

        except Exception as e:
            logger.error(f"❌ 响应生成失败: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        聊天对话

        Args:
            messages: 消息列表，格式: [{"role": "user", "content": "..."}]
            **kwargs: 其他参数

        Returns:
            str: 响应内容
        """
        if not self._initialized:
            self.initialize()

        logger.info(f"💬 聊天对话 - 消息数量: {len(messages)}")

        try:
            # 将消息转换为提示
            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "system":
                    prompt_parts.append(f"系统: {content}")
                elif role == "user":
                    prompt_parts.append(f"用户: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"助手: {content}")

            prompt = "\n".join(prompt_parts)

            # 生成响应
            response = self.generate_response(prompt, **kwargs)

            logger.success("✅ 聊天响应生成完成")
            return response

        except Exception as e:
            logger.error(f"❌ 聊天响应生成失败: {e}")
            raise

    def generate_rag_response(self, query: str, context: str, **kwargs) -> str:
        """
        基于检索上下文生成RAG响应

        Args:
            query: 用户查询
            context: 检索到的上下文
            **kwargs: 其他参数

        Returns:
            str: RAG响应
        """
        if not self._initialized:
            self.initialize()

        logger.info(f"🔍 生成RAG响应 - 查询: {query[:50]}...")

        try:
            # 构建RAG提示
            rag_prompt = self._build_rag_prompt(query, context)

            # 生成响应
            response = self.generate_response(rag_prompt, **kwargs)

            logger.success("✅ RAG响应生成完成")
            return response

        except Exception as e:
            logger.error(f"❌ RAG响应生成失败: {e}")
            raise

    def _build_rag_prompt(self, query: str, context: str) -> str:
        """
        构建RAG提示模板

        Args:
            query: 用户查询
            context: 检索上下文

        Returns:
            str: 构建的提示
        """
        prompt_template = """你是一个专业的AI助手。请基于以下提供的上下文信息来回答用户的问题。

上下文信息：
{context}

用户问题：{query}

请根据上下文信息准确回答问题。如果上下文中没有相关信息，请明确说明。回答要简洁明了，重点突出。

回答："""

        return prompt_template.format(context=context, query=query)

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "model": self.config.model,
            "base_url": self.config.base_url,
            "initialized": self._initialized,
        }

    def close(self):
        """清理资源"""
        if self.llm:
            # LlamaIndex的LLM通常不需要显式关闭
            pass

        self._initialized = False
        logger.info("🔄 LLM服务资源清理完成")


def create_llm_service(config: RAGConfig) -> LLMService:
    """
    创建并初始化LLM服务

    Args:
        config: RAG配置

    Returns:
        LLMService: 初始化后的LLM服务
    """
    service = LLMService(config)
    service.initialize()
    return service


if __name__ == "__main__":
    # 测试代码
    from examples.conf.rag_config import get_rag_config

    config = get_rag_config()
    llm_service = create_llm_service(config)

    # 测试基本响应生成
    test_prompt = "请简单介绍一下人工智能。"
    response = llm_service.generate_response(test_prompt)
    print(f"基本响应: {response}")

    # 测试聊天功能
    messages = [
        {"role": "system", "content": "你是一个专业的AI助手。"},
        {"role": "user", "content": "什么是机器学习？"},
    ]
    chat_response = llm_service.chat(messages)
    print(f"聊天响应: {chat_response}")

    # 测试RAG响应
    test_context = """
    人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
    机器学习是人工智能的一个子集，它使计算机能够从数据中学习而无需明确编程。
    """
    test_query = "什么是机器学习？"
    rag_response = llm_service.generate_rag_response(test_query, test_context)
    print(f"RAG响应: {rag_response}")

    # 获取模型信息
    model_info = llm_service.get_model_info()
    print(f"模型信息: {model_info}")

    llm_service.close()
