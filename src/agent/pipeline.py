import os
import sys

# --- Path Correction ---
# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up two levels to the project root (C.A.R.E.)
ROOT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
# Add the project root to the Python path
sys.path.append(ROOT_DIR)

import pandas as pd
from dotenv import load_dotenv
import pathway as pw
from pathway.xpacks.llm import embedders, llms, parsers, splitters
from pathway.stdlib.indexing.bm25 import TantivyBM25Factory
from pathway.stdlib.indexing import BruteForceKnnFactory, HybridIndexFactory
from pathway.xpacks.llm.document_store import DocumentStore
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.servers import QASummaryRestServer
# This import will now work correctly
from src.prompt_template.prompt_template import RAG_PROMPT_TEMPLATE

# =========================
#       CONFIGURATION
# =========================
load_dotenv()

# --- Path Configurations ---
# Input data configuration
DATA_CSV_PATH = os.path.join(ROOT_DIR, "Data", "raw", "synthea_patients.csv")

# Processed data output paths
PATIENT_TEXT_PATH = os.path.join(ROOT_DIR, "Data", "processed", "patient_text")
RESEARCH_PAPER_PATH = os.path.join(ROOT_DIR, "Data", "processed", "research")

# Local embedding model path
EMBEDDING_MODEL_PATH = os.path.join(ROOT_DIR, "models", "all-MiniLM-L6-v2")


# --- API Key & Model Configurations ---
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
os.environ.setdefault("HF_API_TOKEN", HF_API_TOKEN or "")

LLM_MODEL = "huggingface/meta-llama/Meta-Llama-3-70B-Instruct"
EMBEDDER_DEVICE = "cpu"


# =========================
#       PATHWAY PIPELINE
# =========================

def run_pipeline():
    """
    Defines and runs the Pathway RAG pipeline.
    """
    print("Initializing Pathway RAG pipeline...")

    sources = [
        pw.io.fs.read(
            f"{PATIENT_TEXT_PATH}/*.txt",
            format="binary",
            with_metadata=True,
            mode="streaming"
        ),
        pw.io.fs.read(
            f"{RESEARCH_PAPER_PATH}/*.txt",
            format="binary",
            with_metadata=True,
            mode="streaming"
        )
    ]

    parser = parsers.UnstructuredParser()
    text_splitter = splitters.TokenCountSplitter(min_tokens=50, max_tokens=200)
    embedder = embedders.SentenceTransformerEmbedder(
        model=EMBEDDING_MODEL_PATH,
        device=EMBEDDER_DEVICE,
        batch_size=1
    )
    index = HybridIndexFactory([
        TantivyBM25Factory(),
        BruteForceKnnFactory(embedder=embedder),
    ])
    document_store = DocumentStore(
        docs=sources,
        parser=parser,
        splitter=text_splitter,
        retriever_factory=index
    )
    print("Document store and index created successfully.")

    llm = llms.LiteLLMChat(
        model=LLM_MODEL,
        api_key=HF_API_TOKEN
    )

    qa_answerer = BaseRAGQuestionAnswerer(
        llm=llm,
        indexer=document_store,
        prompt_template=RAG_PROMPT_TEMPLATE
    )

    server_port = 8001
    server = QASummaryRestServer("0.0.0.0", server_port, qa_answerer)
    print(f"Starting Q&A REST server on http://0.0.0.0:{server_port} ...")
    server.run(with_cache=True)


if __name__ == "__main__":
    os.makedirs(RESEARCH_PAPER_PATH, exist_ok=True)
    run_pipeline()

