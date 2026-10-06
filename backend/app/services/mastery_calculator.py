"""Mastery calculation service — deterministic scoring logic."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import math

# Configurable thresholds
MASTERY_THRESHOLDS = {
    "high": 80.0,       # >= 80% mastery = high confidence
    "medium": 50.0,     # >= 50% mastery = medium confidence
    "low": 0.0,         # < 50% = low confidence
    "weak_threshold": 50.0,  # Topics below this are considered weak
    "min_attempts": 3,  # Minimum attempts before confident assessment
}

# Spaced repetition intervals (days)
REVISION_INTERVALS = [1, 3, 7, 14, 30, 60]

# Forgetting curve decay rate (heuristic)
DECAY_RATE = 0.1  # 10% decay per interval period


def calculate_mastery(
    current_mastery: float,
    correct: int,
    total: int,
    weight_recent: float = 0.6,
) -> float:
    """
    Calculate updated mastery score using weighted average of 
    current mastery and recent performance.
    
    Formula: new_mastery = (1 - weight_recent) * current_mastery + weight_recent * recent_accuracy
    
    This gives more weight to recent performance while preserving history.
    """
    if total == 0:
        return current_mastery
    
    recent_accuracy = (correct / total) * 100.0
    new_mastery = (1 - weight_recent) * current_mastery + weight_recent * recent_accuracy
    return round(max(0.0, min(100.0, new_mastery)), 1)


def get_confidence_level(mastery_score: float, total_attempts: int) -> str:
    """Determine confidence level based on mastery and evidence."""
    if total_attempts < MASTERY_THRESHOLDS["min_attempts"]:
        return "unknown"
    if mastery_score >= MASTERY_THRESHOLDS["high"]:
        return "high"
    elif mastery_score >= MASTERY_THRESHOLDS["medium"]:
        return "medium"
    else:
        return "low"


def is_weak_topic(mastery_score: float, total_attempts: int) -> bool:
    """
    Determine if a topic is weak.
    Only marks as weak if there's sufficient evidence (min attempts).
    """
    if total_attempts < MASTERY_THRESHOLDS["min_attempts"]:
        return False  # Insufficient data — don't mark as weak
    return mastery_score < MASTERY_THRESHOLDS["weak_threshold"]


def calculate_next_revision(
    current_interval_index: int,
    was_correct: bool,
    mastery_score: float,
) -> tuple[int, int]:
    """
    Calculate next revision date using spaced repetition.
    Returns (interval_days, new_interval_index).
    
    If performance is good, move to next interval.
    If poor, reset to shorter interval.
    """
    if was_correct and mastery_score >= 70:
        # Move to next interval
        new_index = min(current_interval_index + 1, len(REVISION_INTERVALS) - 1)
    elif was_correct:
        # Stay at same interval
        new_index = current_interval_index
    else:
        # Reset to earlier interval
        new_index = max(0, current_interval_index - 1)
    
    return REVISION_INTERVALS[new_index], new_index


def apply_forgetting_decay(
    mastery_score: float,
    last_reviewed: Optional[datetime],
    interval_days: int = 7,
) -> float:
    """
    Apply forgetting-curve-based decay heuristic.
    
    This is a simplified exponential decay model:
    decayed = mastery * e^(-decay_rate * periods_elapsed)
    
    NOTE: This is a heuristic, not a scientifically validated model.
    Assessment results always override this estimate.
    """
    if not last_reviewed:
        return mastery_score
    
    now = datetime.now(timezone.utc)
    days_elapsed = (now - last_reviewed).days
    
    if days_elapsed <= 0:
        return mastery_score
    
    periods_elapsed = days_elapsed / max(interval_days, 1)
    decay_factor = math.exp(-DECAY_RATE * periods_elapsed)
    decayed = mastery_score * decay_factor
    
    return round(max(0.0, decayed), 1)


def calculate_priority_score(
    mastery_score: float,
    difficulty: str,
    is_weak: bool,
    days_since_last_study: int = 0,
    exam_weightage: float = 1.0,
) -> float:
    """
    Calculate a priority score for scheduling.
    Higher score = higher priority for study.
    """
    score = 0.0
    
    # Low mastery = high priority
    score += (100 - mastery_score) * 0.4
    
    # Weak topics get a boost
    if is_weak:
        score += 25
    
    # Difficulty adjustment
    diff_bonus = {"easy": 0, "medium": 5, "hard": 15}
    score += diff_bonus.get(difficulty, 5)
    
    # Time since last study
    if days_since_last_study > 7:
        score += min(20, days_since_last_study * 1.5)
    
    # Exam weightage
    score *= exam_weightage
    
    return round(score, 1)
