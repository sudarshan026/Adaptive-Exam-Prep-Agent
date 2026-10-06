"""Agent #2 — Profile Analyzer.

Analyzes the student profile to determine learning strategy, identify
gaps in the profile, and generate insights about strong/weak areas.
"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState
from app.models.student import StudentProfile
from app.models.analytics import TopicMastery
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a student profile analysis AI agent. Your job is to analyze 
a student's exam preparation profile and provide actionable insights about their 
learning strategy. Be specific and data-driven in your analysis."""


async def analyze_profile(state: AgentState) -> dict:
    """LangGraph node: Analyze the student profile and generate insights."""
    db: AsyncSession = state["db"]
    user_id = state["user_id"]

    # Fetch profile
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return {
            "result": {"error": "No student profile found. Complete onboarding first."},
            "agents_called": state.get("agents_called", []) + ["profile_analyzer"],
        }

    # Fetch mastery data
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id)
    )
    mastery_records = result.scalars().all()

    weak_topics = [m.topic_name for m in mastery_records if m.mastery_score < 50 and m.total_questions_attempted >= 3]
    strong_topics = [m.topic_name for m in mastery_records if m.mastery_score >= 70]

    prompt = f"""Analyze this student's exam preparation profile and provide insights:

**Profile:**
- Exam Type: {profile.exam_type}
- Current Level: {profile.current_level}
- Target Score: {profile.target_score or 'Not set'}
- Daily Study Hours: {profile.daily_study_hours}h
- Learning Preference: {profile.learning_preference}
- Total Study Hours: {profile.total_study_hours}h
- Study Streak: {profile.study_streak} days
- Exam Date: {profile.exam_date or 'Not set'}

**Self-Reported:**
- Strong Topics: {', '.join(profile.strong_topics) if profile.strong_topics else 'None specified'}
- Weak Topics: {', '.join(profile.weak_topics) if profile.weak_topics else 'None specified'}

**Assessment-Based (from actual performance):**
- Strong Topics (mastery >= 70%): {', '.join(strong_topics) if strong_topics else 'No data yet'}
- Weak Topics (mastery < 50%): {', '.join(weak_topics) if weak_topics else 'No data yet'}

Provide a JSON response with:
{{
    "readiness_level": "low|medium|high",
    "daily_hours_recommendation": <float>,
    "focus_areas": ["topic1", "topic2"],
    "strategy_recommendations": ["recommendation1", "recommendation2"],
    "risk_factors": ["risk1", "risk2"],
    "motivational_note": "short encouraging message"
}}"""

    response = await call_llm(prompt, system_prompt=SYSTEM_PROMPT, json_mode=True)

    if response:
        try:
            from app.services.llm_service import extract_json
            insights = extract_json(response)
        except Exception:
            insights = {"raw_analysis": response}
    else:
        # Fallback analysis when LLM is unavailable
        insights = _fallback_analysis(profile, weak_topics, strong_topics)

    return {
        "result": {
            "profile_analysis": insights,
            "profile_summary": {
                "exam_type": profile.exam_type,
                "current_level": profile.current_level,
                "daily_hours": profile.daily_study_hours,
                "total_hours": profile.total_study_hours,
                "streak": profile.study_streak,
                "weak_count": len(weak_topics),
                "strong_count": len(strong_topics),
            },
        },
        "agents_called": state.get("agents_called", []) + ["profile_analyzer"],
    }


def _fallback_analysis(profile, weak_topics, strong_topics):
    """Deterministic fallback when LLM is unavailable."""
    risk_factors = []
    if profile.daily_study_hours < 2:
        risk_factors.append("Low daily study hours — consider increasing to at least 3-4 hours.")
    if len(weak_topics) > 3:
        risk_factors.append(f"{len(weak_topics)} weak topics detected — prioritize these.")
    if profile.study_streak < 3:
        risk_factors.append("Build consistency — aim for at least a 7-day study streak.")

    return {
        "readiness_level": "high" if len(weak_topics) == 0 else "medium" if len(weak_topics) < 3 else "low",
        "daily_hours_recommendation": max(profile.daily_study_hours, 3.0),
        "focus_areas": weak_topics[:5] if weak_topics else (profile.weak_topics or [])[:5],
        "strategy_recommendations": [
            f"Focus on your {len(weak_topics)} weak topics first.",
            "Take practice quizzes after each study session.",
            "Use spaced repetition for revision.",
        ],
        "risk_factors": risk_factors,
        "motivational_note": "Consistent effort leads to great results. Keep going!",
    }
