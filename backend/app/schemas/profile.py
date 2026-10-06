"""Pydantic schemas for student profiles."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class ProfileCreate(BaseModel):
    exam_type: str = Field(..., min_length=1, max_length=100)
    target_score: Optional[float] = None
    current_level: Optional[str] = "intermediate"
    exam_date: Optional[date] = None
    daily_study_hours: float = Field(default=4.0, ge=0.5, le=16.0)
    learning_preference: str = "balanced"
    strong_topics: List[str] = []
    weak_topics: List[str] = []


class ProfileUpdate(BaseModel):
    exam_type: Optional[str] = None
    target_score: Optional[float] = None
    current_level: Optional[str] = None
    exam_date: Optional[date] = None
    daily_study_hours: Optional[float] = None
    learning_preference: Optional[str] = None
    strong_topics: Optional[List[str]] = None
    weak_topics: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    exam_type: str
    target_score: Optional[float]
    current_level: Optional[str]
    exam_date: Optional[date]
    daily_study_hours: float
    learning_preference: str
    strong_topics: List[str]
    weak_topics: List[str]
    study_streak: int
    total_study_hours: float
    onboarding_completed: int
    created_at: datetime
    days_remaining: Optional[int] = None

    model_config = {"from_attributes": True}
