"""V4: ReAct Agent — 思考-行动-观察循环。

实现 Reasoning + Acting 模式，让面试 Agent 能够：
1. Thought: 分析当前状态，决定下一步行动
2. Action: 执行具体操作（检索、追问、总结等）
3. Observation: 观察结果，调整策略
4. 循环直到找到最佳追问方向
"""

import json
from dataclasses import dataclass, field
from enum import Enum

from src.core.logger import logger
from src.services.llm_service import llm_service
from src.services.retrieval_service import retrieval_service


class ActionType(str, Enum):
    RETRIEVE = "retrieve"       # 检索相关知识
    ASK = "ask"                 # 生成追问
    SUMMARIZE = "summarize"     # 总结当前回答
    TRANSITION = "transition"   # 切换面试阶段
    CLARIFY = "clarify"         # 要求候选人澄清


@dataclass
class ReActStep:
    """ReAct 单步记录。"""
    thought: str = ""
    action: ActionType = ActionType.ASK
    action_input: str = ""
    observation: str = ""
    step_index: int = 0


@dataclass
class ReActTrace:
    """ReAct 完整执行轨迹。"""
    steps: list[ReActStep] = field(default_factory=list)
    final_answer: str = ""
    max_steps: int = 3

    def add_step(self, step: ReActStep) -> None:
        self.steps.append(step)

    def to_context(self) -> str:
        """将执行轨迹转为上下文文本。"""
        lines = []
        for step in self.steps:
            lines.append(f"[Step {step.step_index}]")
            lines.append(f"  Thought: {step.thought}")
            lines.append(f"  Action: {step.action.value}")
            lines.append(f"  Result: {step.observation[:200]}")
        return "\n".join(lines)


class ReActAgent:
    """ReAct 智能体 — 面试场景下的推理-行动循环。

    使用方式：
        trace = await react_agent.run(user_input, context)
        reply = trace.final_answer
    """

    SYSTEM_PROMPT = """你是一个采用 ReAct 模式的 AI 面试官。你需要通过以下步骤来生成最佳的面试追问：

可用行动 (Actions):
- retrieve(query): 从知识库检索相关信息
- ask(question): 向候选人提问
- summarize: 总结当前轮次
- transition(stage): 切换面试阶段
- clarify(topic): 要求候选人澄清某个话题

请严格按照以下 JSON 格式输出你的推理过程：
{
    "thought": "分析当前面试状态和候选人的回答...",
    "action": "retrieve|ask|summarize|transition|clarify",
    "action_input": "具体的操作参数"
}

在生成最终追问时，请使用：
{
    "thought": "综合所有信息，生成最终问题...",
    "action": "final_answer",
    "action_input": "最终的追问内容"
}"""

    def __init__(self, max_steps: int = 3):
        self.max_steps = max_steps

    async def run(
        self,
        user_input: str,
        resume_summary: str = "",
        jd_summary: str = "",
        conversation_history: list[dict[str, str]] | None = None,
        interview_stage: str = "",
    ) -> ReActTrace:
        """执行 ReAct 循环，返回完整轨迹。"""
        trace = ReActTrace(max_steps=self.max_steps)

        context = self._build_context(
            user_input, resume_summary, jd_summary,
            conversation_history, interview_stage,
        )

        for i in range(self.max_steps):
            step = await self._step(context, trace, i)
            trace.add_step(step)

            if step.action == ActionType.ASK:
                # 生成了追问，结束循环
                trace.final_answer = step.action_input
                logger.info(
                    "ReAct: final answer at step {}, {} chars",
                    i, len(trace.final_answer),
                )
                return trace

            if step.action == ActionType.RETRIEVE:
                # 执行检索，观察结果
                observation = await self._execute_retrieve(step.action_input)
                step.observation = observation
                context += f"\n\n检索结果 ({i + 1}):\n{observation[:500]}"

        # 达到最大步数，强制生成回答
        final = await self._force_final(context, trace)
        trace.final_answer = final
        return trace

    async def _step(
        self, context: str, trace: ReActTrace, step_index: int
    ) -> ReActStep:
        """执行单步推理。"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ]
        raw = await llm_service.chat(messages, temperature=0.3)
        step = self._parse_step(raw, step_index)
        return step

    async def _execute_retrieve(self, query: str) -> str:
        """执行检索操作。"""
        hits = await retrieval_service.search(query, top_k=3)
        if not hits:
            return "未检索到相关信息"
        return "\n".join(
            f"[{h.get('score', 0):.2f}] {h.get('text', '')[:300]}"
            for h in hits
        )

    async def _force_final(self, context: str, trace: ReActTrace) -> str:
        """强制生成最终回答。"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"{context}\n\n"
                    f"推理轨迹:\n{trace.to_context()}\n\n"
                    "请基于以上信息直接生成最终追问，输出格式：\n"
                    '{"action": "final_answer", "action_input": "你的追问内容"}'
                ),
            },
        ]
        raw = await llm_service.chat(messages, temperature=0.5)
        try:
            data = json.loads(raw)
            return data.get("action_input", raw)
        except json.JSONDecodeError:
            return raw

    def _parse_step(self, raw: str, step_index: int) -> ReActStep:
        """解析 LLM 输出的 ReAct 步骤。"""
        step = ReActStep(step_index=step_index)
        try:
            data = json.loads(raw)
            step.thought = data.get("thought", "")
            action_str = data.get("action", "ask")
            step.action_input = data.get("action_input", "")

            # 映射 action 字符串到枚举
            action_map = {
                "retrieve": ActionType.RETRIEVE,
                "ask": ActionType.ASK,
                "summarize": ActionType.SUMMARIZE,
                "transition": ActionType.TRANSITION,
                "clarify": ActionType.CLARIFY,
                "final_answer": ActionType.ASK,
            }
            step.action = action_map.get(action_str, ActionType.ASK)
        except (json.JSONDecodeError, KeyError):
            step.thought = "解析失败，使用默认追问"
            step.action = ActionType.ASK
            step.action_input = raw[:500]
        return step

    def _build_context(
        self,
        user_input: str,
        resume_summary: str,
        jd_summary: str,
        conversation_history: list[dict[str, str]] | None,
        interview_stage: str,
    ) -> str:
        parts = []
        if interview_stage:
            parts.append(f"面试阶段: {interview_stage}")
        if resume_summary:
            parts.append(f"简历摘要: {resume_summary[:300]}")
        if jd_summary:
            parts.append(f"岗位要求: {jd_summary[:300]}")
        if conversation_history:
            history_text = "\n".join(
                f"{m['role']}: {m['content'][:200]}"
                for m in conversation_history[-6:]
            )
            parts.append(f"对话历史:\n{history_text}")
        parts.append(f"候选人最新回答: {user_input}")
        return "\n\n".join(parts)


react_agent = ReActAgent(max_steps=3)
