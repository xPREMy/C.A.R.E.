# 🩺 C.A.R.E: Clinical Assistant for Research and Evidence

**C.A.R.E.** (Clinical Assistant for Research and Evidence) is a prototype **Clinical Decision Support System (CDSS)** that combines **Retrieval-Augmented Generation (RAG)** with real-time medical research integration.  

It analyzes patient data, fetches relevant studies from the **Semantic Scholar API**, and generates two intelligent outputs:

1. 🩹 A **Preliminary Treatment Plan** for clinicians.  
2. 📘 A **Patient-Friendly Educational PDF** that explains the treatment plan in simple, empathetic language.

---

## 🧠 1. Project Overview

C.A.R.E. is designed to bridge the gap between **clinical data** and **medical research**.  
By leveraging **RAG pipelines**, it can automatically connect patient information with the latest peer-reviewed evidence to generate a structured, transparent, and human-readable treatment plan.

### **Key Features**
- 🧩 Real-time research retrieval using the **Semantic Scholar API**
- 🧠 Intelligent reasoning powered by **LLMs** (e.g., Meta Llama 3 70B)
- ⚙️ Automated **Pathway RAG pipeline** for hybrid (BM25 + Vector) document search
- 💬 **FastAPI web interface** for clinicians
- 📄 **ReportLab PDF generation** for patient-friendly explanations

---

## 🏗️ 2. System Architecture

C.A.R.E. follows a **microservice-based architecture**, decoupling the user interface from the backend data processing pipeline.

---

### 🧠 **A. Pathway RAG Pipeline (`pipeline.py`)**
**Tech Stack:** `pathway`  
**Runs on:** `http://localhost:8001`  

#### **Role:**
- Acts as the backend reasoning engine.
- Continuously monitors the directories:
  - `Data/processed/patient_text/`
  - `Data/processed/research/`
- Parses and indexes all new `.txt` documents automatically.
- Uses **BM25 + Vector Embeddings** for hybrid information retrieval.
- Exposes an API endpoint `/v2/answer` for structured question answering.

---

### 💻 **B. FastAPI Web Server (`api_server.py`)**
**Tech Stack:** `FastAPI`, `Jinja2`  
**Runs on:** `http://localhost:8000`

#### **Role:**
- Serves as the user-facing orchestration layer.
- Fetches new research papers dynamically through the **Semantic Scholar API**.
- Waits for indexing (~20 seconds), then queries the RAG server.
- Displays structured treatment recommendations.
- Generates downloadable **patient education PDFs**.

---

### 🧱 **Directory Structure**
C.A.R.E/
├── api_server.py
├── src/
│ ├── agent/
│ │ └── pipeline.py
│ ├── data_processing/
│ │ ├── research_fetcher.py
│ │ └── patient_educational_material.py
├── Data/
│ └── processed/
│ ├── patient_text/
│ │ └── patient_123.txt
│ └── research/
├── templates/
│ └── index.html
├── requirements.txt
├── .env
└── README.md 

---

## 💾 3. Input & Output Examples

### **🩺 Input Example**
#### File: `Data/processed/patient_text/patient_123.txt`
Patient ID: 123
Age: 54
Condition: Acute Viral Pharyngitis
Current Medications: Paracetamol
Symptoms: Fever, sore throat, fatigue
Notes: No chronic conditions.

yaml
Copy code

---

### **⚙️ System Flow**
1. The **FastAPI web UI** loads a dropdown of available patient files.
2. The user selects a file and clicks **“Generate Treatment Plan.”**
3. The **research_fetcher** module queries Semantic Scholar for latest papers.
4. Research files are stored and automatically indexed by the **Pathway RAG server**.
5. After indexing (~20s delay), the system queries `/v2/answer` for treatment suggestions.
6. A structured treatment plan appears in the UI.
7. The user can **download a patient-friendly PDF** summarizing it.

---

### **📊 Output Example (Displayed on Web UI)**
| Condition | Suggested Treatment | Supporting Evidence |
|------------|---------------------|----------------------|
| Acute Viral Pharyngitis | Symptomatic treatment with hydration, rest, and antiviral if severe | Semantic Scholar Paper ID: 112345 |

---

### **📄 Output Example (Generated PDF)**
**Title:** *Your Preliminary Treatment Plan Explained*  
**Contents:**
- Overview of the condition in simple language  
- Suggested treatments and why they help  
- Encouraging, compassionate guidance  

---

## ⚙️ 4. Steps to Run the Project

### **1. Prerequisites**
Ensure you have:
- Python **3.10+**
- `pip` and `virtualenv`
- A **Hugging Face API Token**
- Internet connection (for Semantic Scholar API access)

---


## 🧩 Table of Contents
- [1. Clone the Repository](#1-clone-the-repository)
- [2. Create and Activate Virtual Environment](#2-create-and-activate-virtual-environment)
- [3. Install Dependencies](#3-install-dependencies)
- [4. Set Up Environment Variables](#4-set-up-environment-variables)
- [5. Prepare Data Directories](#5-prepare-data-directories)
- [6. Start the RAG Pipeline Server](#6-start-the-rag-pipeline-server)
- [7. Start the FastAPI Web Server](#7-start-the-fastapi-web-server)
- [8. Example Run (Full Command Recap)](#8-example-run-full-command-recap)

---

## 1. Clone the Repository
git clone https://github.com/<your-username>/C.A.R.E.git
cd C.A.R.E

text

---

## 2. Create and Activate Virtual Environment
python -m venv venv
source venv/bin/activate # On Linux/Mac
venv\Scripts\activate # On Windows

text

---

## 3. Install Dependencies
pip install -r requirements.txt

text

💡 If you don’t have a `requirements.txt` file, create one with the following contents:
fastapi[all]
uvicorn
requests
pathway-xpacks
litellm
python-dotenv
reportlab

text

---

## 4. Set Up Environment Variables
Create a file named `.env` in the project root and add:
HF_TOKEN=your_huggingface_token_here
OPENAI_API_KEY=your_openai_api_key_here

text

---

## 5. Prepare Data Directories
mkdir -p Data/processed/patient_text
mkdir -p Data/processed/research

text

Add at least one sample file:
echo "Condition: Flu" > Data/processed/patient_text/sample.txt

text

---

## 6. Start the RAG Pipeline Server
In one terminal:
python src/agent/pipeline.py

text
Wait for logs confirming the server is running at:
http://localhost:8001

text

---

## 7. Start the FastAPI Web Server
In another terminal:
python api_server.py

text
Access the web interface at:
http://localhost:8000

text

---

## 8. Example Run (Full Command Recap)
Clone repo
git clone https://github.com/<your-username>/C.A.R.E.git
cd C.A.R.E

Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Prepare data
mkdir -p Data/processed/patient_text Data/processed/research
echo "Condition: Flu" > Data/processed/patient_text/sample.txt

Run RAG pipeline
python src/agent/pipeline.py

Run FastAPI server (in another terminal)
python api_server.py

text

Access your web app at: [http://localhost:8000](http://localhost:8000)

---

## 🧠 Notes
- Ensure your Hugging Face and OpenAI API keys are valid.
- The `pipeline.py` handles all RAG-based processing.
- The FastAPI interface allows interactive data exploration.

---

## 🛠️ Tech Stack
- FastAPI — Web framework
- Uvicorn — ASGI server
- LiteLLM — Lightweight LLM interface
- Pathway X-Packs — Data processing
- ReportLab — PDF generation
- Python Dotenv — Env management

---
This version is fully GitHub-compatible (renders headers, links, and bash formatting properly).
Would you like it enhanced with badges (Python version, build passing, license, last update)?

Related
Convert the search results into a single copyable text block
Extract only the actionable instructions for creating a Markdown TOC
Create a ready-to-paste README.md with TOC and examples
List VS Code and CLI commands to generate a TOC
Show GitHub-flavored header anchor rules and examples
