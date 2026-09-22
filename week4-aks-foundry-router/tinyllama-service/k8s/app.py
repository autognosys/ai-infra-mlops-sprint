from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

app = FastAPI()
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float32)
model.eval()

class ChatRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 128

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_ID}

@app.post("/generate")
def generate(req: ChatRequest):
    messages = [{"role": "user", "content": req.prompt}]
    inputs = tokenizer.apply_chat_template(
        messages, return_tensors="pt", add_generation_prompt=True, return_dict=True
    )
    with torch.no_grad():
        output = model.generate(
            **inputs, max_new_tokens=req.max_new_tokens, do_sample=True, temperature=0.7
        )
    text = tokenizer.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
    return {"response": text}
