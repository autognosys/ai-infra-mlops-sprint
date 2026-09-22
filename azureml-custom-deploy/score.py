import json
import torch
from transformers import pipeline

def init():
    global pipe
    pipe = pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        device=-1  # CPU
    )

def run(raw_data):
    try:
        data = json.loads(raw_data)
        messages = data.get("messages", [])
        max_new_tokens = data.get("max_new_tokens", 100)
        result = pipe(messages, max_new_tokens=max_new_tokens)
        return json.dumps({"generated_text": result[0]["generated_text"]})
    except Exception as e:
        return json.dumps({"error": str(e)})
