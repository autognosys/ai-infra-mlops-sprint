import os
import logging
import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("opentelemetry.exporter.otlp.proto.grpc.exporter").setLevel(logging.DEBUG)

OTEL_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "tempo.observability.svc.cluster.local:4317")

resource = Resource.create({"service.name": "week4-router-service"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

TINYLLAMA_URL = os.environ.get("TINYLLAMA_URL", "http://tinyllama-server/generate")
FOUNDRY_URL = os.environ["FOUNDRY_URL"]
FOUNDRY_API_KEY = os.environ["FOUNDRY_API_KEY"]
LENGTH_THRESHOLD = int(os.environ.get("LENGTH_THRESHOLD", "100"))

class ChatRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 128

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    prompt_len = len(req.prompt)
    route = "tinyllama" if prompt_len <= LENGTH_THRESHOLD else "foundry"

    with tracer.start_as_current_span("route_decision") as span:
        span.set_attribute("prompt_length", prompt_len)
        span.set_attribute("route", route)
        span.set_attribute("length_threshold", LENGTH_THRESHOLD)

        if route == "tinyllama":
            with tracer.start_as_current_span("call_tinyllama"):
                resp = httpx.post(
                    TINYLLAMA_URL,
                    json={"prompt": req.prompt, "max_new_tokens": req.max_new_tokens},
                    timeout=60,
                )
                resp.raise_for_status()
                result = resp.json()["response"]
        else:
            with tracer.start_as_current_span("call_foundry"):
                resp = httpx.post(
                    FOUNDRY_URL,
                    headers={"api-key": FOUNDRY_API_KEY, "Content-Type": "application/json"},
                    json={
                        "model": "Mistral-Large-3",
                        "messages": [{"role": "user", "content": req.prompt}],
                        "max_tokens": req.max_new_tokens,
                    },
                    timeout=60,
                )
                if resp.status_code >= 400:
                    print(f"Foundry error {resp.status_code}: {resp.text}", flush=True)
                resp.raise_for_status()
                data = resp.json()
                result = data["choices"][0]["message"]["content"]

    return {
        "route": route,
        "prompt_length": prompt_len,
        "response": result,
    }
