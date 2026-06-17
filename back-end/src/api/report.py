from fastapi import APIRouter, HTTPException, status

from src.api.deps import CurrentUser, DbSession
from src.schemas.report import InterviewReportResponse
from src.services.interview_service import interview_service

router = APIRouter()


@router.get("/{session_id}", response_model=InterviewReportResponse)
async def get_report(
    session_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> InterviewReportResponse:
    try:
        return await interview_service.generate_report(
            db, current_user.id, session_id
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="报告不存在",
        ) from exc


@router.post("/{session_id}/generate", response_model=InterviewReportResponse)
async def generate_report(
    session_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> InterviewReportResponse:
    return await interview_service.generate_report(db, current_user.id, session_id)
