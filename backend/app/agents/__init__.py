"""Agent initialization and execution wrapper."""
from typing import Any
from app.agents.state import make_state
from app.agents.orchestrator import agent_graph

async def invoke_agent(task: str, user_id: int, db: Any, input_data: dict = None) -> dict:
    """Helper to invoke the agent graph for a specific task."""
    initial_state = make_state(task=task, user_id=user_id, db=db, input_data=input_data)
    
    # Run the graph
    final_state = await agent_graph.ainvoke(initial_state)
    
    # Return the result
    return final_state.get("result", {})
