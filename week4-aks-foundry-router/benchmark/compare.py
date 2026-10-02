#!/usr/bin/env python3
"""Router comparison: TinyLlama (AKS) vs Mistral Large 3 (Foundry) vs the router itself.

Stdlib only. Run from symphony with the AKS router port-forwarded.

  export FOUNDRY_URL=https://<your-resource>.services.ai.azure.com/models/chat/completions?api-version=2024-05-01-preview
  export FOUNDRY_KEY=...                                  # Foundry api-key
  kubectl port-forward svc/<router-svc> 8080:<port> &     # router
  kubectl port-forward svc/<tinyllama-svc> 8081:<port> &  # TinyLlama direct
  python3 compare.py

Edit the ADAPTERS section if your router / TinyLlama request schema differs.
"""
import csv, json, os, statistics, sys, time, urllib.request, urllib.error

ROUTER_URL = os.getenv("ROUTER_URL", "http://localhost:8080/chat")
TINY_URL = os.getenv("TINY_URL", "http://localhost:8081/generate")
# No default on purpose: set it to your own deployment's chat-completions URL, e.g.
#   https://<your-resource>.services.ai.azure.com/models/chat/completions?api-version=2024-05-01-preview
FOUNDRY_URL = os.getenv("FOUNDRY_URL", "")
FOUNDRY_KEY = os.getenv("FOUNDRY_KEY", "")
FOUNDRY_MODEL = os.getenv("FOUNDRY_MODEL", "Mistral-Large-3")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "200"))
RUNS = int(os.getenv("RUNS", "1"))

# $ per 1M tokens for Foundry (look up your deployment's price; 0 = report tokens only)
FOUNDRY_IN = float(os.getenv("FOUNDRY_IN_PER_M", "0"))
FOUNDRY_OUT = float(os.getenv("FOUNDRY_OUT_PER_M", "0"))
# $/hour for the AKS node that hosts TinyLlama (userpool D4s_v5, check Cost analysis)
NODE_HOURLY = float(os.getenv("NODE_HOURLY", "0.20"))

PROMPTS = [
    # short (<=100 chars): router sends these to TinyLlama
    ("short", "What does exit code 137 mean in Kubernetes?"),
    ("short", "Explain a CrashLoopBackOff in one sentence."),
    ("short", "Name three Prometheus metric types."),
    ("short", "What is the difference between a liveness and readiness probe?"),
    ("short", "Give one cause of high p99 latency."),
    # long (>100 chars): router sends these to Foundry
    ("long", "A pod in production is OOMKilled every 20 minutes after a deploy that raised replicas from 3 to 6. "
             "Memory limit is 512Mi, requests 256Mi, and the app is a Python FastAPI service loading a model at startup. "
             "List the three most likely root causes in order of likelihood and the evidence you would check for each."),
    ("long", "Summarize this incident for an executive in three sentences: At 02:10 a config change set the DB pool size to 5. "
             "At 02:14 API latency rose from 80ms to 4s. At 02:31 on-call rolled back the change and latency recovered by 02:35. "
             "No data was lost; 12 percent of requests timed out."),
    ("long", "Extract JSON with keys service, severity, and action from this alert text and return only JSON: "
             "'CRITICAL checkout-api error rate 18 percent over 5 minutes, last deploy 14 minutes ago, recommend rollback.'"),
    ("long", "Write a PromQL query that alerts when the 5-minute error ratio of http_requests_total for job api "
             "exceeds 2 percent, and explain each part of the query briefly."),
    ("long", "Compare static length-based routing with a classifier-based router for sending prompts to a small versus large model. "
             "Cover cost, latency, and failure modes in under 150 words."),
]


def post(url, body, headers=None, timeout=180):
    h = {"Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
        return time.perf_counter() - t0, json.loads(raw), None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        detail = e.read().decode()[:300] if isinstance(e, urllib.error.HTTPError) else str(e)
        return time.perf_counter() - t0, None, detail


# ---------------- ADAPTERS: edit these to match your services ----------------
def call_router(prompt):
    lat, resp, err = post(ROUTER_URL, {"prompt": prompt, "max_new_tokens": MAX_TOKENS})
    r = resp or {}
    text = (r.get("response") or r.get("text") or r.get("output") or r.get("content")
            or (json.dumps(r)[:500] if r else ""))
    backend = r.get("backend") or r.get("route") or r.get("routed_to") or r.get("path") or ""
    return lat, text, {"backend": backend}, err


def call_tiny(prompt):
    lat, resp, err = post(TINY_URL, {"prompt": prompt, "max_new_tokens": MAX_TOKENS})
    text = (resp or {}).get("response") or (resp or {}).get("text") or json.dumps(resp)[:500] if resp else ""
    return lat, text, {}, err


def call_foundry(prompt):
    if not FOUNDRY_URL:
        return 0.0, "", {}, "FOUNDRY_URL is not set"
    body = {"model": FOUNDRY_MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": MAX_TOKENS}
    lat, resp, err = post(FOUNDRY_URL, body, {"api-key": FOUNDRY_KEY})
    if not resp:
        return lat, "", {}, err
    u = resp.get("usage", {})
    cost = (u.get("prompt_tokens", 0) * FOUNDRY_IN + u.get("completion_tokens", 0) * FOUNDRY_OUT) / 1e6
    return lat, resp["choices"][0]["message"]["content"], {
        "in_tok": u.get("prompt_tokens"), "out_tok": u.get("completion_tokens"), "cost_usd": round(cost, 6)}, None
# ------------------------------------------------------------------------------

ALL_TARGETS = {"router": call_router, "tinyllama_aks": call_tiny, "foundry_mistral": call_foundry}
# ONLY=tinyllama_aks runs just that target; LABEL=cpu4 tags the output filenames
_only = [t for t in os.getenv("ONLY", ",".join(ALL_TARGETS)).split(",") if t]
TARGETS = {k: v for k, v in ALL_TARGETS.items() if k in _only}
LABEL = os.getenv("LABEL", "")


def main():
    if "foundry_mistral" in TARGETS and not (FOUNDRY_KEY and FOUNDRY_URL):
        print("warning: FOUNDRY_URL and FOUNDRY_KEY must both be set; foundry_mistral calls will fail",
              file=sys.stderr)
    rows = []
    for name, fn in TARGETS.items():
        for kind, prompt in PROMPTS:
            for i in range(RUNS):
                lat, text, extra, err = fn(prompt)
                rows.append({"target": name, "kind": kind, "run": i + 1, "latency_s": round(lat, 2),
                             "error": err or "", "response": text, "quality_1to5": "", **extra})
                print(f"{name:16} {kind:5} {lat:6.2f}s {'ERR ' + err[:60] if err else ''}")
    stamp = time.strftime("%Y%m%d-%H%M") + (f"-{LABEL}" if LABEL else "")
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k != "target", k))
    with open(f"comparison-{stamp}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)

    lines = ["| target | calls | errors | p50 s | p95 s | foundry $ total |", "|---|---|---|---|---|---|"]
    for name in TARGETS:
        rs = [r for r in rows if r["target"] == name]
        ok = sorted(r["latency_s"] for r in rs if not r["error"])
        p = lambda q: ok[min(len(ok) - 1, int(q * len(ok)))] if ok else float("nan")
        cost = sum(r.get("cost_usd") or 0 for r in rs)
        lines.append(f"| {name} | {len(rs)} | {sum(1 for r in rs if r['error'])} | "
                     f"{statistics.median(ok) if ok else float('nan'):.2f} | {p(0.95):.2f} | {cost:.4f} |")
    summary = "\n".join(lines)
    print("\n" + summary)
    print(f"\nTinyLlama has no per-call price: the node costs ~${NODE_HOURLY}/hr regardless of load.")
    with open(f"comparison-{stamp}.md", "w") as f:
        f.write(summary + f"\n\nTinyLlama node: ~${NODE_HOURLY}/hr fixed. "
                          "Fill quality_1to5 in the CSV by reading the responses.\n")


if __name__ == "__main__":
    main()
