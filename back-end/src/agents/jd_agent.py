"""V2: JD 分析 Agent — 负责分析岗位需求。"""

from src.services.llm_service import llm_service
from src.utils.prompt_builder import build_jd_analysis_prompt


class JDAgent:
    async def analyze(self, text: str) -> dict:
        messages = build_jd_analysis_prompt(text)
        # TODO: 技能图谱、级别推断
        raw = await llm_service.chat(messages)
        return {"raw": raw}


jd_agent = JDAgent()
