"""V4: 面试 Agent — ReAct 推理 + 阶段状态机 + 记忆系统 + 动态追问策略。"""

from enum import Enum

from src.agents.memory import (
    ConversationMemory,
    long_term_memory,
    short_term_memory,
)
from src.agents.react_agent import react_agent
from src.core.logger import logger
from src.services.rag_service import rag_service


class InterviewStage(str, Enum):
    OPENING = "opening"
    SELF_INTRO = "self_intro"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    CLOSING = "closing"


class InterviewAgent:
    """面试智能体 (V4)。

    核心能力：
    - ReAct 推理：Think → Act → Observe 循环
    - 阶段状态机：自动追踪面试进展到哪个阶段
    - 记忆系统：短期记忆(滑动窗口) + 长期记忆(候选人画像)
    - 动态追问：根据候选人回答质量，自动调整追问深度
    """

    STAGE_TRANSITIONS: dict[InterviewStage, InterviewStage] = {
        InterviewStage.OPENING: InterviewStage.SELF_INTRO,
        InterviewStage.SELF_INTRO: InterviewStage.TECHNICAL,
        InterviewStage.TECHNICAL: InterviewStage.BEHAVIORAL,
        InterviewStage.BEHAVIORAL: InterviewStage.CLOSING,
    }

    STAGE_MIN_ROUNDS: dict[InterviewStage, int] = {
        InterviewStage.OPENING: 1,
        InterviewStage.SELF_INTRO: 2,
        InterviewStage.TECHNICAL: 6,
        InterviewStage.BEHAVIORAL: 4,
        InterviewStage.CLOSING: 1,
    }

    FOLLOW_UP_STRATEGIES = {
        "deep_dive": "请深入说明具体实现细节、技术选型理由和遇到的挑战。",
        "comparison": "你提到了 {topic}，能否对比一下它和其他方案的优劣？",
        "scenario": "假设在实际工作中遇到 {scenario}，你会如何处理？",
        "metrics": "你如何衡量这项工作的成果？有哪些关键指标？",
        "failure": "在类似场景中，你遇到过什么失败经历？是如何解决的？",
    }

    def __init__(self):
        self.conversation_memory: ConversationMemory | None = None
        self.use_react: bool = True  # 可切换 ReAct 模式

    async def ask(
        self,
        user_input: str,
        resume_summary: str = "",
        jd_summary: str = "",
        conversation_history: list[dict[str, str]] | None = None,
        stage: str = "",
        user_id: str = "",
    ) -> str:
        """生成面试问题，支持 ReAct + Memory。"""
        strategy = self._select_strategy(conversation_history or [], stage)
        logger.info("InterviewAgent: stage={}, strategy={}, react={}", stage, strategy, self.use_react)

        # V4: 获取长期记忆中候选人的弱项
        weak_areas = []
        if user_id:
            weak_areas = long_term_memory.get_weak_areas(user_id)
            if weak_areas:
                logger.info("InterviewAgent: weak areas for user {}: {}", user_id, weak_areas)

        # 构建增强的上下文（含弱项提示）
        enhanced_resume = resume_summary
        if weak_areas:
            enhanced_resume += f"\n[重点关注领域]: {', '.join(weak_areas)}"

        if self.use_react:
            # V4: 使用 ReAct 模式
            trace = await react_agent.run(
                user_input=user_input,
                resume_summary=enhanced_resume,
                jd_summary=jd_summary,
                conversation_history=conversation_history,
                interview_stage=f"{stage} ({strategy})",
            )
            # 记录 ReAct 步骤到短期记忆
            short_term_memory.add(
                f"ReAct trace: {trace.to_context()}", "system", importance=0.5
            )
            return trace.final_answer

        # 降级：直接 RAG 生成
        return await rag_service.generate(
            question=user_input,
            resume_summary=enhanced_resume,
            jd_summary=jd_summary,
            conversation_history=conversation_history,
            interview_stage=f"{stage} ({strategy})",
        )

    async def ask_stream(
        self,
        user_input: str,
        resume_summary: str = "",
        jd_summary: str = "",
        conversation_history: list[dict[str, str]] | None = None,
        stage: str = "",
        user_id: str = "",
    ):
        """流式生成面试问题。"""
        strategy = self._select_strategy(conversation_history or [], stage)

        weak_areas = []
        if user_id:
            weak_areas = long_term_memory.get_weak_areas(user_id)

        enhanced_resume = resume_summary
        if weak_areas:
            enhanced_resume += f"\n[重点关注领域]: {', '.join(weak_areas)}"

        # 流式场景暂不使用 ReAct（ReAct 需要完整推理后再输出）
        async for token in rag_service.generate_stream(
            question=user_input,
            resume_summary=enhanced_resume,
            jd_summary=jd_summary,
            conversation_history=conversation_history,
            interview_stage=f"{stage} ({strategy})",
        ):
            yield token

    def record_exchange(self, user_msg: str, assistant_msg: str) -> None:
        """记录一轮对话到记忆系统。"""
        short_term_memory.add(user_msg, "user", importance=0.8)
        short_term_memory.add(assistant_msg, "assistant", importance=0.8)
        if self.conversation_memory:
            self.conversation_memory.add_exchange(user_msg, assistant_msg)

    def start_conversation_memory(self) -> None:
        """开始记录对话记忆。"""
        self.conversation_memory = ConversationMemory()

    def add_key_point(self, point: str) -> None:
        """记录关键信息。"""
        if self.conversation_memory:
            self.conversation_memory.add_key_point(point)
        short_term_memory.add(point, "system", importance=0.9)

    def _select_strategy(
        self, history: list[dict[str, str]], stage: str
    ) -> str:
        if stage == InterviewStage.OPENING:
            return "warm_up"
        if stage == InterviewStage.SELF_INTRO:
            return "deep_dive" if len(history) > 4 else "basic"
        if stage == InterviewStage.TECHNICAL:
            user_messages = [m for m in history if m.get("role") == "user"]
            if user_messages:
                last_answer = user_messages[-1].get("content", "")
                if len(last_answer) < 30:
                    return "deep_dive"
                elif len(last_answer) > 200:
                    return "comparison"
            return "scenario"
        if stage == InterviewStage.BEHAVIORAL:
            return "metrics" if len(history) % 4 == 0 else "failure"
        return "standard"

    def determine_stage(
        self, message_count: int, current_stage: str = ""
    ) -> InterviewStage:
        cumulative = 0
        for stage in InterviewStage:
            cumulative += self.STAGE_MIN_ROUNDS[stage] * 2
            if message_count < cumulative:
                return stage
        return InterviewStage.CLOSING

    def should_transition(
        self, stage: InterviewStage, message_count: int
    ) -> bool:
        min_msgs = self.STAGE_MIN_ROUNDS.get(stage, 4) * 2
        return message_count >= min_msgs


interview_agent = InterviewAgent()

