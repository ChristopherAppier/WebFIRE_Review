import random
import requests
import json
import yaml

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
        raw_output, think_output = single_analysis(config, chunk_name, chunk_text, system_prompt)
        
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

        # Adding additional information into JSON
        payload = {
                    "audit_flag": audit_flag,
                    "chunk_name": chunk_name.stem,
                    "think_output": think_output,
                    "facility_name": None, #TODO add logic to pull from state report request
                    "review_start_time": None, #TODO add logic to pull from state report request
                    "review_end_time": None, #TODO add logic to pull from state report request
                    "llm_seed": None, #TODO add logic to pull from state report request
                    "prompt_name": None, #TODO add logic to pull from state report request
                    "RAG_requests": None, #TODO add logic to pull from state report request
                    "RAG_responses": None #TODO add logic to pull from state report request
                }

        for key, value in payload.items():
            json_output[key] = value

        # Storing the JSON output containing the analysis for that chunk
        save_path = paths['rev_json_dir'] / f"{chunk_name.stem}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2)

    print(f"\nLLM review complete") #TODO Add more stat tracking
    
    return

def single_analysis(config, chunk_name, chunk_text, sys_prompt):
    """Gives a system prompt to a chosen AI model to conduct an analysis on the chunk of data"""
    
    payload = {
        "model": config['llm']['review'],
        "stream": False,
        "think": True,
        "format": "json",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": chunk_text}
            ]
    }
    try:
        print(f"Reviewing {chunk_name.stem}")
        response = requests.post(config['llm_url'], json=payload, timeout=tuple(config['llm_timeout']))
        response.raise_for_status()
        response_data = response.json()
        print(f"Review complete\n")
        return response_data.get("message", {}).get("content", "No content field found."), response_data.get("message", {}).get("thinking", "No think field found.")

    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {e}\n(Make sure Ollama is running!)", None
    except Exception as e:
        return f"An unexpected error occurred: {e}", None

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

def json_add(json_dict, payload):
    """Adds additional information to the JSON dict"""
    
    json_dict['chunk_name'] = payload.get('chunk_name', None)
    json_dict['system_prompt'] = payload.get('system_prompt', None)
    json_dict['think_output'] = payload.get('think_output', None)
    json_dict['facility_name'] = payload.get('facility_name', None)
    json_dict['audit_flag'] = payload.get('audit_flag', None)
    json_dict['review_start_time'] = payload.get('review_start_time', None)
    json_dict['review_end_time'] = payload.get('review_end_time', None)
    json_dict['llm_seed'] = payload.get('llm_seed', None)
    json_dict['prompt_name'] = payload.get('prompt_name', None)
    json_dict['RAG requests'] = payload.get('RAG requests', None)
    json_dict['RAG responses'] = payload.get('RAG responses', None)

    return json_dict

def store_for_audit(config, paths):
    """Stores associated chunks and the output JSON in an auditing folder for audit at a later time based on issue flags and audit chance defined in settings.yml
    """
    
    print(f"\n Selecting all reviews with issued flagged and {config['audit_chance']}% of all other reviews for auditing")

    return

if __name__ == "__main__":
    from common import utilities

    # Load configuration
    config = utilities.load_config()

    # Builds the paths for the data directories
    paths = utilities.build_paths(config)

    analyze_chunks(config, paths)