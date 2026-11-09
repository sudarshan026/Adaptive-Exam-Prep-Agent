"""Shared state definition for the multi-agent system.

Each agent reads/writes fields in this state dict.
The orchestrator routes tasks to specialist agents based on the 'task' field.
"""
from typing import TypedDict, Any, Optional
from typing_extensions import Required


class AgentState(TypedDict, total=False):
    """Shared state passed between all agents in the LangGraph workflow."""

    # ─── Routing ───────────────────────────────────────────────
    task: Required[str]          # Task identifier, e.g. "generate_questions"
    user_id: Required[int]       # Authenticated user ID

    # ─── Database ──────────────────────────────────────────────
    db: Any                      # AsyncSession — not serializable but we don't checkpoint

    # ─── Input ─────────────────────────────────────────────────
    input_data: dict             # Task-specific input payload

    # ─── Output ────────────────────────────────────────────────
    result: dict                 # Final result returned to the caller
    error: Optional[str]         # Error message if something went wrong

    # ─── Agent Tracking ───────────────────────────────────────
    agents_called: list[str]     # Which agents have executed
    next_agent: Optional[str]    # Next agent to call (for chaining)

    # ─── Advanced Agent Coordination ──────────────────────────
    retrieved_chunks: list[dict] # RAG retrieved knowledge chunks with citations
    parallel_outputs: dict       # Aggregated outputs from concurrent fan-out agents
    review_feedback: Optional[dict] # Reviewer critique in planner-reviewer loop
    iteration_count: int         # Reflection loop iteration counter
    is_approved: bool            # Verification approval status


def make_state(
    task: str,
    user_id: int,
    db: Any,
    input_data: dict | None = None,
) -> AgentState:
    """Helper to create an initial AgentState dict."""
    return AgentState(
        task=task,
        user_id=user_id,
        db=db,
        input_data=input_data or {},
        result={},
        error=None,
        agents_called=[],
        next_agent=None,
    )
