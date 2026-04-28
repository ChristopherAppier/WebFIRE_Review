#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 14:03:42 2026

@author: chris
"""

import requests
import json

def call_ollama(user_prompt, system_prompt, model):
    """
    Sends a prompt to a local Ollama instance and returns the response.
    
    Args:
        prompt (str): The text you want to send to the AI.
        model (str): The name of the model you have downloaded in Ollama.
                     (e.g., 'llama3', 'mistral', 'phi3')
    
    Returns:
        str: The AI's response text.
    """
    # The local URL where Ollama is running
    url = "http://100.67.89.6:11434/api/chat"
    
    # The data payload
    # It allows us to define the 'system' instructions separately from the 'user' task.
    payload = {
       "model": model,
       "stream": False,
       "messages": [
           {"role": "system", "content": system_prompt},
           {"role": "user", "content": user_prompt}
           ]
            }
    try:
        print(f"--- Sending prompt to {model} ---")
        
        # Sending the POST request
        response = requests.post(url, json=payload)
        
        # Check if the request was successful (HTTP 200)
        response.raise_for_status()
        
        # Parse the JSON response from Ollama
        response_data = response.json()
        
        # Print the JSON file for debugging
        #print(json.dumps(response_data, indent=4))
        
        # The actual text response is in the 'response' field
        return response_data.get("message", {}).get("content", "No content field found.")

    # Error handling
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {e}\n(Make sure Ollama is running!)"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    # 1. Define your input and choose a model
    user_input = "What is the color of the sky at different times of the day?"
    system_input = "You are a pirate"
    use_model = "qwen3.5:9b"
    
    # 2. Call the function
    result = call_ollama(user_input, system_input, use_model)
    
    # 3. Print the result
    print("\nAI Response:")
    print(result)