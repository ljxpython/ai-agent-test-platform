"""
UI测试运行时
基于AI核心框架的UI测试专用运行时实现
"""

from typing import Any, Dict

from autogen_core import DefaultTopicId, SingleThreadedAgentRuntime
from loguru import logger

from backend.ai_core.runtime import BaseRuntime
from backend.services.ui_testing.agents import (
    InteractionAnalysisAgent,
    InteractionAnalysisMessage,
    MidsceneGenerationAgent,
    MidsceneGenerationMessage,
    ScriptGenerationAgent,
    ScriptGenerationMessage,
    UIAnalysisAgent,
    UIAnalysisMessage,
)


class UITestingRuntime(BaseRuntime):
    """UI测试专用运行时"""

    def __init__(self):
        super().__init__()
        self.topic_types = {
            "ui_analysis": "ui_analysis",
            "interaction_analysis": "interaction_analysis",
            "midscene_generation": "midscene_generation",
            "script_generation": "script_generation",
        }

        logger.info("🎯 [UI测试运行时] 初始化完成")

    async def register_agents(
        self, runtime: SingleThreadedAgentRuntime, conversation_id: str
    ) -> None:
        """
        注册UI测试相关的智能体

        Args:
            runtime: 运行时实例
            conversation_id: 对话ID
        """
        logger.info(f"🤖 [UI测试运行时] 注册智能体 | 对话ID: {conversation_id}")

        try:
            # 注册UI分析智能体
            await UIAnalysisAgent.register(
                runtime,
                self.topic_types["ui_analysis"],
                lambda: UIAnalysisAgent(description="UI元素分析智能体"),
            )
            logger.debug("✅ UI分析智能体注册完成")

            # 注册交互分析智能体
            await InteractionAnalysisAgent.register(
                runtime,
                self.topic_types["interaction_analysis"],
                lambda: InteractionAnalysisAgent(description="交互分析智能体"),
            )
            logger.debug("✅ 交互分析智能体注册完成")

            # 注册Midscene生成智能体
            await MidsceneGenerationAgent.register(
                runtime,
                self.topic_types["midscene_generation"],
                lambda: MidsceneGenerationAgent(description="Midscene用例生成智能体"),
            )
            logger.debug("✅ Midscene生成智能体注册完成")

            # 注册脚本生成智能体
            await ScriptGenerationAgent.register(
                runtime,
                self.topic_types["script_generation"],
                lambda: ScriptGenerationAgent(description="脚本生成智能体"),
            )
            logger.debug("✅ 脚本生成智能体注册完成")

            logger.success(
                f"🎉 [UI测试运行时] 所有智能体注册完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI测试运行时] 智能体注册失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise

    async def start_ui_analysis(
        self, conversation_id: str, image_paths: list, user_requirement: str
    ) -> None:
        """
        启动UI分析

        Args:
            conversation_id: 对话ID
            image_paths: 图片路径列表
            user_requirement: 用户需求
        """
        logger.info(f"🔍 [UI测试运行时] 启动UI分析 | 对话ID: {conversation_id}")
        logger.info(f"📷 图片数量: {len(image_paths)}")

        try:
            runtime = self.get_runtime(conversation_id)
            if not runtime:
                raise RuntimeError(f"运行时不存在: {conversation_id}")

            # 为每张图片启动UI分析
            for i, image_path in enumerate(image_paths):
                logger.info(f"📷 处理图片 {i+1}/{len(image_paths)}: {image_path}")

                # 创建UI分析消息
                ui_msg = UIAnalysisMessage(
                    conversation_id=conversation_id,
                    image_path=image_path,
                    user_requirement=user_requirement,
                )

                await runtime.publish_message(
                    ui_msg,
                    topic_id=DefaultTopicId(type=self.topic_types["ui_analysis"]),
                )

                logger.debug(f"✅ UI分析请求已发布 - 图片: {image_path}")

            logger.success(
                f"✅ [UI测试运行时] UI分析启动完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI测试运行时] UI分析启动失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise

    async def start_interaction_analysis(
        self, conversation_id: str, ui_elements: str, user_requirement: str
    ) -> None:
        """
        启动交互分析

        Args:
            conversation_id: 对话ID
            ui_elements: UI元素分析结果
            user_requirement: 用户需求
        """
        logger.info(f"🔄 [UI测试运行时] 启动交互分析 | 对话ID: {conversation_id}")

        try:
            runtime = self.get_runtime(conversation_id)
            if not runtime:
                raise RuntimeError(f"运行时不存在: {conversation_id}")

            # 创建交互分析消息
            interaction_msg = InteractionAnalysisMessage(
                conversation_id=conversation_id,
                ui_elements=ui_elements,
                user_requirement=user_requirement,
            )

            await runtime.publish_message(
                interaction_msg,
                topic_id=DefaultTopicId(type=self.topic_types["interaction_analysis"]),
            )

            logger.success(
                f"✅ [UI测试运行时] 交互分析启动完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI测试运行时] 交互分析启动失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise

    async def start_midscene_generation(
        self,
        conversation_id: str,
        ui_analysis: str,
        interaction_analysis: str,
        user_requirement: str,
    ) -> None:
        """
        启动Midscene生成

        Args:
            conversation_id: 对话ID
            ui_analysis: UI分析结果
            interaction_analysis: 交互分析结果
            user_requirement: 用户需求
        """
        logger.info(f"🎯 [UI测试运行时] 启动Midscene生成 | 对话ID: {conversation_id}")

        try:
            runtime = self.get_runtime(conversation_id)
            if not runtime:
                raise RuntimeError(f"运行时不存在: {conversation_id}")

            # 创建Midscene生成消息
            midscene_msg = MidsceneGenerationMessage(
                conversation_id=conversation_id,
                ui_analysis=ui_analysis,
                interaction_analysis=interaction_analysis,
                user_requirement=user_requirement,
            )

            await runtime.publish_message(
                midscene_msg,
                topic_id=DefaultTopicId(type=self.topic_types["midscene_generation"]),
            )

            logger.success(
                f"✅ [UI测试运行时] Midscene生成启动完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI测试运行时] Midscene生成启动失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise

    async def start_script_generation(
        self, conversation_id: str, midscene_json: str, user_requirement: str
    ) -> None:
        """
        启动脚本生成

        Args:
            conversation_id: 对话ID
            midscene_json: Midscene JSON结果
            user_requirement: 用户需求
        """
        logger.info(f"📜 [UI测试运行时] 启动脚本生成 | 对话ID: {conversation_id}")

        try:
            runtime = self.get_runtime(conversation_id)
            if not runtime:
                raise RuntimeError(f"运行时不存在: {conversation_id}")

            # 创建脚本生成消息
            script_msg = ScriptGenerationMessage(
                conversation_id=conversation_id,
                midscene_json=midscene_json,
                user_requirement=user_requirement,
            )

            await runtime.publish_message(
                script_msg,
                topic_id=DefaultTopicId(type=self.topic_types["script_generation"]),
            )

            logger.success(
                f"✅ [UI测试运行时] 脚本生成启动完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI测试运行时] 脚本生成启动失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            raise


# 创建全局运行时实例
_ui_testing_runtime: UITestingRuntime = None


def get_ui_testing_runtime() -> UITestingRuntime:
    """获取UI测试运行时实例（单例模式）"""
    global _ui_testing_runtime
    if _ui_testing_runtime is None:
        _ui_testing_runtime = UITestingRuntime()
    return _ui_testing_runtime
