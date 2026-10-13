"""Agent #8 — Weakness Detection.

Identifies weak areas based on performance data and mastery scores,
provides deep LLM-driven analysis of why topics are weak and how to fix them.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert learning diagnostician. Your role is to analyze 
student performance data, identify underlying reasons for weak areas, detect patterns 
in mistakes, and provide targeted remediation strategies. Look beyond surface-level 
metrics to understand root causes of difficulty."""


async def detect_weaknesses(state: AgentState) -> dict:
    """LangGraph node: Deep weakness analysis with LLM insights."""
    input_data = state.get("input_data", {})
    mastery_data = input_data.get("mastery_data", [])
    assessment_history = input_data.get("assessment_history", [])
    exam_type = input_data.get("exam_type", "General")
    total_study_hours = input_data.get("total_study_hours", 0)

    mastery_text = "\n".join(
        f"  - {m.get('topic_name', 'Unknown')}: mastery={m.get('mastery_score', 0):.0f}%, "
        f"attempted={m.get('total_attempted', 0)}, correct={m.get('correct', 0)}, "
        f"confidence={m.get('confidence_level', 'unknown')}"
        for m in mastery_data
    ) if mastery_data else "  No mastery data available"

    history_text = "\n".join(
        f"  - {h.get('title', 'Test')}: {h.get('accuracy', 0):.0f}% accuracy, "
        f"topic={h.get('topic_name', 'Mixed')}"
        for h in assessment_history[:10]
    ) if assessment_history else "  No assessment history"

    prompt = f"""Perform a deep weakness analysis for this student:

Exam Type: {exam_type}
Total Study Hours: {total_study_hours:.1f}

Topic Mastery Scores:
{mastery_text}

Recent Assessment History:
{history_text}

Provide a JSON response in this exact format:
{{
  "weakness_analysis": {{
    "critical_weaknesses": [
      {{
        "topic": "Topic name",
        "severity": "critical",
        "root_cause": "Why this topic is weak (e.g., foundational gaps, insufficient practice)",
        "remediation": "Specific steps to improve",
        "estimated_recovery_hours": 5
      }}
    ],
    "moderate_weaknesses": [
      {{
        "topic": "Topic name", 
        "severity": "moderate",
        "root_cause": "Analysis of why",
        "remediation": "Steps to improve",
        "estimated_recovery_hours": 3
      }}
    ],
    "patterns_detected": ["List of patterns in the student's weaknesses"],
    "prerequisite_gaps": ["Topics where foundational knowledge may be missing"],
    "overall_diagnosis": "2-3 sentence summary of the student's weakness profile",
    "priority_action_plan": "What the student should do immediately"
  }}
}}"""

    response = await call_llm(prompt, system_prompt=SYSTEM_PROMPT, json_mode=True)

    analysis = {}
    if response:
        try:
            from app.services.llm_service import extract_json
            analysis = extract_json(response)
        except Exception as e:
            logger.error("Failed to parse weakness detection response: %s", e)

    if not analysis:
        weak_topics = [m for m in mastery_data if m.get("mastery_score", 100) < 50]
        analysis = {
            "weakness_analysis": {
                "critical_weaknesses": [
                    {
                        "topic": w.get("topic_name", "Unknown"),
                        "severity": "critical" if w.get("mastery_score", 0) < 30 else "moderate",
                        "root_cause": "Insufficient practice and review needed.",
                        "remediation": f"Dedicate focused study time to {w.get('topic_name', 'this topic')}.",
                        "estimated_recovery_hours": 5,
                    }
                    for w in weak_topics[:5]
                ],
                "moderate_weaknesses": [],
                "patterns_detected": ["Some topics need more practice attempts."],
                "prerequisite_gaps": [],
                "overall_diagnosis": f"Found {len(weak_topics)} weak topics requiring attention.",
                "priority_action_plan": "Focus on the lowest-scoring topics first.",
            }
        }

    return {
        "result": analysis,
        "agents_called": state.get("agents_called", []) + ["weakness_detector"],
    }
