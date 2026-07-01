from typing import TypedDict, List, Dict, Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

from state import AgentState
from nodes import (
    alignment_strategist, 
    human_tuning_interrupt, 
    component_pitcher, 
    human_approval_interrupt, 
    resume_strategist
)

def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("alignment_strategist", alignment_strategist)
    workflow.add_node("human_tuning_interrupt", human_tuning_interrupt)
    workflow.add_node("component_pitcher", component_pitcher)
    workflow.add_node("human_approval_interrupt", human_approval_interrupt)
    workflow.add_node("resume_strategist", resume_strategist)

    workflow.set_entry_point("alignment_strategist")
    workflow.add_edge("alignment_strategist", "human_tuning_interrupt")
    workflow.add_edge("human_tuning_interrupt", "component_pitcher")
    workflow.add_edge("component_pitcher", "human_approval_interrupt")
    workflow.add_edge("human_approval_interrupt", "resume_strategist")
    workflow.set_finish_point("resume_strategist")

    return workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=[
            "human_tuning_interrupt",
            "human_approval_interrupt",
        ],
    )

compiled_graph = build_graph()
