# Agentic Suite

A suite of highly-complementary protocols, design principles, and paradigms for building agentic software.

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agentic Suite                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  Agentic Repo   │ →│ Agentic DevOps  │ →│ Agentic Runtime │  │
│  │  (code)         │  │ (deploy)        │  │ (operate)       │  │
│  │                 │  │                 │  │                 │  │
│  │  SOUL.md        │  │ DEVOPS_RUNBOOK  │  │ RUNTIME_TOOLS   │  │
│  │  skills.md      │  │ DEPLOY_SKILLS   │  │ RUNTIME_SKILLS  │  │
│  │  AGENTS.md      │  │ MONITOR_CONFIG  │  │ RUNTIME_AGENTS  │  │
│  │  TOOLS.md       │  │                 │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  Shared Foundation                        │  │
│  │  AMCP (memory/consent) · Policy Engine · Provenance       │  │
│  │  Observability · Eval Harness · Framework Adapters        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Descriptions

| Layer | Module | Purpose |
|-------|--------|---------|
| **Agentic Repo** | `personified_software/openclaw_scaffold/` | Developer ↔ Code — agents that understand and modify code through conversation |
| **Agentic DevOps** | `agentic_devops/` | Code → Production — automated build, test, deploy, monitor, and incident response |
| **Agentic Runtime** | `agentic_runtime/` | User ↔ Running Software — natural-language interface for using any running application |

### Cross-Layer Workflows

1. **Code → Deploy → Runtime**: Code changes → DevOps auto-deploys → Runtime refreshes tool registry
2. **Runtime → Incident → DevOps**: Runtime anomaly → auto-create incident → DevOps diagnoses and rollbacks
3. **Incident → Repo**: Post-incident review → auto-create issue/RFC → Agentic Repo assists with fix

## Modules

### `personified_software/` — Agentic Repo

Universal OpenClaw-like scaffold toolkit for turning **any repository** into an agent-ready, personified workspace. Profiles a repo's structure, language, commands, and risks, then generates `SOUL.md`, `skills.md`, `AGENTS.md`, `TOOLS.md`.

```bash
python3 -m personified_software.openclaw_scaffold.cli /path/to/repo
```

### `agentic_runtime/` — Agentic Runtime

Discovers what a running application can do (API endpoints, CLI commands, etc.) and exposes those capabilities as typed tools for conversational interaction.

```bash
python3 -m agentic_runtime.cli profile --app-name my-api --openapi-url http://localhost:8000/openapi.json
python3 -m agentic_runtime.cli generate --profile profile.json --output-dir ./
```

### `agentic_devops/` — Agentic DevOps

Scans a repository for deployment infrastructure and provides saga-based pipeline orchestration, health monitoring, incident management, and safe rollback.

```bash
python3 -m agentic_devops.cli detect /path/to/repo
python3 -m agentic_devops.cli deploy /path/to/repo --env staging --dry-run
python3 -m agentic_devops.cli monitor --target http://localhost:8000/health --type http
```

### `amcp/` — Agent Memory Custodian Protocol

Minimal protocol for user-controlled agent memory ownership with consent-based access, cooperative ownership, and portable migration.

```bash
python3 amcp/main.py demo
python3 amcp/main.py self-test
```

## Design Patterns (from BRAIN_STORM.md)

All modules share patterns from the [design space document](BRAIN_STORM.md):

| Pattern | Used in |
|---------|---------|
| Typed Tool Invocation | Runtime (ToolManifest), DevOps (PipelineStage) |
| Capability Negotiation | Runtime (ToolRegistry.refresh_from_profile) |
| Planner-Executor Separation | DevOps (PipelineEngine) |
| Saga with Compensating Actions | Runtime (executor.execute_saga), DevOps (pipeline compensators) |
| Human Approval Gate | Runtime (PolicyEngine), DevOps (deployment/remediation gates) |
| Provenance and Attestation | Runtime (ExecutionProvenance), DevOps (PipelineProvenance) |
| Observability Layer | DevOps (MonitorEngine, HealthCheck) |

## Framework Adapters

Both `agentic_runtime` and `agentic_devops` provide adapters for:

- **PydanticAI** — agent with tool functions
- **LangGraph** — state graph with policy-gated nodes

These follow the same port-adapter architecture as `amcp/adapters.py`.

## Testing

```bash
# All tests
python3 -m pytest -q

# Per module
python3 -m pytest -q agentic_runtime/
python3 -m pytest -q agentic_devops/
```
