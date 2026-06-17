"""V2: 面试 Agent — 负责生成问题与追问。"""

from src.services.rag_service import rag_service


class InterviewAgent:
    async def ask(
        self,
        user_input: str,
        resume_summary: str = "",
        jd_summary: str = "",
    ) -> str:
        # TODO: 面试阶段状态机、难度调节
        return await rag_service.generate(
            question=user_input,
            resume_summary=resume_summary,
            jd_summary=jd_summary,
        )


interview_agent = InterviewAgent()
