"""Orchestrator Agent and LangGraph definition.

This module defines the graph and routes requests to the correct agent.
All 10 specialist agents are registered as nodes in the state graph.
"""
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.profile_analyzer import analyze_profile
from app.agents.syllabus_manager import manage_syllabus
from app.agents.resource_discovery import discover_resources
from app.agents.study_planner import plan_study
from app.agents.question_generator import generate_questions
from app.agents.content_tutor import explain_concept
from app.agents.assessment_agent import analyze_assessment
from app.agents.weakness_detector import detect_weaknesses
from app.agents.adaptive_planner import adapt_plan
from app.agents.coaching_advisor import provide_coaching

logger = logging.getLogger(__name__)


async def route_request(state: AgentState) -> dict:
    """Orchestrator node: Determine which agent to call based on the task."""
    task = state["task"]
    next_agent = None
    
    if task == "analyze_profile":
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


def get_agent_graph():
    """Build and return the LangGraph state graph with all 10 agents."""
    builder = StateGraph(AgentState)
    
    # Add nodes — Master Orchestrator + 10 specialist agents
    builder.add_node("orchestrator", route_request)
    builder.add_node("profile_analyzer", analyze_profile)       # Agent #1
    builder.add_node("syllabus_manager", manage_syllabus)       # Agent #2
    builder.add_node("resource_discovery", discover_resources)  # Agent #3
    builder.add_node("study_planner", plan_study)               # Agent #4
    builder.add_node("content_tutor", explain_concept)          # Agent #5
    builder.add_node("question_generator", generate_questions)  # Agent #6
    builder.add_node("assessment_agent", analyze_assessment)    # Agent #7
    builder.add_node("weakness_detector", detect_weaknesses)    # Agent #8
    builder.add_node("adaptive_planner", adapt_plan)            # Agent #9
    builder.add_node("coaching_advisor", provide_coaching)      # Agent #10
    
    # Add edges
    builder.add_edge(START, "orchestrator")
    
    # Conditional routing from orchestrator to all agents
    builder.add_conditional_edges(
        "orchestrator",
        lambda state: state["next_agent"],
        {
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
    
    # End edges — each agent returns to END
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
