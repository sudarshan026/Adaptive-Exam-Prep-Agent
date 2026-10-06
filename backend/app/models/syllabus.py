"""Syllabus, subject, topic, and resource models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from app.database.base import Base


class UploadedSyllabus(Base):
    __tablename__ = "uploaded_syllabi"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    extracted_text = Column(Text, nullable=True)
    parsed_structure = Column(JSON, nullable=True)  # Structured syllabus as JSON
    status = Column(String(20), default="uploaded")  # uploaded, parsing, parsed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    weightage = Column(Float, default=1.0)  # Relative importance for exam
    order_index = Column(Integer, default=0)
    color = Column(String(7), default="#6366f1")  # Hex color for UI
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    estimated_hours = Column(Float, default=2.0)
    order_index = Column(Integer, default=0)
    is_completed = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TopicDependency(Base):
    __tablename__ = "topic_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)
    depends_on_topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False)


class LearningResource(Base):
    __tablename__ = "learning_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=True)
    resource_type = Column(String(50), default="article")  # video, article, book, notes, question_bank
    description = Column(Text, nullable=True)
    is_saved = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
