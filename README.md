# ai-infra-mlops-sprint

A 6-week, ~1hr/day sprint learning GPU infrastructure and MLOps on Azure — provisioning, orchestrating, observing, and fine-tuning — while keeping cloud spend under control.

## Why this repo exists

**Focus:** AI infra & MLOps (provisioning, orchestration, observability, deployment) — leaning into existing K8s/SRE depth rather than starting ML from scratch. Fine-tuning is included as hands-on practice, not the main focus.

**Constraints:**
- Limited cloud budget, so nothing runs longer than it needs to
- ~1 hour/day, 6 weeks (~42 hours total)
- Pulumi for anything that costs money; manual/CLI for the ML/experimentation layer itself
- No CI/CD — overkill for a solo project at this scale

## Structure

```
docs/learning-sprint/
├── progress-log.md              # daily 1-hr entries
├── week-01-gpu-fundamentals.md
├── week-02-aks-gpu.md
├── week-03-mlops-pipeline.md
├── week-04-observability.md
├── week-05-finetuning.md
├── week-06-capstone.md
└── final-writeup.md             # end-of-sprint blog post / retrospective
infra/                           # Pulumi (Python) IaC, one reused stack per week's exercise
```

## Progress

| Week | Focus | Status | Artifact |
|---|---|---|---|
| 1 | GPU fundamentals + IaC discipline | ⬜ | |
| 2 | GPU workloads on Kubernetes (AKS) | ⬜ | |
| 3 | MLOps pipeline (Azure ML endpoints) | ⬜ | |
| 4 | Observability for AI workloads | ⬜ | |
| 5 | Hands-on LoRA fine-tuning | ⬜ | |
| 6 | Capstone + writeup | ⬜ | |

Status legend: ⬜ not started · 🟨 in progress · ✅ done

## Toolchain

- **IaC:** Pulumi (Python), `uv` for dependency management
- **Discipline:** always `pulumi preview` before `pulumi up`; `pulumi destroy` at the end of every session
- **Cloud:** Azure (this sprint) — provisioning targets AKS, Azure ML, and standalone GPU VMs across the six weeks
