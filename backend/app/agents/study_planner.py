"""Agent #4 — Study Planner with Planner-Reviewer Reflection & Critique Loop.

Uses a dual-agent pattern:
1. Planner Node: Generates an intelligent, personalized study schedule.
2. Reviewer Node: Evaluates the plan against pedagogical rubrics (cognitive load,
   weak topic coverage, active recall ratio). Loops back with critique if needed.
"""
import logging
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.services.llm_service import call_llm, extract_json

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are an expert academic study planner and learning strategist. 
Your role is to create optimized, personalized study schedules that account for:
- The student's strengths and weaknesses
- Spaced repetition principles
- Cognitive load management
- Time available before the exam
- Topic difficulty and dependencies
Provide practical, actionable study strategies. If previous reviewer critique is provided, you MUST address all points."""

REVIEWER_SYSTEM_PROMPT = """You are a rigorous Academic Curriculum Reviewer and QA Critic.
Your role is to critically evaluate study strategies to ensure:
1. Weak topics are explicitly prioritized in early phases.
2. Cognitive load is balanced and respects the student's daily study hours.
3. Active practice and spaced repetition constitute at least 35% of daily breakdown.
4. The strategy is realistic for the days remaining.
Output your evaluation strictly in valid JSON format."""


async def plan_study(state: AgentState) -> dict:
    """Planner Node: Generates or refines intelligent study plan recommendations."""
    input_data = state.get("input_data", {})
    topics = input_data.get("topics", [])
    weak_topics = input_data.get("weak_topics", [])
    strong_topics = input_data.get("strong_topics", [])
    days_remaining = input_data.get("days_remaining", 90)
    daily_hours = input_data.get("daily_hours", 4)
    exam_type = input_data.get("exam_type", "General")
    mastery_data = input_data.get("mastery_data", [])
    
    # Check for reviewer critique from previous loop iteration
    prior_critique = state.get("review_feedback")
    iteration = state.get("iteration_count", 1)

    topics_summary = ", ".join(t[:50] for t in topics[:20]) if topics else "Not specified"
    weak_summary = ", ".join(w[:50] for w in weak_topics[:10]) if weak_topics else "None identified"
    strong_summary = ", ".join(s[:50] for s in strong_topics[:10]) if strong_topics else "None identified"
    mastery_summary = "; ".join(
        f"{m.get('topic', 'Unknown')}: {m.get('score', 0):.0f}%"
        for m in mastery_data[:15]
    ) if mastery_data else "No mastery data yet"

    critique_prompt = ""
    if prior_critique and not prior_critique.get("is_approved", True):
        critique_prompt = f"""
PREVIOUS REVIEWER CRITIQUE (Iteration {iteration - 1}):
Quality Score: {prior_critique.get('score', 0)}/100
Deficiencies: {'; '.join(prior_critique.get('deficiencies', []))}
Required Adjustments: {'; '.join(prior_critique.get('improvement_directives', []))}
Please revise the study plan to directly address every deficiency above!
"""

    prompt = f"""Create a personalized study strategy for this student:

Exam Type: {exam_type}
Days Remaining: {days_remaining}
Daily Study Hours Available: {daily_hours}
Topics: {topics_summary}
Weak Topics: {weak_summary}
Strong Topics: {strong_summary}
Current Mastery: {mastery_summary}
Iteration: {iteration}
{critique_prompt}

Provide a JSON response in this exact format:
{{
  "strategy": {{
    "overall_approach": "Brief description of the recommended study approach",
    "phase_plan": [
      {{
        "phase_name": "Phase 1: Addressing Core Weaknesses",
        "duration_days": 14,
        "focus_areas": ["topic1", "topic2"],
        "daily_breakdown": "2hrs theory + 1hr practice + 1hr revision",
        "tips": "Specific tips for this phase"
      }}
    ],
    "daily_schedule_template": {{
      "morning": "Focus on difficult/weak topics when energy is high",
      "afternoon": "Practice questions and problem-solving",
      "evening": "Revision of morning topics + spaced retrieval"
    }},
    "priority_topics": ["List of topics to prioritize"],
    "revision_strategy": "How to handle revisions",
    "exam_week_plan": "Special strategy for the final week"
  }}
}}"""

    response = await call_llm(prompt, system_prompt=PLANNER_SYSTEM_PROMPT, json_mode=True)

    strategy = {}
    if response:
        try:
            strategy = extract_json(response)
        except Exception as e:
            logger.error("Failed to parse study planner response: %s", e)

    if not strategy:
        strategy = {
            "strategy": {
                "overall_approach": f"Prioritize high-yield weak areas first with {daily_hours}hrs/day over {days_remaining} days.",
                "phase_plan": [
                    {
                        "phase_name": "Phase 1: Remediation of Weak Topics",
                        "duration_days": min(days_remaining // 3, 30),
                        "focus_areas": weak_topics[:5] if weak_topics else ["Core foundational concepts"],
                        "daily_breakdown": f"{daily_hours}hrs: 40% concept acquisition + 40% active practice + 20% spaced revision",
                        "tips": "Focus on active recall and error analysis rather than passive reading.",
                    },
                    {
                        "phase_name": "Phase 2: Comprehensive Mastery & Synthesis",
                        "duration_days": min(days_remaining // 3, 30),
                        "focus_areas": [t for t in topics[:5] if t not in weak_topics],
                        "daily_breakdown": f"{daily_hours}hrs: 30% theory + 50% problem solving + 20% review",
                        "tips": "Solve timed sectionals and interleave related topics.",
                    }
                ],
                "priority_topics": weak_topics[:5] if weak_topics else (topics[:5] if topics else []),
                "revision_strategy": "Spaced repetition intervals: Day 1, Day 3, Day 7, Day 14.",
                "exam_week_plan": "High-yield formula review, error log audit, and timed mock exams.",
            }
        }

    return {
        "result": strategy,
        "agents_called": state.get("agents_called", []) + [f"study_planner_v{iteration}"],
    }


async def review_study_plan(state: AgentState) -> dict:
    """Reviewer / Critic Node: Audits the study plan and triggers revision loop if needed."""
    current_result = state.get("result", {})
    strategy = current_result.get("strategy", {})
    input_data = state.get("input_data", {})
    weak_topics = input_data.get("weak_topics", [])
    daily_hours = input_data.get("daily_hours", 4)
    days_remaining = input_data.get("days_remaining", 90)
    iteration = state.get("iteration_count", 1)

    prompt = f"""Critique the following study plan:
Study Strategy: {strategy}
Student Weak Topics: {weak_topics}
Available Daily Hours: {daily_hours}
Days to Exam: {days_remaining}

Evaluate against:
1. Are weak topics properly prioritized in Phase 1?
2. Is the daily hours breakdown realistic and <= {daily_hours} hours?
3. Is active recall/practice >= 35% of the time allocation?
4. Is spaced repetition included?

Output strictly JSON:
{{
  "is_approved": true/false (true if score >= 80),
  "score": 85.0,
  "deficiencies": ["list of issues if any"],
  "improvement_directives": ["specific actionable improvements"]
}}"""

    response = await call_llm(prompt, system_prompt=REVIEWER_SYSTEM_PROMPT, json_mode=True)
    critique = {}
    if response:
        try:
            critique = extract_json(response)
        except Exception as e:
            logger.warning("Failed to parse study reviewer critique: %s", e)

    # Deterministic fallback evaluation if LLM is unavailable
    if not critique:
        score = 85.0
        deficiencies = []
        directives = []
        
        # Check if weak topics are mentioned in priority
        priority_topics = strategy.get("priority_topics", [])
        if weak_topics and not any(w in priority_topics for w in weak_topics):
            score -= 15.0
            deficiencies.append("Priority topics list does not highlight student's identified weak areas.")
            directives.append("Elevate identified weak topics to the top of Phase 1 and priority list.")

        critique = {
            "is_approved": score >= 80.0,
            "score": score,
            "deficiencies": deficiencies,
            "improvement_directives": directives,
        }

    is_approved = critique.get("is_approved", True) or iteration >= 2

    # Attach critique and approval metadata to the final result
    current_result["peer_review"] = {
        "status": "APPROVED" if is_approved else "REVISED",
        "score": critique.get("score", 85.0),
        "iteration": iteration,
        "deficiencies_resolved": critique.get("deficiencies", []),
    }

    return {
        "result": current_result,
        "review_feedback": critique,
        "is_approved": is_approved,
        "iteration_count": iteration + 1,
        "agents_called": state.get("agents_called", []) + [f"plan_reviewer_v{iteration}"],
    }
