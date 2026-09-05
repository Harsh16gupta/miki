import os
from dotenv import load_dotenv
import httpx

# Load variables from .env
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY is not set in .env")

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": "deepseek/deepseek-chat",  # Cheap, fast model for sanity test
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful AI assistant for technical interview preparation.",
        },
        {
            "role": "user",
            "content": "Say hello in one short sentence and confirm you are online.",
        },
    ],
}

print("Sending request to OpenRouter...")
response = httpx.post(url, headers=headers, json=payload, timeout=30.0)

if response.status_code == 200:
    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    print("\n--- Success! Response from model ---")
    print(reply)
else:
    print(f"\nError {response.status_code}: {response.text}")