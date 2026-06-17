from fastapi import APIRouter, BackgroundTasks, File, UploadFile, status

from src.api.deps import CurrentUser, DbSession
from src.schemas.jd import JDAnalysisResponse, JDCreateRequest, JobDescriptionResponse
from src.services.jd_service import jd_service

router = APIRouter()


@router.post("/upload", response_model=JobDescriptionResponse)
async def upload_jd(
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> JobDescriptionResponse:
    result = await jd_service.upload(db, current_user.id, file)
    background_tasks.add_task(jd_service.process, result.id)
    return result


@router.post("", response_model=JobDescriptionResponse)
async def create_jd(
    data: JDCreateRequest,
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> JobDescriptionResponse:
    result = await jd_service.create(db, current_user.id, data)
    background_tasks.add_task(jd_service.process, result.id)
    return result


@router.get("", response_model=list[JobDescriptionResponse])
async def list_jds(
    db: DbSession,
    current_user: CurrentUser,
) -> list[JobDescriptionResponse]:
    return await jd_service.list_by_user(db, current_user.id)


@router.get("/{jd_id}", response_model=JobDescriptionResponse)
async def get_jd(
    jd_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> JobDescriptionResponse:
    return await jd_service.get_by_id(db, current_user.id, jd_id)


@router.get("/{jd_id}/analysis", response_model=JDAnalysisResponse)
async def get_jd_analysis(
    jd_id: str,
    db: DbSession,
    current_user: CurrentUser,
    resume_id: str | None = None,
) -> JDAnalysisResponse:
    return await jd_service.get_analysis(
        db, current_user.id, jd_id, resume_id=resume_id
    )


@router.delete("/{jd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_jd(
    jd_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    await jd_service.delete(db, current_user.id, jd_id)
