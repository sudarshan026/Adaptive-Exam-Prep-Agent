"""Agent #7 — Assessment Agent.

Conducts topic tests, weekly tests, and mock exams with LLM-driven
analysis of student performance and personalized feedback.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert exam assessor and educational analyst. 
Your role is to analyze student test performance deeply, provide detailed feedback 
on each topic, identify patterns in mistakes, and give actionable improvement advice.
Be encouraging but honest about areas needing work."""


async def analyze_assessment(state: AgentState) -> dict:
    """LangGraph node: Analyze assessment results and provide LLM-driven feedback."""
    input_data = state.get("input_data", {})
    assessment_title = input_data.get("title", "Assessment")
    topic_name = input_data.get("topic_name", "General")
    score = input_data.get("score", 0)
    total = input_data.get("total_questions", 0)
    accuracy = input_data.get("accuracy", 0)
    topic_breakdown = input_data.get("topic_breakdown", [])
    weak_topics = input_data.get("weak_topics", [])
    time_taken = input_data.get("time_taken_minutes", 0)

    breakdown_text = "\n".join(
        f"  - {t.get('topic_name', 'Unknown')}: {t.get('correct', 0)}/{t.get('total', 0)} "
        f"({t.get('accuracy', 0):.0f}%)"
        for t in topic_breakdown
    ) if topic_breakdown else "  No breakdown available"

    prompt = f"""Analyze this student's assessment performance and provide detailed feedback:

Assessment: {assessment_title}
Topic: {topic_name}
Score: {score}/{total} ({accuracy:.1f}%)
Time Taken: {time_taken} minutes
Weak Topics Identified: {', '.join(weak_topics) if weak_topics else 'None'}

Topic Breakdown:
{breakdown_text}

Provide a JSON response in this exact format:
{{
  "overall_feedback": "2-3 sentences of overall performance feedback",
  "strength_areas": ["List of topics/areas where student performed well"],
  "improvement_areas": ["List of topics/areas needing improvement"],
  "specific_advice": [
    {{
      "topic": "Topic name",
      "advice": "Specific actionable advice for improving in this topic",
      "priority": "high"
    }}
  ],
  "study_recommendations": "What the student should focus on next",
  "encouragement": "A brief motivational message",
  "estimated_readiness": "A percentage estimate of exam readiness based on this performance"
}}"""

    response = await call_llm(prompt, system_prompt=SYSTEM_PROMPT, json_mode=True)

    analysis = {}
    if response:
        try:
            from app.services.llm_service import extract_json
            analysis = extract_json(response)
        except Exception as e:
            logger.error("Failed to parse assessment analysis: %s", e)

    if not analysis:
        performance = "excellent" if accuracy >= 80 else "good" if accuracy >= 60 else "needs improvement"
        analysis = {
            "overall_feedback": f"You scored {accuracy:.0f}% on {assessment_title}. Your performance is {performance}.",
            "strength_areas": [t.get("topic_name") for t in topic_breakdown if t.get("accuracy", 0) >= 70],
            "improvement_areas": weak_topics,
            "specific_advice": [
                {"topic": w, "advice": f"Review fundamentals of {w} and practice more questions.", "priority": "high"}
                for w in weak_topics
            ],
            "study_recommendations": "Focus on weak topics before moving to new material.",
            "encouragement": "Keep practicing! Every assessment is a learning opportunity.",
            "estimated_readiness": f"{min(accuracy, 95):.0f}%",
        }

    return {
        "result": {"assessment_analysis": analysis},
        "agents_called": state.get("agents_called", []) + ["assessment_agent"],
    }
