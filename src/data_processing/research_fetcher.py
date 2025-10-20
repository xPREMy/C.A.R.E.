import os
import re
import requests
import time

# --- Configuration ---
# Navigate three levels up from the current script's location (src/data_processing/research_fetcher.py) to reach the project root.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESEARCH_PAPER_PATH = os.path.join(ROOT_DIR, "Data", "processed", "research")

# --- Core Functions ---

def extract_conditions(patient_info: str) -> list:
    """
    Extracts a list of medical conditions from the patient information text.
    It specifically targets lines marked with '(disorder)' for accuracy.
    """
    conditions = []
    # Use regex to find the block of text between "Conditions:" and the next major heading
    match = re.search(r"Conditions:(.*?)(?:\n\n[A-Z][a-z]+:|$)", patient_info, re.DOTALL)
    if match:
        conditions_text = match.group(1)
        
        # Split the block into lines and process each one.
        potential_conditions = re.split(r'[\n;]', conditions_text)
        
        for item in potential_conditions:
            # Only keep items that are explicitly marked as disorders.
            if "(disorder)" in item:
                # Clean the string: remove the tag, dashes, and extra whitespace.
                clean_condition = item.replace("(disorder)", "").strip("- ").strip()
                if clean_condition:
                    conditions.append(clean_condition)
                    
    print(f"[Research Fetcher] Found conditions: {conditions}")
    return conditions

def _perform_search(query: str, condition: str) -> list:
    """Helper function to perform a single search with retries."""
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {'query': query, 'limit': 5, 'fields': 'title,abstract'}
    found_files = []

    for attempt in range(4):  # Retry up to 4 times
        try:
            response = requests.get(search_url, params=params, timeout=15)
            
            if response.status_code == 429:
                wait_time = 2 ** attempt
                print(f"[Research Fetcher] Rate limit hit for '{condition}'. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            results = response.json()
            
            if results and results.get("data"):
                for paper in results["data"]:
                    if paper and paper.get("abstract"):
                        title = paper.get("title", "Untitled Paper")
                        abstract = paper.get("abstract", "No abstract available.")
                        
                        safe_filename = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:60]
                        filepath = os.path.join(RESEARCH_PAPER_PATH, f"{safe_filename}.txt")
                        
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(f"Title: {title}\n\nAbstract: {abstract}")
                        found_files.append(filepath)
            
            return found_files # Return successfully found files

        except requests.exceptions.RequestException as e:
            print(f"[Research Fetcher] API request failed on attempt {attempt + 1} for '{condition}': {e}")
            if attempt < 3:
                time.sleep(2 ** attempt)
            else:
                print(f"[Research Fetcher] All retries failed for '{condition}'.")
    return [] # Return empty list if all retries fail


def fetch_and_save_papers(patient_info: str) -> list:
    """
    Fetches research papers for each unique condition. If a specific search fails,
    it attempts a broader fallback search.
    """
    conditions = extract_conditions(patient_info)
    unique_conditions = sorted(list(set(conditions)))
    created_files = []
    
    os.makedirs(RESEARCH_PAPER_PATH, exist_ok=True)

    for condition in unique_conditions:
        # **KEY CHANGE**: Implement a primary and fallback search strategy.
        
        # 1. Primary, specific search
        print(f"[Research Fetcher] Searching for: 'treatment and management of {condition}'")
        query_specific = f"treatment and management of {condition}"
        paper_files = _perform_search(query_specific, condition)
        
        # 2. Fallback, broad search if the primary search found nothing
        if not paper_files:
            print(f"[Research Fetcher] Fallback Search for: '{condition}'")
            query_broad = condition
            paper_files = _perform_search(query_broad, condition)

        if paper_files:
            print(f"[Research Fetcher] Found {len(paper_files)} paper(s) for '{condition}'.")
            created_files.extend(paper_files)
        else:
            print(f"[Research Fetcher] No papers with abstracts found for '{condition}' after all attempts.")
        
        time.sleep(1) # Polite delay between different conditions

    print(f"[Research Fetcher] Saved a total of {len(created_files)} new research files.")
    return created_files

def cleanup_papers(file_paths: list):
    """
    Removes the temporary research paper files created during a request.
    """
    print(f"[Research Fetcher] Cleaning up {len(file_paths)} file(s)...")
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as e:
            print(f"[Research Fetcher] Error cleaning up file {path}: {e}")

