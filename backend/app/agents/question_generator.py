"""Agent #6 — Question Generator.

Creates difficulty-calibrated practice questions for a specific topic
using the LLM.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert exam question creator. Generate high-quality, accurate, 
and challenging multiple-choice questions for the requested topic. Ensure the questions test 
conceptual understanding rather than just rote memorization. The difficulty should match the request."""


async def generate_questions(state: AgentState) -> dict:
    """LangGraph node: Generate practice questions."""
    input_data = state.get("input_data", {})
    topic_name = input_data.get("topic_name", "General Knowledge")
    subject_name = input_data.get("subject_name", "General")
    difficulty = input_data.get("difficulty", "medium")
    num_questions = input_data.get("num_questions", 5)
    
    prompt = f"""Generate {num_questions} multiple-choice questions about "{topic_name}" 
(Subject: {subject_name}).
Difficulty level: {difficulty}

Format the output strictly as JSON:
{{
  "questions": [
    {{
      "question_text": "The actual question?",
      "question_type": "mcq",
      "difficulty": "{difficulty}",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "Why A is correct.",
      "tags": ["{topic_name}"]
    }}
  ]
}}"""

    response = await call_llm(prompt, system_prompt=SYSTEM_PROMPT, json_mode=True)
    
    questions_data = []
    if response:
        try:
            from app.services.llm_service import extract_json
            parsed = extract_json(response)
            questions_data = parsed.get("questions", [])
        except Exception as e:
            logger.error("Failed to parse LLM response for questions: %s", e)
    
    if not questions_data:
        # Fallback deterministic questions
        logger.warning("Using fallback questions for %s", topic_name)
        for i in range(num_questions):
            questions_data.append({
                "question_text": f"Fallback Question {i+1} about {topic_name}",
                "question_type": "mcq",
                "difficulty": difficulty,
                "options": ["Option A (Correct)", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A (Correct)",
                "explanation": "This is a placeholder explanation generated because the AI service is unavailable.",
                "tags": [topic_name]
            })

    return {
        "result": {"questions": questions_data},
        "agents_called": state.get("agents_called", []) + ["question_generator"],
    }
