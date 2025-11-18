from dataclasses import dataclass
from typing import Literal

from llms import get_default_model
from pydantic import BaseModel, Field


class ReviewResult(BaseModel):
    """测试用例评审结果"""

    passed: bool = Field(description="评审是否通过，True表示通过，False表示不通过")
    feedback: str = Field(
        description="评审反馈意见，如果通过则给出肯定意见，如果不通过则详细说明需要改进的地方"
    )
    score: int = Field(description="评审分数，0-100分", ge=0, le=100)


@dataclass
class GradeDocuments:
    """文档评分模型"""

    binary_score: Literal["yes", "no"]


def structure_output(output: str) -> GradeDocuments:
    """结构化输出"""
    return (
        get_default_model()
        .with_structured_output(GradeDocuments)
        .invoke([{"role": "user", "content": output}])
    )


def review_documents(output: str) -> ReviewResult:
    """对文档进行评分"""
    return (
        get_default_model()
        .with_structured_output(ReviewResult)
        .invoke([{"role": "user", "content": output}])
    )


if __name__ == "__main__":
    # result = structure_output("文档内容符合要求")
    # print(result)
    result = review_documents("文档内容符合要求")
    print(result)
