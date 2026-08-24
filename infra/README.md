# infra/

Pulumi (Python, uv toolchain) for everything in this sprint that costs money. One stack, reused/extended week to week — `pulumi destroy` at the end of every session.

## Setup (one time)

```bash
cd infra
uv sync
pulumi stack init week1
pulumi config set azure-native:location eastus     # or your preferred region
pulumi config set weeklyBudgetUsd 100
pulumi config set alertEmail you@example.com
```

## Every session

```bash
pulumi preview     # always read the diff before applying
pulumi up
# ... do the day's work ...
pulumi destroy      # do not skip this
```

## Day-by-day additions (Week 1)

- **Day 1:** resource group + budget alert (current state of `__main__.py`)
- **Day 2:** NC-series spot GPU VM
- **Day 3-5:** no new infra — same VM, reused via `pulumi up`/`pulumi destroy` each session
