"""


文档加载

文本拆分

嵌入

检索


"""

from re import search

from langchain.agents import create_agent
from langchain_community.document_loaders.parsers import LLMImageBlobParser
from langchain_core.vectorstores import VectorStore
from langchain_milvus import Milvus
from langchain_ollama import OllamaEmbeddings

## pdf 加载
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from llms import get_default_model, get_doubao_model


# 文档加载
def extract_pdf_text_with_images(pdf_file: str) -> list:
    """
    提取pdf中的文本信息，如果包含图片，也同步解析成文本
    :param pdf_file:
    :return:
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
        model=get_doubao_model(),
        prompt=_PROMPT_IMAGES_TO_DESCRIPTION,
    )

    loader = PyMuPDF4LLMLoader(
        pdf_file,
        mode="single",  # 作为单个文档处理
        extract_images=True,  # 提取图片
        table_strategy="lines",  # 提取表格
        images_parser=llm_parser,
    )
    documents = loader.load()
    print(documents)
    return documents


from langchain_text_splitters import RecursiveCharacterTextSplitter


# 文档拆分
def spill_pdf_text(documents) -> list:
    """
    将PDF文件拆分为多个小文件，每个小文件包含一个页面的内容
    :param documents:
    :return:
    """

    # markdown格式解析
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1024, chunk_overlap=200
    )
    doc_splits = text_splitter.split_documents(documents)
    print(doc_splits)
    return doc_splits


# 入库
def embedding_text_into_vector_store(doc_splits):
    from langchain_core.vectorstores import InMemoryVectorStore

    embedding = OllamaEmbeddings(
        model="qwen3-embedding:0.6b",
        base_url="http://101.126.90.71:11434",
        temperature=0,
    )
    # vector_1 = embedding.embed_query(doc_splits[0].page_content)
    # print(vector_1)

    URI = "http://101.126.90.71:19530"
    # 将texts转换为向量，并保存在向量数据库中
    vector_store = Milvus(
        embedding_function=embedding,
        connection_args={"uri": URI},
        index_params={"index_type": "FLAT", "metric_type": "L2"},
    )
    ids = vector_store.add_documents(documents=doc_splits)

    # vector_store = Milvus.from_documents(doc_splits,
    #                                      embedding=embedding,
    #                                      collection_name="langchainweb",
    #                                      connection_args={"uri": URI})

    # vector_store = Milvus(
    #     embedding_function=embedding,
    #     connection_args={"uri": URI},
    #     index_params={"index_type": "FLAT", "metric_type": "L2"},
    # )

    # 将文本信息转换为向量存储
    # vector_store = InMemoryVectorStore.from_documents(
    #     documents=docs, embedding=embedding
    # )
    # s = vectorstore.search("去哪里旅行了",search_type="similarity")
    # print(s)
    s = vector_store.similarity_search("如何保持多轮对话")
    print(s)
    return vector_store


# 创建向量库检索
def creat_vector_store():
    embedding = OllamaEmbeddings(
        model="qwen3-embedding:0.6b",
        base_url="http://101.126.90.71:11434",
        temperature=0,
    )

    URI = "http://101.126.90.71:19530"
    # 将texts转换为向量，并保存在向量数据库中
    vector_store = Milvus(
        embedding_function=embedding,
        connection_args={"uri": URI},
        index_params={"index_type": "FLAT", "metric_type": "L2"},
    )
    return vector_store


# 把文档解析,分块,入库联起来
def add_document_to_vectorstore_pdf(pdf_file: str):
    docs = extract_pdf_text_with_images(pdf_file=pdf_file)
    doc_splits = spill_pdf_text(documents=docs)
    vector_store = embedding_text_into_vector_store(doc_splits=doc_splits)
    return vector_store


# 检索
def create_retriever():
    vector_store = creat_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        # search_kwargs={"k": 1},
    )
    # s = retriever.invoke('如何保持多轮对话')
    s = retriever.invoke(input="如何保持多轮对话")
    print(s)
    return retriever


def create_retriever_tool(vectorstore: VectorStore):
    from langchain_classic.tools.retriever import create_retriever_tool

    # “VectorStoreRetriever
    # 支持 “相似性”（默认）、“mmr”（最大边际相关性，上文已描述）和 “相似性分数阈值” 这几种搜索类型。我们可以使用最后一种类型，根据相似性分数对检索器输出的文档进行阈值筛选。检索器可以轻松地集成到更复杂的应用程序中，例如检索增强型生成（RAG）应用程序，它将给定的问题与检索到的上下文结合起来，为
    # LLM
    # 构造提示。
    #
    # ### 解释说明
    # - ** VectorStoreRetriever
    # 支持的搜索类型 **：
    # - ** 相似性（similarity） ** ：这是默认的搜索类型，它会根据文档与查询之间的相似性来检索文档。相似性通常是通过计算文档向量和查询向量之间的距离（如余弦相似度）来衡量的。
    # - ** 最大边际相关性（mmr，maximum
    # marginal
    # relevance） ** ：这种搜索类型旨在平衡检索结果的相似性和多样性。它不仅考虑文档与查询的相似性，还会考虑文档之间的差异性，以避免检索到过于相似的文档，从而提高检索结果的多样性。
    # - ** 相似性分数阈值（similarity_score_threshold） ** ：这种搜索类型允许用户设置一个相似性分数的阈值，只有当文档的相似性分数高于这个阈值时，才会被检索出来。这可以用于过滤掉与查询相关性较低的文档，提高检索结果的质量。
    # - ** 检索器的应用 **：
    # - 检索器可以集成到更复杂的应用程序中，例如检索增强型生成（RAG）应用程序。

    retriever = vectorstore.as_retriever()

    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_document",
        "擅长知识文档检索",
    )
    # retriever_tool.invoke({"query": "他们乘坐什么航班去旅行了"})
    return retriever_tool


def retrieve_tool():
    from langchain_ollama import OllamaEmbeddings

    embedding = OllamaEmbeddings(
        model="qwen3-embedding:0.6b",
        base_url="http://101.126.90.71:11434",
        temperature=0,
    )
    URI = "http://101.126.90.71:19530"
    vector_store = Milvus(
        embedding_function=embedding,
        connection_args={"uri": URI},
        index_params={"index_type": "FLAT", "metric_type": "L2"},
    )
    s = vector_store.similarity_search("如何保持多轮对话")
    # print(s)
    return create_retriever_tool(vector_store)


def creat_retriever_agent():
    re_tool = retrieve_tool()
    agent = create_agent(
        model=get_default_model(),
        tools=[re_tool],
        system_prompt="你是一位擅长文献检索和知识整合的大师,当检索不出知识时,要告知用户,而非根据自己的知识进行讲解",
    )
    return agent


agent = creat_retriever_agent()

if __name__ == "__main__":
    # docs = extract_pdf_text_with_images("/Users/bytedance/PycharmProjects/test/2025-11-01_graph_python/src/agentic_rag/pdf_test.pdf")
    # # print(docs)
    # doc_splits = spill_pdf_text(documents=docs)
    # embedding_text_into_vector_store(doc_splits=doc_splits)
    # vector_store = creat_vector_store()
    # s = vector_store.similarity_search("如何保持多轮对话")
    # print(s)
    # create_retriever()
    from langchain.messages import HumanMessage

    # question = HumanMessage(content="如何保持多轮对话")
    question = HumanMessage(content="如何处理速冻食品")
    agent = creat_retriever_agent()
    resp = agent.invoke({"messages": question})
    for i in resp["messages"]:
        i.pretty_print()
    pass
