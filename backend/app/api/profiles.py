"""Student profile API endpoints."""
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.base import get_db
from app.models.student import StudentProfile
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.core.security import get_current_user_id

router = APIRouter(prefix="/api/profile", tags=["Student Profile"])


def _add_days_remaining(profile: StudentProfile) -> ProfileResponse:
    """Convert model to response with computed days_remaining."""
    resp = ProfileResponse.model_validate(profile)
    if profile.exam_date:
        delta = profile.exam_date - date.today()
        resp.days_remaining = max(0, delta.days)
    return resp


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: ProfileCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create student profile (onboarding)."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")
    
    profile = StudentProfile(
        user_id=user_id,
        exam_type=data.exam_type,
        target_score=data.target_score,
        current_level=data.current_level,
        exam_date=data.exam_date,
        daily_study_hours=data.daily_study_hours,
        learning_preference=data.learning_preference,
        strong_topics=data.strong_topics,
        weak_topics=data.weak_topics,
        onboarding_completed=1,
    )
    db.add(profile)
    await db.flush()
    return _add_days_remaining(profile)


@router.get("/", response_model=ProfileResponse)
async def get_profile(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current student's profile."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Complete onboarding first.")
    return _add_days_remaining(profile)


@router.put("/", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update student profile."""
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    
    profile.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return _add_days_remaining(profile)
