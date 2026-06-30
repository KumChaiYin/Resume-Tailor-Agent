from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict, total=False):
    jd_text: str                       # Target Job Description
    resume_text: str                   # Original Resume content
    alignment_strategy: Dict[str, Any] # Structured output from Node 1 (strengths, gaps, soft skills)
    alignment_remarks: str             # User response to the alignment_strategy
    retrieved_projects: List[Dict]     # Raw projects fetched from the RAG database
    approved_projects: List[Dict]      # Filtered projects approved by the user
    project_remarks: str               # Additional context provided by the user
    final_draft: str                   # The generated resume bullet points and actionable advice