import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = "https://rocky.cs.kent.edu/v1/responses"
headers = {
    "Authorization": f"Bearer {os.environ['ROCKY_API_KEY']}"
}

models_response = requests.get(
    "https://rocky.cs.kent.edu/v1/models",
    headers=headers,
    timeout=30,
)
models_response.raise_for_status()
model = models_response.json()["data"][0]["id"]

payload = {
    "model": model,
    "input": "Recommend me a good card to play in Magic The Gathering.",
    "max_output_tokens": 1000,
    "store": False,
}

response = requests.post(url, headers=headers, json=payload, timeout=390)
response.raise_for_status()

print(response.json()["output_text"])
