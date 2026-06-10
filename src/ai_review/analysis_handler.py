import random
import requests
import json
import yaml
from pathlib import Path

def load_config():
    """Load configuration from settings.yaml."""
    project_root = Path(__file__).parent.parent.parent # Finds the root folder of the project based on this main.py file location
    config_path = project_root / "config" / "settings.yaml" # Sets the path for the settings.yaml file
    
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
    return


def single_analysis(model, model_url, chunk, sys_prompt):
    """Gives a system prompt to a chosen AI model to conduct an analysis on the chunk of data"""
    
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": chunk}
            ]
    }
    try:
        print(f"--- Sending prompt to {model} ---")
        response = requests.post(model_url, json=payload)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("message", {}).get("content", "No content field found.")

    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {e}\n(Make sure Ollama is running!)"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


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


def store_for_audit(json_output, chunk_name):
    """Stores a chunk and the output JSON in an auditing folder for audit at a later time"""
    
    return


def random_chance(percent_chance):
    """Returns a 0 or 1. 1 is chosen {percent_chance} % of the time, rounded to whole numbers"""
    
    return 1 if random.random() < (percent_chance / 100) else 0


def store_json(json_output, save_folder, file_name):
    save_folder = Path(save_folder)
    save_folder.mkdir(parents=True, exist_ok=True)
    
    save_path = save_folder / f"{file_name}.json"
    
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2)
    
    
    return


def analyze_chunks():
    
    folder = Path(__file__).parent.parent.parent / 'data' / 'pdfs' / 'chunks'
    config = load_config()
    save_folder = folder.parent / "JSONs"
    
    # Loading settings based on settings.yaml file
    system_prompt = config['prompts']['system']['analyze']
    ai_model = config['ai_models']['analyze']
    audit_chance = config['audit_chance']
    model_url = config['ai_urls']['analyze']
    
    #Looping through all pdf files
    for chunk_name in folder.iterdir():
        
        # Skips the file if it isn't a text file
        if chunk_name.suffix != ".txt":
            continue
        
        # Load text from chunk_name.txt
        with open(chunk_name,"r") as f:
            chunk_text = f.read()
        
        # Get the AI's response as a string
        raw_output = single_analysis(ai_model, model_url, chunk_text, system_prompt)
        
        # Trying to load the string as a JSON with error handling
        try:
            json_output = json_check(raw_output)
        except ValueError as e:
            print(f"Skipping {chunk_name} — {e}")
            continue

        # Adding the chunk name to the JSON output for traceability
        json_output['chunk_name'] = chunk_name.stem
        
        # If an issue is flagged - send the chunk analyzed and JSON to the auditor folder for review
        if json_output.get('issue') == 1:
            store_for_audit(json_output, chunk_name)
            
        # If no issue is flagged, there is a X% chance (defined in settings.yaml) to set aside in auditor folder for review
        elif random.random() < (audit_chance / 100):
            store_for_audit(json_output, chunk_name)
    
        # Storing the JSON output containing the analysis for that chunk
        store_json(json_output, save_folder, chunk_name.stem)    
    
    return


if __name__ == "__main__":
    analyze_chunks()