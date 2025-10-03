# MedCare AI Assistant 🩺

![Status: In Development](https://img.shields.io/badge/status-in_development-orange)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

This project is an advanced clinical decision support system designed to assist healthcare professionals by providing real-time, evidence-based insights. It leverages an **agentic AI architecture** to intelligently synthesize patient data with a continuously updated medical knowledge base.

The core challenge this project addresses is the overwhelming volume of new medical research published daily. MedCare AI provides a solution by creating an intelligent assistant that can reason, use specialized tools, and provide tailored suggestions based on the latest evidence and specific patient constraints.

---

## ⚙️ How It Works

The system operates on a sophisticated two-part architecture: a real-time data pipeline and an interactive agentic brain.

1.  **The Data Engine (Pathway)**: A continuously running process watches a specified folder for medical documents (PDFs, text files, etc.). When a new document is added, the pipeline automatically processes it, creates vector embeddings, and updates a live knowledge index. This ensures the agent's knowledge is always current without any manual re-indexing or downtime.

2.  **The Agentic Brain (LangChain)**: An interactive agent that receives a clinician's query. It uses a **ReAct (Reasoning and Acting)** framework to break down the query and decide which specialized tool to use. It can look up patient history, check for drug interactions, or query the live knowledge index to form a comprehensive, evidence-based answer.

![Architecture Diagram](https://i.imgur.com/your-architecture-diagram.png) 
*(A flowchart showing how a query goes to the agent, which then uses its tools—including the Pathway-powered RAG pipeline—to find an answer.)*

---

## ✨ Key Features

-   **🧠 Agentic Framework**: The system uses a multi-tool agent that can reason and decide whether to look up patient history, search medical research, or check for drug interactions, mimicking a clinician's workflow.
-   **🚀 Real-Time Knowledge Base**: Built on **Pathway**, the RAG pipeline automatically updates its knowledge by streaming data from a source folder, ensuring all suggestions are based on the absolute latest research.
-   **🛠️ Multi-Tool Capability**:
    -   `get_patient_history`: Retrieves patient-specific history and known constraints (e.g., allergies).
    -   `search_medical_research`: Queries the live vector index for the latest medical research.
    -   `check_drug_interactions`: Uses the live **NIH RxNav API** to check for potential drug-drug interactions in real-time.
-   **⚡ High-Speed LLM**: Powered by the **Groq API** with **Llama 3** for near-instantaneous reasoning and response generation, making it suitable for fast-paced clinical environments.
-   **🤖 Interactive & Robust**: Designed with a simple command-line interface for direct interaction and robust error handling.

---

## 🛠️ Tech Stack

-   **Data Pipeline**: [Pathway](https://github.com/pathwaycom/pathway)
-   **AI Orchestration**: [LangChain](https://www.langchain.com/)
-   **LLM**: Llama 3 via [Groq API](https://groq.com/)
-   **Embeddings**: OpenAI API
-   **External Data**: NIH RxNav API for drug interactions
-   **Core Language**: Python 3.10+