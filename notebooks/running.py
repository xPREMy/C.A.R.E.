import os
import pandas as pd
from dotenv import load_dotenv
import pathway as pw
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.stdlib.indexing.bm25 import TantivyBM25Factory
from pathway.stdlib.indexing import BruteForceKnnFactory, HybridIndexFactory
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.servers import QASummaryRestServer

# =========================
#       CONFIGURATION
# =========================
# Load environment variables from .env file
load_dotenv()

# --- Path Configurations ---
# It's good practice to define paths relative to the script location.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) # Assumes script is in a subdirectory

# Input data configuration
DATA_CSV_PATH = os.path.join(ROOT_DIR, "Data", "raw", "synthea_patients.csv")

# Processed data output path
PATIENT_TEXT_PATH = os.path.join(ROOT_DIR, "Data", "processed", "patient_text")

# Local embedding model path
EMBEDDING_MODEL_PATH = os.path.join(ROOT_DIR, "models", "all-MiniLM-L6-v2")


# --- API Key Configurations ---
# Fetch API keys from environment variables
# This keeps your keys secure and out of the source code.
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Set environment variables for underlying libraries that might need them
os.environ.setdefault("HF_API_TOKEN", HF_API_TOKEN or "")
os.environ.setdefault("GOOGLE_API_KEY", GOOGLE_API_KEY or "")


# --- Model Configurations ---
# Upgraded to a powerful 70B parameter model.
# NOTE: This model requires a Hugging Face Pro subscription and a corresponding Pro API key.
LLM_MODEL = "huggingface/meta-llama/Meta-Llama-3-70B-Instruct"
EMBEDDER_DEVICE = "cpu" # Change to "cuda" if you have a GPU


# =========================
#       INGESTION STEP
# =========================

def ingest_synthea_csv(csv_file: str, output_folder: str):
    """
    Converts Synthea CSV patient data to individual patient text files.
    This function is idempotent and will not re-create files if they exist.
    """
    print("Starting data ingestion...")
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: The file {csv_file} was not found.")
        print("Please ensure your `synthea_patients.csv` is in the `Data/raw` directory.")
        return

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    for _, row in df.iterrows():
        patient_id = row["id"]
        filename = os.path.join(output_folder, f"{patient_id}.txt")

        # Skip if the file already exists to avoid redundant processing
        if os.path.exists(filename):
            continue

        # Create a concise, readable description for each patient
        patient_text = (
            f"Patient ID: {row['id']}\n"
            f"Name: {row['name']}\n"
            f"Gender: {row['gender']}\n"
            f"Birth Date: {row['birthDate']}\n"
            f"Conditions: {row.get('conditions', 'N/A')}\n"
            f"Medications: {row.get('medications', 'N/A')}\n"
        )

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(patient_text)
        except IOError as e:
            print(f"Could not write file for patient {patient_id}. Error: {e}")

    print(f"Ingestion check completed. Patient files are located in: {output_folder}")


# =========================
#       PATHWAY PIPELINE
# =========================

def run_pipeline():
    """
    Defines and runs the Pathway RAG pipeline.
    """
    print("Initializing Pathway RAG pipeline...")

    # Use pw.io.fs.read to monitor a directory for new files.
    # This creates a streaming data source.
    sources = [
        pw.io.fs.read(
            f"{PATIENT_TEXT_PATH}/*.txt",
            format="binary",
            with_metadata=True,
            mode="streaming"
        )
    ]

    # Define the components for processing and indexing the documents.
    # 1. Parser: To read the raw text from the files.
    parser = parsers.UnstructuredParser()

    # 2. Splitter: To break down large documents into smaller, manageable chunks.
    text_splitter = splitters.TokenCountSplitter(min_tokens=50, max_tokens=200)

    # 3. Embedder: To convert text chunks into numerical vectors for semantic search.
    # Using a local SentenceTransformer model.
    embedder = embedders.SentenceTransformerEmbedder(
        model=EMBEDDING_MODEL_PATH,
        device=EMBEDDER_DEVICE,
        batch_size=1
    )

    # 4. Retriever: A hybrid retriever combining two search methods:
    #    - TantivyBM25Factory: A sparse retriever (keyword-based). Good for specific terms.
    #    - BruteForceKnnFactory: A dense retriever (vector-based). Good for semantic similarity.
    index = HybridIndexFactory([
        TantivyBM25Factory(),
        BruteForceKnnFactory(embedder=embedder),
    ])

    # 5. Document Store: This component brings everything together.
    #    It takes the raw data sources, applies parsing and splitting,
    #    and builds the retrieval index.
    document_store = DocumentStore(
        docs=sources,
        parser=parser,
        splitter=text_splitter,
        retriever_factory=index
    )
    print("Document store and index created successfully.")

    # 6. Large Language Model (LLM): The model that will generate answers.
    #    Using LiteLLM to connect to a Hugging Face Inference API.
    #    Removed device and batch_size as they are not supported by the serverless API.
    llm = llms.LiteLLMChat(
        model=LLM_MODEL,
        api_key=HF_API_TOKEN # Use the Hugging Face API Token
    )

    # 7. QA Answerer: The final component that orchestrates the RAG process.
    #    It takes a user query, uses the document_store to find a relevant context,
    #    and then passes the query and context to the LLM to generate an answer.
    qa_answerer = BaseRAGQuestionAnswerer(
        llm=llm,
        indexer=document_store
    )

    # 8. Server: Expose the RAG pipeline as a REST API.
    server = QASummaryRestServer("0.0.0.0", 8000, qa_answerer)
    print("Starting Q&A REST server on http://0.0.0.0:8000 ...")
    server.run(with_cache=True)


if __name__ == "__main__":
    # Step 1: Run the data ingestion process.
    # This will prepare the text files needed by the Pathway pipeline.
    ingest_synthea_csv(DATA_CSV_PATH, PATIENT_TEXT_PATH)

    # Step 2: Start the Pathway pipeline and the API server.
    run_pipeline()

