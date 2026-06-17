from datetime import datetime
from typing import Literal, Optional

from pydantic import Field

from src.schemas.base import CamelModel


MessageRole = Literal["user", "assistant", "system"]
SessionStatus = Literal["idle", "active", "completed"]


class CreateInterviewRequest(CamelModel):
    resume_id: str
    jd_id: str


class MessageRequest(CamelModel):
    content: str = Field(min_length=1)


class MessageResponse(CamelModel):
    id: str
    role: MessageRole
    content: str
    created_at: datetime = Field(serialization_alias="createdAt")


class InterviewSessionResponse(CamelModel):
    id: str
    resume_id: str
    jd_id: str
    status: SessionStatus
    messages: list[MessageResponse] = []
    started_at: Optional[datetime] = Field(
        default=None, serialization_alias="startedAt"
    )
    ended_at: Optional[datetime] = Field(
        default=None, serialization_alias="endedAt"
    )
