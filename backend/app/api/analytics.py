"""Analytics, weakness detection, adaptive replanning, and coaching endpoints."""
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.base import get_db
from app.models.student import StudentProfile
from app.models.syllabus import Subject, Topic
from app.models.study import StudyPlan, StudySession, StudyLog
from app.models.assessment import Assessment, Question, StudentResponse
from app.models.analytics import TopicMastery, CoachingInsight
from app.schemas.analytics import (
    TopicMasteryResponse, PerformanceAnalytics, WeaknessReport,
    CoachingInsightResponse,
)
from app.core.security import get_current_user_id
from app.services.mastery_calculator import is_weak_topic, calculate_priority_score
from app.agents import invoke_agent

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/performance", response_model=PerformanceAnalytics)
async def get_performance(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive performance analytics."""
    # Profile
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete onboarding first")
    
    # Overall stats
    result = await db.execute(
        select(
            func.count(StudentResponse.id),
            func.sum(StudentResponse.is_correct),
        ).where(StudentResponse.user_id == user_id)
    )
    row = result.one()
    total_attempted = row[0] or 0
    total_correct = int(row[1] or 0)
    overall_accuracy = (total_correct / total_attempted * 100) if total_attempted > 0 else 0
    
    # Assessment count
    result = await db.execute(
        select(func.count(Assessment.id)).where(
            Assessment.user_id == user_id, Assessment.status == "completed"
        )
    )
    total_assessments = result.scalar() or 0
    
    # Topic mastery
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id).order_by(TopicMastery.mastery_score.desc())
    )
    mastery_list = [TopicMasteryResponse.model_validate(m) for m in result.scalars().all()]
    
    # Strong/weak topics
    strong_topics = [m.topic_name for m in mastery_list if m.mastery_score >= 70 and m.topic_name]
    weak_topics = [m.topic_name for m in mastery_list if m.mastery_score < 50 and m.total_questions_attempted >= 3 and m.topic_name]
    
    # Assessment history
    result = await db.execute(
        select(Assessment).where(
            Assessment.user_id == user_id, Assessment.status == "completed"
        ).order_by(Assessment.completed_at.desc()).limit(20)
    )
    assessment_history = [
        {"id": a.id, "title": a.title, "score": a.score, "accuracy": a.accuracy,
         "topic_name": a.topic_name, "completed_at": str(a.completed_at),
         "total_questions": a.total_questions}
        for a in result.scalars().all()
    ]
    
    # Study hours by day (last 30 days)
    today = date.today()
    study_by_day = []
    for i in range(30):
        d = today - timedelta(days=i)
        result = await db.execute(
            select(func.sum(StudyLog.duration_minutes)).where(
                StudyLog.user_id == user_id,
                func.date(StudyLog.logged_at) == d,
            )
        )
        mins = result.scalar() or 0
        study_by_day.append({"date": str(d), "hours": round(mins / 60.0, 1)})
    study_by_day.reverse()
    
    # Improvement trend (accuracy over time by assessment)
    improvement = []
    for ah in reversed(assessment_history):
        improvement.append({
            "date": ah["completed_at"],
            "accuracy": ah["accuracy"],
            "title": ah["title"],
        })
    
    return PerformanceAnalytics(
        overall_accuracy=round(overall_accuracy, 1),
        total_assessments=total_assessments,
        total_questions_attempted=total_attempted,
        total_correct=total_correct,
        study_hours_total=round(profile.total_study_hours, 1),
        study_streak=profile.study_streak,
        topic_mastery=mastery_list,
        assessment_history=assessment_history,
        study_hours_by_day=study_by_day,
        strong_topics=strong_topics,
        weak_topics=weak_topics,
        improvement_trend=improvement,
    )


@router.get("/weakness-report", response_model=WeaknessReport)
async def get_weakness_report(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Analyze assessment history and identify weak topics."""
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id)
    )
    all_mastery = result.scalars().all()
    
    weak = []
    insufficient = []
    recommendations = []
    
    for m in all_mastery:
        if m.total_questions_attempted < 3:
            insufficient.append(m.topic_name or f"Topic #{m.topic_id}")
            continue
        
        if is_weak_topic(m.mastery_score, m.total_questions_attempted):
            weak.append({
                "topic_name": m.topic_name,
                "subject_name": m.subject_name,
                "mastery_score": m.mastery_score,
                "total_attempted": m.total_questions_attempted,
                "correct": m.correct_answers,
                "accuracy": round(m.correct_answers / m.total_questions_attempted * 100, 1),
                "confidence_level": m.confidence_level,
            })
    
    # Generate recommendations
    if weak:
        weak.sort(key=lambda x: x["mastery_score"])
        for w in weak[:5]:
            recommendations.append(
                f"Focus on {w['topic_name']} (mastery: {w['mastery_score']:.0f}%). "
                f"Consider reviewing fundamentals and practicing more questions."
            )
    
    if not weak and not insufficient:
        recommendations.append("Great progress! All assessed topics show good mastery.")
    
    return WeaknessReport(
        weak_topics=weak,
        recommendations=recommendations,
        insufficient_data_topics=insufficient,
    )


@router.post("/adapt-plan")
async def adapt_study_plan(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Trigger adaptive replanning based on latest assessment results."""
    # Get profile
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
    # Get active plan
    result = await db.execute(
        select(StudyPlan).where(StudyPlan.user_id == user_id, StudyPlan.is_active == 1)
    )
    old_plan = result.scalar_one_or_none()
    if not old_plan:
        raise HTTPException(status_code=400, detail="No active study plan to adapt")
    
    # Get weak topics
    result = await db.execute(
        select(TopicMastery).where(
            TopicMastery.user_id == user_id,
            TopicMastery.mastery_score < 50,
            TopicMastery.total_questions_attempted >= 3,
        ).order_by(TopicMastery.mastery_score)
    )
    weak_mastery = result.scalars().all()
    
    if not weak_mastery:
        return {"message": "No weak topics detected. Plan remains unchanged.", "adapted": False}
    
    today = date.today()
    exam_date = profile.exam_date or (today + timedelta(days=90))
    daily_minutes = int(profile.daily_study_hours * 60)
    
    # Get existing future sessions
    result = await db.execute(
        select(StudySession).where(
            StudySession.plan_id == old_plan.id,
            StudySession.scheduled_date > today,
            StudySession.status == "pending",
        ).order_by(StudySession.scheduled_date)
    )
    future_sessions = result.scalars().all()
    
    # Deactivate old plan
    old_plan.is_active = 0
    
    # Create new plan version
    result = await db.execute(
        select(func.max(StudyPlan.version)).where(StudyPlan.user_id == user_id)
    )
    max_version = result.scalar() or 0
    
    change_reasons = [f"Weak topic detected: {m.topic_name} (mastery: {m.mastery_score:.0f}%)" for m in weak_mastery[:5]]
    
    new_plan = StudyPlan(
        user_id=user_id,
        version=max_version + 1,
        is_active=1,
        change_reason="Adaptive replanning: " + "; ".join(change_reasons),
    )
    db.add(new_plan)
    await db.flush()
    
    # Copy completed sessions from old plan
    result = await db.execute(
        select(StudySession).where(
            StudySession.plan_id == old_plan.id,
            StudySession.status == "completed",
        )
    )
    for completed in result.scalars().all():
        copy = StudySession(
            plan_id=new_plan.id,
            user_id=user_id,
            topic_id=completed.topic_id,
            subject_name=completed.subject_name,
            topic_name=completed.topic_name,
            session_type=completed.session_type,
            scheduled_date=completed.scheduled_date,
            estimated_duration_minutes=completed.estimated_duration_minutes,
            actual_duration_minutes=completed.actual_duration_minutes,
            priority=completed.priority,
            status="completed",
            completed_at=completed.completed_at,
            order_in_day=completed.order_in_day,
        )
        db.add(copy)
    
    # Add revision/practice sessions for weak topics at the front
    next_date = today + timedelta(days=1)
    added_sessions = []
    
    for wm in weak_mastery:
        if next_date > exam_date:
            break
        
        # Add extra revision session
        revision = StudySession(
            plan_id=new_plan.id,
            user_id=user_id,
            topic_id=wm.topic_id,
            subject_name=wm.subject_name,
            topic_name=wm.topic_name,
            session_type="revision",
            scheduled_date=next_date,
            estimated_duration_minutes=45,
            priority="critical",
            order_in_day=0,
        )
        db.add(revision)
        added_sessions.append(revision)
        
        # Add extra practice session
        practice = StudySession(
            plan_id=new_plan.id,
            user_id=user_id,
            topic_id=wm.topic_id,
            subject_name=wm.subject_name,
            topic_name=wm.topic_name,
            session_type="practice",
            scheduled_date=next_date,
            estimated_duration_minutes=30,
            priority="high",
            order_in_day=1,
        )
        db.add(practice)
        added_sessions.append(practice)
        
        next_date += timedelta(days=1)
    
    # Re-add remaining future sessions from old plan
    for fs in future_sessions:
        # Skip if we already added a session for the same topic today
        existing_topic_dates = {(s.topic_id, s.scheduled_date) for s in added_sessions}
        if (fs.topic_id, fs.scheduled_date) in existing_topic_dates:
            continue
        
        new_session = StudySession(
            plan_id=new_plan.id,
            user_id=user_id,
            topic_id=fs.topic_id,
            subject_name=fs.subject_name,
            topic_name=fs.topic_name,
            session_type=fs.session_type,
            scheduled_date=fs.scheduled_date,
            estimated_duration_minutes=fs.estimated_duration_minutes,
            priority=fs.priority,
            order_in_day=fs.order_in_day,
        )
        db.add(new_session)
    
    await db.flush()
    
    return {
        "message": f"Study plan adapted. Added {len(added_sessions)} revision/practice sessions for weak topics.",
        "adapted": True,
        "new_plan_version": new_plan.version,
        "changes": change_reasons,
        "weak_topics_addressed": [m.topic_name for m in weak_mastery],
    }


@router.get("/coaching", response_model=list[CoachingInsightResponse])
async def get_coaching_insights(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get coaching insights and motivational messages."""
    # Get profile and stats
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete onboarding first")
    
    # Get weak topics
    result = await db.execute(
        select(TopicMastery).where(
            TopicMastery.user_id == user_id,
            TopicMastery.mastery_score < 50,
            TopicMastery.total_questions_attempted >= 3,
        )
    )
    weak = [m.topic_name for m in result.scalars().all() if m.topic_name]
    
    # Overall accuracy
    from app.models.assessment import StudentResponse as SR
    result = await db.execute(
        select(func.count(SR.id), func.sum(SR.is_correct)).where(SR.user_id == user_id)
    )
    row = result.one()
    total = row[0] or 0
    correct = int(row[1] or 0)
    accuracy = (correct / total * 100) if total > 0 else 0
    
    days_remaining = None
    if profile.exam_date:
        days_remaining = max(0, (profile.exam_date - date.today()).days)
    
    # Generate coaching message
    stats = {
        "streak": profile.study_streak,
        "total_hours": profile.total_study_hours,
        "accuracy": accuracy,
        "weak_topics": weak,
        "days_remaining": days_remaining,
    }
    result = await invoke_agent(
        task="provide_coaching",
        user_id=user_id,
        db=db,
        input_data={"stats": stats}
    )
    coaching_msg = result.get("coaching_message", "Keep up the great work!")

    
    # Save insight
    insight = CoachingInsight(
        user_id=user_id,
        insight_type="encouragement",
        title="Daily Coaching",
        message=coaching_msg,
        data=stats,
    )
    db.add(insight)
    await db.flush()
    
    # Get recent insights
    result = await db.execute(
        select(CoachingInsight).where(CoachingInsight.user_id == user_id)
        .order_by(CoachingInsight.created_at.desc()).limit(10)
    )
    return [CoachingInsightResponse.model_validate(c) for c in result.scalars().all()]


@router.get("/mastery", response_model=list[TopicMasteryResponse])
async def get_mastery(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all topic mastery data."""
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id)
        .order_by(TopicMastery.mastery_score.desc())
    )
    return [TopicMasteryResponse.model_validate(m) for m in result.scalars().all()]
