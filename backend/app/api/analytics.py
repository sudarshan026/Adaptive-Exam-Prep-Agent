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


@router.get("/predicted-score")
async def get_predicted_score(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Predict exam score based on mastery data and assessment history."""
    # Get profile
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete onboarding first")

    # Get all mastery data
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id)
    )
    mastery_list = result.scalars().all()

    # Get assessment history
    result = await db.execute(
        select(Assessment).where(
            Assessment.user_id == user_id, Assessment.status == "completed"
        ).order_by(Assessment.completed_at.desc()).limit(20)
    )
    assessments = result.scalars().all()

    # Get topic count
    result = await db.execute(
        select(func.count(Topic.id)).where(Topic.user_id == user_id)
    )
    total_topics = result.scalar() or 1

    # Calculate predicted score using weighted factors
    # Factor 1: Average mastery score (40% weight)
    if mastery_list:
        avg_mastery = sum(m.mastery_score for m in mastery_list) / len(mastery_list)
        coverage = len(mastery_list) / max(total_topics, 1)
    else:
        avg_mastery = 0
        coverage = 0

    # Factor 2: Recent assessment accuracy trend (30% weight)
    if assessments:
        recent_accuracies = [a.accuracy for a in assessments[:5] if a.accuracy is not None]
        avg_recent_accuracy = sum(recent_accuracies) / len(recent_accuracies) if recent_accuracies else 0
    else:
        avg_recent_accuracy = 0

    # Factor 3: Coverage and consistency (20% weight)
    coverage_score = coverage * 100

    # Factor 4: Study consistency / streak bonus (10% weight)
    streak_bonus = min(profile.study_streak * 2, 20)  # Max 20 points from streak

    # Weighted prediction
    predicted = (
        avg_mastery * 0.40 +
        avg_recent_accuracy * 0.30 +
        coverage_score * 0.20 +
        streak_bonus * 0.10
    )
    predicted = round(max(0, min(100, predicted)), 1)

    # Confidence level
    data_points = len(mastery_list) + len(assessments)
    if data_points >= 20:
        confidence = "high"
    elif data_points >= 8:
        confidence = "medium"
    else:
        confidence = "low"

    # Trend (improving, stable, declining)
    trend = "stable"
    if len(assessments) >= 3:
        recent_avg = sum(a.accuracy for a in assessments[:3] if a.accuracy) / 3
        older_avg = sum(a.accuracy for a in assessments[3:6] if a.accuracy) / max(1, min(3, len(assessments[3:6])))
        if recent_avg > older_avg + 5:
            trend = "improving"
        elif recent_avg < older_avg - 5:
            trend = "declining"

    # Breakdown by component
    breakdown = {
        "mastery_component": round(avg_mastery * 0.40, 1),
        "assessment_component": round(avg_recent_accuracy * 0.30, 1),
        "coverage_component": round(coverage_score * 0.20, 1),
        "consistency_component": round(streak_bonus * 0.10, 1),
    }

    return {
        "predicted_score": predicted,
        "confidence": confidence,
        "trend": trend,
        "breakdown": breakdown,
        "factors": {
            "avg_mastery": round(avg_mastery, 1),
            "avg_recent_accuracy": round(avg_recent_accuracy, 1),
            "topic_coverage": round(coverage * 100, 1),
            "study_streak": profile.study_streak,
            "total_study_hours": round(profile.total_study_hours, 1),
            "assessments_completed": len(assessments),
            "topics_assessed": len(mastery_list),
            "total_topics": total_topics,
        },
    }


@router.get("/knowledge-graph")
async def get_knowledge_graph(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get topic dependency graph data for visualization."""
    from app.models.syllabus import TopicDependency

    # Get subjects
    result = await db.execute(
        select(Subject).where(Subject.user_id == user_id).order_by(Subject.order_index)
    )
    subjects = result.scalars().all()

    # Get topics with mastery
    result = await db.execute(
        select(Topic).where(Topic.user_id == user_id).order_by(Topic.order_index)
    )
    topics = result.scalars().all()

    # Get mastery data
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id)
    )
    mastery_map = {m.topic_id: m for m in result.scalars().all()}

    # Get dependencies
    topic_ids = [t.id for t in topics]
    edges = []
    if topic_ids:
        result = await db.execute(
            select(TopicDependency).where(TopicDependency.topic_id.in_(topic_ids))
        )
        edges = [
            {"from": d.depends_on_topic_id, "to": d.topic_id}
            for d in result.scalars().all()
        ]

    # Build nodes
    subject_map = {s.id: s for s in subjects}
    nodes = []
    for t in topics:
        mastery = mastery_map.get(t.id)
        subj = subject_map.get(t.subject_id)
        nodes.append({
            "id": t.id,
            "label": t.name,
            "subject": subj.name if subj else "Unknown",
            "subject_id": t.subject_id,
            "color": subj.color if subj else "#6366f1",
            "difficulty": t.difficulty,
            "mastery_score": mastery.mastery_score if mastery else 0,
            "confidence": mastery.confidence_level if mastery else "unknown",
            "is_completed": bool(t.is_completed),
        })

    # Build subject groups
    groups = [
        {"id": s.id, "label": s.name, "color": s.color}
        for s in subjects
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "groups": groups,
        "total_topics": len(nodes),
        "total_edges": len(edges),
    }


@router.post("/deep-weakness-analysis")
async def deep_weakness_analysis(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Run the Weakness Detection Agent for deep LLM-driven analysis."""
    # Get profile
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete onboarding first")

    # Get mastery data
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id)
    )
    mastery_data = [
        {
            "topic_name": m.topic_name,
            "subject_name": m.subject_name,
            "mastery_score": m.mastery_score,
            "total_attempted": m.total_questions_attempted,
            "correct": m.correct_answers,
            "confidence_level": m.confidence_level,
        }
        for m in result.scalars().all()
    ]

    # Get assessment history
    result = await db.execute(
        select(Assessment).where(
            Assessment.user_id == user_id, Assessment.status == "completed"
        ).order_by(Assessment.completed_at.desc()).limit(10)
    )
    assessment_history = [
        {"title": a.title, "accuracy": a.accuracy, "topic_name": a.topic_name}
        for a in result.scalars().all()
    ]

    # Invoke weakness detector agent
    analysis = await invoke_agent(
        task="detect_weaknesses",
        user_id=user_id,
        db=db,
        input_data={
            "mastery_data": mastery_data,
            "assessment_history": assessment_history,
            "exam_type": profile.exam_type,
            "total_study_hours": profile.total_study_hours,
        }
    )

    return analysis


@router.post("/adaptive-strategy")
async def get_adaptive_strategy(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Run the Adaptive Planner Agent for LLM-driven plan modifications."""
    # Get profile
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete onboarding first")

    # Get mastery data for weak/strong topics
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id)
    )
    all_mastery = result.scalars().all()
    weak_topics = [m.topic_name for m in all_mastery if m.mastery_score < 50 and m.total_questions_attempted >= 3]
    strong_topics = [m.topic_name for m in all_mastery if m.mastery_score >= 70]

    # Recent accuracy
    from app.models.assessment import StudentResponse as SR
    result = await db.execute(
        select(func.count(SR.id), func.sum(SR.is_correct)).where(SR.user_id == user_id)
    )
    row = result.one()
    total = row[0] or 0
    correct = int(row[1] or 0)
    recent_accuracy = (correct / total * 100) if total > 0 else 0

    days_remaining = None
    if profile.exam_date:
        days_remaining = max(0, (profile.exam_date - date.today()).days)

    # Invoke adaptive planner agent
    strategy = await invoke_agent(
        task="adapt_plan",
        user_id=user_id,
        db=db,
        input_data={
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
            "days_remaining": days_remaining or 90,
            "daily_hours": profile.daily_study_hours,
            "recent_accuracy": recent_accuracy,
            "study_streak": profile.study_streak,
        }
    )

    return strategy


@router.post("/discover-resources")
async def discover_resources(
    topic_name: str = "General",
    subject_name: str = "",
    difficulty: str = "medium",
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Run the Resource Discovery Agent to find learning resources for a topic."""
    result = await invoke_agent(
        task="discover_resources",
        user_id=user_id,
        db=db,
        input_data={
            "topic_name": topic_name,
            "subject_name": subject_name,
            "difficulty": difficulty,
            "num_resources": 6,
        }
    )

    resources = result.get("resources", [])

    # Optionally save discovered resources to DB
    from app.models.syllabus import LearningResource, Topic as TopicModel
    topic_result = await db.execute(
        select(TopicModel).where(TopicModel.user_id == user_id, TopicModel.name == topic_name)
    )
    topic = topic_result.scalar_one_or_none()

    saved = []
    for r in resources:
        lr = LearningResource(
            user_id=user_id,
            topic_id=topic.id if topic else None,
            title=r.get("title", "Resource"),
            url=r.get("url", ""),
            resource_type=r.get("resource_type", "article"),
            description=r.get("description", ""),
        )
        db.add(lr)
        saved.append(lr)

    await db.flush()

    return {
        "resources": resources,
        "saved_count": len(saved),
        "topic_name": topic_name,
    }


@router.post("/study-strategy")
async def get_study_strategy(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Run the Study Planner Agent for LLM-enhanced study strategy."""
    # Get profile
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete onboarding first")

    # Get topics
    result = await db.execute(
        select(Topic).join(Subject).where(Subject.user_id == user_id)
    )
    topics = [t.name for t in result.scalars().all()]

    # Get mastery
    result = await db.execute(
        select(TopicMastery).where(TopicMastery.user_id == user_id)
    )
    mastery_data = [
        {"topic": m.topic_name, "score": m.mastery_score}
        for m in result.scalars().all()
    ]

    weak_topics = [m["topic"] for m in mastery_data if m["score"] < 50]
    strong_topics = [m["topic"] for m in mastery_data if m["score"] >= 70]

    days_remaining = 90
    if profile.exam_date:
        days_remaining = max(1, (profile.exam_date - date.today()).days)

    strategy = await invoke_agent(
        task="plan_study",
        user_id=user_id,
        db=db,
        input_data={
            "topics": topics,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
            "days_remaining": days_remaining,
            "daily_hours": profile.daily_study_hours,
            "exam_type": profile.exam_type,
            "mastery_data": mastery_data,
        }
    )

    return strategy
