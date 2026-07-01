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


def component_pitcher(state: AgentState) -> Dict[str, Any]:
    print("Executing Node component_pitcher...")
    return {
        "proposed_components": [
            {
                "component_id": "01", 
                "title": "Distributed Web Crawler",
                "summary": "Built a scalable crawler using Redis queue...",
                "reason": "Addresses 'distributed systems' and 'backend scalability' mentioned in the JD's technical gaps.",
                "target_skills_addressed": ["Redis", "Scalability", "System Design"], 
                "source_file": "past-resumes/distributed_crawler.md",
                "original_snippets": [
                    "Engineered a distributed crawler handling 10k requests/sec",
                    "Integrated Redis for job queuing"
                ] 

            }, 
            {
                "component_id": "02", 
                "title": "Teaching Assistant (Systems)",
                "summary": "Led OS and Systems architecture recitations...",
                "reason": "Demonstrates the technical communication and cross-functional leadership requested in JD soft skills.",
                "source_file": "details/ta_systems.md",
                "original_snippets": [
                    "Mentored 50+ students in C++ and Linux kernel concepts",
                    "Translated complex system architecture into clear documentation"
                ] 
            }
        ]
    }


def human_approval_interrupt(state: AgentState) -> Dict[str, Any]:
    print("Executing Node human_approval_interrupt...")
    return {}


def resume_strategist(state: AgentState) -> Dict[str, Any]:
    print("Executing Node resume_strategist...")

    approved = state.get("approved_components", [])
    component_titles = ", ".join(c.get("title", "") for c in approved)
    snippets = " | ".join([s for c in approved for s in c.get('original_snippets', [])])

    align_remarks = state.get('alignment_remarks', '') or 'None'
    comp_remarks = state.get('component_remarks', '') or 'None'
    strategy = state.get('alignment_strategy', {})
    
    return {
        "final_draft": (
            "**Draft Resume Bullets:**\n\n"
            f"**Curated Experiences:** {component_titles}\n"
            f"**Original Snippets integrated:** {snippets}\n\n"
            f"> *System Note: Addressed Technical Gaps ({', '.join(strategy.get('technical_gaps', []))}).*\n"
            f"> *Alignment Remarks:* {align_remarks}\n"
            f"> *Component Remarks:* {comp_remarks}"
        )
    }