from fastapi import APIRouter, BackgroundTasks, File, UploadFile, status

from src.api.deps import CurrentUser, DbSession
from src.schemas.resume import ResumeAnalysisResponse, ResumeResponse
from src.services.resume_service import resume_service

router = APIRouter()


@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> ResumeResponse:
    result = await resume_service.upload(db, current_user.id, file)
    background_tasks.add_task(resume_service.process, result.id)
    return result


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(
    db: DbSession,
    current_user: CurrentUser,
) -> list[ResumeResponse]:
    return await resume_service.list_by_user(db, current_user.id)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> ResumeResponse:
    return await resume_service.get_by_id(db, current_user.id, resume_id)


@router.get("/{resume_id}/analysis", response_model=ResumeAnalysisResponse)
async def get_resume_analysis(
    resume_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> ResumeAnalysisResponse:
    return await resume_service.get_analysis(db, current_user.id, resume_id)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    await resume_service.delete(db, current_user.id, resume_id)
