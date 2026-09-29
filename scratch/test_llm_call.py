"""Phase 0 sanity check: one raw HTTP call to the LLM provider.

Run with ``PYTHONPATH=. venv/bin/python scratch/test_llm_call.py``.
Requires META_API_KEY in .env (default provider: Meta Model API,
muse-spark-1.3-contributor); set LLM_PROVIDER=openrouter + OPENROUTER_API_KEY
to check the fallback. Prints the reply on success. Superseded by
app/llm/router.py (Phase 2), kept as the original "LLM access works" proof.
"""

import os

import httpx
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

provider = os.getenv("LLM_PROVIDER", "meta").lower().strip() or "meta"
if provider == "openrouter":
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in .env")
    url = "https://openrouter.ai/api/v1/chat/completions"
    model = "deepseek/deepseek-chat"  # Cheap, fast model for sanity test
else:
    api_key = os.getenv("META_API_KEY") or os.getenv("MODEL_API_KEY")
    if not api_key:
        raise ValueError("META_API_KEY is not set in .env")
    url = os.getenv("META_BASE_URL", "https://api.meta.ai/v1/chat/completions")
    model = "muse-spark-1.3-contributor"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": model,
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

print(f"Sending request to {provider} ({model})...")
response = httpx.post(url, headers=headers, json=payload, timeout=30.0)

if response.status_code == 200:
    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    print("\n--- Success! Response from model ---")
    print(reply)
else:
    print(f"\nError {response.status_code}: {response.text}")
