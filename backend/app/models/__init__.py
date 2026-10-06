"""Models package — import all models so they register with SQLAlchemy."""
from app.models.user import User
from app.models.student import StudentProfile, Exam
from app.models.syllabus import UploadedSyllabus, Subject, Topic, TopicDependency, LearningResource
from app.models.study import StudyPlan, StudySession, StudyLog
from app.models.assessment import Question, Assessment, AssessmentQuestion, StudentResponse
from app.models.analytics import TopicMastery, CoachingInsight, TutorConversation

__all__ = [
    "User", "StudentProfile", "Exam",
    "UploadedSyllabus", "Subject", "Topic", "TopicDependency", "LearningResource",
    "StudyPlan", "StudySession", "StudyLog",
    "Question", "Assessment", "AssessmentQuestion", "StudentResponse",
    "TopicMastery", "CoachingInsight", "TutorConversation",
]
