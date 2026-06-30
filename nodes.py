import json
import ollama
from typing import Dict, Any
from state import AgentState

# ==========================================
# Prompts Definition
# ==========================================

ALIGNMENT_STRATEGIST_PROMPT = """
You are an elite Technical Recruiter and Resume Strategist. Your objective is to conduct a ruthless, multidimensional alignment check between a candidate's Resume and a target Job Description (JD).

You must analyze the inputs and output a strict JSON object mapping the strategic alignment. 

# INSTRUCTIONS FOR ANALYSIS:
1.  **strengths**: Identify 2-3 key technical skills or project experiences in the resume that perfectly align with the JD's core requirements.
2.  **irrelevancies**: Identify experiences that dilute the core professional narrative for this specific role. Ruthlessly separate distinct domains. For example, if the target JD is for a traditional Machine Learning or Backend Engineering role, explicitly flag specialized visual/creative tech projects (e.g., real-time rendering, shaders, physics simulations, or artistic tools) as irrelevant so they can be removed to maintain a strict engineering focus.
3.  **technical_gaps**: Identify 1-2 critical hard skills or tools required by the JD that are completely missing or weakly represented in the resume.
4.  **recommended_soft_skills**: Infer 2 critical soft skills based on the JD's tone and requirements (e.g., cross-functional leadership, stakeholder management).

# CONSTRAINTS:
- Output ONLY valid JSON. 
- Do NOT include markdown blocks like ```json ... ```.
- Do NOT output any conversational text, greetings, or explanations before or after the JSON.

# EXPECTED JSON SCHEMA:
{{
  "strengths": ["string", "string"],
  "irrelevancies": ["string", "string"],
  "technical_gaps": ["string", "string"],
  "recommended_soft_skills": ["string", "string"]
}}

# INPUTS:
[JOB DESCRIPTION]
{jd_text}

[CANDIDATE RESUME]
{resume_text}
"""

def alignment_strategist(state: AgentState) -> Dict[str, Any]:
    print("Executing Node alignment_strategist...")

    jd_text = state.get("jd_text", "")
    resume_text = state.get("resume_text", "")

    prompt = ALIGNMENT_STRATEGIST_PROMPT.format(
        jd_text=jd_text, 
        resume_text=resume_text
    )

    try:
        # Call Ollama with JSON format enforced
        response = ollama.chat(
            model="llama3.1:8b",
            messages=[{'role': 'system', 'content': prompt}],
            format='json'
        )
        
        output = response['message']['content']
        parsed_json = json.loads(output)
        print("✅ Node 1: JSON successfully generated and parsed!")
        
        # Return only the state update
        return {
            "alignment_strategy": parsed_json
        }
    
    except json.JSONDecodeError:
        print("❌ Node 1: Failed to parse JSON from LLM response.")
        # Fallback dictionary to prevent LangGraph from crashing
        return {
            "alignment_strategy": {
                "strengths": ["Error parsing strengths from LLM"],
                "irrelevancies": ["Error parsing irrelevancies from LLM"],
                "technical_gaps": ["Error parsing technical gaps from LLM"],
                "recommended_soft_skills": ["Error parsing soft skills from LLM"]
            }
        }
    except Exception as e:
        print(f"❌ Node 1: Error during Ollama call: {e}")
        return {"alignment_strategy": {}}


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