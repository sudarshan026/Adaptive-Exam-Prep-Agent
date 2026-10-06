"""Assessment, question, and student response models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from app.database.base import Base


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    subject_name = Column(String(200), nullable=True)
    topic_name = Column(String(300), nullable=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(30), default="mcq")  # mcq, true_false, short_answer
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    options = Column(JSON, nullable=True)  # List of option strings for MCQ
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Assessment(Base):
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    assessment_type = Column(String(30), default="topic_quiz")  # topic_quiz, weekly_test, mock_exam
    subject_name = Column(String(200), nullable=True)
    topic_name = Column(String(300), nullable=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    total_questions = Column(Integer, default=0)
    total_marks = Column(Float, default=0)
    score = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)  # Percentage 0-100
    time_limit_minutes = Column(Integer, nullable=True)
    time_taken_minutes = Column(Integer, nullable=True)
    status = Column(String(20), default="created")  # created, in_progress, completed, abandoned
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, default=0)
    marks = Column(Float, default=1.0)


class StudentResponse(Base):
    __tablename__ = "student_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_answer = Column(String(500), nullable=True)
    is_correct = Column(Integer, nullable=True)  # 0 or 1, SQLite compat
    marks_obtained = Column(Float, default=0)
    time_spent_seconds = Column(Integer, nullable=True)
    answered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
