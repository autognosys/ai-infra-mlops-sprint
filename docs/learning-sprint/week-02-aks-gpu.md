# Week 2 — GPU Workloads on Kubernetes (AKS)

**Goal:** AKS cluster with a GPU node pool, containerized inference service, autoscale-to-zero. Leans directly on existing K8s/SRE depth.

**Status:** ⬜ not started

## Daily plan
- Day 1: AKS cluster (Pulumi) + GPU node pool
- Day 2: Containerize the Week 1 inference workload
- Day 3: Deploy to AKS, expose service, verify GPU scheduling
- Day 4: Autoscale-to-zero configuration + test
- Day 5: Cost pass + teardown hardening

## Weekend consolidation
- [ ] Architecture diagram (AKS GPU pool + scaling behavior)
- [ ] Short writeup / LinkedIn-worthy post
- [ ] Update root README progress table

## Artifact links
- Pulumi code: `infra/`
- Diagram: _(add path)_

## Resume bullet (draft)
> Deployed and autoscaled GPU inference workloads on AKS, including scale-to-zero GPU node pools.
