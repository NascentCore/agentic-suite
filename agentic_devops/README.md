# Agentic DevOps

Automated build, test, deploy, monitor, and incident response for **any software**.

## What this module provides

Agentic DevOps scans a repository for deployment infrastructure (CI config,
Dockerfiles, k8s manifests), builds a deploy profile, and provides an agentic
layer for the full CI/CD lifecycle: build → test → deploy → monitor → incident
response → rollback.

### Position in the Agentic Suite

| Layer | Module | Purpose |
|-------|--------|---------|
| **Agentic Repo** | `personified_software/openclaw_scaffold/` | Developer ↔ Code (via conversation) |
| **Agentic Runtime** | `agentic_runtime/` | User ↔ Running Software (via conversation) |
| **Agentic DevOps** | `agentic_devops/` ← **this** | Automated deploy, monitor, incident response |

## Architecture

```
pipeline_detector.py   →  Discover CI/CD config (GitHub Actions, Docker, k8s)
        ↓
pipeline_engine.py     →  Saga-based pipeline orchestration
        ↓
policy_engine.py       →  Deployment approval gates + environment protection
        ↓
monitor.py             →  Health checks (HTTP, TCP, command)
        ↓
incident_manager.py    →  Detect → Diagnose → Propose → Execute → Verify
        ↓
rollback.py            →  Version tracking + safe rollback
        ↓
adapters.py            →  PydanticAI agent / LangGraph graph
        ↓
templates.py           →  Generate DEVOPS_RUNBOOK / DEPLOY_SKILLS / MONITOR_CONFIG
        ↓
cli.py                 →  CLI: detect / generate / deploy / monitor / rollback
```

## Key patterns reused from BRAIN_STORM.md

| Pattern | Where used |
|---------|------------|
| Planner-Executor Separation | `PipelineEngine` — plan then execute stages |
| Saga with Compensating Actions | Stage compensator commands + reverse rollback |
| Human Approval Gate | Production deploy + high-risk remediation gating |
| Async Job Protocol | `PipelineRun` with queued/running/succeeded/failed states |
| Provenance and Attestation | `PipelineProvenance` on every run |
| Observability Layer | `MonitorEngine` with health checks and status tracking |

## Quick start

### 1) Detect deploy profile

```bash
python3 -m agentic_devops.cli detect /path/to/repo --output deploy_profile.json
```

### 2) Generate DevOps config files

```bash
python3 -m agentic_devops.cli generate --repo /path/to/repo --output-dir ./devops_config
```

Generates:
- `DEVOPS_RUNBOOK.md` — deployment runbook
- `DEPLOY_SKILLS.md` — DevOps agent skill contract
- `MONITOR_CONFIG.md` — monitoring configuration

### 3) Dry-run a deployment

```bash
python3 -m agentic_devops.cli deploy /path/to/repo --env staging --dry-run
```

### 4) Health check

```bash
python3 -m agentic_devops.cli monitor --target http://localhost:8000/health --type http
```

## Framework adapters

### PydanticAI

```python
from agentic_devops.adapters import create_devops_pydantic_agent

agent = create_devops_pydantic_agent(profile, model="openai:gpt-4o")
```

### LangGraph

```python
from agentic_devops.adapters import build_devops_langgraph_app

app = build_devops_langgraph_app(profile)
result = app.invoke({"action": "monitor", ...})
```

## Testing

```bash
python3 -m pytest -q agentic_devops/
```
