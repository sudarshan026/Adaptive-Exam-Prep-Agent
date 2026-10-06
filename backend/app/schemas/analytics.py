"""Pydantic schemas for analytics, coaching, and tutor."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Topic Mastery ---
class TopicMasteryResponse(BaseModel):
    id: int
    user_id: int
    topic_id: int
    subject_name: Optional[str]
    topic_name: Optional[str]
    mastery_score: float
    total_questions_attempted: int
    correct_answers: int
    confidence_level: str
    last_assessed_at: Optional[datetime]
    next_revision_date: Optional[datetime]
    model_config = {"from_attributes": True}


# --- Coaching ---
class CoachingInsightResponse(BaseModel):
    id: int
    insight_type: str
    title: str
    message: str
    data: Optional[dict]
    is_read: int
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Tutor ---
class TutorMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    topic_id: Optional[int] = None
    topic_name: Optional[str] = None

class TutorResponse(BaseModel):
    role: str
    content: str
    topic_name: Optional[str]
    suggested_questions: List[str] = []
    is_demo_mode: bool = False

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    topic_id: Optional[int]
    topic_name: Optional[str]
    role: str
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Analytics ---
class PerformanceAnalytics(BaseModel):
    overall_accuracy: float
    total_assessments: int
    total_questions_attempted: int
    total_correct: int
    study_hours_total: float
    study_streak: int
    topic_mastery: List[TopicMasteryResponse]
    assessment_history: List[dict]
    study_hours_by_day: List[dict]
    strong_topics: List[str]
    weak_topics: List[str]
    improvement_trend: List[dict]


class WeaknessReport(BaseModel):
    weak_topics: List[dict]
    recommendations: List[str]
    insufficient_data_topics: List[str]
