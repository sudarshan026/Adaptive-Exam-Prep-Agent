"""Analytics, mastery, coaching, and tutor conversation models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from app.database.base import Base


class TopicMastery(Base):
    __tablename__ = "topic_mastery"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_name = Column(String(200), nullable=True)
    topic_name = Column(String(300), nullable=True)
    mastery_score = Column(Float, default=0.0)  # 0.0 to 100.0
    total_questions_attempted = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    last_assessed_at = Column(DateTime, nullable=True)
    last_revision_at = Column(DateTime, nullable=True)
    next_revision_date = Column(DateTime, nullable=True)  # Spaced repetition
    revision_interval_days = Column(Integer, default=1)  # Current interval
    confidence_level = Column(String(20), default="unknown")  # unknown, low, medium, high
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CoachingInsight(Base):
    __tablename__ = "coaching_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    insight_type = Column(String(50), nullable=False)  # streak, improvement, weakness, milestone, encouragement
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Supporting data
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TutorConversation(Base):
    __tablename__ = "tutor_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    topic_name = Column(String(300), nullable=True)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
