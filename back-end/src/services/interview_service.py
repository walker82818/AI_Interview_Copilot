import json
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.agents.interview_agent import InterviewStage, interview_agent
from src.models.interview_session import InterviewSession
from src.models.job_description import JobDescription
from src.models.message import Message
from src.models.resume import Resume
from src.schemas.interview import (
    CreateInterviewRequest,
    InterviewSessionResponse,
    MessageResponse,
)
from src.schemas.report import InterviewReportResponse, ScoreDimension, Suggestion
from src.services.jd_service import jd_service
from src.services.llm_service import llm_service
from src.services.resume_service import resume_service
from src.utils.prompt_builder import (
    build_interview_closing_prompt,
    build_interview_opening_prompt,
)

InterviewStage = Literal["opening", "self_intro", "technical", "behavioral", "closing"]


class InterviewService:
    # 面试阶段配置
    STAGES: list[InterviewStage] = [
        "opening",
        "self_intro",
        "technical",
        "behavioral",
        "closing",
    ]
    # 每阶段最少消息轮数（用户+AI 各算 1 条）
    STAGE_MIN_ROUNDS: dict[InterviewStage, int] = {
        "opening": 1,
        "self_intro": 2,
        "technical": 6,
        "behavioral": 4,
        "closing": 1,
    }

    def _current_stage(self, session: InterviewSession) -> InterviewStage:
        """根据消息数量自动推断面试阶段。"""
        msg_count = len(session.messages) if session.messages else 0
        stages: list[tuple[int, InterviewStage]] = []
        cumulative = 0
        for stage in self.STAGES:
            stages.append((cumulative, stage))
            cumulative += self.STAGE_MIN_ROUNDS[stage] * 2  # 用户+AI
        current = "opening"
        for threshold, stage in stages:
            if msg_count >= threshold:
                current = stage
        return current  # type: ignore[return-value]

    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        data: CreateInterviewRequest,
    ) -> InterviewSessionResponse:
        await self._ensure_resources(db, user_id, data.resume_id, data.jd_id)

        # 获取上下文用于生成个性化开场白
        resume_summary, jd_summary, jd_title = await self._get_context_full(
            db, data.resume_id, data.jd_id
        )

        session = InterviewSession(
            user_id=user_id,
            resume_id=data.resume_id,
            jd_id=data.jd_id,
            status="active",
        )
        db.add(session)
        await db.flush()

        # 使用 LLM 生成个性化开场白，失败时使用默认
        try:
            opening_prompt = build_interview_opening_prompt(
                resume_summary=resume_summary,
                jd_summary=jd_summary,
                jd_title=jd_title,
            )
            opening_content = await llm_service.chat(opening_prompt, temperature=0.8)
        except Exception:
            opening_content = (
                f"你好！欢迎参加 {jd_title} 岗位的模拟面试。"
                "请先做一个简短的自我介绍吧。"
            )

        opening = Message(
            session_id=session.id,
            role="assistant",
            content=opening_content,
        )
        db.add(opening)
        await db.flush()
        result = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.id == session.id)
            .options(selectinload(InterviewSession.messages))
        )
        session = result.scalar_one()
        return await self._to_response(db, session)

    async def get_session(
        self, db: AsyncSession, user_id: str, session_id: str
    ) -> InterviewSessionResponse:
        session = await self._get_owned(db, user_id, session_id)
        return await self._to_response(db, session)

    async def list_recent(
        self, db: AsyncSession, user_id: str, limit: int = 10
    ) -> list[InterviewSessionResponse]:
        result = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.started_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()
        return [
            InterviewSessionResponse(
                id=s.id,
                resume_id=s.resume_id,
                jd_id=s.jd_id,
                status=s.status,  # type: ignore[arg-type]
                messages=[],
                started_at=s.started_at,
                ended_at=s.ended_at,
            )
            for s in sessions
        ]

    async def send_message(
        self,
        db: AsyncSession,
        user_id: str,
        session_id: str,
        content: str,
    ) -> MessageResponse:
        session = await self._get_owned(db, user_id, session_id)
        if session.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="面试已结束",
            )

        user_msg = Message(session_id=session.id, role="user", content=content)
        db.add(user_msg)
        await db.flush()

        reply_text = await self._generate_reply(db, session, content)
        assistant_msg = Message(
            session_id=session.id, role="assistant", content=reply_text
        )
        db.add(assistant_msg)
        await db.flush()
        return MessageResponse(
            id=assistant_msg.id,
            role="assistant",  # type: ignore[arg-type]
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
        )

    async def send_message_stream(
        self,
        db: AsyncSession,
        user_id: str,
        session_id: str,
        content: str,
    ):
        session = await self._get_owned(db, user_id, session_id)
        if session.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="面试已结束",
            )

        user_msg = Message(session_id=session.id, role="user", content=content)
        db.add(user_msg)
        await db.flush()

        resume_summary, jd_summary = await self._get_context(db, session)
        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in (session.messages or [])
        ]
        stage = self._current_stage(session)

        full_reply = ""
        async for token in interview_agent.ask_stream(
            user_input=content,
            resume_summary=resume_summary,
            jd_summary=jd_summary,
            conversation_history=conversation_history,
            stage=stage,
        ):
            full_reply += token
            yield token

        assistant_msg = Message(
            session_id=session.id, role="assistant", content=full_reply
        )
        db.add(assistant_msg)
        await db.flush()

    async def end_session(
        self, db: AsyncSession, user_id: str, session_id: str
    ) -> InterviewSessionResponse:
        session = await self._get_owned(db, user_id, session_id)
        if session.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="面试已结束",
            )

        # 生成结束语
        try:
            history = [
                {"role": m.role, "content": m.content}
                for m in (session.messages or [])
            ]
            closing_prompt = build_interview_closing_prompt(history)
            closing_content = await llm_service.chat(closing_prompt, temperature=0.8)
        except Exception:
            closing_content = (
                "感谢你参与本次模拟面试！你的表现我们已经记录下来，"
                "请查看评分报告了解详细反馈。祝你求职顺利！"
            )

        closing_msg = Message(
            session_id=session.id, role="assistant", content=closing_content
        )
        db.add(closing_msg)
        await db.flush()

        session.status = "completed"
        session.ended_at = datetime.now(timezone.utc)
        await db.refresh(session, attribute_names=["messages"])
        return await self._to_response(db, session)

    async def generate_report(
        self, db: AsyncSession, user_id: str, session_id: str
    ) -> InterviewReportResponse:
        # 延迟导入避免循环依赖
        from src.agents.evaluation_agent import evaluation_agent
        from src.agents.memory import long_term_memory

        session = await self._get_owned(db, user_id, session_id)
        result = await db.execute(
            select(InterviewSession)
            .where(InterviewSession.id == session_id)
            .options(selectinload(InterviewSession.messages))
        )
        session = result.scalar_one()

        resume_result = await db.execute(
            select(Resume).where(Resume.id == session.resume_id)
        )
        jd_result = await db.execute(
            select(JobDescription).where(JobDescription.id == session.jd_id)
        )
        resume = resume_result.scalar_one()
        jd = jd_result.scalar_one()

        messages = [
            {"role": m.role, "content": m.content} for m in session.messages
        ]
        # 使用 EvaluationAgent 进行多步评估
        data = await evaluation_agent.evaluate(
            messages=messages,
            resume_summary=resume_service.get_summary(resume),
            jd_title=jd.title,
        )

        report = InterviewReportResponse(
            id=str(uuid.uuid4()),
            session_id=session.id,
            overall_score=float(data.get("overallScore", data.get("overall_score", 75))),
            dimensions=[
                ScoreDimension(
                    name=d.get("name", "维度"),
                    score=float(d.get("score", 70)),
                    max_score=float(d.get("maxScore", d.get("max_score", 100))),
                )
                for d in data.get("dimensions", [])
            ]
            or self._default_dimensions(),
            suggestions=[
                Suggestion(
                    category=s.get("category", "综合"),
                    content=s.get("content", ""),
                    priority=s.get("priority", "medium"),  # type: ignore[arg-type]
                )
                for s in data.get("suggestions", [])
            ]
            or self._default_suggestions(),
            summary=data.get("summary", "面试表现整体良好，建议继续加强技术深度表达。"),
            created_at=datetime.now(timezone.utc),
        )

        # 保存报告到数据库
        session.report_json = report.model_dump_json()
        await db.commit()

        # V4: 记录到长期记忆
        long_term_memory.record_interview(
            user_id=session.user_id,
            score=report.overall_score,
            dimensions=[
                {"name": d.name, "score": d.score} for d in report.dimensions
            ],
            summary=report.summary,
        )

        return report

    async def _generate_reply(
        self, db: AsyncSession, session: InterviewSession, content: str
    ) -> str:
        resume_summary, jd_summary = await self._get_context(db, session)
        conversation_history = [
            {"role": m.role, "content": m.content}
            for m in (session.messages or [])
        ]
        stage = self._current_stage(session)
        # V4: 使用 Agent 层 + ReAct + Memory
        reply = await interview_agent.ask(
            user_input=content,
            resume_summary=resume_summary,
            jd_summary=jd_summary,
            conversation_history=conversation_history,
            stage=stage,
            user_id=session.user_id,
        )
        # 记录到记忆系统
        interview_agent.record_exchange(content, reply)
        return reply

    async def _get_context(
        self, db: AsyncSession, session: InterviewSession
    ) -> tuple[str, str]:
        resume_result = await db.execute(
            select(Resume).where(Resume.id == session.resume_id)
        )
        jd_result = await db.execute(
            select(JobDescription).where(JobDescription.id == session.jd_id)
        )
        resume = resume_result.scalar_one_or_none()
        jd = jd_result.scalar_one_or_none()
        return (
            resume_service.get_summary(resume) if resume else "",
            jd_service.get_summary(jd) if jd else "",
        )

    async def _get_context_full(
        self, db: AsyncSession, resume_id: str, jd_id: str
    ) -> tuple[str, str, str]:
        """获取简历摘要、JD 摘要和 JD 标题。"""
        resume_result = await db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        jd_result = await db.execute(
            select(JobDescription).where(JobDescription.id == jd_id)
        )
        resume = resume_result.scalar_one_or_none()
        jd = jd_result.scalar_one_or_none()
        return (
            resume_service.get_summary(resume) if resume else "",
            jd_service.get_summary(jd) if jd else "",
            jd.title if jd else "",
        )

    async def _ensure_resources(
        self,
        db: AsyncSession,
        user_id: str,
        resume_id: str,
        jd_id: str,
    ) -> None:
        resume_result = await db.execute(
            select(Resume).where(
                Resume.id == resume_id, Resume.user_id == user_id
            )
        )
        jd_result = await db.execute(
            select(JobDescription).where(
                JobDescription.id == jd_id, JobDescription.user_id == user_id
            )
        )
        if not resume_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="简历不存在")
        if not jd_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="JD 不存在")

    async def _get_owned(
        self, db: AsyncSession, user_id: str, session_id: str
    ) -> InterviewSession:
        result = await db.execute(
            select(InterviewSession)
            .where(
                InterviewSession.id == session_id,
                InterviewSession.user_id == user_id,
            )
            .options(selectinload(InterviewSession.messages))
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="面试会话不存在")
        return session

    async def _to_response(
        self, db: AsyncSession, session: InterviewSession
    ) -> InterviewSessionResponse:
        if not session.messages:
            await db.refresh(session, attribute_names=["messages"])
        return InterviewSessionResponse(
            id=session.id,
            resume_id=session.resume_id,
            jd_id=session.jd_id,
            status=session.status,  # type: ignore[arg-type]
            messages=[
                MessageResponse(
                    id=m.id,
                    role=m.role,  # type: ignore[arg-type]
                    content=m.content,
                    created_at=m.created_at,
                )
                for m in session.messages
            ],
            started_at=session.started_at,
            ended_at=session.ended_at,
        )

    def _default_report_data(self) -> dict:
        return {
            "overallScore": 75,
            "dimensions": [
                {"name": "技术能力", "score": 78, "maxScore": 100},
                {"name": "沟通表达", "score": 72, "maxScore": 100},
                {"name": "问题解决", "score": 74, "maxScore": 100},
                {"name": "学习能力", "score": 76, "maxScore": 100},
                {"name": "岗位匹配度", "score": 70, "maxScore": 100},
            ],
            "suggestions": [
                {
                    "category": "技术深度",
                    "content": "回答时可补充更多实现细节与权衡考量。",
                    "priority": "high",
                }
            ],
            "summary": "整体表现良好，建议在项目经验描述上更加结构化。",
        }

    def _default_dimensions(self) -> list[ScoreDimension]:
        return [
            ScoreDimension(name="技术能力", score=78, max_score=100),
            ScoreDimension(name="沟通表达", score=72, max_score=100),
            ScoreDimension(name="问题解决", score=74, max_score=100),
            ScoreDimension(name="学习能力", score=76, max_score=100),
            ScoreDimension(name="岗位匹配度", score=70, max_score=100),
        ]

    def _default_suggestions(self) -> list[Suggestion]:
        return [
            Suggestion(
                category="综合",
                content="建议使用 STAR 法则组织回答。",
                priority="medium",
            )
        ]


interview_service = InterviewService()
