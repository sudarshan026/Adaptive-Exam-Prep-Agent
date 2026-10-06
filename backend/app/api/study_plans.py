"""Study plan, sessions, and dashboard endpoints."""
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database.base import get_db
from app.models.student import StudentProfile
from app.models.syllabus import Subject, Topic
from app.models.study import StudyPlan, StudySession, StudyLog
from app.models.assessment import Assessment
from app.models.analytics import TopicMastery
from app.schemas.study import (
    StudySessionResponse, StudySessionUpdate, StudyPlanResponse,
    GeneratePlanRequest, DashboardResponse,
)
from app.core.security import get_current_user_id
from app.core.config import settings

router = APIRouter(prefix="/api/study", tags=["Study Plans"])


@router.post("/generate-plan", response_model=StudyPlanResponse)
async def generate_study_plan(
    req: GeneratePlanRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a personalized study plan based on profile and syllabus."""
    # Get profile
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    
    # Get topics
    result = await db.execute(
        select(Topic).join(Subject).where(Subject.user_id == user_id).order_by(Topic.order_index)
    )
    topics = result.scalars().all()
    if not topics:
        raise HTTPException(status_code=400, detail="Add subjects and topics first")
    
    # Get subject names for topics
    subject_map = {}
    result = await db.execute(select(Subject).where(Subject.user_id == user_id))
    for s in result.scalars().all():
        subject_map[s.id] = s.name
    
    # Get existing mastery data
    result = await db.execute(select(TopicMastery).where(TopicMastery.user_id == user_id))
    mastery_map = {m.topic_id: m for m in result.scalars().all()}
    
    # Deactivate old plans
    result = await db.execute(
        select(StudyPlan).where(StudyPlan.user_id == user_id, StudyPlan.is_active == 1)
    )
    for old_plan in result.scalars().all():
        old_plan.is_active = 0
    
    # Calculate plan version
    result = await db.execute(
        select(func.max(StudyPlan.version)).where(StudyPlan.user_id == user_id)
    )
    max_version = result.scalar() or 0
    
    # Create new plan
    plan = StudyPlan(
        user_id=user_id,
        version=max_version + 1,
        is_active=1,
        change_reason="Initial plan generation" if max_version == 0 else "Manual regeneration",
    )
    db.add(plan)
    await db.flush()
    
    # --- Study Planning Algorithm ---
    today = date.today()
    exam_date = profile.exam_date or (today + timedelta(days=90))
    days_remaining = max(1, (exam_date - today).days)
    daily_hours = profile.daily_study_hours or 4.0
    daily_minutes = int(daily_hours * 60)
    
    # Categorize topics by priority
    weak_topic_names = set(profile.weak_topics or [])
    strong_topic_names = set(profile.strong_topics or [])
    
    prioritized = []
    for topic in topics:
        if topic.is_completed:
            continue
        mastery = mastery_map.get(topic.id)
        mastery_score = mastery.mastery_score if mastery else 0
        
        # Priority scoring
        priority_score = 0
        subject_name = subject_map.get(topic.subject_id, "Unknown")
        
        # Weak topics get highest priority
        if topic.name in weak_topic_names or subject_name in weak_topic_names:
            priority_score += 30
        # Strong topics get lower priority
        if topic.name in strong_topic_names or subject_name in strong_topic_names:
            priority_score -= 10
        # Low mastery = higher priority
        priority_score += max(0, (100 - mastery_score)) * 0.3
        # Hard topics need more time
        if topic.difficulty == "hard":
            priority_score += 10
        elif topic.difficulty == "easy":
            priority_score -= 5
        
        prioritized.append({
            "topic": topic,
            "subject_name": subject_name,
            "priority_score": priority_score,
            "mastery": mastery_score,
            "est_minutes": int(topic.estimated_hours * 60),
        })
    
    # Sort by priority (highest first)
    prioritized.sort(key=lambda x: x["priority_score"], reverse=True)
    
    # Distribute across days
    current_date = today + timedelta(days=1)  # Start tomorrow
    day_minutes_used = 0
    order_in_day = 0
    sessions_created = []
    
    for item in prioritized:
        topic = item["topic"]
        est_mins = item["est_minutes"]
        subject_name = item["subject_name"]
        
        # Determine priority label
        if item["priority_score"] >= 25:
            priority = "critical"
        elif item["priority_score"] >= 15:
            priority = "high"
        elif item["priority_score"] >= 5:
            priority = "medium"
        else:
            priority = "low"
        
        # Learning session
        learn_mins = min(est_mins, 60)
        if day_minutes_used + learn_mins > daily_minutes:
            current_date += timedelta(days=1)
            day_minutes_used = 0
            order_in_day = 0
            if current_date > exam_date:
                break
        
        session = StudySession(
            plan_id=plan.id,
            user_id=user_id,
            topic_id=topic.id,
            subject_name=subject_name,
            topic_name=topic.name,
            session_type="learning",
            scheduled_date=current_date,
            estimated_duration_minutes=learn_mins,
            priority=priority,
            order_in_day=order_in_day,
        )
        db.add(session)
        sessions_created.append(session)
        day_minutes_used += learn_mins
        order_in_day += 1
        
        # Practice session (after learning)
        practice_mins = min(30, est_mins // 2)
        if day_minutes_used + practice_mins > daily_minutes:
            current_date += timedelta(days=1)
            day_minutes_used = 0
            order_in_day = 0
            if current_date > exam_date:
                break
        
        practice = StudySession(
            plan_id=plan.id,
            user_id=user_id,
            topic_id=topic.id,
            subject_name=subject_name,
            topic_name=topic.name,
            session_type="practice",
            scheduled_date=current_date,
            estimated_duration_minutes=practice_mins,
            priority=priority,
            order_in_day=order_in_day,
        )
        db.add(practice)
        sessions_created.append(practice)
        day_minutes_used += practice_mins
        order_in_day += 1
        
        # Schedule revision 3 days later
        revision_date = current_date + timedelta(days=3)
        if revision_date <= exam_date:
            revision = StudySession(
                plan_id=plan.id,
                user_id=user_id,
                topic_id=topic.id,
                subject_name=subject_name,
                topic_name=topic.name,
                session_type="revision",
                scheduled_date=revision_date,
                estimated_duration_minutes=20,
                priority="medium",
                order_in_day=0,
            )
            db.add(revision)
            sessions_created.append(revision)
    
    # Add weekly assessment sessions
    assessment_date = today + timedelta(days=7)
    while assessment_date <= exam_date:
        assess = StudySession(
            plan_id=plan.id,
            user_id=user_id,
            topic_id=None,
            subject_name="Mixed",
            topic_name="Weekly Assessment",
            session_type="assessment",
            scheduled_date=assessment_date,
            estimated_duration_minutes=60,
            priority="high",
            order_in_day=0,
        )
        db.add(assess)
        sessions_created.append(assess)
        assessment_date += timedelta(days=7)
    
    await db.flush()
    
    # Build response
    resp = StudyPlanResponse.model_validate(plan)
    resp.sessions = [StudySessionResponse.model_validate(s) for s in sessions_created]
    return resp


@router.get("/plan", response_model=StudyPlanResponse)
async def get_active_plan(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the active study plan with all sessions."""
    result = await db.execute(
        select(StudyPlan).where(StudyPlan.user_id == user_id, StudyPlan.is_active == 1)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="No active study plan. Generate one first.")
    
    result = await db.execute(
        select(StudySession).where(StudySession.plan_id == plan.id).order_by(
            StudySession.scheduled_date, StudySession.order_in_day
        )
    )
    sessions = [StudySessionResponse.model_validate(s) for s in result.scalars().all()]
    resp = StudyPlanResponse.model_validate(plan)
    resp.sessions = sessions
    return resp


@router.get("/sessions", response_model=list[StudySessionResponse])
async def get_sessions(
    date_from: date = None,
    date_to: date = None,
    status_filter: str = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get study sessions with optional date and status filters."""
    query = select(StudySession).where(StudySession.user_id == user_id)
    if date_from:
        query = query.where(StudySession.scheduled_date >= date_from)
    if date_to:
        query = query.where(StudySession.scheduled_date <= date_to)
    if status_filter:
        query = query.where(StudySession.status == status_filter)
    query = query.order_by(StudySession.scheduled_date, StudySession.order_in_day)
    result = await db.execute(query)
    return [StudySessionResponse.model_validate(s) for s in result.scalars().all()]


@router.put("/sessions/{session_id}", response_model=StudySessionResponse)
async def update_session(
    session_id: int,
    data: StudySessionUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a study session (mark complete, reschedule, etc.)."""
    result = await db.execute(
        select(StudySession).where(StudySession.id == session_id, StudySession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    if "status" in update_data and update_data["status"] == "completed":
        session.completed_at = datetime.now(timezone.utc)
        # Log study time
        duration = update_data.get("actual_duration_minutes", session.estimated_duration_minutes)
        log = StudyLog(
            user_id=user_id,
            session_id=session.id,
            topic_id=session.topic_id,
            activity_type=session.session_type,
            duration_minutes=duration,
        )
        db.add(log)
        # Update profile study hours
        profile_result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile:
            profile.total_study_hours += duration / 60.0
    
    for key, value in update_data.items():
        setattr(session, key, value)
    
    await db.flush()
    return StudySessionResponse.model_validate(session)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated dashboard data."""
    from app.models.user import User
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    # Get profile
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete onboarding first")
    
    today = date.today()
    days_remaining = None
    if profile.exam_date:
        days_remaining = max(0, (profile.exam_date - today).days)
    
    # Today's sessions
    result = await db.execute(
        select(StudySession).where(
            StudySession.user_id == user_id,
            StudySession.scheduled_date == today,
        ).order_by(StudySession.order_in_day)
    )
    today_sessions = [StudySessionResponse.model_validate(s) for s in result.scalars().all()]
    
    # Completed hours today
    result = await db.execute(
        select(func.sum(StudyLog.duration_minutes)).where(
            StudyLog.user_id == user_id,
            func.date(StudyLog.logged_at) == today,
        )
    )
    completed_minutes_today = result.scalar() or 0
    
    # Upcoming sessions (next 7 days)
    result = await db.execute(
        select(StudySession).where(
            StudySession.user_id == user_id,
            StudySession.scheduled_date > today,
            StudySession.scheduled_date <= today + timedelta(days=7),
            StudySession.status == "pending",
        ).order_by(StudySession.scheduled_date, StudySession.order_in_day).limit(10)
    )
    upcoming_sessions = [StudySessionResponse.model_validate(s) for s in result.scalars().all()]
    
    # Topics stats
    result = await db.execute(
        select(func.count(Topic.id)).where(Topic.user_id == user_id)
    )
    topics_total = result.scalar() or 0
    result = await db.execute(
        select(func.count(Topic.id)).where(Topic.user_id == user_id, Topic.is_completed == 1)
    )
    topics_completed = result.scalar() or 0
    
    overall_progress = (topics_completed / topics_total * 100) if topics_total > 0 else 0
    
    # Recent assessments
    result = await db.execute(
        select(Assessment).where(
            Assessment.user_id == user_id, Assessment.status == "completed"
        ).order_by(Assessment.completed_at.desc()).limit(5)
    )
    recent_assessments = [
        {"id": a.id, "title": a.title, "score": a.score, "accuracy": a.accuracy,
         "topic_name": a.topic_name, "completed_at": str(a.completed_at)}
        for a in result.scalars().all()
    ]
    
    # Weak topics (mastery < 50%)
    result = await db.execute(
        select(TopicMastery).where(
            TopicMastery.user_id == user_id, TopicMastery.mastery_score < 50
        ).order_by(TopicMastery.mastery_score)
    )
    weak_topics = [
        {"topic_name": m.topic_name, "subject_name": m.subject_name,
         "mastery_score": m.mastery_score, "confidence_level": m.confidence_level}
        for m in result.scalars().all()
    ]
    
    # Mastery summary
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id).order_by(TopicMastery.mastery_score.desc())
    )
    mastery_summary = [
        {"topic_name": m.topic_name, "subject_name": m.subject_name,
         "mastery_score": m.mastery_score, "confidence_level": m.confidence_level}
        for m in result.scalars().all()
    ]
    
    # Calculate study streak
    streak = 0
    check_date = today
    while True:
        result = await db.execute(
            select(func.count(StudyLog.id)).where(
                StudyLog.user_id == user_id,
                func.date(StudyLog.logged_at) == check_date,
            )
        )
        if result.scalar() > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    # Update streak in profile
    if streak != profile.study_streak:
        profile.study_streak = streak
    
    return DashboardResponse(
        welcome_name=user.full_name if user else "Student",
        exam_type=profile.exam_type,
        days_remaining=days_remaining,
        daily_target_hours=profile.daily_study_hours,
        completed_hours_today=round(completed_minutes_today / 60.0, 1),
        study_streak=streak,
        total_study_hours=round(profile.total_study_hours, 1),
        overall_progress=round(overall_progress, 1),
        topics_total=topics_total,
        topics_completed=topics_completed,
        today_sessions=today_sessions,
        upcoming_sessions=upcoming_sessions,
        recent_assessments=recent_assessments,
        weak_topics=weak_topics,
        mastery_summary=mastery_summary,
        is_demo_mode=settings.is_demo_mode,
    )
