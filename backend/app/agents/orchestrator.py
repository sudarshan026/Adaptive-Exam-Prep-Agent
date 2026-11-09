"""Orchestrator Agent and LangGraph definition with Parallel Agents & Reflection Loops.

Features:
- Standard routing to all 10 specialist agents
- Parallel Agent Execution: Concurrent fan-out of Weakness Detector + Resource Discovery + Coaching Advisor
- Planner-Reviewer Pipeline: Dual-agent feedback loop with pedagogical critique
"""
import asyncio
import logging
from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.profile_analyzer import analyze_profile
from app.agents.syllabus_manager import manage_syllabus
from app.agents.resource_discovery import discover_resources
from app.agents.study_planner import plan_study, review_study_plan
from app.agents.question_generator import generate_questions
from app.agents.content_tutor import explain_concept
from app.agents.assessment_agent import analyze_assessment
from app.agents.weakness_detector import detect_weaknesses
from app.agents.adaptive_planner import adapt_plan
from app.agents.coaching_advisor import provide_coaching

logger = logging.getLogger(__name__)


async def parallel_remediation_fanout(state: AgentState) -> dict:
    """Parallel Agent Execution (Fan-Out / Fan-In):

    Executes Weakness Detection, Resource Discovery, and Coaching Advisory
    concurrently in parallel, then aggregates their outputs for the Adaptive Planner.
    """
    input_data = state.get("input_data", {})
    topic_name = input_data.get("topic_name", "General")
    weak_topics = input_data.get("weak_topics", [topic_name])

    # Construct individual agent input states
    weakness_state = AgentState(
        task="detect_weaknesses",
        user_id=state["user_id"],
        db=state.get("db"),
        input_data=input_data,
        agents_called=list(state.get("agents_called", [])),
    )
    resource_state = AgentState(
        task="discover_resources",
        user_id=state["user_id"],
        db=state.get("db"),
        input_data={"topic_name": topic_name, "num_resources": 4},
        agents_called=list(state.get("agents_called", [])),
    )
    coaching_state = AgentState(
        task="provide_coaching",
        user_id=state["user_id"],
        db=state.get("db"),
        input_data={"stats": input_data.get("stats", {})},
        agents_called=list(state.get("agents_called", [])),
    )

    logger.info("Executing 3 agents in parallel (Weakness Detector, Resource Discovery, Coaching Advisor)...")

    # Concurrent Execution via asyncio.gather (Fan-out)
    weakness_res, resource_res, coaching_res = await asyncio.gather(
        detect_weaknesses(weakness_state),
        discover_resources(resource_state),
        provide_coaching(coaching_state),
        return_exceptions=True
    )

    # Fan-In: Consolidate parallel results
    parallel_outputs = {
        "weakness_analysis": weakness_res.get("result", {}) if isinstance(weakness_res, dict) else {},
        "discovered_resources": resource_res.get("result", {}).get("resources", []) if isinstance(resource_res, dict) else [],
        "coaching_message": coaching_res.get("result", {}).get("coaching_message", "") if isinstance(coaching_res, dict) else "",
    }

    # Pass consolidated insights to Adaptive Planner
    adaptive_input = dict(input_data)
    adaptive_input["weakness_insights"] = parallel_outputs["weakness_analysis"]
    adaptive_input["curated_resources"] = parallel_outputs["discovered_resources"]
    adaptive_input["coaching_context"] = parallel_outputs["coaching_message"]

    adaptive_state = AgentState(
        task="adapt_plan",
        user_id=state["user_id"],
        db=state.get("db"),
        input_data=adaptive_input,
        agents_called=list(state.get("agents_called", [])) + [
            "parallel_weakness_detector",
            "parallel_resource_discovery",
            "parallel_coaching_advisor"
        ],
    )
    adaptive_res = await adapt_plan(adaptive_state)

    consolidated_result = {
        "adapted_strategy": adaptive_res.get("result", {}),
        "parallel_agent_outputs": parallel_outputs,
        "coordination_mode": "fan_out_fan_in_parallel",
    }

    return {
        "result": consolidated_result,
        "parallel_outputs": parallel_outputs,
        "agents_called": state.get("agents_called", []) + [
            "orchestrator",
            "parallel_fanout_dispatcher",
            "weakness_detector",
            "resource_discovery",
            "coaching_advisor",
            "adaptive_planner"
        ],
    }


async def route_request(state: AgentState) -> dict:
    """Orchestrator node: Determine which agent or pipeline to call based on the task."""
    task = state["task"]
    next_agent = None
    
    if task == "parallel_remediation_pipeline":
        next_agent = "parallel_remediation"
    elif task == "plan_study_with_review":
        next_agent = "study_planner_node"
    elif task == "analyze_profile":
        next_agent = "profile_analyzer"
    elif task == "manage_syllabus":
        next_agent = "syllabus_manager"
    elif task == "discover_resources":
        next_agent = "resource_discovery"
    elif task == "plan_study":
        next_agent = "study_planner"
    elif task == "generate_questions":
        next_agent = "question_generator"
    elif task == "explain_concept":
        next_agent = "content_tutor"
    elif task == "analyze_assessment":
        next_agent = "assessment_agent"
    elif task == "detect_weaknesses":
        next_agent = "weakness_detector"
    elif task == "adapt_plan":
        next_agent = "adaptive_planner"
    elif task == "provide_coaching":
        next_agent = "coaching_advisor"
    else:
        logger.warning("Unknown task: %s", task)
        return {"error": f"Unknown task: {task}", "next_agent": END}
        
    return {"next_agent": next_agent, "agents_called": state.get("agents_called", []) + ["orchestrator"]}


def should_continue_review_loop(state: AgentState) -> str:
    """Conditional Edge for Planner-Reviewer Loop."""
    is_approved = state.get("is_approved", False)
    iteration = state.get("iteration_count", 1)

    if is_approved or iteration >= 3:
        return END
    return "study_planner_node"


def get_agent_graph():
    """Build and return the LangGraph state graph with parallel agents and reflection loops."""
    builder = StateGraph(AgentState)
    
    # Core Orchestrator
    builder.add_node("orchestrator", route_request)

    # Parallel Execution Node
    builder.add_node("parallel_remediation", parallel_remediation_fanout)

    # Planner-Reviewer Nodes (Reflection Loop)
    builder.add_node("study_planner_node", plan_study)
    builder.add_node("plan_reviewer_node", review_study_plan)

    # 10 Specialist Agents
    builder.add_node("profile_analyzer", analyze_profile)
    builder.add_node("syllabus_manager", manage_syllabus)
    builder.add_node("resource_discovery", discover_resources)
    builder.add_node("study_planner", plan_study)
    builder.add_node("content_tutor", explain_concept)
    builder.add_node("question_generator", generate_questions)
    builder.add_node("assessment_agent", analyze_assessment)
    builder.add_node("weakness_detector", detect_weaknesses)
    builder.add_node("adaptive_planner", adapt_plan)
    builder.add_node("coaching_advisor", provide_coaching)
    
    # Graph Edges
    builder.add_edge(START, "orchestrator")
    
    # Conditional routing from orchestrator
    builder.add_conditional_edges(
        "orchestrator",
        lambda state: state["next_agent"],
        {
            "parallel_remediation": "parallel_remediation",
            "study_planner_node": "study_planner_node",
            "profile_analyzer": "profile_analyzer",
            "syllabus_manager": "syllabus_manager",
            "resource_discovery": "resource_discovery",
            "study_planner": "study_planner",
            "content_tutor": "content_tutor",
            "question_generator": "question_generator",
            "assessment_agent": "assessment_agent",
            "weakness_detector": "weakness_detector",
            "adaptive_planner": "adaptive_planner",
            "coaching_advisor": "coaching_advisor",
            END: END
        }
    )

    # Planner-Reviewer Feedback Loop Edges
    builder.add_edge("study_planner_node", "plan_reviewer_node")
    builder.add_conditional_edges(
        "plan_reviewer_node",
        should_continue_review_loop,
        {
            "study_planner_node": "study_planner_node",
            END: END,
        }
    )
    
    # Standard terminal edges
    builder.add_edge("parallel_remediation", END)
    builder.add_edge("profile_analyzer", END)
    builder.add_edge("syllabus_manager", END)
    builder.add_edge("resource_discovery", END)
    builder.add_edge("study_planner", END)
    builder.add_edge("content_tutor", END)
    builder.add_edge("question_generator", END)
    builder.add_edge("assessment_agent", END)
    builder.add_edge("weakness_detector", END)
    builder.add_edge("adaptive_planner", END)
    builder.add_edge("coaching_advisor", END)
    
    return builder.compile()

# Global compiled graph instance
agent_graph = get_agent_graph()
