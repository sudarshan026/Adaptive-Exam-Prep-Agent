"""AI Tutor chat endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.base import get_db
from app.models.analytics import TutorConversation
from app.schemas.analytics import TutorMessage, TutorResponse, ConversationResponse
from app.core.security import get_current_user_id
from app.agents import invoke_agent

router = APIRouter(prefix="/api/tutor", tags=["AI Tutor"])


@router.post("/chat", response_model=TutorResponse)
async def chat(
    msg: TutorMessage,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the AI tutor."""
    topic_name = msg.topic_name or ""
    
    # Get conversation history for context
    result = await db.execute(
        select(TutorConversation).where(
            TutorConversation.user_id == user_id
        ).order_by(TutorConversation.created_at.desc()).limit(10)
    )
    history = [
        {"role": c.role, "content": c.content}
        for c in reversed(list(result.scalars().all()))
    ]
    
    # Save user message
    user_msg = TutorConversation(
        user_id=user_id,
        topic_id=msg.topic_id,
        topic_name=topic_name,
        role="user",
        content=msg.content,
    )
    db.add(user_msg)
    
    # Get AI response
    response = await invoke_agent(
        task="explain_concept",
        user_id=user_id,
        db=db,
        input_data={
            "mode": "chat",
            "message": msg.content,
            "topic_name": topic_name,
            "conversation_history": history,
        }
    )
    
    # Save assistant message
    assistant_msg = TutorConversation(
        user_id=user_id,
        topic_id=msg.topic_id,
        topic_name=topic_name,
        role="assistant",
        content=response["content"],
    )
    db.add(assistant_msg)
    await db.flush()
    
    return TutorResponse(
        role="assistant",
        content=response["content"],
        topic_name=topic_name,
        suggested_questions=response.get("suggested_questions", []),
        is_demo_mode=response.get("is_demo_mode", False),
    )


@router.post("/explain", response_model=TutorResponse)
async def explain(
    msg: TutorMessage,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a concept explanation for a topic."""
    from app.models.student import StudentProfile
    
    # Get learning preference
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    preference = profile.learning_preference if profile else "balanced"
    
    topic_name = msg.topic_name or msg.content
    response = await invoke_agent(
        task="explain_concept",
        user_id=user_id,
        db=db,
        input_data={
            "mode": "explain",
            "topic_name": topic_name,
            "preference": preference,
        }
    )
    
    # Save to conversation
    db.add(TutorConversation(
        user_id=user_id, topic_id=msg.topic_id, topic_name=topic_name,
        role="user", content=f"Explain: {topic_name}",
    ))
    db.add(TutorConversation(
        user_id=user_id, topic_id=msg.topic_id, topic_name=topic_name,
        role="assistant", content=response["content"],
    ))
    await db.flush()
    
    return TutorResponse(
        role="assistant",
        content=response["content"],
        topic_name=topic_name,
        suggested_questions=response.get("suggested_questions", []),
        is_demo_mode=response.get("is_demo_mode", False),
    )


@router.get("/history", response_model=list[ConversationResponse])
async def get_history(
    topic_id: int = None,
    limit: int = 50,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get conversation history."""
    query = select(TutorConversation).where(TutorConversation.user_id == user_id)
    if topic_id:
        query = query.where(TutorConversation.topic_id == topic_id)
    query = query.order_by(TutorConversation.created_at.desc()).limit(limit)
    result = await db.execute(query)
    conversations = list(reversed(list(result.scalars().all())))
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.delete("/history")
async def clear_history(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Clear conversation history."""
    from sqlalchemy import delete
    await db.execute(
        delete(TutorConversation).where(TutorConversation.user_id == user_id)
    )
    return {"message": "Conversation history cleared"}
