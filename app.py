import gradio as gr

def tailor_resume(jd_text, resume_text):
    return "Hello" #TODO

# Interface
demo = gr.Interface(
    fn=tailor_resume,
    inputs=[
        gr.Textbox(lines=10, label="Job Description (JD)", placeholder="Paste the Job Description here..."),
        gr.Textbox(lines=10, label="Current Resume", placeholder="Paste your current resume here...")
    ],
    outputs=gr.Markdown(label="Tailored Suggestions"),
    title="✂️ Resume Tailor",
    description="An AI agent help you tailor your resume based on JD."
)

if __name__ == "__main__":
    demo.launch()