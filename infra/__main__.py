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
#gpu_vm = gcp.compute.Instance(
#    "gpu-sprint-vm",
#    project=gcp_project,
#    zone=gcp_zone,
#    machine_type="n1-standard-4",
#    tags=["gpu-sprint"],
#    boot_disk=gcp.compute.InstanceBootDiskArgs(
#        initialize_params=gcp.compute.InstanceBootDiskInitializeParamsArgs(
#            image="projects/deeplearning-platform-release/global/images/family/pytorch-2-9-cu129-ubuntu-2204-nvidia-580",
#            size=100,
#        ),
#    ),
#    guest_accelerators=[
#        gcp.compute.InstanceGuestAcceleratorArgs(
#            type="nvidia-tesla-t4",
#            count=1,
#        ),
#   ],
# GPUs require manual host maintenance handling, and preemptible
# instances can't auto-restart — both required for this SKU combo.
#    scheduling=gcp.compute.InstanceSchedulingArgs(
#        preemptible=True,
#        automatic_restart=False,
#        on_host_maintenance="TERMINATE",
#    ),
#    network_interfaces=[
#        gcp.compute.InstanceNetworkInterfaceArgs(
#            network="default",
#            access_configs=[gcp.compute.InstanceNetworkInterfaceAccessConfigArgs()],  # ephemeral external IP
#        ),
#    ],
#    metadata={
#        "install-nvidia-driver": "True",  # DLVM image auto-installs/verifies driver on boot
#    },
#)

#pulumi.export("gpu_vm_name", gpu_vm.name)
#pulumi.export("gpu_vm_external_ip", gpu_vm.network_interfaces[0].access_configs[0].nat_ip)

# ============================================================================
# Week 2, Day 1 — AKS cluster with CPU-only node pool
# ============================================================================
# No GPU quota needed here — standard CPU VM sizes aren't gated the way the
# NC-series GPU VMs were. This is real, meaningful Azure spend (the original
# point of this sprint), separate from the GPU-scheduling concepts (handled
# via a compact RunPod/k3s exercise on Day 2 instead of a full AKS GPU node
# pool, which would hit the same NC-series quota wall).

from pulumi_azure_native import containerservice, authorization

aks_cluster = containerservice.ManagedCluster(
    "ai-infra-sprint-aks",
    resource_group_name=resource_group.name,
    resource_name_="ai-infra-sprint-aks",
    dns_prefix="ai-infra-sprint",
    identity=containerservice.ManagedClusterIdentityArgs(
        type=containerservice.ResourceIdentityType.SYSTEM_ASSIGNED,
    ),
    agent_pool_profiles=[
        containerservice.ManagedClusterAgentPoolProfileArgs(
            name="cpupool",
            count=2,
            vm_size="Standard_D2s_v5",  # 2 vCPU, 8GB RAM — no quota gating
            os_type=containerservice.OSType.LINUX,
            mode=containerservice.AgentPoolMode.SYSTEM,
            type=containerservice.AgentPoolType.VIRTUAL_MACHINE_SCALE_SETS,
        ),
    ],
)

# Separate user node pool, sized for the inference workload — keeping the
# original "cpupool" as a small system pool (AKS won't let you resize an
# existing pool's VM size in place; adding a new pool is the standard
# pattern for workload-specific sizing).
inference_node_pool = containerservice.AgentPool(
    "inference-userpool",
    resource_group_name=resource_group.name,
    resource_name_=aks_cluster.name,
    agent_pool_name="userpool",
    count=1,
    vm_size="Standard_D4s_v5",  # 4 vCPU, 16GB RAM
    os_type=containerservice.OSType.LINUX,
    mode=containerservice.AgentPoolMode.USER,
    type=containerservice.AgentPoolType.VIRTUAL_MACHINE_SCALE_SETS,
)

pulumi.export("aks_cluster_name", aks_cluster.name)
pulumi.export(
    "aks_get_credentials_cmd",
    pulumi.Output.concat(
        "az aks get-credentials --resource-group ", resource_group.name,
        " --name ", aks_cluster.name,
    ),
)

# ============================================================================
# Week 2, Day 1 (cont.) — Azure Container Registry, attached to AKS
# ============================================================================
from pulumi_azure_native import containerregistry

acr = containerregistry.Registry(
    "ai-infra-sprint-acr",
    resource_group_name=resource_group.name,
    registry_name="aiinfrasprintacr",  # must be globally unique, alphanumeric only
    sku=containerregistry.SkuArgs(name="Basic"),
    admin_user_enabled=True,  # simplest auth path for a solo learning sprint
)

# Grant the AKS cluster's kubelet identity pull access to this registry
acr_pull_role = authorization.RoleAssignment(
    "aks-acr-pull",
    principal_id=aks_cluster.identity_profile.apply(
        lambda profile: profile["kubeletidentity"].object_id
    ),
    principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
    role_definition_id="/subscriptions/7e21c167-fe3e-423d-b07f-106b2caf1539/providers/Microsoft.Authorization/roleDefinitions/7f951dda-4ed3-4680-a7ca-43fe172d538d",  # AcrPull built-in role
    scope=acr.id,
)

pulumi.export("acr_login_server", acr.login_server)
pulumi.export("acr_name", acr.name)
