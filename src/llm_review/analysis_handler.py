import random
import json
import re
import csv
from datetime import datetime, timezone
import yaml
import openai
from openai import OpenAI

def analyze_chunks(config, paths):

    print(f"\n{'*' * 50}\n\nAnalyzing text chunks using: {config['llm']['review']}\n")

    #Looping through all chunks
    for chunk_name in paths['chunk_dir'].iterdir():
        
        # Skips the file if it isn't a text file
        if chunk_name.suffix != ".txt":
            continue

        # Loads the system prompt based on the file type/name being reviewed
        system_prompt = load_system_prompt(paths, chunk_name)
        
        # Load text from chunk_name.txt
        with open(chunk_name,"r") as f:
            chunk_text = f.read()
        
        # Get the AI's response as a string
        raw_output, think_output, t_start, t_end = single_analysis(config, chunk_name, chunk_text, system_prompt)
        
        # Trying to load the response string as a JSON with error handling
        try:
            json_output = json_check(raw_output)
        except ValueError as e:
            print(f"Skipping {chunk_name}: {e}")
            continue

        # Determining if audit flag triggers
        if json_output['issue_flag'] == True or random.random() < (config['audit_chance'] / 100):
            audit_flag = True
        else:
            audit_flag = False

        # Pulling information from the report table csv to the JSON
        file_name = find_file_name(paths, chunk_name)
        file_info = pull_file_info(paths, file_name)

        # Calculating total review time in seconds
        t_total = int((datetime.fromisoformat(t_end) - datetime.fromisoformat(t_start)).total_seconds())

        # Adding additional information into JSON
        payload = {
                    "audit_flag": audit_flag,
                    "file_name": file_name,
                    "chunk_name": chunk_name.stem,
                    "organization": file_info.get("Organization"),
                    "facility": file_info.get("Facility"),               
                    "city": file_info.get("City"),
                    "state": file_info.get("State"),
                    "report_type": file_info.get("Report Type"),
                    "report_subtype": file_info.get("Report Sub Type"),
                    "submission_date": file_info.get("Submission Date"),
                    "review_start_time": t_start,
                    "review_end_time": t_end,
                    "total_review_time": t_total,
                    "think_output": think_output,
                    "llm_seed": None,
                    "prompt_name": None,
        }

        for key, value in payload.items():
            json_output[key] = value

        # Storing the JSON output containing the analysis for that chunk
        save_path = paths['review_dir'] / f"{chunk_name.stem}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2)

    print(f"LLM review complete") #TODO Add more stat tracking
    
    return

def single_analysis(config, chunk_name, chunk_text, sys_prompt):
    """Gives a system prompt to a chosen AI model to conduct an analysis on the chunk of data"""

    t_start = datetime.now(timezone.utc).isoformat()

    try:    
        print(f"Reviewing {chunk_name.stem}")

        # Setting up the OpenAI client with the provided configuration
        client = OpenAI(
        api_key=config['llm_api_key'],
        base_url=config['llm_url'],
        timeout=config['llm_timeout'],
        max_retries=config['llm_retries']
    )
        # Making the request to the OpenAI API with the specified model, system prompt, and chunk text
        response = client.responses.create(model=config['llm']['review'],instructions=sys_prompt, input=chunk_text)
        t_end = datetime.now(timezone.utc).isoformat()
        print(f"Review complete\n")

        # Capturing the "think" output from the response if it exists, otherwise setting it to None
        think_output = "\n".join(
            part.text
            for item in (response.output or [])
            if getattr(item, "type", None) == "reasoning"
            for part in (getattr(item, "summary", None) or [])
            if getattr(part, "text", None)
        ) or None

        return response.output_text, think_output, t_start, t_end

    except openai.APIConnectionError as e:
        t_end = datetime.now(timezone.utc).isoformat()
        return f"The server could not be reached: {e.__cause__}", None, t_start, t_end
    except openai.RateLimitError as e:
        t_end = datetime.now(timezone.utc).isoformat()
        return f"A 429 status code was received; we should back off a bit.", None, t_start, t_end
    except openai.APIStatusError as e:
        t_end = datetime.now(timezone.utc).isoformat()
        return f"Another non-200-range status code was received: {e.status_code}, {e.response}", None, t_start, t_end   

def load_system_prompt(paths, chunk_name):
    """Loads the appropriate system prompt based on the file type/name being reviewed (currently just uses a single default prompt for MVP implementation)"""

    # Load the list of prompts available from the prompt_bank.yml
    prompt_bank_dir = paths['config_dir'] / "prompt_bank.yml"
    
    with open(prompt_bank_dir, "r", encoding="utf-8") as f:
        prompt_bank = yaml.safe_load(f)

    # Selecting the appropriate prompt based on the file type/name (currently all use one default)
    prompt = prompt_bank['review']['generic']

    return prompt

def json_check(raw_string):
    """Strips markdown fences if present, then parses and returns a JSON dict.
    Raises ValueError if the string cannot be parsed as valid JSON."""
    
    cleaned = raw_string.strip()
    
    # Strip markdown fences if present
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```")
        cleaned = cleaned.removesuffix("```").strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON: {e}\nRaw output:\n{raw_string}")

def store_for_audit(config, paths):
    """Stores associated chunks and the output JSON in an auditing folder for audit at a later time based on issue flags and audit chance defined in settings.yml
    """
    
    print(f"\n Selecting all reviews with issued flagged and {config['audit_chance']}% of all other reviews for auditing")

    # PLACEHOLDER FUNCTION - ADD FUNCTIONALITY

    return

def find_file_name(paths, chunk_name):
    """Finds the original file name for a chunk using Document List in report_table.csv."""

    chunk_base = re.sub(r"_chunk_\d+$", "", chunk_name.stem).lower()
    table_path = paths['http_dir'] / "report_table.csv"

    if not table_path.exists():
        return chunk_base

    with open(table_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for doc_name in (row.get("Document List") or "").split("|"):
                doc_name = doc_name.strip()
                if not doc_name:
                    continue

                doc_stem = doc_name.rsplit(".", 1)[0].lower()
                if doc_stem == chunk_base:
                    return doc_name

    return chunk_base

def pull_file_info(paths, file_name):
    """Finds the row for file_name in report_table.csv and returns key file metadata."""

    table_path = paths['http_dir'] / "report_table.csv"
    if not table_path.exists():
        return {}

    target = file_name.lower().strip()

    with open(table_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_names = [name.strip() for name in (row.get("Document List") or "").split("|") if name.strip()]

            for doc_name in doc_names:
                if doc_name.lower() == target:
                    return {
                        "Organization": row.get("Organization"),
                        "Facility": row.get("Facility"),
                        "City": row.get("City"),
                        "State": row.get("State"),
                        "Report Type": row.get("Report Type"),
                        "Report Sub Type": row.get("Report Sub Type"),
                        "Submission Date": row.get("Submission Date"),
                    }

    return {}

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    analyze_chunks(config, paths)