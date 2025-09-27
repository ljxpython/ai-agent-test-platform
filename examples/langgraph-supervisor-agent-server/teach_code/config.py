import os

from dotenv import load_dotenv

load_dotenv()

# 使用用户提供的可用 LLM 初始化代码
from langchain.chat_models import init_chat_model

# 获取 API 密钥 - 使用用户 .env 文件中可用的密钥
api_key = os.getenv("OPENAI_API_KEY")


def get_llm(provider="deepseek", model="gpt-3.5-turbo"):
    """获取配置好的 LLM 实例 - 使用用户提供的可用代码"""
    if provider == "openai":
        return init_chat_model(
            model=model, model_provider="openai", api_key=api_key, temperature=0.0
        )
    elif provider == "deepseek":
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment")
        return init_chat_model(
            model="deepseek-chat",
            model_provider="deepseek",
            api_key=deepseek_api_key,
            temperature=0.0,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


# 默认 LLM 实例 - 使用用户 .env 文件中可用的 OpenAI 配置
llm = get_llm()


# 工具配置 - 使用用户提供的可用代码
def get_tools():
    """获取可用工具"""
    try:
        from langchain_tavily import TavilySearch

        tool = TavilySearch(max_results=2)
        tools = [tool]
        return tools
    except ImportError:
        print("警告: TavilySearch 不可用，将使用模拟工具")
        return []
