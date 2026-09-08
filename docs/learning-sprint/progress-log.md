# Progress Log

Daily 1-hour entries, newest first. Keep each entry to 3-5 bullets — this is raw material for the weekly writeups, not the writeup itself.

Template for each entry:

```
## YYYY-MM-DD (Week N, Day X)
- Did:
- Hit/broke:
- Learned:
- Spend so far this week: $X
```

---
## Week 2, Day 1 (AKS cluster + inference deployment)
- Did: Provisioned AKS cluster + ACR via Pulumi; containerized and deployed the TinyLlama inference service; debugged two rounds of OOM crashes
- Hit/broke: Pod OOM-killed on undersized node (D2s_v5, ~5.6GB allocatable); tried resizing the node pool's VM size in place — Azure rejected it ("not allowed... in an api-version before 2026-01-02-preview" — actually an AKS platform constraint, not an API version issue); fixed by adding a separate user node pool (D4s_v5) instead of resizing the existing one; had a second OOM round after forgetting to actually raise the pod's memory limit to match the bigger node
- Learned: AKS node pools can't be VM-size-resized in place — standard pattern is small system pool + workload-sized user pool(s); `pulumi refresh` is essential after any failed/partial apply, since local state can drift from Azure's actual state; real memory footprint for a loaded 1.1B model is ~5.3GB, needs real headroom
- Real numbers: CPU inference — 100 tokens/15.2s, 500 tokens/46.9s (vs. near-instant on RTX 3090 in Week 1)
- Full session log: https://docs.google.com/document/d/1vBre9X__r10yGzn5wstJ1_UDLdYJag-t0MWuTLpxxro/edit
- Spend so far this week: [check `az consumption budget list` — was still showing lagged/$0 as of this session]

<!-- New entries go above this line -->
