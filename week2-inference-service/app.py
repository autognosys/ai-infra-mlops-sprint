from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI(title="ai-infra-sprint inference service")

# Loaded once at startup, reused across requests — avoids reloading the
# model on every call. CPU-only since this cluster has no GPU node pool.
pipe = pipeline(
    "text-generation",
    model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    device=-1,  # -1 = CPU
)


class GenerateRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 100


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
def generate(req: GenerateRequest):
    messages = [{"role": "user", "content": req.prompt}]
    result = pipe(messages, max_new_tokens=req.max_new_tokens, do_sample=True, temperature=0.7)
    return {"response": result[0]["generated_text"][-1]["content"]}
