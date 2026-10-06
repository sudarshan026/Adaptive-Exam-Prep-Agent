"""Agent #10 — Coaching Advisor.

Generates motivational messages, daily strategies, and coaching insights
based on recent performance and study stats.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an empathetic, encouraging, and highly effective academic coach. 
Your goal is to motivate the student, provide practical study advice, and help them 
stay on track for their exam. Keep messages concise (2-4 sentences)."""


async def provide_coaching(state: AgentState) -> dict:
    """LangGraph node: Generate coaching insights."""
    input_data = state.get("input_data", {})
    stats = input_data.get("stats", {})
    
    streak = stats.get("streak", 0)
    total_hours = stats.get("total_hours", 0)
    accuracy = stats.get("accuracy", 0)
    weak_topics = stats.get("weak_topics", [])
    days_remaining = stats.get("days_remaining")
    
    prompt = f"""Generate a personalized, motivating daily coaching message for a student.

Current Stats:
- Study Streak: {streak} days
- Total Hours: {total_hours}
- Overall Accuracy: {accuracy:.1f}%
- Weak Topics: {', '.join(weak_topics[:3]) if weak_topics else 'None identified yet'}
- Days until exam: {days_remaining if days_remaining is not None else 'Unknown'}

Provide practical advice mixed with encouragement. Don't be overly cheesy. Do not use markdown headers."""

    response = await call_llm(prompt, system_prompt=SYSTEM_PROMPT, json_mode=False)
    
    if not response:
        # Fallback
        if streak >= 3:
            response = f"Great job maintaining a {streak}-day study streak! Keep up the momentum. "
        else:
            response = "Consistency is key. Try to study a little bit every day. "
            
        if weak_topics:
            response += f"Today, consider reviewing {weak_topics[0]} to strengthen your weak areas."
        else:
            response += "Focus on understanding concepts deeply rather than memorizing."

    return {
        "result": {"coaching_message": response},
        "agents_called": state.get("agents_called", []) + ["coaching_advisor"],
    }
