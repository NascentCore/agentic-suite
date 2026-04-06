# Agentic Runtime

Natural-language interface for interacting with **running software**.

## What this module provides

Agentic Runtime automatically discovers what a running application can do
(API endpoints, CLI commands, database operations, etc.) and exposes those
capabilities as typed tools that an LLM agent can invoke on behalf of users
through conversation.

### Position in the Agentic Suite

| Layer | Module | Purpose |
|-------|--------|---------|
| **Agentic Repo** | `personified_software/openclaw_scaffold/` | Developer ↔ Code (via conversation) |
| **Agentic Runtime** | `agentic_runtime/` ← **this** | User ↔ Running Software (via conversation) |
| **Agentic DevOps** | `agentic_devops/` | Automated deploy, monitor, incident response |

## Architecture

```
runtime_detector.py   →  Discover capabilities (OpenAPI, CLI, manifest)
        ↓
tool_registry.py      →  Register typed tool manifests
        ↓
policy_engine.py      →  Evaluate RBAC / approval / rate limits
        ↓
executor.py           →  Execute tools safely (sync, saga compensation)
        ↓
session.py            →  Track multi-turn conversation state
        ↓
adapters.py           →  PydanticAI agent / LangGraph graph
        ↓
templates.py          →  Generate RUNTIME_TOOLS.md / SKILLS / AGENTS
        ↓
cli.py                →  CLI entrypoint: profile / generate / execute
```

## Key patterns reused from BRAIN_STORM.md

| Pattern | Where used |
|---------|------------|
| Typed Tool Invocation | `ToolManifest` + `ToolRegistry` |
| Policy Engine | `RuntimePolicyEngine` (RBAC + approval + rate limit) |
| Human Approval Gate | `require_approval` action + approval token flow |
| Saga with Compensating Actions | `RuntimeExecutor.execute_saga()` |
| Provenance and Attestation | `ExecutionProvenance` on every response |
| Capability Negotiation | `ToolRegistry.refresh_from_profile()` |

## Quick start

### 1) Detect runtime capabilities

```bash
# From an OpenAPI spec
python3 -m agentic_runtime.cli profile --app-name my-api --openapi-url http://localhost:8000/openapi.json

# From a manifest file
python3 -m agentic_runtime.cli profile --app-name my-app --manifest runtime_manifest.yaml --output profile.json
```

### 2) Generate agent config files

```bash
python3 -m agentic_runtime.cli generate --profile profile.json --output-dir ./runtime_config
```

Generates:
- `RUNTIME_TOOLS.md` — tool catalogue
- `RUNTIME_SKILLS.md` — interaction skill contract
- `RUNTIME_AGENTS.md` — agent boot instructions

### 3) Execute a tool

```bash
python3 -m agentic_runtime.cli execute --profile profile.json --tool list_users --params '{"limit": 10}'
```

## Framework adapters

### PydanticAI

```python
from agentic_runtime.adapters import create_runtime_pydantic_agent, RuntimeAgentDeps

agent = create_runtime_pydantic_agent(profile, model="openai:gpt-4o")
```

### LangGraph

```python
from agentic_runtime.adapters import build_runtime_langgraph_app

app = build_runtime_langgraph_app(profile)
result = app.invoke({...})
```

## Testing

```bash
python3 -m pytest -q agentic_runtime/
```
