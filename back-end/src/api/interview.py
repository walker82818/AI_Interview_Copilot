from collections.abc import AsyncIterator

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from src.api.deps import CurrentUser, DbSession
from src.schemas.interview import (
    CreateInterviewRequest,
    InterviewSessionResponse,
    MessageRequest,
    MessageResponse,
)
from src.services.interview_service import interview_service

router = APIRouter()


@router.post("", response_model=InterviewSessionResponse)
async def create_interview(
    data: CreateInterviewRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> InterviewSessionResponse:
    return await interview_service.create_session(db, current_user.id, data)


@router.get("/recent", response_model=list[InterviewSessionResponse])
async def list_recent_interviews(
    db: DbSession,
    current_user: CurrentUser,
) -> list[InterviewSessionResponse]:
    return await interview_service.list_recent(db, current_user.id)


@router.get("/{session_id}", response_model=InterviewSessionResponse)
async def get_interview(
    session_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> InterviewSessionResponse:
    return await interview_service.get_session(db, current_user.id, session_id)


@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    data: MessageRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> MessageResponse:
    return await interview_service.send_message(
        db, current_user.id, session_id, data.content
    )


@router.post("/{session_id}/messages/stream")
async def send_message_stream(
    session_id: str,
    data: MessageRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> StreamingResponse:
    async def event_generator() -> AsyncIterator[str]:
        async for token in interview_service.send_message_stream(
            db, current_user.id, session_id, data.content
        ):
            yield token

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")


@router.post("/{session_id}/end", response_model=InterviewSessionResponse)
async def end_interview(
    session_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> InterviewSessionResponse:
    return await interview_service.end_session(db, current_user.id, session_id)
