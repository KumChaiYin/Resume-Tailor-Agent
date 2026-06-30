## Project Structure

```text
├── data/         # Stores raw PDF files and past project documentation
├── storage/      # The vector database generated after data ingestion
├── ingest.py     # The data ingestion pipeline script
├── state.py      # Defines the memory state schema (AgentState)
├── nodes.py      # Declares all the core node logic and functions
├── graph.py      # Assembles the workflow (StateGraph, add_node, add_edge) and outputs the compiled graph
└── app.py        # Application entry point (Gradio UI, interaction logic, and graph invocation)
```