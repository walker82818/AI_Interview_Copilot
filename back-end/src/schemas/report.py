from datetime import datetime
from typing import Literal

from pydantic import Field

from src.schemas.base import CamelModel


SuggestionPriority = Literal["high", "medium", "low"]


class ScoreDimension(CamelModel):
    name: str
    score: float
    max_score: float = Field(serialization_alias="maxScore")


class Suggestion(CamelModel):
    category: str
    content: str
    priority: SuggestionPriority


class InterviewReportResponse(CamelModel):
    id: str
    session_id: str
    overall_score: float
    dimensions: list[ScoreDimension]
    suggestions: list[Suggestion]
    summary: str
    created_at: datetime = Field(serialization_alias="createdAt")
