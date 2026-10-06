"""Assessment and question generation endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.base import get_db
from app.models.assessment import Question, Assessment, AssessmentQuestion, StudentResponse
from app.models.analytics import TopicMastery
from app.schemas.assessment import (
    QuestionResponse, QuestionWithAnswer, AssessmentCreate, AssessmentResponse,
    AssessmentSubmission, AssessmentResult, GenerateQuestionsRequest,
)
from app.core.security import get_current_user_id
from app.agents import invoke_agent
from app.services.mastery_calculator import calculate_mastery, get_confidence_level, calculate_next_revision

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.post("/generate-questions", response_model=list[QuestionResponse])
async def generate_questions(
    req: GenerateQuestionsRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate practice questions for a topic."""
    topic_name = req.topic_name or "General"
    subject_name = req.subject_name or ""
    
    result = await invoke_agent(
        task="generate_questions",
        user_id=user_id,
        db=db,
        input_data={
            "topic_name": topic_name,
            "subject_name": subject_name,
            "difficulty": req.difficulty,
            "num_questions": req.num_questions,
            "question_type": req.question_type,
        }
    )
    questions_data = result.get("questions", [])
    
    saved_questions = []
    for qd in questions_data:
        q = Question(
            user_id=user_id,
            topic_id=req.topic_id,
            subject_name=subject_name,
            topic_name=topic_name,
            question_text=qd.get("question_text", ""),
            question_type=qd.get("question_type", "mcq"),
            difficulty=qd.get("difficulty", req.difficulty),
            options=qd.get("options"),
            correct_answer=qd.get("correct_answer", ""),
            explanation=qd.get("explanation"),
            tags=qd.get("tags", []),
        )
        db.add(q)
        saved_questions.append(q)
    
    await db.flush()
    return [QuestionResponse.model_validate(q) for q in saved_questions]


@router.post("/create", response_model=AssessmentResponse)
async def create_assessment(
    req: AssessmentCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new assessment (quiz/test) and generate questions."""
    topic_name = req.topic_name or "Mixed Topics"
    subject_name = req.subject_name or ""
    title = req.title or f"{req.assessment_type.replace('_', ' ').title()}: {topic_name}"
    
    # Generate questions
    result = await invoke_agent(
        task="generate_questions",
        user_id=user_id,
        db=db,
        input_data={
            "topic_name": topic_name,
            "subject_name": subject_name,
            "difficulty": req.difficulty,
            "num_questions": req.num_questions,
            "question_type": "mcq",
        }
    )
    questions_data = result.get("questions", [])
    
    # Save questions
    question_objects = []
    for qd in questions_data:
        q = Question(
            user_id=user_id,
            topic_id=req.topic_id,
            subject_name=subject_name,
            topic_name=topic_name,
            question_text=qd.get("question_text", ""),
            question_type=qd.get("question_type", "mcq"),
            difficulty=qd.get("difficulty", req.difficulty),
            options=qd.get("options"),
            correct_answer=qd.get("correct_answer", ""),
            explanation=qd.get("explanation"),
        )
        db.add(q)
        question_objects.append(q)
    
    await db.flush()
    
    # Create assessment
    assessment = Assessment(
        user_id=user_id,
        title=title,
        assessment_type=req.assessment_type,
        subject_name=subject_name,
        topic_name=topic_name,
        topic_id=req.topic_id,
        total_questions=len(question_objects),
        total_marks=float(len(question_objects)),
        time_limit_minutes=req.time_limit_minutes,
        status="created",
    )
    db.add(assessment)
    await db.flush()
    
    # Link questions to assessment
    for i, q in enumerate(question_objects):
        aq = AssessmentQuestion(
            assessment_id=assessment.id,
            question_id=q.id,
            order_index=i,
            marks=1.0,
        )
        db.add(aq)
    
    await db.flush()
    return AssessmentResponse.model_validate(assessment)


@router.get("/{assessment_id}/questions", response_model=list[QuestionResponse])
async def get_assessment_questions(
    assessment_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get questions for an assessment (without answers for active tests)."""
    # Verify ownership
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id, Assessment.user_id == user_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    # Mark as in_progress if just created
    if assessment.status == "created":
        assessment.status = "in_progress"
        assessment.started_at = datetime.now(timezone.utc)
    
    # Get linked questions
    result = await db.execute(
        select(Question).join(AssessmentQuestion).where(
            AssessmentQuestion.assessment_id == assessment_id
        ).order_by(AssessmentQuestion.order_index)
    )
    questions = result.scalars().all()
    return [QuestionResponse.model_validate(q) for q in questions]


@router.post("/{assessment_id}/submit", response_model=AssessmentResult)
async def submit_assessment(
    assessment_id: int,
    submission: AssessmentSubmission,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit answers and get scored results."""
    # Get assessment
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id, Assessment.user_id == user_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status == "completed":
        raise HTTPException(status_code=400, detail="Assessment already submitted")
    
    # Get questions with answers
    result = await db.execute(
        select(Question).join(AssessmentQuestion).where(
            AssessmentQuestion.assessment_id == assessment_id
        )
    )
    questions = {q.id: q for q in result.scalars().all()}
    
    # Score answers
    total_correct = 0
    total_answered = 0
    responses_data = []
    topic_scores = {}  # topic_name -> {correct, total}
    
    for answer in submission.answers:
        question = questions.get(answer.question_id)
        if not question:
            continue
        
        is_correct = answer.selected_answer.strip().lower() == question.correct_answer.strip().lower()
        if is_correct:
            total_correct += 1
        total_answered += 1
        
        # Track by topic
        tname = question.topic_name or "General"
        if tname not in topic_scores:
            topic_scores[tname] = {"correct": 0, "total": 0, "topic_id": question.topic_id}
        topic_scores[tname]["total"] += 1
        if is_correct:
            topic_scores[tname]["correct"] += 1
        
        # Save response
        resp = StudentResponse(
            assessment_id=assessment_id,
            question_id=answer.question_id,
            user_id=user_id,
            selected_answer=answer.selected_answer,
            is_correct=1 if is_correct else 0,
            marks_obtained=1.0 if is_correct else 0.0,
        )
        db.add(resp)
        responses_data.append({
            "question_id": answer.question_id,
            "selected_answer": answer.selected_answer,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
        })
    
    # Update assessment
    score = float(total_correct)
    accuracy = (total_correct / total_answered * 100) if total_answered > 0 else 0
    assessment.score = score
    assessment.accuracy = round(accuracy, 1)
    assessment.status = "completed"
    assessment.completed_at = datetime.now(timezone.utc)
    assessment.time_taken_minutes = submission.time_taken_minutes
    
    # Update topic mastery
    weak_topics = []
    topic_breakdown = []
    for tname, tdata in topic_scores.items():
        topic_breakdown.append({
            "topic_name": tname,
            "correct": tdata["correct"],
            "total": tdata["total"],
            "accuracy": round(tdata["correct"] / tdata["total"] * 100, 1) if tdata["total"] > 0 else 0,
        })
        
        # Update or create mastery record
        topic_id = tdata.get("topic_id")
        if topic_id:
            result = await db.execute(
                select(TopicMastery).where(
                    TopicMastery.user_id == user_id,
                    TopicMastery.topic_id == topic_id,
                )
            )
            mastery = result.scalar_one_or_none()
            if not mastery:
                mastery = TopicMastery(
                    user_id=user_id,
                    topic_id=topic_id,
                    subject_name=assessment.subject_name,
                    topic_name=tname,
                )
                db.add(mastery)
            
            # Update mastery score
            mastery.total_questions_attempted += tdata["total"]
            mastery.correct_answers += tdata["correct"]
            mastery.mastery_score = calculate_mastery(
                mastery.mastery_score, tdata["correct"], tdata["total"]
            )
            mastery.confidence_level = get_confidence_level(
                mastery.mastery_score, mastery.total_questions_attempted
            )
            mastery.last_assessed_at = datetime.now(timezone.utc)
            
            # Update spaced repetition
            was_correct = tdata["correct"] / tdata["total"] >= 0.7
            interval_days, _ = calculate_next_revision(
                mastery.revision_interval_days - 1 if mastery.revision_interval_days > 1 else 0,
                was_correct, mastery.mastery_score
            )
            mastery.revision_interval_days = interval_days
            mastery.next_revision_date = datetime.now(timezone.utc) + __import__('datetime').timedelta(days=interval_days)
            
            if mastery.mastery_score < 50 and mastery.total_questions_attempted >= 3:
                weak_topics.append(tname)
    
    await db.flush()
    
    # Build result
    questions_with_answers = [QuestionWithAnswer.model_validate(q) for q in questions.values()]
    
    return AssessmentResult(
        assessment=AssessmentResponse.model_validate(assessment),
        questions=questions_with_answers,
        responses=responses_data,
        topic_breakdown=topic_breakdown,
        weak_topics_identified=weak_topics,
    )


@router.get("/", response_model=list[AssessmentResponse])
async def list_assessments(
    status_filter: str = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all assessments for the current user."""
    query = select(Assessment).where(Assessment.user_id == user_id)
    if status_filter:
        query = query.where(Assessment.status == status_filter)
    query = query.order_by(Assessment.created_at.desc())
    result = await db.execute(query)
    return [AssessmentResponse.model_validate(a) for a in result.scalars().all()]


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Assessment).where(Assessment.id == assessment_id, Assessment.user_id == user_id)
    )
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse.model_validate(assessment)
