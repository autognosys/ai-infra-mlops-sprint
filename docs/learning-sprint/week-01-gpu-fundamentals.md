# Week 1 — GPU Fundamentals + IaC Discipline

**Goal:** Stand up a spot GPU VM entirely through Pulumi, run real inference on it, and prove a clean nightly teardown ritual with zero orphaned resources. This week is as much about the *discipline* (budget alerts, teardown) as the GPU itself — it's what makes the rest of the sprint sustainable.

**Status:** ⬜ not started

## Daily plan

### Day 1 (Mon) — Pulumi scaffold + resource group
- New Pulumi project/stack (`ai-infra-mlops-sprint`, stack `week1`)
- Resource group
- Budget alert (50% / 80% / 100% of a per-week cap, e.g. $100-150/week)
- No VM yet — get the "expensive resources" pattern right first
- **Output:** `pulumi preview` clean, budget alert test notification received

### Day 2 (Tue) — Spot GPU VM
- Add NC-series spot VM (T4 to start)
- SSH access, confirm drivers via `nvidia-smi`
- `pulumi up` → verify → `pulumi destroy` — first rep of the teardown ritual
- **Output:** VM provisioned and destroyed once, cleanly

### Day 3 (Wed) — Real inference workload
- `pulumi up`, install minimal inference stack (HF `transformers` + small/quantized model)
- Run actual generation, not just `nvidia-smi`
- Note load time, tokens/sec, VRAM usage
- **Output:** Screenshot/log of real inference output + basic perf numbers

### Day 4 (Thu) — Cost + monitoring pass
- Check actual spend in Azure Cost Management vs. budget alert thresholds
- Note $/hour for the VM size chosen
- If time allows: compare a second GPU SKU
- **Output:** Small cost table (SKU, $/hr, VRAM, best use)

### Day 5 (Fri) — Harden teardown + document IaC
- One-command teardown (`pulumi destroy -y`, aliased/scripted)
- Confirm no orphaned resources (disks, IPs) survive
- Clean up Pulumi code, add comments/README to the stack
- **Output:** Repo-ready Pulumi code for Week 1

## Weekend consolidation

- [ ] What was built (summary)
- [ ] Cost table
- [ ] One thing that broke and how it was fixed
- [ ] Screenshot of inference output
- [ ] Link to Pulumi code
- [ ] Update root README progress table

## Artifact links
- Pulumi code: `infra/`
- Screenshots: _(add path once captured)_

## Resume bullet (draft)
> Provisioned and tore down cost-controlled spot GPU infrastructure on Azure via Pulumi (Python), with automated budget alerting and zero-orphaned-resource teardown discipline.
