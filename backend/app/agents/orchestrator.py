"""Orchestrator Agent and LangGraph definition.

This module defines the graph and routes requests to the correct agent.
"""
import logging
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.profile_analyzer import analyze_profile
from app.agents.syllabus_manager import manage_syllabus
from app.agents.question_generator import generate_questions
from app.agents.coaching_advisor import provide_coaching
from app.agents.content_tutor import explain_concept

logger = logging.getLogger(__name__)


async def route_request(state: AgentState) -> dict:
    """Orchestrator node: Determine which agent to call based on the task."""
    task = state["task"]
    next_agent = None
    
    if task == "analyze_profile":
        next_agent = "profile_analyzer"
    elif task == "manage_syllabus":
        next_agent = "syllabus_manager"
    elif task == "generate_questions":
        next_agent = "question_generator"
    elif task == "provide_coaching":
        next_agent = "coaching_advisor"
    elif task == "explain_concept":
        next_agent = "content_tutor"
    else:
        logger.warning("Unknown task: %s", task)
        return {"error": f"Unknown task: {task}", "next_agent": END}
        
    return {"next_agent": next_agent, "agents_called": state.get("agents_called", []) + ["orchestrator"]}


def get_agent_graph():
    """Build and return the LangGraph state graph."""
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("orchestrator", route_request)
    builder.add_node("profile_analyzer", analyze_profile)
    builder.add_node("syllabus_manager", manage_syllabus)
    builder.add_node("question_generator", generate_questions)
    builder.add_node("coaching_advisor", provide_coaching)
    builder.add_node("content_tutor", explain_concept)
    
    # Add edges
    builder.add_edge(START, "orchestrator")
    
    # Conditional routing from orchestrator
    builder.add_conditional_edges(
        "orchestrator",
        lambda state: state["next_agent"],
        {
            "profile_analyzer": "profile_analyzer",
            "syllabus_manager": "syllabus_manager",
            "question_generator": "question_generator",
            "coaching_advisor": "coaching_advisor",
            "content_tutor": "content_tutor",
            END: END
        }
    )
    
    # End edges
    builder.add_edge("profile_analyzer", END)
    builder.add_edge("syllabus_manager", END)
    builder.add_edge("question_generator", END)
    builder.add_edge("coaching_advisor", END)
    builder.add_edge("content_tutor", END)
    
    return builder.compile()

# Global compiled graph instance
agent_graph = get_agent_graph()
