import os
import re
from io import BytesIO
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from pathway.xpacks.llm import llms
import litellm
from src.prompt_template.prompt_template import PATIENT_EDUCATION_PROMPT_TEMPLATE

# --- Configuration ---
load_dotenv()
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
LLM_MODEL = "huggingface/meta-llama/Meta-Llama-3-70B-Instruct"

def generate_educational_pdf(treatment_plan: list) -> BytesIO:
    """
    Generates a patient educational PDF by explaining the treatment plan in simple terms using an LLM.

    Args:
        treatment_plan: A list of dictionaries, where each dictionary represents a medical condition and its details.

    Returns:
        An in-memory bytes buffer containing the generated PDF file.
    """
    print("[PDF Generator] Starting patient educational material generation...")
    
    # 1. Format the treatment plan data for the LLM prompt.
    plan_str = ""
    for item in treatment_plan:
        condition = item.get('condition', 'N/A')
        details_list = item.get('details', [])
        details = "\n  - ".join(details_list) if isinstance(details_list, list) else "No details."
        plan_str += f"- Condition: {condition}\n  - Details: {details}\n"

    # 2. Configure the LLM using the pathway object, but execute with a direct call for a clean response.
    llm = llms.LiteLLMChat(model=LLM_MODEL, api_key=HF_API_TOKEN)
    prompt = PATIENT_EDUCATION_PROMPT_TEMPLATE.format(treatment_plan=plan_str)
    
    print("[PDF Generator] Sending request to LLM for explanation...")
    explanation_text = ""
    try:
        # Use litellm.completion for a direct call, using config from the pathway object.
        # This respects the "do not remove pathway" constraint while getting a clean string.
        messages = [{"role": "user", "content": prompt}]
        response = litellm.completion(
            model=llm.model,
            messages=messages,
            api_key=HF_API_TOKEN
        )
        explanation_text = response.choices[0].message.content
        print("[PDF Generator] Received explanation from LLM.")
    except Exception as e:
        print(f"[PDF Generator] ERROR: Failed to get explanation from LLM: {e}")
        explanation_text = "There was an error generating the detailed explanation for your treatment plan. Please consult your doctor directly."

    # 3. Use reportlab to create a well-formatted PDF document.
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title
    story.append(Paragraph("Your Preliminary Treatment Plan Explained", styles['h1']))
    story.append(Spacer(1, 24))

    # **DEFINITIVE FIX**: Process the LLM text to create well-formatted paragraphs.
    # Split the response into blocks based on empty lines (the standard for paragraphs).
    blocks = re.split(r'\n\s*\n', explanation_text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # Convert markdown-style bold (**) to reportlab's <b> tag.
        block = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', block)
        
        # Convert single newlines within a block into <br/> tags for line breaks.
        block = block.replace('\n', '<br/>')
        
        story.append(Paragraph(block, styles['BodyText']))
        story.append(Spacer(1, 12)) # Add a small space after each paragraph

    doc.build(story)
    
    buffer.seek(0)
    print("[PDF Generator] PDF generation complete.")
    return buffer

