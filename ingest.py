import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.ollama import OllamaEmbedding

# 1. Local model settings
load_dotenv()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

def build_index():
    print("Starting Data Ingestion (Local Ollama Stack)...")

    # 2. Configure embedding model
    # Embeddings create the vectors used by the index.
    Settings.embed_model = OllamaEmbedding(
        model_name=OLLAMA_EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    # 3. Load Data
    if not os.path.exists("./data"):
        os.makedirs("./data")
        print("The 'data' folder was missing. I created it. Please put your files in ./data and run again.")
        return

    documents = SimpleDirectoryReader("./data").load_data()
    
    if not documents:
        print("No documents found in /data. Add some .md or .pdf files first!")
        return

    print(f"Loaded {len(documents)} documents from /data")
    print(f"Using Ollama embedding model: {OLLAMA_EMBED_MODEL}")

    # 4. Create Index
    index = VectorStoreIndex.from_documents(documents)

    # 5. Save to Disk
    index.storage_context.persist(persist_dir="./storage")
    print("Index built and saved to ./storage folder!")

if __name__ == "__main__":
    build_index()
