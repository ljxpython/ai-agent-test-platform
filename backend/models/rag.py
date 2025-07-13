"""
RAG相关的数据库模型
"""

from datetime import datetime
from typing import Optional

from tortoise import fields
from tortoise.models import Model


class RAGCollection(Model):
    """RAG Collection模型"""

    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, description="Collection名称")
    display_name = fields.CharField(max_length=200, description="显示名称")
    description = fields.TextField(description="描述")
    business_type = fields.CharField(
        max_length=50, default="general", description="业务类型"
    )

    # 项目关联 - 暂时注释掉，避免project_id字段问题
    # project = fields.ForeignKeyField(
    #     "models.Project",
    #     related_name="rag_collections",
    #     null=True,
    #     description="所属项目",
    # )

    # 配置信息
    dimension = fields.IntField(default=768, description="向量维度")
    chunk_size = fields.IntField(default=1000, description="分块大小")
    chunk_overlap = fields.IntField(default=200, description="分块重叠")
    top_k = fields.IntField(default=5, description="检索数量")
    similarity_threshold = fields.FloatField(default=0.7, description="相似度阈值")

    # 状态信息
    is_active = fields.BooleanField(default=True, description="是否激活")
    document_count = fields.IntField(default=0, description="文档数量")
    last_updated = fields.DatetimeField(auto_now=True, description="最后更新时间")

    # 元数据
    metadata = fields.JSONField(default=dict, description="元数据")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "rag_collections"
        table_description = "RAG知识库Collections"
        unique_together = (("name",),)

    def __str__(self):
        return f"RAGCollection({self.name})"


class RAGDocument(Model):
    """RAG文档模型"""

    id = fields.IntField(pk=True)
    collection = fields.ForeignKeyField(
        "models.RAGCollection",
        related_name="documents",
        on_delete=fields.CASCADE,
        description="所属Collection",
    )

    # 文档信息
    title = fields.CharField(max_length=500, description="文档标题")
    content = fields.TextField(description="文档内容")
    source = fields.CharField(max_length=500, null=True, description="文档来源")
    file_path = fields.CharField(max_length=1000, null=True, description="文件路径")
    file_type = fields.CharField(max_length=50, null=True, description="文件类型")
    file_size = fields.IntField(null=True, description="文件大小(字节)")

    # 处理信息
    node_count = fields.IntField(default=0, description="节点数量")
    embedding_status = fields.CharField(
        max_length=20,
        default="pending",
        description="嵌入状态: pending, processing, completed, failed",
    )

    # 元数据
    metadata = fields.JSONField(default=dict, description="元数据")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "rag_documents"
        table_description = "RAG文档"

    def __str__(self):
        return f"RAGDocument({self.title})"


class RAGQueryLog(Model):
    """RAG查询日志模型"""

    id = fields.IntField(pk=True)
    collection = fields.ForeignKeyField(
        "models.RAGCollection",
        related_name="query_logs",
        on_delete=fields.CASCADE,
        description="查询的Collection",
    )

    # 查询信息
    query_text = fields.TextField(description="查询文本")
    query_embedding = fields.TextField(null=True, description="查询向量(JSON)")

    # 结果信息
    retrieved_count = fields.IntField(default=0, description="检索到的文档数量")
    response_text = fields.TextField(null=True, description="生成的回答")
    response_time = fields.FloatField(description="响应时间(秒)")

    # 评分信息
    relevance_score = fields.FloatField(null=True, description="相关性评分")
    user_feedback = fields.CharField(
        max_length=20, null=True, description="用户反馈: positive, negative, neutral"
    )

    # 元数据
    metadata = fields.JSONField(default=dict, description="元数据")

    # 时间戳
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "rag_query_logs"
        table_description = "RAG查询日志"

    def __str__(self):
        return f"RAGQueryLog({self.query_text[:50]}...)"
