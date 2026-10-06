"""Pydantic schemas for study plans and sessions."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class StudySessionResponse(BaseModel):
    id: int
    plan_id: int
    user_id: int
    topic_id: Optional[int]
    subject_name: Optional[str]
    topic_name: Optional[str]
    session_type: str
    scheduled_date: date
    estimated_duration_minutes: int
    actual_duration_minutes: Optional[int]
    priority: str
    status: str
    notes: Optional[str]
    order_in_day: int
    created_at: datetime
    completed_at: Optional[datetime]
    model_config = {"from_attributes": True}


class StudySessionUpdate(BaseModel):
    status: Optional[str] = None
    actual_duration_minutes: Optional[int] = None
    scheduled_date: Optional[date] = None
    notes: Optional[str] = None


class StudyPlanResponse(BaseModel):
    id: int
    user_id: int
    version: int
    is_active: int
    change_reason: Optional[str]
    created_at: datetime
    sessions: List[StudySessionResponse] = []
    model_config = {"from_attributes": True}


class GeneratePlanRequest(BaseModel):
    """Request to generate a new study plan."""
    force_regenerate: bool = False


class DashboardResponse(BaseModel):
    """Aggregated dashboard data."""
    welcome_name: str
    exam_type: str
    days_remaining: Optional[int]
    daily_target_hours: float
    completed_hours_today: float
    study_streak: int
    total_study_hours: float
    overall_progress: float  # percentage
    topics_total: int
    topics_completed: int
    today_sessions: List[StudySessionResponse]
    upcoming_sessions: List[StudySessionResponse]
    recent_assessments: List[dict]
    weak_topics: List[dict]
    mastery_summary: List[dict]
    is_demo_mode: bool
