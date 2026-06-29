# Architecture Spec: Resume-Tailoring AI Agent

**Frameworks:** LangGraph (Agentic Workflow), LlamaIndex/LangChain (RAG Tooling)
**User Interface:** Gradio

## 1. Global State Definition

The core data structure passed between nodes. Defined using Python's `TypedDict`.

```python
from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    jd_text: str                     # Target Job Description
    resume_text: str                 # Original Resume content
    alignment_strategy: Dict[str, Any] # Structured output from Node 1 (strengths, gaps, soft skills)
    alignment_remarks: str           # User response to the alignment_strategy
    retrieved_projects: List[Dict]   # Raw projects fetched from the RAG database
    approved_projects: List[Dict]    # Filtered projects approved by the user
    project_remarks: str             # Additional context provided by the user
    final_draft: str                 # The generated resume bullet points and actionable advice

```

## 2. Node Architecture & Workflow

### Node 1: Alignment Strategist (`LLM Worker`)

* **Input:** `jd_text`, `resume_text`
* **Action:** Acts as a senior recruiter. Conducts a multidimensional comparison between the current resume and the target JD.
* **Output (`alignment_strategy` JSON schema):**
* `strengths`: What is already working well and should be kept.
* `irrelevancies`: Experiences that should be downplayed or removed to maintain focus.
* `technical_gaps`: Missing hard skills required by the JD.
* `recommended_soft_skills`: Key soft skills inferred from the JD (e.g., cross-functional communication, leadership) that need to be demonstrated.

### Node 2: Human Interrupt I (Strategy Tuning)

* **LangGraph Config:** `interrupt_before=["Project_Retriever"]`
* **Action:** The workflow pauses, presenting the `alignment_strategy` to the user via Gradio. The user can manually tweak the strategy by adding comments. For example, they might specify: *"Tie the 'cross-functional communication' soft skill directly to my backend optimization project."*
* **Output:** Updates `alignment_strategy` and appends any specific `alignment_remarks`.

### Node 3: Project Retriever (`ReAct Agent`)

* **Input:** `alignment_strategy`, `alignment_remarks`
* **Action:** An autonomous ReAct loop equipped with a **RAG Tool** (accessing the user's career/project database).
* The LLM analyzes the technical gaps and strategic needs.
* It autonomously generates specific query strings to search the vector database.
* It loops until it finds the best matching historical projects/experiences.

* **Output (`retrieved_projects`):** A list of candidate projects fetched from the database.

### Node 4: Human Interrupt II (Project Curation)

* **LangGraph Config:** `interrupt_before=["Resume_Strategist"]`
* **Action:** The workflow pauses again. The user reviews the `retrieved_projects` surfaced by the RAG tool. The user acts as a filter, checking boxes to approve relevant projects and discarding irrelevant ones (e.g., removing a graphics rendering project when applying for a traditional backend role).
* **Output:** Updates `approved_projects` and appends any final `project_remarks`.

### Node 5: Resume Strategist (`Generator`)

* **Input:** `jd_text`, `resume_text`, `approved_projects`, `alignment_remarks`, `alignment_strategy`, `project_remarks`
* **Action:** Synthesizes all approved data. Drafts highly tailored resume bullet points using the exact terminology from the JD. Ensures the tone is professional and directly addresses the initial gaps.
* **Output (`final_draft`):** The final actionable advice and ready-to-copy resume bullet points.

---

### Suggested Workflow Routing (For Vibe Coding Context)

```text
START 
  -> alignment_strategist 
  -> human_tuning_interrupt 
  -> project_retriever (ReAct) 
  -> human_approval_interrupt 
  -> resume_strategist 
  -> END

```