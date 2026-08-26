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

# ============================================================================
# GCP — Week 1 Day 2: preemptible T4 GPU VM (autognosys-net project)
# ============================================================================
# Azure NC-series quota was denied on this subscription (sponsorship/startup
# subscriptions don't get GPU quota by default — see docs/learning-sprint/
# week-01-gpu-fundamentals.md for the full story). autognosys-net already has
# billing history and GPU quota (NVIDIA_T4_GPUS: 1) in us-central1, so the
# GPU exercises for this sprint run there instead. The Azure resource group +
# budget above stay as-is and get used in later weeks (Azure ML, AKS control
# plane, observability) that don't need this specific quota.

import pulumi_gcp as gcp

gcp_config = pulumi.Config("gcp")
gcp_project = gcp_config.require("project")
gcp_zone = gcp_config.get("zone") or "us-central1-a"

# Firewall: allow SSH only, scoped to instances tagged "gpu-sprint" —
# nothing else in the project is affected.
gpu_sprint_ssh_firewall = gcp.compute.Firewall(
    "gpu-sprint-allow-ssh",
    project=gcp_project,
    network="default",
    allows=[gcp.compute.FirewallAllowArgs(protocol="tcp", ports=["22"])],
    source_ranges=["0.0.0.0/0"],  # tighten to your IP if you want it stricter
    target_tags=["gpu-sprint"],
)

# Preemptible n1-standard-4 + 1x T4, using the Deep Learning VM image
# (CUDA + PyTorch preinstalled) so Day 3's "real inference" step doesn't
# burn a session on driver/toolkit setup.
gpu_vm = gcp.compute.Instance(
    "gpu-sprint-vm",
    project=gcp_project,
    zone=gcp_zone,
    machine_type="n1-standard-4",
    tags=["gpu-sprint"],
    boot_disk=gcp.compute.InstanceBootDiskArgs(
        initialize_params=gcp.compute.InstanceBootDiskInitializeParamsArgs(
            image="projects/deeplearning-platform-release/global/images/family/pytorch-2-9-cu129-ubuntu-2204-nvidia-580",
            size=100,
        ),
    ),
    guest_accelerators=[
        gcp.compute.InstanceGuestAcceleratorArgs(
            type="nvidia-tesla-t4",
            count=1,
        ),
    ],
    # GPUs require manual host maintenance handling, and preemptible
    # instances can't auto-restart — both required for this SKU combo.
    scheduling=gcp.compute.InstanceSchedulingArgs(
        preemptible=True,
        automatic_restart=False,
        on_host_maintenance="TERMINATE",
    ),
    network_interfaces=[
        gcp.compute.InstanceNetworkInterfaceArgs(
            network="default",
            access_configs=[gcp.compute.InstanceNetworkInterfaceAccessConfigArgs()],  # ephemeral external IP
        ),
    ],
    metadata={
        "install-nvidia-driver": "True",  # DLVM image auto-installs/verifies driver on boot
    },
)

pulumi.export("gpu_vm_name", gpu_vm.name)
pulumi.export("gpu_vm_external_ip", gpu_vm.network_interfaces[0].access_configs[0].nat_ip)

# --- Day 3 adds here: run real inference on the VM (manual/CLI, not IaC) ---
