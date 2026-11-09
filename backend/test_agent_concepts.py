"""Unit and integration tests for RAG, Parallel Agents, and Planner-Reviewer Loop."""
import os
import sys

# Set demo mode for instantaneous test execution without external network delays
os.environ["GROQ_API_KEY"] = ""

import asyncio
from app.core.config import settings
settings.GROQ_API_KEY = ""

from app.services.rag_service import rag_index
from app.agents.orchestrator import parallel_remediation_fanout
from app.agents.study_planner import plan_study, review_study_plan
from app.agents.state import make_state, AgentState


# ------------------------------------------------------------------------------
# 1. RAG (Retrieval-Augmented Generation) Tests
# ------------------------------------------------------------------------------
def test_rag_chunking_and_retrieval():
    sample_syllabus_text = """
    COMPUTER NETWORKS & DISTRIBUTED SYSTEMS
    Unit 3: Transport Layer Protocols.
    The Transmission Control Protocol (TCP) provides reliable, ordered, and error-checked delivery of a stream
    of octets between applications running on hosts communicating via an IP network. Major mechanisms include
    the three-way handshake (SYN, SYN-ACK, ACK), flow control via sliding window buffer sizes, and congestion control
    algorithms (Slow Start, Congestion Avoidance, Fast Retransmit, and Fast Recovery).
    In contrast, User Datagram Protocol (UDP) is a connectionless, unreliable transport protocol suitable for low-latency
    audio/video streaming and DNS lookups.
    """

    # 1. Chunk and index document
    chunks = rag_index.chunk_document(
        text=sample_syllabus_text,
        source_document="Gate_CS_Curriculum.pdf",
        user_id=999,
        subject_name="Computer Networks",
        topic_name="TCP & Transport Layer",
        chunk_size=300,
        chunk_overlap=50,
    )
    assert len(chunks) >= 1
    assert any("sliding window" in c.text.lower() for c in chunks)

    # 2. Retrieve relevant chunks
    results = rag_index.retrieve(
        query="Explain TCP three-way handshake and flow control sliding window",
        user_id=999,
        top_k=2
    )
    assert len(results) >= 1
    top_chunk = results[0]
    assert top_chunk.score > 0.20
    assert "Gate_CS_Curriculum.pdf" in top_chunk.citation
    assert "three-way handshake" in top_chunk.text.lower()

    # 3. Format prompt context
    prompt_context = rag_index.format_context_for_prompt(results)
    assert "RETRIEVED SYLLABUS & CURRICULUM CONTEXT" in prompt_context
    assert "[Source: Gate_CS_Curriculum.pdf" in prompt_context


# ------------------------------------------------------------------------------
# 2. Parallel Agent Execution (Fan-Out / Fan-In) Tests
# ------------------------------------------------------------------------------
async def test_parallel_agent_execution_fanout():
    initial_state = make_state(
        task="parallel_remediation_pipeline",
        user_id=1,
        db=None,
        input_data={
            "topic_name": "Dynamic Programming",
            "weak_topics": ["Dynamic Programming", "Graph Theory"],
            "daily_hours": 3.0,
            "days_remaining": 45,
            "stats": {"streak": 5, "hours": 24.0, "accuracy": 62.0},
        }
    )

    # Execute fan-out / fan-in node
    result_state = await parallel_remediation_fanout(initial_state)

    # Verify that all 3 parallel branches ran
    parallel_outputs = result_state["parallel_outputs"]
    assert "weakness_analysis" in parallel_outputs
    assert "discovered_resources" in parallel_outputs
    assert "coaching_message" in parallel_outputs

    # Verify consolidation into adaptive planner
    final_result = result_state["result"]
    assert final_result["coordination_mode"] == "fan_out_fan_in_parallel"
    assert "adapted_strategy" in final_result

    # Verify execution trace contains all parallel agents called
    agents = result_state["agents_called"]
    assert "weakness_detector" in agents
    assert "resource_discovery" in agents
    assert "coaching_advisor" in agents
    assert "adaptive_planner" in agents


# ------------------------------------------------------------------------------
# 3. Planner-Reviewer Reflection & Critique Loop Tests
# ------------------------------------------------------------------------------
async def test_planner_reviewer_feedback_loop():
    # Step 1: Planner Node generates initial draft
    planner_state = make_state(
        task="plan_study_with_review",
        user_id=1,
        db=None,
        input_data={
            "topics": ["Binary Trees", "Graphs", "Dynamic Programming"],
            "weak_topics": ["Dynamic Programming"],
            "daily_hours": 3.0,
            "days_remaining": 60,
        }
    )
    plan_output = await plan_study(planner_state)
    assert "strategy" in plan_output["result"]
    strategy = plan_output["result"]["strategy"]
    assert "phase_plan" in strategy

    # Step 2: Reviewer / Critic Node evaluates the plan
    reviewer_state = dict(planner_state)
    reviewer_state["result"] = plan_output["result"]
    reviewer_state["iteration_count"] = 1

    review_output = await review_study_plan(reviewer_state)
    critique = review_output["review_feedback"]
    assert "is_approved" in critique
    assert "score" in critique
    assert critique["score"] > 0

    # Step 3: Peer review metadata attached to final strategy
    final_strategy = review_output["result"]
    assert "peer_review" in final_strategy
    assert final_strategy["peer_review"]["status"] in ("APPROVED", "REVISED")
    assert final_strategy["peer_review"]["score"] > 0


if __name__ == "__main__":
    print("1. Testing RAG Chunking and Retrieval...")
    test_rag_chunking_and_retrieval()
    print("   [OK] RAG Index & Semantic Retrieval verified.")

    print("2. Testing Parallel Agent Fan-Out / Fan-In...")
    asyncio.run(test_parallel_agent_execution_fanout())
    print("   [OK] Parallel Agent Execution (Weakness + Resources + Coaching -> Adaptive Planner) verified.")

    print("3. Testing Planner-Reviewer Feedback Loop...")
    asyncio.run(test_planner_reviewer_feedback_loop())
    print("   [OK] Planner-Reviewer Reflection & Critique Loop verified.")

    print("\nSUCCESS: All 3 Core Agentic Concepts Functioning Seamlessly!")
