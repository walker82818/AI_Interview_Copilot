"""V2: 评估 Agent — 负责评分与学习建议。"""

from src.services.llm_service import llm_service
from src.utils.prompt_builder import build_evaluation_prompt


class EvaluationAgent:
    async def evaluate(
        self,
        messages: list[dict],
        resume_summary: str,
        jd_title: str,
    ) -> dict:
        prompt = build_evaluation_prompt(messages, resume_summary, jd_title)
        raw = await llm_service.chat(prompt)
        # TODO: 多维度 rubric 打分
        return {"raw": raw}


evaluation_agent = EvaluationAgent()
