"""Student profile, exam, and learning preference models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Date, JSON
from app.database.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    exam_type = Column(String(100), nullable=False)  # e.g., "GATE CSE", "JEE", "NEET"
    target_score = Column(Float, nullable=True)
    current_level = Column(String(50), nullable=True)  # beginner, intermediate, advanced
    exam_date = Column(Date, nullable=True)
    daily_study_hours = Column(Float, default=4.0)
    learning_preference = Column(String(50), default="balanced")  # visual, reading, practice, balanced
    strong_topics = Column(JSON, default=list)  # list of topic names/IDs
    weak_topics = Column(JSON, default=list)
    study_streak = Column(Integer, default=0)
    total_study_hours = Column(Float, default=0.0)
    onboarding_completed = Column(Integer, default=0)  # 0=false, 1=true (SQLite compat)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # Engineering, Medical, etc.
    total_marks = Column(Float, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
