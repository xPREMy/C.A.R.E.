import os
import time
import requests
import ast
import re
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from src.data_processing import research_fetcher
# Corrected function name to match the provided file
from src.agent.patient_educational_material import generate_educational_pdf

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = SCRIPT_DIR
PATIENT_TEXT_PATH = os.path.join(ROOT_DIR, "Data", "processed", "patient_text")
RESEARCH_PAPER_PATH = os.path.join(ROOT_DIR, "Data", "processed", "research")
# New temporary directory for plan data
TMP_DIR = os.path.join(ROOT_DIR, "tmp") 
RAG_PIPELINE_URL = "http://localhost:8001/v2/answer"

# --- FastAPI App Initialization ---
app = FastAPI()
os.makedirs(os.path.join(SCRIPT_DIR, "templates"), exist_ok=True)
# Ensure the temporary directory exists
os.makedirs(TMP_DIR, exist_ok=True)
templates = Jinja2Templates(directory=os.path.join(SCRIPT_DIR, "templates"))

# --- Helper Functions ---
def get_patient_list():
    """Reads the processed patient text files to get a list of patient IDs."""
    if not os.path.exists(PATIENT_TEXT_PATH):
        return []
    patients = [f.replace(".txt", "") for f in os.listdir(PATIENT_TEXT_PATH) if f.endswith(".txt")]
    return sorted(patients)

def parse_treatment_plan(plan_text: str):
    """
    Parses a string that is either markdown-like or a string representation
    of a Python list into a structured list of dictionaries.
    """
    if not isinstance(plan_text, str) or "No plan was generated" in plan_text or "Failed to generate" in plan_text:
        return []

    try:
        parsed_data = ast.literal_eval(plan_text)
        if isinstance(parsed_data, list) and all(isinstance(item, dict) for item in parsed_data):
            print("[API Server] Successfully parsed string response with ast.literal_eval.")
            return parsed_data
    except (ValueError, SyntaxError):
        print("[API Server] ast.literal_eval failed, falling back to markdown parser.")

    print("[API Server] Using markdown parser.")
    sections = []
    parts = plan_text.split('**')
    i = 1
    while i < len(parts) - 1:
        title = parts[i].strip().replace(':', '')
        if "Preliminary Treatment Plan" in title or not title:
            i += 2
            continue
        content_block = parts[i+1]
        details = [detail.strip() for detail in content_block.strip().split('*') if detail.strip()]
        if title and details:
            sections.append({"condition": title, "details": details})
        i += 2
    return sections

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main page with a list of patients."""
    return templates.TemplateResponse("index.html", {"request": request, "patients": get_patient_list()})

@app.post("/generate-plan", response_class=HTMLResponse)
async def generate_treatment_plan(request: Request, patient_id: str = Form(...)):
    """
    Handles form submission, fetches research, queries the RAG server,
    parses the result, saves it to a temporary file, and cleans up research files.
    """
    patient_file_path = os.path.join(PATIENT_TEXT_PATH, f"{patient_id}.txt")
    with open(patient_file_path, "r", encoding="utf-8") as f:
        patient_info_text = f.read()

    created_files = []
    treatment_plan_structured = []
    error_message = None
    plan_file_path = None # Initialize plan file path

    try:
        created_files = research_fetcher.fetch_and_save_papers(patient_info_text)
        wait_time = 23
        print(f"[API Server] Waiting for {wait_time} seconds for RAG server to index new files...")
        time.sleep(wait_time)

        conditions_raw = research_fetcher.extract_conditions(patient_info_text)
        conditions_list = conditions_raw if isinstance(conditions_raw, list) else re.split(r'[,;]', str(conditions_raw))
        unique_conditions = sorted(list(set([cond.strip() for cond in conditions_list if cond.strip()])))
        cleaned_conditions = [re.sub(r'[^a-zA-Z\s]', '', cond).strip() for cond in unique_conditions]
        final_conditions = [re.sub(r'\s+', ' ', cond) for cond in cleaned_conditions if cond]
        prompt = " ".join(final_conditions) if final_conditions else "No conditions listed"
        
        print(f"[API Server] Sending sanitized, keyword-only prompt to RAG pipeline: \"{prompt}\"")

        response = requests.post(
            RAG_PIPELINE_URL,
            json={"prompt": prompt},
            timeout=180
        )
        response.raise_for_status()
        
        rag_response = response.json().get("response")

        if isinstance(rag_response, list):
            print("[API Server] RAG response is a valid list.")
            treatment_plan_structured = rag_response
        elif isinstance(rag_response, str):
            print("[API Server] RAG response is a string, attempting to parse.")
            treatment_plan_structured = parse_treatment_plan(rag_response)
            
        # If a plan was successfully generated, save it to a temporary file.
        if treatment_plan_structured:
            plan_file_path = os.path.join(TMP_DIR, f"{patient_id}_{int(time.time())}_plan.json")
            with open(plan_file_path, "w") as f:
                json.dump(treatment_plan_structured, f)
            print(f"[API Server] Treatment plan saved to temporary file: {plan_file_path}")


    except requests.exceptions.RequestException as e:
        error_message = f"Could not connect to the RAG Pipeline Server. Is it running? Error: {e}"
        print(f"[API Server] ERROR: {error_message}")
    
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        print(f"[API Server] UNEXPECTED ERROR: {error_message}")

    finally:
        if created_files:
            print(f"[API Server] Cleaning up {len(created_files)} temporary research file(s)...")
            research_fetcher.cleanup_papers(created_files)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "patients": get_patient_list(),
        "selected_patient_id": patient_id,
        "patient_info": patient_info_text,
        "treatment_plan": treatment_plan_structured,
        "plan_file_path": plan_file_path, # Pass the file path to the template
        "error": error_message,
    })

@app.post("/generate-education-material", response_class=StreamingResponse)
async def generate_education_material_pdf(request: Request, plan_file_path: str = Form(...)):
    """
    Receives the path to a temporary file containing the treatment plan,
    reads it, generates a PDF, and streams it back for download.
    """
    try:
        # Check if the file path is within the allowed temporary directory to prevent path traversal attacks.
        if not os.path.abspath(plan_file_path).startswith(os.path.abspath(TMP_DIR)):
            raise ValueError("Invalid file path provided.")

        print(f"[API Server] Reading treatment plan from: {plan_file_path}")
        with open(plan_file_path, "r") as f:
            plan_data = json.load(f)

        if not isinstance(plan_data, list):
             raise ValueError("Data in plan file is not a list.")

        pdf_buffer = generate_educational_pdf(plan_data)
        
        headers = {
            'Content-Disposition': 'attachment; filename="patient_education_material.pdf"'
        }
        return StreamingResponse(pdf_buffer, media_type='application/pdf', headers=headers)

    except (ValueError, json.JSONDecodeError) as e:
        print(f"[API Server] ERROR generating PDF: {e}")
        return HTMLResponse(content=f"<h1>Error processing data for PDF generation: {e}</h1>", status_code=500)
    except FileNotFoundError:
        print(f"[API Server] ERROR: Plan file not found at {plan_file_path}")
        return HTMLResponse(content=f"<h1>Error: Plan file not found. Please generate the plan again.</h1>", status_code=404)
    except Exception as e:
        print(f"[API Server] UNEXPECTED ERROR during PDF generation: {e}")
        return HTMLResponse(content=f"<h1>An unexpected error occurred during PDF generation: {e}</h1>", status_code=500)
    finally:
        # Clean up the temporary plan file after use.
        if plan_file_path and os.path.exists(plan_file_path):
            try:
                os.remove(plan_file_path)
                print(f"[API Server] Cleaned up temporary plan file: {plan_file_path}")
            except Exception as e:
                 print(f"[API Server] ERROR cleaning up plan file {plan_file_path}: {e}")

