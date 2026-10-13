"""Agent #3 — Resource Discovery.

Finds relevant learning resources (videos, articles, books, notes, question banks)
for a given topic using LLM recommendations and optional YouTube search.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert educational resource curator. Given a topic and subject, 
recommend high-quality, freely available learning resources. Include a mix of resource types:
videos, articles, online notes, textbooks, and practice question banks.
For each resource, provide a title, URL (use real, well-known educational URLs like Khan Academy, 
MIT OCW, GeeksforGeeks, W3Schools, Coursera, etc.), resource type, and a brief description."""


async def discover_resources(state: AgentState) -> dict:
    """LangGraph node: Discover learning resources for a topic."""
    input_data = state.get("input_data", {})
    topic_name = input_data.get("topic_name", "General")
    subject_name = input_data.get("subject_name", "")
    difficulty = input_data.get("difficulty", "medium")
    num_resources = input_data.get("num_resources", 6)

    prompt = f"""Find {num_resources} high-quality learning resources for:
Topic: {topic_name}
Subject: {subject_name}
Student Level: {difficulty}

Provide a JSON response in this exact format:
{{
  "resources": [
    {{
      "title": "Resource Title",
      "url": "https://example.com/resource",
      "resource_type": "video",
      "description": "Brief description of what this resource covers",
      "difficulty": "medium",
      "estimated_time_minutes": 30
    }}
  ]
}}

Resource types must be one of: video, article, book, notes, question_bank, course
Include a good mix of resource types. Use real, well-known educational website URLs."""

    response = await call_llm(prompt, system_prompt=SYSTEM_PROMPT, json_mode=True)

    resources = []
    if response:
        try:
            from app.services.llm_service import extract_json
            parsed = extract_json(response)
            resources = parsed.get("resources", [])
        except Exception as e:
            logger.error("Failed to parse resource discovery response: %s", e)

    if not resources:
        # Fallback resources
        resources = [
            {
                "title": f"{topic_name} - Khan Academy",
                "url": "https://www.khanacademy.org",
                "resource_type": "video",
                "description": f"Comprehensive video lessons on {topic_name}",
                "difficulty": difficulty,
                "estimated_time_minutes": 30,
            },
            {
                "title": f"{topic_name} - Wikipedia Overview",
                "url": "https://en.wikipedia.org",
                "resource_type": "article",
                "description": f"Detailed encyclopedia article on {topic_name}",
                "difficulty": "medium",
                "estimated_time_minutes": 15,
            },
        ]

    return {
        "result": {"resources": resources},
        "agents_called": state.get("agents_called", []) + ["resource_discovery"],
    }
