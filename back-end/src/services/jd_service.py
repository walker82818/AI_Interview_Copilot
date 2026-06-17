import json
import traceback

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.models.job_description import JobDescription
from src.models.resume import Resume
from src.schemas.jd import JDAnalysisResponse, JDCreateRequest, JobDescriptionResponse
from src.services.llm_service import llm_service
from src.utils.file_handler import delete_file, save_upload_file
from src.utils.pdf_parser import parse_document
from src.utils.prompt_builder import build_jd_analysis_prompt


class JDService:
    async def upload(
        self,
        db: AsyncSession,
        user_id: str,
        file: UploadFile,
    ) -> JobDescriptionResponse:
        """上传 JD 文件并返回 pending 状态，解析由 process 后台完成"""
        file_name, file_path = await save_upload_file(file, subdir=f"jd/{user_id}")
        try:
            content = parse_document(file_path)
            title = file_name.rsplit(".", 1)[0]
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件解析失败: {exc}",
            ) from exc

        jd = JobDescription(
            user_id=user_id,
            title=title,
            company="",
            content=content,
            file_path=str(file_path),
            status="pending",
        )
        db.add(jd)
        await db.commit()
        await db.refresh(jd)
        return self._to_response(jd)

    async def process(self, jd_id: str) -> None:
        """后台异步调用 LLM 分析 JD"""
        from src.db.postgres import async_session_factory

        logger.info("JD process started: {}", jd_id)
        async with async_session_factory() as db:
            result = await db.execute(
                select(JobDescription).where(JobDescription.id == jd_id)
            )
            jd = result.scalar_one_or_none()
            if not jd:
                logger.warning("JD not found for processing: {}", jd_id)
                return

            try:
                analysis = await self._analyze_text(jd.content)
                logger.info(
                    "JD {} LLM analysis done, required_skills={}",
                    jd_id,
                    len(analysis.get("requiredSkills", analysis.get("required_skills", []))),
                )
                jd.analysis_json = json.dumps(analysis, ensure_ascii=False)
                jd.status = "analyzed"
                logger.info("JD {} marked as analyzed", jd_id)
            except Exception:
                logger.error(
                    "JD {} processing failed:\n{}",
                    jd_id,
                    traceback.format_exc(),
                )
                jd.status = "failed"

            await db.commit()

    async def create(
        self,
        db: AsyncSession,
        user_id: str,
        data: JDCreateRequest,
    ) -> JobDescriptionResponse:
        """创建 JD 记录并返回 pending 状态，解析由 process 后台完成"""
        jd = JobDescription(
            user_id=user_id,
            title=data.title,
            company=data.company,
            content=data.content,
            status="pending",
        )
        db.add(jd)
        await db.commit()
        await db.refresh(jd)
        return self._to_response(jd)

    async def list_by_user(
        self, db: AsyncSession, user_id: str
    ) -> list[JobDescriptionResponse]:
        result = await db.execute(
            select(JobDescription)
            .where(JobDescription.user_id == user_id)
            .order_by(JobDescription.uploaded_at.desc())
        )
        return [self._to_response(j) for j in result.scalars().all()]

    async def get_by_id(
        self, db: AsyncSession, user_id: str, jd_id: str
    ) -> JobDescriptionResponse:
        jd = await self._get_owned(db, user_id, jd_id)
        return self._to_response(jd)

    async def get_analysis(
        self,
        db: AsyncSession,
        user_id: str,
        jd_id: str,
        resume_id: str | None = None,
    ) -> JDAnalysisResponse:
        jd = await self._get_owned(db, user_id, jd_id)
        if jd.status != "analyzed" or not jd.analysis_json:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="JD 分析结果不可用",
            )
        data = json.loads(jd.analysis_json)
        match_score = None
        if resume_id:
            match_score = await self._calc_match_score(db, user_id, resume_id, data)
        return JDAnalysisResponse(
            jd_id=jd.id,
            required_skills=data.get("requiredSkills", data.get("required_skills", [])),
            preferred_skills=data.get(
                "preferredSkills", data.get("preferred_skills", [])
            ),
            responsibilities=data.get("responsibilities", []),
            match_score=match_score,
        )

    async def delete(
        self, db: AsyncSession, user_id: str, jd_id: str
    ) -> None:
        jd = await self._get_owned(db, user_id, jd_id)
        if jd.file_path:
            delete_file(jd.file_path)
        await db.delete(jd)

    async def _get_owned(
        self, db: AsyncSession, user_id: str, jd_id: str
    ) -> JobDescription:
        result = await db.execute(
            select(JobDescription).where(
                JobDescription.id == jd_id, JobDescription.user_id == user_id
            )
        )
        jd = result.scalar_one_or_none()
        if not jd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="JD 不存在"
            )
        return jd

    async def _analyze_text(self, text: str) -> dict:
        messages = build_jd_analysis_prompt(text)
        raw = await llm_service.chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "requiredSkills": [],
                "preferredSkills": [],
                "responsibilities": [raw[:300]],
            }

    async def _calc_match_score(
        self,
        db: AsyncSession,
        user_id: str,
        resume_id: str,
        jd_data: dict,
    ) -> float:
        result = await db.execute(
            select(Resume).where(
                Resume.id == resume_id, Resume.user_id == user_id
            )
        )
        resume = result.scalar_one_or_none()
        if not resume or not resume.analysis_json:
            return 0.0
        resume_data = json.loads(resume.analysis_json)
        resume_skills = set(resume_data.get("skills", []))
        required = set(
            jd_data.get("requiredSkills", jd_data.get("required_skills", []))
        )
        if not required:
            return 75.0
        matched = len(resume_skills & required)
        return round(matched / len(required) * 100, 1)

    def _to_response(self, jd: JobDescription) -> JobDescriptionResponse:
        return JobDescriptionResponse(
            id=jd.id,
            title=jd.title,
            company=jd.company,
            uploaded_at=jd.uploaded_at,
            status=jd.status,  # type: ignore[arg-type]
        )

    def get_summary(self, jd: JobDescription) -> str:
        return jd.content[:800]


jd_service = JDService()
