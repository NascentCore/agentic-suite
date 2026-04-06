# agentic_suite

A suite of protocols, design principles, and paradigms for building agentic software.

## Components

### AMCP — Agent Memory Custodian Protocol

A minimal protocol for **user-controlled ownership of agent memory**, inspired by AT Protocol concepts (portable identity, explicit consent, content-addressable records).

- **Core policy**: same-runner + original-purpose access is always allowed; cross-purpose access requires explicit consent from every memory owner.
- **Cooperative ownership**: multi-user memories require unanimous consent for cross-purpose use.
- **Framework adapters**: PydanticAI and LangGraph integrations.
- **Migration**: portable memory bundles with manifest integrity checks and staged import/activate lifecycle.

See [`amcp/README.md`](amcp/README.md) for full documentation and [`amcp/ROADMAP.md`](amcp/ROADMAP.md) for the roadmap.

### Personified Software Scaffold

A universal toolkit for turning **any repository** into an agent-ready, personified workspace. Generates standardized agent boot files:

- `SOUL.md` — identity, mission, values, domain context
- `skills.md` — read/modify skill contract
- `AGENTS.md` — boot sequence and operating loop
- `TOOLS.md` — command playbook
- Optional `SKILL.md` compatibility shim

See [`personified_software/README.md`](personified_software/README.md) for usage.

### Design Documents

- [`BRAIN_STORM.md`](BRAIN_STORM.md) — tool protocol patterns and architectural paradigms for agentic systems
- [`personified_software/INSTRUCTIONS.md`](personified_software/INSTRUCTIONS.md) — personified repository design principles and self-evolution loop
- [`docs/FR_IMATE_DEVELOPMENT_PLAN.md`](docs/FR_IMATE_DEVELOPMENT_PLAN.md) — codebase review findings and improvement plan

## Quick Start

```bash
# Install in development mode
pip install -e ".[all]"

# Run AMCP demo
python3 -m amcp.main demo

# Run all tests
python3 -m pytest

# Generate scaffold for any repo
python3 -m personified_software.openclaw_scaffold.cli /path/to/target-repo --dry-run
```

## Project Structure

```
agentic_suite/
├── amcp/                          # Agent Memory Custodian Protocol
│   ├── core.py                    #   policy engine + data models
│   ├── adapters.py                #   PydanticAI + LangGraph integrations
│   ├── migration.py               #   portable memory migration
│   ├── main.py                    #   CLI entry (demo, self-test, export)
│   └── test_*.py                  #   tests (12 tests)
├── personified_software/          # Personified Software toolkit
│   ├── openclaw_scaffold/         #   scaffold generator
│   │   ├── detector.py            #     repo profiling heuristics
│   │   ├── templates.py           #     template rendering (loads from template_assets/)
│   │   ├── generator.py           #     generation orchestration
│   │   ├── cli.py                 #     CLI interface
│   │   ├── models.py              #     data models
│   │   └── template_assets/       #     markdown templates (single source of truth)
│   └── examples/                  #   sample generated output
├── tests/                         # Scaffold tests (64 tests)
├── docs/                          # Development plans and architecture
├── BRAIN_STORM.md                 # Protocol design patterns
└── pyproject.toml                 # Project configuration
```

## Development

```bash
# Install with all dependencies
pip install -e ".[all]"

# Run tests
python3 -m pytest -v

# Lint
ruff check .
```

## License

MIT
