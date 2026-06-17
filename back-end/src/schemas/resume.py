from datetime import datetime
from typing import Literal

from pydantic import Field

from src.schemas.base import CamelModel


ResumeStatus = Literal["pending", "parsed", "failed"]


class ResumeResponse(CamelModel):
    id: str
    file_name: str = Field(serialization_alias="fileName")
    uploaded_at: datetime = Field(serialization_alias="uploadedAt")
    status: ResumeStatus


class ResumeAnalysisResponse(CamelModel):
    resume_id: str
    skills: list[str]
    experience: list[str]
    education: list[str]
    summary: str
