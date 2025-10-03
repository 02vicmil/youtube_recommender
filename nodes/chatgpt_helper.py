import json
import pathlib
from openai import OpenAI  # Updated import for v1.0+
import os

def get_directory_path(__file__in, up_directories=0):
    """Return the absolute directory path of the current file, optionally going up folders."""
    return str(pathlib.Path(__file__in).parents[up_directories].resolve()).replace("\\", "/")

def load_api_key(config_file_path):
    """
    Load the API key from a JSON config file.
    
    Returns:
        str: API key if found, else None.
    """
    if not os.path.exists(config_file_path):
        return None
    
    try:
        with open(config_file_path, "r") as f:
            config = json.load(f)
        return config.get("CHATGPT_API_KEY")
    except (json.JSONDecodeError, KeyError):
        return None

def ask_chatgpt(prompt, model="gpt-4o-mini", system_message="You are a helpful assistant."):
    """
    Sends a prompt to OpenAI's Chat API and returns the response.
    
    Args:
        prompt (str): The user's message to the AI.
        model (str): The model to use ("gpt-4o-mini" or "gpt-3.5-turbo").
        system_message (str): Instructions for the AI.
    
    Returns:
        str: The AI's reply, or an error message if the API key is missing.
    """
    # Load API key
    api_key = load_api_key(get_directory_path(__file__) + "/config.json")
    
    if not api_key:
        return "No API key found. No API tool could be used."

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during API call: {e}"

# Example usage:
if __name__ == "__main__":
    user_prompt = "Hello! Can you help me with an API call?"
    answer = ask_chatgpt(user_prompt)
    print(answer)
