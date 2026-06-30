from typing import Dict, Any
from state import AgentState

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