from datetime import datetime
from typing import Literal, Optional

from pydantic import Field

from src.schemas.base import CamelModel


JDStatus = Literal["pending", "analyzed", "failed"]


class JDCreateRequest(CamelModel):
    title: str
    company: str = ""
    content: str


class JobDescriptionResponse(CamelModel):
    id: str
    title: str
    company: str
    uploaded_at: datetime = Field(serialization_alias="uploadedAt")
    status: JDStatus


class JDAnalysisResponse(CamelModel):
    jd_id: str
    required_skills: list[str]
    preferred_skills: list[str]
    responsibilities: list[str]
    match_score: Optional[float] = None
