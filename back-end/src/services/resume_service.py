import json
import traceback

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.models.resume import Resume
from src.schemas.resume import ResumeAnalysisResponse, ResumeResponse
from src.services.llm_service import llm_service
from src.utils.file_handler import delete_file, save_upload_file
from src.utils.pdf_parser import parse_document
from src.utils.prompt_builder import build_resume_analysis_prompt


class ResumeService:
    async def upload(
        self,
        db: AsyncSession,
        user_id: str,
        file: UploadFile,
    ) -> ResumeResponse:
        """创建简历记录并返回，解析由 process 在后台异步完成"""
        file_name, file_path = await save_upload_file(file, subdir=f"resumes/{user_id}")

        resume = Resume(
            user_id=user_id,
            file_name=file_name,
            file_path=str(file_path),
            status="pending",
        )
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        return self._to_response(resume)

    async def process(self, resume_id: str) -> None:
        """后台异步解析简历文本并调用 LLM 分析"""
        from src.db.postgres import async_session_factory

        logger.info("Resume process started: {}", resume_id)
        async with async_session_factory() as db:
            result = await db.execute(select(Resume).where(Resume.id == resume_id))
            resume = result.scalar_one_or_none()
            if not resume:
                logger.warning("Resume not found for processing: {}", resume_id)
                return

            try:
                raw_text = parse_document(resume.file_path)
                logger.info("Resume {} PDF parsed, {} chars", resume_id, len(raw_text))
                resume.raw_text = raw_text

                analysis = await self._analyze_text(raw_text)
                logger.info(
                    "Resume {} LLM analysis done, skills={}, experience={}",
                    resume_id,
                    len(analysis.get("skills", [])),
                    len(analysis.get("experience", [])),
                )
                resume.analysis_json = json.dumps(analysis, ensure_ascii=False)
                resume.status = "parsed"
                logger.info("Resume {} marked as parsed", resume_id)
            except Exception:
                logger.error(
                    "Resume {} processing failed:\n{}",
                    resume_id,
                    traceback.format_exc(),
                )
                resume.status = "failed"
                try:
                    raw_text = parse_document(resume.file_path)
                    resume.raw_text = raw_text
                except Exception:
                    logger.warning("Resume {} fallback text extraction also failed", resume_id)

            await db.commit()

    async def list_by_user(
        self, db: AsyncSession, user_id: str
    ) -> list[ResumeResponse]:
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.uploaded_at.desc())
        )
        return [self._to_response(r) for r in result.scalars().all()]

    async def get_by_id(
        self, db: AsyncSession, user_id: str, resume_id: str
    ) -> ResumeResponse:
        resume = await self._get_owned(db, user_id, resume_id)
        return self._to_response(resume)

    async def get_analysis(
        self, db: AsyncSession, user_id: str, resume_id: str
    ) -> ResumeAnalysisResponse:
        resume = await self._get_owned(db, user_id, resume_id)
        if resume.status != "parsed" or not resume.analysis_json:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="简历解析结果不可用",
            )
        data = json.loads(resume.analysis_json)
        return ResumeAnalysisResponse(
            resume_id=resume.id,
            skills=data.get("skills", []),
            experience=data.get("experience", []),
            education=data.get("education", []),
            summary=data.get("summary", ""),
        )

    async def delete(
        self, db: AsyncSession, user_id: str, resume_id: str
    ) -> None:
        resume = await self._get_owned(db, user_id, resume_id)
        delete_file(resume.file_path)
        await db.delete(resume)

    async def _get_owned(
        self, db: AsyncSession, user_id: str, resume_id: str
    ) -> Resume:
        result = await db.execute(
            select(Resume).where(
                Resume.id == resume_id, Resume.user_id == user_id
            )
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="简历不存在"
            )
        return resume

    async def _analyze_text(self, text: str) -> dict:
        messages = build_resume_analysis_prompt(text)
        raw = await llm_service.chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "skills": [],
                "experience": [],
                "education": [],
                "summary": raw[:500],
            }

    def _to_response(self, resume: Resume) -> ResumeResponse:
        return ResumeResponse(
            id=resume.id,
            file_name=resume.file_name,
            uploaded_at=resume.uploaded_at,
            status=resume.status,  # type: ignore[arg-type]
        )

    def get_summary(self, resume: Resume) -> str:
        if resume.analysis_json:
            data = json.loads(resume.analysis_json)
            return data.get("summary", resume.raw_text or "")[:500]
        return (resume.raw_text or "")[:500]


resume_service = ResumeService()
