from typing import TypedDict, List, Dict, Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph


class AgentState(TypedDict):
    jd_text: str                     # Target Job Description
    resume_text: str                 # Original Resume content
    alignment_strategy: Dict[str, Any] # Structured output from Node 1 (strengths, gaps, soft skills)
    alignment_remarks: str           # User response to the alignment_strategy
    retrieved_projects: List[Dict]   # Raw projects fetched from the RAG database
    approved_projects: List[Dict]    # Filtered projects approved by the user
    project_remarks: str             # Additional context provided by the user
    final_draft: str                 # The generated resume bullet points and actionable advice


def alignment_strategist(state: AgentState) -> Dict[str, Any]:
    print("Executing Node alignment_strategist...")
    # only return modified term
    return {
        "alignment_strategy": {
            "strengths": [
                "Backend engineering experience aligns with the target role.",
                "Project ownership can be positioned as product impact.",
            ],
            "irrelevancies": [
                "Downplay unrelated academic or hobby projects.",
            ],
            "technical_gaps": [
                "Distributed systems",
                "Cloud deployment",
            ],
            "recommended_soft_skills": [
                "Cross-functional communication",
                "Technical leadership",
            ],
        }
    }


def human_tuning_interrupt(state: AgentState) -> Dict[str, Any]:
    print("Executing Node human_tuning_interrupt...")
    return {}


def project_retriever(state: AgentState) -> Dict[str, Any]:
    print("Executing Node project_retriever...")
    return {
        "retrieved_projects": [
            {
                "id": "project_001",
                "title": "Backend Optimization Project",
                "summary": "Reduced API latency by profiling bottlenecks and improving database access patterns.",
                "matched_gaps": ["Distributed systems", "Cloud deployment"],
            },
            {
                "id": "project_002",
                "title": "Internal Automation Tool",
                "summary": "Built a workflow tool used by multiple stakeholders to reduce manual reporting.",
                "matched_gaps": ["Cross-functional communication"],
            },
        ]
    }


def human_approval_interrupt(state: AgentState) -> Dict[str, Any]:
    print("Executing Node human_approval_interrupt...")
    approved_projects = state.get("approved_projects") or state["retrieved_projects"][:1]
    return {
        "approved_projects": approved_projects,
    }


def resume_strategist(state: AgentState) -> Dict[str, Any]:
    print("Executing Node resume_strategist...")
    project_titles = ", ".join(project["title"] for project in state["approved_projects"])

    align_remarks = state.get('alignment_remarks', '') or 'None'
    proj_remarks = state.get('project_remarks', '') or 'None'
    
    return {
        "final_draft": (
            "Draft resume bullets:\n"
            f"- Reframed approved experience around: {project_titles}.\n"
            "- Emphasized backend impact, measurable outcomes, and JD-aligned terminology.\n"
            f"- Alignment Remarks incorporated: {align_remarks}\n"
            f"- Project Curation Remarks incorporated: {proj_remarks}"
        )
    }


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("alignment_strategist", alignment_strategist)
    workflow.add_node("human_tuning_interrupt", human_tuning_interrupt)
    workflow.add_node("project_retriever", project_retriever)
    workflow.add_node("human_approval_interrupt", human_approval_interrupt)
    workflow.add_node("resume_strategist", resume_strategist)

    workflow.set_entry_point("alignment_strategist")
    workflow.add_edge("alignment_strategist", "human_tuning_interrupt")
    workflow.add_edge("human_tuning_interrupt", "project_retriever")
    workflow.add_edge("project_retriever", "human_approval_interrupt")
    workflow.add_edge("human_approval_interrupt", "resume_strategist")
    workflow.set_finish_point("resume_strategist")

    return workflow.compile(
        checkpointer=MemorySaver(),
        interrupt_before=[
            "human_tuning_interrupt",
            "human_approval_interrupt",
        ],
    )


def _print_snapshot(graph, config: Dict[str, Any]) -> None:
    snapshot = graph.get_state(config)
    print("\nCurrent state:")
    for key, value in snapshot.values.items():
        print(f"{key}: {value}")
    if snapshot.next:
        print(f"\nPaused before: {snapshot.next}") 


def _collect_project_approvals(retrieved_projects: List[Dict]) -> List[Dict]:
    if not retrieved_projects:
        return []

    print("\nRetrieved projects:")
    for index, project in enumerate(retrieved_projects, start=1):
        print(f"{index}. {project['title']} - {project['summary']}")

    raw_selection = input(
        "Approve project numbers separated by commas, or press Enter to approve the first: "
    ).strip()
    if not raw_selection:
        return retrieved_projects[:1]

    approved_projects = []
    for token in raw_selection.split(","):
        try:
            selected_index = int(token.strip()) - 1
        except ValueError:
            continue

        if 0 <= selected_index < len(retrieved_projects):
            approved_projects.append(retrieved_projects[selected_index])

    return approved_projects or retrieved_projects[:1]

def get_multiline_input(prompt: str) -> str:
    print(prompt + " (Press Enter twice to finish):")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return "\n".join(lines)

if __name__ == "__main__":
    graph = build_graph()
    config = {"configurable": {"thread_id": "terminal-test-run"}}

    initial_state: AgentState = {
        "jd_text": get_multiline_input("Paste a mock Job Description") or "Mock backend engineer JD",
        "resume_text": get_multiline_input("Paste a mock resume") or "Mock backend engineer resume",
        "alignment_strategy": {},
        "alignment_remarks": "",
        "retrieved_projects": [],
        "approved_projects": [],
        "project_remarks": "",
        "final_draft": "",
    }

    graph.invoke(initial_state, config)

    while True:
        snapshot = graph.get_state(config)
        if not snapshot.next:
            break

        _print_snapshot(graph, config)
        next_node = snapshot.next[0]

        if next_node == "human_tuning_interrupt":
            remarks = input("\nStrategy tuning remarks, or press Enter to keep mock strategy: ").strip()
            if remarks:
                graph.update_state(
                    config,
                    {"alignment_remarks": remarks},
                    as_node="alignment_strategist",
                )

        elif next_node == "human_approval_interrupt":
            approved = _collect_project_approvals(snapshot.values.get("retrieved_projects", []))
            remarks = input("Final project curation remarks, or press Enter to skip: ").strip()
            updates: Dict[str, Any] = {"approved_projects": approved}
            if remarks:
                updates["project_remarks"] = remarks
            
            graph.update_state(config, updates, as_node="project_retriever")

        graph.invoke(None, config)

    _print_snapshot(graph, config)
    print("\nFinal draft:")
    print(graph.get_state(config).values["final_draft"])
