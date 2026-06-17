"""V2: 简历分析 Agent — 负责分析简历、提取技能。"""

from src.services.llm_service import llm_service
from src.utils.prompt_builder import build_resume_analysis_prompt


class ResumeAgent:
    async def analyze(self, text: str) -> dict:
        messages = build_resume_analysis_prompt(text)
        # TODO: 多步推理、结构化输出校验
        raw = await llm_service.chat(messages)
        return {"raw": raw}


resume_agent = ResumeAgent()
