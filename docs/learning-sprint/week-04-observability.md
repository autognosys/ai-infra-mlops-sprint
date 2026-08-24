# Week 4 — Observability for AI Workloads

**Goal:** Pipe GPU + inference metrics (latency, token throughput, GPU utilization) into the existing OTel Collector + OpenObserve stack. Ties directly to Autognosys's AIOps positioning.

**Status:** ⬜ not started

## Daily plan
- Day 1: Identify metrics sources (GPU exporter, app-level inference metrics)
- Day 2: Wire OTel Collector to scrape/receive them
- Day 3: Route into OpenObserve, confirm data flowing
- Day 4: Build a small dashboard
- Day 5: Cost pass + teardown

## Weekend consolidation
- [ ] Dashboard screenshot
- [ ] Config committed
- [ ] Update root README progress table

## Artifact links
- Config: `infra/` or `docs/learning-sprint/`
- Dashboard screenshot: _(add path)_

## Resume bullet (draft)
> Built observability for GPU/inference workloads (latency, throughput, GPU utilization) using OpenTelemetry and OpenObserve.
