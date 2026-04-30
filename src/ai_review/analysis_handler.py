import random
import requests
import json

def single_analysis(model, model_url, chunk, sys_prompt):
    """Gives a system prompt to a chosen AI model to conduct an analysis on the chunk of data"""
    
    # The data payload
    # It allows us to define the 'system' instructions separately from the 'user' task.
    payload = {
       "model": model,
       "stream": False,
       "messages": [
           {"role": "system", "content": sys_prompt},
           {"role": "user", "content": chunk}
           ]
            }
    try:
        print(f"--- Sending prompt to {model} ---")
        
        # Sending the POST request
        response = requests.post(model_url, json=payload)
        
        # Check if the request was successful (HTTP 200)
        response.raise_for_status()
        
        # Parse the JSON response from Ollama
        response_data = response.json()
        
        # Print the JSON file for debugging
        #print(json.dumps(response_data, indent=4))
        
        # The actual text response is in the 'response' field
        return response_data.get("message", {}).get("content", "No content field found.")

    # Error handling                              #TODO this needs to return in JSON format
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {e}\n(Make sure Ollama is running!)"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    
    return

def store_for_audit(json_output, chunk_name):
    """Stores a chunk and the output JSON in an auditing folder for audit at a later time"""
    
    return


def json_check(json_output):
    """Checks if a valid JSON format is present"""
    
    return

def random_chance(percent_chance):
    """Returns a 0 or 1. 1 is chosen {percent_chance} % of the time, rounded to whole numbers"""
    
    # Choose a random number
    random_number = random.randint(1,100)
    
    # Create a list of numbers the size of {percent_chance}
    num_list = []
    i = 1
    while i < int(percent_chance):
        num_list[i] = i
        i+=1
        
    # Will return 1 if random number is chosen in list, 0 otherwise
    if random_number in num_list:
        in_list = 1
    else:
        in_list = 0
    
    return in_list

def store_json(json_output):
    
    
    return

def analyze_chunks():
    
    folder = [] #TODO NEEDS SET
    config = [] #TODO NEEDS SET
    
    # Loading settings based on settings.yaml file
    system_prompt = config['prompts']['system']['analyze'] #TODO ADD AI PROMPT INFO TO SETTINGS.YAML
    ai_model = config['ai_models']['analyze'] #TODO ADD AI MODEL INFO TO SETTINGS.YAML
    audit_chance = config['audit_chance'] #TODO ADD AI MODEL INFO TO SETTINGS.YAML
    model_url = config['ai_urls']['analyze'] #TODO ADD AI MODEL INFO TO SETTINGS.YAML
    
    #Looping through all pdf files
    for chunk_name in folder: #TODO NEEDS CORRECTED 
        
        # Send out file for analysis
        json_output = single_analysis(ai_model, model_url, chunk_name, system_prompt)
        
        # Check that the model returned valid JSON formatting and attempt to fix
        json_check(json_output) #TODO NEED ERROR HANDLING - WHAT IF IT IS NOT VALID? TRY TO FIX? ASK TO REDO?
        
        # If an issue is flagged - send the chunk analyzed and JSON to the auditor folder for review
        if json_output['issue'] == 1:
            store_for_audit(json_output, chunk_name)
            
        # If no issue is flagged, there is a X% chance (defined in settings.yaml) to set aside in auditor folder for review
        elif json_output['issue'] == 0 and random_chance(audit_chance) == 1:
            store_for_audit(json_output, chunk_name)
    
        # Storing the JSON output containing the analysis for that chunk
        store_json(json_output)    
    
    
    return