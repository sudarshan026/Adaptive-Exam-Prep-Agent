"""Pydantic schemas for assessments, questions, and responses."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Questions ---
class QuestionCreate(BaseModel):
    topic_id: Optional[int] = None
    subject_name: Optional[str] = None
    topic_name: Optional[str] = None
    question_text: str
    question_type: str = "mcq"
    difficulty: str = "medium"
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    tags: List[str] = []

class QuestionResponse(BaseModel):
    id: int
    topic_id: Optional[int]
    subject_name: Optional[str]
    topic_name: Optional[str]
    question_text: str
    question_type: str
    difficulty: str
    options: Optional[List[str]]
    explanation: Optional[str]
    tags: List[str]
    created_at: datetime
    model_config = {"from_attributes": True}

class QuestionWithAnswer(QuestionResponse):
    correct_answer: str


# --- Assessments ---
class AssessmentCreate(BaseModel):
    title: Optional[str] = None
    assessment_type: str = "topic_quiz"
    topic_id: Optional[int] = None
    topic_name: Optional[str] = None
    subject_name: Optional[str] = None
    difficulty: str = "medium"
    num_questions: int = Field(default=5, ge=1, le=50)
    time_limit_minutes: Optional[int] = None

class AssessmentResponse(BaseModel):
    id: int
    user_id: int
    title: str
    assessment_type: str
    subject_name: Optional[str]
    topic_name: Optional[str]
    topic_id: Optional[int]
    total_questions: int
    total_marks: float
    score: Optional[float]
    accuracy: Optional[float]
    time_limit_minutes: Optional[int]
    time_taken_minutes: Optional[int]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}

class AnswerSubmit(BaseModel):
    question_id: int
    selected_answer: str

class AssessmentSubmission(BaseModel):
    answers: List[AnswerSubmit]
    time_taken_minutes: Optional[int] = None

class AssessmentResult(BaseModel):
    assessment: AssessmentResponse
    questions: List[QuestionWithAnswer]
    responses: List[dict]
    topic_breakdown: List[dict]
    weak_topics_identified: List[str]


# --- Question Generation ---
class GenerateQuestionsRequest(BaseModel):
    topic_id: Optional[int] = None
    topic_name: Optional[str] = None
    subject_name: Optional[str] = None
    difficulty: str = "medium"
    num_questions: int = Field(default=5, ge=1, le=20)
    question_type: str = "mcq"
