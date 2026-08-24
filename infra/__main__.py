"""
ai-infra-mlops-sprint — Week 1, Day 1

Scope for today: resource group + a budget alert. No GPU VM yet —
the goal is to get the "anything that costs money goes through Pulumi,
and gets destroyed at the end of the session" pattern right first.

Usage:
    cd infra
    uv sync
    pulumi login                      # or your preferred backend
    pulumi stack init week1           # first time only
    pulumi config set azure-native:location <region>   # e.g. eastus
    pulumi config set weeklyBudgetUsd 100
    pulumi config set alertEmail you@example.com
    pulumi preview
    pulumi up
    ...
    pulumi destroy                    # ALWAYS run this at the end of the session
"""

import pulumi
import pulumi_azure_native as azure_native
from pulumi_azure_native import resources, consumption

config = pulumi.Config()
weekly_budget_usd = config.get_float("weeklyBudgetUsd") or 100.0
alert_email = config.require("alertEmail")

# --- Resource group -----------------------------------------------------
# Everything for this sprint lives in one resource group so a single
# `pulumi destroy` (or a manual RG delete as a fallback) cleans up everything.
resource_group = resources.ResourceGroup(
    "ai-infra-sprint-rg",
    resource_group_name="ai-infra-mlops-sprint-rg",
    tags={
        "project": "ai-infra-mlops-sprint",
        "purpose": "learning",
        "teardown": "nightly",
    },
)

# --- Budget alert ---------------------------------------------------------
# Fires at 50/80/100% of the weekly cap. This is a safety net, not the
# primary cost control — the primary control is `pulumi destroy` every
# session. Scoped to the resource group so it only tracks this sprint's spend.
budget = consumption.Budget(
    "ai-infra-sprint-weekly-budget",
    budget_name="ai-infra-mlops-sprint-weekly",
    scope=resource_group.id,
    amount=weekly_budget_usd,
    time_grain=consumption.TimeGrainType.MONTHLY,  # Consumption Budget API has no WEEKLY grain; monitored manually per-week via cost checks
    time_period=consumption.BudgetTimePeriodArgs(
        start_date="2026-09-01T00:00:00Z",
    ),
    category=consumption.CategoryType.COST,
    notifications={
        "Actual_GreaterThan_50_Percent": consumption.NotificationArgs(
            enabled=True,
            operator=consumption.OperatorType.GREATER_THAN,
            threshold=50,
            contact_emails=[alert_email],
            threshold_type=consumption.ThresholdType.ACTUAL,
        ),
        "Actual_GreaterThan_80_Percent": consumption.NotificationArgs(
            enabled=True,
            operator=consumption.OperatorType.GREATER_THAN,
            threshold=80,
            contact_emails=[alert_email],
            threshold_type=consumption.ThresholdType.ACTUAL,
        ),
        "Actual_GreaterThan_100_Percent": consumption.NotificationArgs(
            enabled=True,
            operator=consumption.OperatorType.GREATER_THAN,
            threshold=100,
            contact_emails=[alert_email],
            threshold_type=consumption.ThresholdType.ACTUAL,
        ),
    },
)

pulumi.export("resource_group_name", resource_group.name)
pulumi.export("weekly_budget_usd", weekly_budget_usd)

# --- Day 2 adds here: NC-series spot GPU VM -------------------------------
