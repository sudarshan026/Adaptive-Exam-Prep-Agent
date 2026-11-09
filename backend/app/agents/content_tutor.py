"""Agent #5 — Content Tutor with RAG (Retrieval-Augmented Generation).

Provides AI explanations, answers questions, and chats with the student.
Leverages RAG to retrieve relevant syllabus and course material chunks,
grounding explanations directly in the student's curriculum with citations.
"""
import logging
from app.agents.state import AgentState
from app.services.llm_service import call_llm
from app.services.rag_service import rag_index

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI tutor helping a student prepare for an exam. 
Provide clear, accurate, and concise explanations. Format your responses using markdown. 
If curriculum context is provided, ground your explanation in that curriculum and reference it.
If the user's question is unclear, ask for clarification. Encourage the student and make learning engaging."""


async def explain_concept(state: AgentState) -> dict:
    """LangGraph node: Explain a topic or answer a question with RAG grounding."""
    input_data = state.get("input_data", {})
    message = input_data.get("message", "")
    topic_name = input_data.get("topic_name", "")
    history = input_data.get("conversation_history", [])
    mode = input_data.get("mode", "chat") # 'chat' or 'explain'
    preference = input_data.get("preference", "balanced")
    user_id = state.get("user_id", 0)

    # -------------------------------------------------------------
    # RAG Retrieval Stage
    # -------------------------------------------------------------
    search_query = topic_name or message
    retrieved_chunks = rag_index.retrieve(query=search_query, user_id=user_id, top_k=3)
    rag_context = rag_index.format_context_for_prompt(retrieved_chunks)
    source_citations = [c.citation for c in retrieved_chunks]
    
    if mode == "explain":
        prompt = f"""Explain the topic '{topic_name}' for a student whose learning 
preference is '{preference}'.

Provide a clear, engaging, and well-structured explanation using markdown. Include examples."""
        if rag_context:
            prompt += f"\n\n{rag_context}\n"
        prompt += "\nEnd your explanation with 3 suggested follow-up questions the student might want to ask."
    else:
        # Chat mode
        prompt = "Here is the conversation history:\n"
        for h in history:
            prompt += f"{h['role'].upper()}: {h['content']}\n\n"
            
        prompt += f"USER: {message}\n"
        if topic_name:
            prompt += f"(Context: We are discussing '{topic_name}')\n"
        if rag_context:
            prompt += f"\n{rag_context}\n"
        prompt += "\nRespond as the AI tutor. Include 2-3 suggested follow-up questions at the very end in a separate section."

    response_text = await call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    
    if not response_text:
        is_demo = True
        if retrieved_chunks:
            top_excerpt = retrieved_chunks[0].text.strip()
            response_text = f"**{topic_name or 'Concept'} Overview**\n\nBased on your curriculum:\n> {top_excerpt}\n\n*Key takeaway:* Focus on understanding the core definitions and problem-solving steps for this topic."
        else:
            response_text = f"**{topic_name or 'Concept'} Overview**\n\nThis core exam topic covers fundamental principles, standard problem variations, and efficient solution techniques. Practice foundational problems to build intuition."
        suggested_questions = [
            f"What are common exam questions for {topic_name or 'this topic'}?",
            f"Can you provide a practice problem on {topic_name or 'this topic'}?",
            "How does this relate to other syllabus units?"
        ]
    else:
        is_demo = False
        suggested_questions = _extract_questions(response_text)

    # If RAG sources were used, append source citations
    if source_citations:
        response_text += f"\n\n*📚 Grounded in Syllabus: {', '.join(set(source_citations))}*"

    return {
        "result": {
            "content": response_text,
            "suggested_questions": suggested_questions,
            "is_demo_mode": is_demo,
            "rag_sources": source_citations,
            "chunks_retrieved_count": len(retrieved_chunks),
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
