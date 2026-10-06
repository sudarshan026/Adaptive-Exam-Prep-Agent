"""Agent #5 — Content Tutor.

Provides AI explanations, answers questions, and chats with the student.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI tutor helping a student prepare for an exam. 
Provide clear, accurate, and concise explanations. Format your responses using markdown. 
If the user's question is unclear, ask for clarification. Encourage the student and make learning engaging."""


async def explain_concept(state: AgentState) -> dict:
    """LangGraph node: Explain a topic or answer a question."""
    input_data = state.get("input_data", {})
    message = input_data.get("message", "")
    topic_name = input_data.get("topic_name", "")
    history = input_data.get("conversation_history", [])
    mode = input_data.get("mode", "chat") # 'chat' or 'explain'
    preference = input_data.get("preference", "balanced")
    
    if mode == "explain":
        prompt = f"""Explain the topic '{topic_name}' for a student whose learning 
preference is '{preference}'.

Provide a clear, engaging, and well-structured explanation using markdown. Include examples.
End your explanation with 3 suggested follow-up questions the student might want to ask."""
    else:
        # Chat mode
        prompt = "Here is the conversation history:\n"
        for h in history:
            prompt += f"{h['role'].upper()}: {h['content']}\n\n"
            
        prompt += f"USER: {message}\n"
        if topic_name:
            prompt += f"(Context: We are discussing '{topic_name}')\n"
        prompt += "\nRespond as the AI tutor. Include 2-3 suggested follow-up questions at the very end in a separate section."

    response_text = await call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    
    if not response_text:
        response_text = f"I'm sorry, I'm currently unable to access my knowledge base to explain {topic_name}. Please check my API connection."
        suggested_questions = []
        is_demo = True
    else:
        is_demo = False
        suggested_questions = _extract_questions(response_text)

    return {
        "result": {
            "content": response_text,
            "suggested_questions": suggested_questions,
            "is_demo_mode": is_demo
        },
        "agents_called": state.get("agents_called", []) + ["content_tutor"],
    }


def _extract_questions(text: str) -> list[str]:
    """Extract suggested questions from the LLM response text."""
    questions = []
    lines = text.split('\n')
    
    extracting = False
    for line in lines:
        line = line.strip()
        if "suggested" in line.lower() and "question" in line.lower():
            extracting = True
            continue
            
        if extracting and line.startswith(('1.', '2.', '3.', '-', '*')):
            q = line.lstrip('1234567890.-* \t')
            if q:
                questions.append(q)
                
    return questions[:3]
