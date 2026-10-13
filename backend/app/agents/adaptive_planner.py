"""Agent #9 — Adaptive Planner.

Modifies study plans dynamically based on weak areas and progress,
using LLM to generate intelligent adaptation strategies.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert adaptive learning strategist. Your role is to 
dynamically modify study plans based on a student's evolving performance. Analyze 
what's working, what isn't, and recommend specific schedule changes. Consider 
cognitive load, motivation, and exam proximity in your recommendations."""


async def adapt_plan(state: AgentState) -> dict:
    """LangGraph node: Generate adaptive plan modifications using LLM."""
    input_data = state.get("input_data", {})
    weak_topics = input_data.get("weak_topics", [])
    strong_topics = input_data.get("strong_topics", [])
    current_plan_summary = input_data.get("current_plan_summary", "")
    days_remaining = input_data.get("days_remaining", 90)
    daily_hours = input_data.get("daily_hours", 4)
    recent_accuracy = input_data.get("recent_accuracy", 0)
    study_streak = input_data.get("study_streak", 0)

    prompt = f"""Analyze this student's progress and recommend study plan adaptations:

Days Until Exam: {days_remaining}
Daily Study Hours: {daily_hours}
Recent Accuracy: {recent_accuracy:.1f}%
Study Streak: {study_streak} days
Weak Topics: {', '.join(weak_topics) if weak_topics else 'None detected'}
Strong Topics: {', '.join(strong_topics) if strong_topics else 'None yet'}
Current Plan Summary: {current_plan_summary or 'Standard study schedule'}

Provide a JSON response in this exact format:
{{
  "adaptations": {{
    "urgency": "high",
    "summary": "Brief summary of recommended changes",
    "schedule_changes": [
      {{
        "change_type": "increase_time",
        "topic": "Topic name",
        "reason": "Why this change is needed",
        "recommended_hours_per_week": 3
      }}
    ],
    "topics_to_deprioritize": ["Topics the student has mastered and can reduce time on"],
    "topics_to_prioritize": ["Topics needing more focus"],
    "new_revision_targets": ["Topics due for spaced revision"],
    "study_method_changes": [
      {{
        "current_method": "Current approach",
        "suggested_method": "Better approach to try",
        "reason": "Why this might work better"
      }}
    ],
    "motivation_note": "Encouraging message about the adaptations",
    "risk_assessment": "Assessment of exam readiness with current trajectory"
  }}
}}"""

    response = await call_llm(prompt, system_prompt=SYSTEM_PROMPT, json_mode=True)

    adaptations = {}
    if response:
        try:
            from app.services.llm_service import extract_json
            adaptations = extract_json(response)
        except Exception as e:
            logger.error("Failed to parse adaptive planner response: %s", e)

    if not adaptations:
        urgency = "high" if days_remaining < 30 else "medium" if days_remaining < 60 else "low"
        adaptations = {
            "adaptations": {
                "urgency": urgency,
                "summary": f"{'Urgent: ' if urgency == 'high' else ''}Focus more time on weak topics.",
                "schedule_changes": [
                    {
                        "change_type": "increase_time",
                        "topic": w,
                        "reason": f"Low mastery in {w} needs more dedicated practice.",
                        "recommended_hours_per_week": 3,
                    }
                    for w in weak_topics[:3]
                ],
                "topics_to_deprioritize": strong_topics[:3],
                "topics_to_prioritize": weak_topics[:5],
                "new_revision_targets": [],
                "study_method_changes": [],
                "motivation_note": "Every adjustment gets you closer to your goal!",
                "risk_assessment": f"With {days_remaining} days remaining, consistent effort will pay off.",
            }
        }

    return {
        "result": adaptations,
        "agents_called": state.get("agents_called", []) + ["adaptive_planner"],
    }
