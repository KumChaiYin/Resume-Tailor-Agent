import gradio as gr
import uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

from graph import compiled_graph as graph

# ==========================================
# 1. Bind Gradio Interaction Logic
# ==========================================

def start_workflow(jd, resume):
    """Step 1: Submit JD and Resume, run the graph until the first breakpoint"""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "jd_text": jd,
        "resume_text": resume,
    }
    
    # Trigger execution, it will pause before human_tuning_interrupt
    graph.invoke(initial_state, config)
    snapshot = graph.get_state(config)
    
    strategy = snapshot.values.get("alignment_strategy", {})
    
    # Return state, and toggle UI visibility
    return (
        config,
        gr.update(interactive=False), # jd_input lock
        gr.update(interactive=False), # resume_input lock
        gr.update(visible=False),     # Hide start button
        gr.update(visible=True),      # Show Step 2
        strategy                      # Output Strategy
    )

def submit_tuning(config, remarks):
    """Step 2: User submits tuning remarks, run graph to the second breakpoint"""
    if remarks.strip():
        graph.update_state(
            config,
            {"alignment_remarks": remarks},
            as_node="alignment_strategist",
        )
    
    # Resume execution, it will pause before human_approval_interrupt
    graph.invoke(None, config)
    snapshot = graph.get_state(config)

    
    proposed_components = snapshot.values.get("proposed_components", [])
    
    # Assemble options format for the CheckboxGroup
    # Construct markdown for display
    components_md = "### 📂 Proposed Components\n\n"
    choices = []
    
    for c in proposed_components:
        components_md += f"**{c['component_id']} - {c['title']}**\n"
        components_md += f"> **Summary:** {c['summary']}  \n"
        components_md += f"> **Reason:** {c['reason']}  \n"
        components_md += f"> **Original Snippets:** \n"
        for o in c.get('original_snippets', []):
            components_md += f"> - {o}  \n"
        components_md += "\n---\n"

        choices.append(f"{c['component_id']} - {c['title']}")
    
    return (
        gr.update(interactive=False), # lock tuning remarks
        gr.update(visible=False),     # hide tuning submit button
        gr.update(visible=True),      # show Step 3
        components_md,                   # populate project details Markdown
        gr.update(choices=choices, value=choices) # populate checkboxes
    )

def submit_approval(config, selected_choices, remarks, jd_val, resume_val):
    """Step 3: Approve components. Transition to Step 4, output side-by-side view."""
    snapshot = graph.get_state(config)
    proposed_components = snapshot.values.get("proposed_components", [])
    
    # Extract approved components based on user's Checkbox selection
    approved_components = []
    for choice in selected_choices:
        p_id = choice.split(" - ")[0]
        for p in proposed_components:
            if p["component_id"] == p_id:
                approved_components.append(p)
                break
                
    # Fallback: If nothing is selected, default to the first one
    if not approved_components and proposed_components:
        approved_components = proposed_components[:1]

    updates = {"approved_components": approved_components}
    if remarks.strip():
        updates["component_remarks"] = remarks

    # Update the state with user inputs
    graph.update_state(
        config,
        updates,
        as_node="human_approval_interrupt"
    )
    
    # Resume execution until the end
    graph.invoke(None, config)
    snapshot = graph.get_state(config)
    
    final_draft = snapshot.values.get("final_draft", "")
    
    return (
        gr.update(interactive=False), # lock checkboxes
        gr.update(interactive=False), # lock project remarks
        gr.update(visible=False),     # hide approval button
        gr.update(visible=True),      # show Step 4
        jd_val,                       # pass jd to step 4 display
        resume_val,                   # pass resume to step 4 display
        final_draft                   # output final draft
    )

def reset_workflow():
    """Reset everything to original state."""
    return (
        gr.update(interactive=True, value="Mock backend engineer JD"), 
        gr.update(interactive=True, value="Mock backend engineer resume"),
        gr.update(visible=True),      # show start button
        gr.update(visible=False),     # hide step 2
        gr.update(value={}),          # clear strategy
        gr.update(interactive=True, value=""), # clear tuning remarks
        gr.update(visible=True),      # show tuning button
        gr.update(visible=False),     # hide step 3
        gr.update(value=""),          # clear projects MD
        gr.update(interactive=True, choices=[], value=[]), # clear checkboxes
        gr.update(interactive=True, value=""), # clear project remarks
        gr.update(visible=True),      # show approval button
        gr.update(visible=False),     # hide step 4
        gr.update(value=""),          # clear step 4 jd
        gr.update(value=""),          # clear step 4 resume
        gr.update(value=""),          # clear step 4 final output
        {}                            # clear config
    )


# ==========================================
# 2. Build Gradio Interface
# ==========================================

custom_css = """
.scrollable-json {
    max-height: 250px;
    overflow-y: auto;
}
"""

# Add the soft theme to make the UI more modern
with gr.Blocks(title="AI Resume Tailor (Human-in-the-loop)") as demo:
    gr.Markdown("# 📄 AI Resume Tailor with Human-in-the-Loop")
    
    session_config = gr.State({})

    # [Step 1]
    with gr.Column(visible=True) as step_1_col:
        gr.Markdown("### Step 1: Input Job Description & Resume")
        # Display side-by-side to save space
        with gr.Row():
            # [UI UPDATE]: Added `max_lines=8`. Setting `max_lines` equal to `lines` forces the textbox to keep a fixed height but adds a vertical scrollbar when text overflows.
            jd_input = gr.Textbox(lines=8, max_lines=8, label="Job Description", value="Mock backend engineer JD")
            resume_input = gr.Textbox(lines=8, max_lines=8, label="Current Resume", value="Mock backend engineer resume")
        btn_start = gr.Button("Start Processing", variant="primary")

    # [Step 2]
    with gr.Column(visible=False) as step_2_col:
        gr.Markdown("---")
        gr.Markdown("### Step 2: Review Alignment Strategy")
        strategy_json = gr.JSON(label="Generated Alignment Strategy", elem_classes="scrollable-json")
        tuning_remarks = gr.Textbox(lines=3, max_lines=3, label="Your Remarks for Tuning (Optional)", placeholder="e.g., Focus more on Cloud deployment...")
        btn_submit_tuning = gr.Button("Submit & Continue", variant="primary")

    # [Step 3]
    with gr.Column(visible=False) as step_3_col:
        gr.Markdown("---")
        gr.Markdown("### Step 3: Curate Proposed Components")
        components_details_md = gr.Markdown()
        components_checkboxes = gr.CheckboxGroup(label="Select Capability Components to Include")
        component_remarks = gr.Textbox(lines=3, max_lines=3, label="Final Curation Remarks (Optional)", placeholder="e.g., Keep bullets concise, emphasize metrics.")
        btn_submit_approval = gr.Button("Approve Components & Generate Draft", variant="primary")

    # [Step 4] 
    with gr.Column(visible=False) as step_4_col:
        gr.Markdown("---")
        gr.Markdown("### 🎉 Step 4: Final Draft & Comparison Dashboard")
        # Three-column comparison panel to compare JD / Old / New side-by-side
        with gr.Row():
            with gr.Column(scale=1):
                # [UI UPDATE]: Added `max_lines=10` to the reference textboxes so they remain a fixed size but allow scrolling.
                jd_display = gr.Textbox(lines=10, max_lines=10, label="Reference: Target JD", interactive=False)
                resume_display = gr.Textbox(lines=10, max_lines=10, label="Reference: Old Resume", interactive=False)
            with gr.Column(scale=1):
                # [UI UPDATE]: Added `max_lines=23` to the final output to keep it aligned with the left column's height.
                final_output = gr.Textbox(lines=23, max_lines=23, label="✨ Optimized Resume Bullets", interactive=False)
        btn_reset = gr.Button("Start Over", variant="secondary")

    # ====================
    # Bind Events
    # ====================
    btn_start.click(
        fn=start_workflow,
        inputs=[jd_input, resume_input],
        outputs=[
            session_config, 
            jd_input, resume_input, btn_start, # Controls Step 1
            step_2_col, strategy_json          # Controls Step 2
        ]
    )
    
    btn_submit_tuning.click(
        fn=submit_tuning,
        inputs=[session_config, tuning_remarks],
        outputs=[
            tuning_remarks, btn_submit_tuning,                         # Controls Step 2
            step_3_col, components_details_md, components_checkboxes   # Controls Step 3
        ]
    )
    
    btn_submit_approval.click(
        fn=submit_approval,
        inputs=[session_config, components_checkboxes, component_remarks, jd_input, resume_input],
        outputs=[
            components_checkboxes, component_remarks, btn_submit_approval, # Controls Step 3
            step_4_col, jd_display, resume_display, final_output           # Controls Step 4
        ]
    )
    
    btn_reset.click(
        fn=reset_workflow,
        inputs=[],
        outputs=[
            jd_input, resume_input, btn_start,
            step_2_col, strategy_json, tuning_remarks, btn_submit_tuning,
            step_3_col, components_details_md, components_checkboxes, component_remarks, btn_submit_approval,
            step_4_col, jd_display, resume_display, final_output,
            session_config
        ]
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Default(), css=custom_css)