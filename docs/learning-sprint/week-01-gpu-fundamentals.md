# Week 1 — GPU Fundamentals + IaC Discipline

**Goal:** Stand up a spot GPU VM entirely through Pulumi, run real inference on it, and prove a clean nightly teardown ritual with zero orphaned resources. This week is as much about the *discipline* (budget alerts, teardown) as the GPU itself — it's what makes the rest of the sprint sustainable.

**Status:** 🟨 in progress

## What actually happened (worth keeping — this is the real story)

The original plan was a single-cloud (Azure) week. It didn't go that way:

- Day 1 completed on Azure as planned — resource group + budget alert, one bug fixed along the way (Consumption Budget `start_date` must be first-of-month).
- Day 2 hit a wall: Azure denied the NC-series GPU quota request outright. Root cause — Microsoft for Startups sponsorship subscriptions are structurally excluded from self-service GPU quota, regardless of region (tried Central India, Southeast Asia, West US 2 — all backlogged/denied). This is a known, widely-documented pattern, not something specific to this subscription.
- Pivoted the GPU-specific exercises to GCP (`autognosys-net` project), which already had `NVIDIA_T4_GPUS` quota (limit 1) in `us-central1` — because it's a real paid account with billing history, not a free-trial project. No request needed for the regional SKU-specific quota.
- Hit a *second*, separate quota gate on GCP: `GPUS_ALL_REGIONS` (a global, project-wide aggregate cap) was also 0, independent of the regional T4 quota. Requested an increase — denied, with GCP citing insufficient billing history despite the project being several months old, suggesting the gate is keyed to cumulative spend rather than account age. Advised to wait 48h and resubmit, or escalate via sales.
- Given two separate cloud providers both gated GPU access at the account/subscription level (for structurally similar anti-abuse reasons), pivoted to **RunPod** (GPU rental, no quota system) — got a real RTX 3090 running within minutes, no gatekeeping at all.
- The Azure resource group + budget from Day 1 stay in place and get used in later weeks (Azure ML, AKS control plane, observability) that don't touch this specific GPU quota. The GCP T4 regional quota also stays granted for potential future use (e.g. Week 2's Kubernetes GPU scheduling, if Azure/GCP clear up by then).

This ended up being a genuinely useful lesson in multi-cloud pragmatism, cloud-specific quota/governance models, and prompt formatting (chat-templated vs. raw text) — arguably more representative of real platform engineering work than if Week 1 had gone smoothly.

## Daily plan

### Day 1 (Mon) — Pulumi scaffold + resource group
- New Pulumi project/stack (`ai-infra-mlops-sprint`, stack `week1`)
- Resource group
- Budget alert (50% / 80% / 100% of a per-week cap, e.g. $100-150/week)
- No VM yet — get the "expensive resources" pattern right first
- **Output:** `pulumi preview` clean, budget alert test notification received

### Day 2 (Tue) — Spot GPU VM
- ~~Add NC-series spot VM (T4 to start)~~ — blocked, Azure denied GPU quota on this subscription (see above)
- Pivoted to GCP: preemptible `n1-standard-4` + 1x T4 in `us-central1`, Deep Learning VM image (CUDA + PyTorch preinstalled)
- SSH access via `gcloud compute ssh`, confirm drivers via `nvidia-smi`
- `pulumi up` → verify → `pulumi destroy` — first rep of the teardown ritual
- **Output:** VM provisioned and destroyed once, cleanly

### Day 3 (Wed) — Real inference workload
- ~~`pulumi up`, install minimal inference stack~~
- Ran real inference on the RunPod RTX 3090: `transformers` + TinyLlama-1.1B-Chat
- Hit a real, instructive bug: raw string prompts produced incoherent/off-topic output — TinyLlama-Chat expects its chat template (`messages=[{"role": "user", ...}]`), not freeform text. Fixing this produced a correct, coherent answer.
- **Output:** confirmed working inference pipeline, with a genuine "prompt formatting matters" lesson learned along the way

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
> Diagnosed and worked around GPU quota restrictions across Azure and GCP sponsorship/credit-based subscriptions; pivoted to an alternative GPU provider to keep a self-directed AI infrastructure learning sprint on schedule. Provisioned and tore down cost-controlled infrastructure via Pulumi (Python) with automated budget alerting.
