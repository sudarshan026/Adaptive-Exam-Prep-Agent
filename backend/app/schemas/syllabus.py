"""Pydantic schemas for syllabus, subjects, topics, and resources."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Subject ---
class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    weightage: float = 1.0
    color: str = "#6366f1"

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    weightage: Optional[float] = None
    color: Optional[str] = None

class SubjectResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    weightage: float
    order_index: int
    color: str
    created_at: datetime
    topics: List["TopicResponse"] = []
    model_config = {"from_attributes": True}


# --- Topic ---
class TopicCreate(BaseModel):
    subject_id: int
    name: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    difficulty: str = "medium"
    estimated_hours: float = 2.0

class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_hours: Optional[float] = None
    is_completed: Optional[int] = None

class TopicResponse(BaseModel):
    id: int
    subject_id: int
    user_id: int
    name: str
    description: Optional[str]
    difficulty: str
    estimated_hours: float
    order_index: int
    is_completed: int
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Dependency ---
class DependencyCreate(BaseModel):
    topic_id: int
    depends_on_topic_id: int

class DependencyResponse(BaseModel):
    id: int
    topic_id: int
    depends_on_topic_id: int
    model_config = {"from_attributes": True}


# --- Learning Resource ---
class ResourceCreate(BaseModel):
    topic_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=500)
    url: Optional[str] = None
    resource_type: str = "article"
    description: Optional[str] = None

class ResourceResponse(BaseModel):
    id: int
    user_id: int
    topic_id: Optional[int]
    title: str
    url: Optional[str]
    resource_type: str
    description: Optional[str]
    is_saved: int
    created_at: datetime
    model_config = {"from_attributes": True}


# --- Syllabus Upload ---
class SyllabusUploadResponse(BaseModel):
    id: int
    filename: str
    status: str
    parsed_structure: Optional[dict] = None
    created_at: datetime
    model_config = {"from_attributes": True}
