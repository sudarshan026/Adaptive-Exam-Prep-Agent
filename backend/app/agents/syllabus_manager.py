"""Agent #3 — Syllabus Manager.

Parses uploaded syllabus text/PDFs, structures topics, and generates a study outline.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a curriculum and syllabus expert. 
Your task is to parse raw text from a syllabus or exam notification and extract a highly structured 
list of subjects and topics. Organize them logically."""

async def manage_syllabus(state: AgentState) -> dict:
    """LangGraph node: Parse syllabus text into structured subjects and topics."""
    input_data = state.get("input_data", {})
    raw_text = input_data.get("raw_text", "")
    exam_type = input_data.get("exam_type", "General")
    
    if not raw_text:
        return {
            "result": {"error": "No syllabus text provided."},
            "agents_called": state.get("agents_called", []) + ["syllabus_manager"],
        }
        
    prompt = f"""Extract the curriculum structure from this syllabus text for {exam_type}.

Raw Syllabus Text:
{raw_text[:3000]}  # Limit to avoid token overflow

Provide a JSON response in this exact format:
{{
  "subjects": [
    {{
      "name": "Subject Name",
      "description": "Short description",
      "weightage": 1.0,
      "color": "#6366f1",
      "topics": [
        {{
          "name": "Topic Name",
          "description": "Short description",
          "difficulty": "medium",
          "estimated_hours": 2.0
        }}
      ]
    }}
  ]
}}"""

    response = await call_llm(prompt, system_prompt=SYSTEM_PROMPT, json_mode=True)
    
    parsed_syllabus = {}
    if response:
        try:
            from app.services.llm_service import extract_json
            parsed_syllabus = extract_json(response)
        except Exception as e:
            logger.error("Failed to parse LLM response for syllabus: %s", e)
    
    if not parsed_syllabus:
        # Fallback basic structure
        parsed_syllabus = {
            "subjects": [
                {
                    "name": f"{exam_type} Core Fundamentals",
                    "description": "Auto-generated subject based on extraction failure",
                    "weightage": 1.0,
                    "color": "#6366f1",
                    "topics": [
                        {
                            "name": "Topic 1 from syllabus",
                            "description": "Review text to map manually",
                            "difficulty": "medium",
                            "estimated_hours": 2.0
                        }
                    ]
                }
            ]
        }
        
    return {
        "result": {"parsed_syllabus": parsed_syllabus},
        "agents_called": state.get("agents_called", []) + ["syllabus_manager"],
    }
