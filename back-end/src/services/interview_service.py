import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from src.services.rag_service import rag_service
from src.services.resume_service import resume_service
from src.utils.prompt_builder import build_evaluation_prompt


class InterviewService:
    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        data: CreateInterviewRequest,
    ) -> InterviewSessionResponse:
        await self._ensure_resources(db, user_id, data.resume_id, data.jd_id)

        session = InterviewSession(
            user_id=user_id,
            resume_id=data.resume_id,
            jd_id=data.jd_id,
            status="active",
        )
        db.add(session)
        await db.flush()

        opening = Message(
            session_id=session.id,
            role="assistant",
            content="你好，欢迎参加本次模拟面试。请先做一个简短的自我介绍。",
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
            .options(selectinload(InterviewSession.messages))
            .order_by(InterviewSession.started_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()
        return [await self._to_response(db, s) for s in sessions]

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
        full_reply = ""
        async for token in rag_service.generate_stream(
            question=content,
            resume_summary=resume_summary,
            jd_summary=jd_summary,
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
        session.status = "completed"
        session.ended_at = datetime.now(timezone.utc)
        await db.refresh(session, attribute_names=["messages"])
        return await self._to_response(db, session)

    async def generate_report(
        self, db: AsyncSession, user_id: str, session_id: str
    ) -> InterviewReportResponse:
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
        eval_messages = build_evaluation_prompt(
            messages=messages,
            resume_summary=resume_service.get_summary(resume),
            jd_title=jd.title,
        )
        raw = await llm_service.chat(eval_messages)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = self._default_report_data()

        return InterviewReportResponse(
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

    async def _generate_reply(
        self, db: AsyncSession, session: InterviewSession, content: str
    ) -> str:
        resume_summary, jd_summary = await self._get_context(db, session)
        return await rag_service.generate(
            question=content,
            resume_summary=resume_summary,
            jd_summary=jd_summary,
        )

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
