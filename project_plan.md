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

### Node 3: Component Pitcher (`ReAct Agent`)

* **Input:** `alignment_strategy`, `alignment_remarks`
* **Action:** An autonomous ReAct loop equipped with a **RAG Tool** accessing the career database. Instead of merely fetching raw projects, it performs **Capability Mapping**.
* The LLM analyzes the technical gaps and strategic needs identified in Node 1.
* It autonomously generates query strings to search the vector database for relevant experiences (e.g., framing a Teaching Assistant role as a technical communication component, or a Hack4Good win as agile problem-solving).
* It loops and synthesizes the retrieved data to pitch how specific past experiences address the JD's requirements.
* **Output (`proposed_components`):** A list of exactly 5 structured capability components. Each component includes `component_id`, `title`, `summary`, `reason` (how it aligns with the JD), `source_file`, and highly specific `original_snippets` for source grounding.

### Node 4: Human Interrupt II (Component Curation)

* **LangGraph Config:** `interrupt_before=["Resume_Strategist"]`
* **Action:** The workflow pauses, presenting the 5 `proposed_components` to the user via Gradio. The user acts as a strategic filter to review the pitched capabilities:
* Approving or discarding specific components (e.g., rejecting a Technical Artist module focused on graphics rendering when tailoring the resume for a strictly Machine Learning Engineer role).
* Adding manual refinements via an input box (e.g., "Shift the focus of this component from general leadership to specific cross-functional collaboration").
* **Output:** Updates `approved_components` and appends any final `component_remarks`.

### Node 5: Resume Strategist (`Generator`)

* **Input:** `jd_text`, `resume_text`, `approved_components`, `component_remarks`, `alignment_remarks`, `alignment_strategy`
* **Action:** Synthesizes all approved data. Acts as a precision copywriter to draft highly tailored resume bullet points using the exact terminology from the JD. It uses the `original_snippets` passed from Node 3 as a strict generation constraint—ensuring that all metrics, technical details, and past contributions are faithfully represented without hallucination.
* **Output (`final_draft`):** The final actionable advice and ready-to-copy, high-fidelity resume bullet points.

---

### Suggested Workflow Routing (For Vibe Coding Context)

```text
START 
  -> alignment_strategist 
  -> human_tuning_interrupt
  -> component pitcher (ReAct)
  -> human_approval_interrupt 
  -> resume_strategist 
  -> END

```