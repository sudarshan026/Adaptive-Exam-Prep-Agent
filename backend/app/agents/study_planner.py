"""Agent #4 — Study Planner.

Uses LLM to generate intelligent, personalized study strategies and
enhanced scheduling recommendations beyond algorithmic planning.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert academic study planner and learning strategist. 
Your role is to create optimized, personalized study schedules that account for:
- The student's strengths and weaknesses
- Spaced repetition principles
- Cognitive load management
- Time available before the exam
- Topic difficulty and dependencies
Provide practical, actionable study strategies."""


async def plan_study(state: AgentState) -> dict:
    """LangGraph node: Generate intelligent study plan recommendations."""
    input_data = state.get("input_data", {})
    topics = input_data.get("topics", [])
    weak_topics = input_data.get("weak_topics", [])
    strong_topics = input_data.get("strong_topics", [])
    days_remaining = input_data.get("days_remaining", 90)
    daily_hours = input_data.get("daily_hours", 4)
    exam_type = input_data.get("exam_type", "General")
    mastery_data = input_data.get("mastery_data", [])

    topics_summary = ", ".join(t[:50] for t in topics[:20]) if topics else "Not specified"
    weak_summary = ", ".join(w[:50] for w in weak_topics[:10]) if weak_topics else "None identified"
    strong_summary = ", ".join(s[:50] for s in strong_topics[:10]) if strong_topics else "None identified"
    mastery_summary = "; ".join(
        f"{m.get('topic', 'Unknown')}: {m.get('score', 0):.0f}%"
        for m in mastery_data[:15]
    ) if mastery_data else "No mastery data yet"

    prompt = f"""Create a personalized study strategy for this student:

Exam Type: {exam_type}
Days Remaining: {days_remaining}
Daily Study Hours Available: {daily_hours}
Topics: {topics_summary}
Weak Topics: {weak_summary}
Strong Topics: {strong_summary}
Current Mastery: {mastery_summary}

Provide a JSON response in this exact format:
{{
  "strategy": {{
    "overall_approach": "Brief description of the recommended study approach",
    "phase_plan": [
      {{
        "phase_name": "Phase 1: Foundation",
        "duration_days": 14,
        "focus_areas": ["topic1", "topic2"],
        "daily_breakdown": "2hrs theory + 1hr practice + 1hr revision",
        "tips": "Specific tips for this phase"
      }}
    ],
    "daily_schedule_template": {{
      "morning": "Focus on difficult/weak topics when energy is high",
      "afternoon": "Practice questions and problem-solving",
      "evening": "Revision of morning topics + light reading"
    }},
    "priority_topics": ["List of topics to prioritize"],
    "revision_strategy": "How to handle revisions",
    "exam_week_plan": "Special strategy for the final week"
  }}
}}"""

    response = await call_llm(prompt, system_prompt=SYSTEM_PROMPT, json_mode=True)

    strategy = {}
    if response:
        try:
            from app.services.llm_service import extract_json
            strategy = extract_json(response)
        except Exception as e:
            logger.error("Failed to parse study planner response: %s", e)

    if not strategy:
        strategy = {
            "strategy": {
                "overall_approach": f"Focus on weak topics first, with {daily_hours}hrs/day for {days_remaining} days.",
                "phase_plan": [
                    {
                        "phase_name": "Phase 1: Address Weaknesses",
                        "duration_days": min(days_remaining // 3, 30),
                        "focus_areas": weak_topics[:5] if weak_topics else ["Core fundamentals"],
                        "daily_breakdown": f"{daily_hours}hrs: 50% learning + 30% practice + 20% revision",
                        "tips": "Start with basics and build up gradually.",
                    }
                ],
                "priority_topics": weak_topics[:5] if weak_topics else [],
                "revision_strategy": "Use spaced repetition: review after 1, 3, 7, and 14 days.",
                "exam_week_plan": "Focus on revision and mock tests only.",
            }
        }

    return {
        "result": strategy,
        "agents_called": state.get("agents_called", []) + ["study_planner"],
    }
