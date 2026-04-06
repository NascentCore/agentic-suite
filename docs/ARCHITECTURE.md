# Architecture Overview — agentic_suite

## Component Relationship

```
┌─────────────────────────────────────────────────────────┐
│                     agentic_suite                        │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  BRAIN_STORM  │    │   personified_software/       │   │
│  │  .md          │    │   INSTRUCTIONS.md             │   │
│  │               │    │                               │   │
│  │  Protocol     │    │  Design principles for        │   │
│  │  patterns &   │    │  personified repositories     │   │
│  │  paradigms    │    │                               │   │
│  └───────┬───────┘    └──────────────┬────────────────┘   │
│          │ informs                   │ guides              │
│          ▼                           ▼                     │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │    amcp/      │    │  openclaw_scaffold/           │   │
│  │               │    │                               │   │
│  │  Memory       │    │  Universal scaffold           │   │
│  │  Custodian    │◄───│  generator for any repo       │   │
│  │  Protocol     │    │                               │   │
│  │               │    │  Generates: SOUL.md,          │   │
│  │  core.py      │    │  skills.md, AGENTS.md,        │   │
│  │  adapters.py  │    │  TOOLS.md, SKILL.md,          │   │
│  │  migration.py │    │  STYLE.md                     │   │
│  └──────────────┘    └──────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │                  .persona/                        │   │
│  │  Living proof that the repo practices what it     │   │
│  │  preaches: identity, memory, decision log         │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## How the Components Relate

### Design Documents → Implementations

- **BRAIN_STORM.md** defines the protocol suite vision (Tool Registry, Policy Engine, Memory Layer, etc.). AMCP implements the **Memory Layer** component.
- **INSTRUCTIONS.md** defines how repositories should be "personified" with identity, self-models, and evolution loops. The **scaffold generator** automates the initial scaffolding step.

### AMCP ← Scaffold

When the scaffold generator profiles a target repository, it detects capabilities and governance needs. AMCP's consent-based memory model can then be applied to the scaffolded workspace — the scaffold creates the agent identity files, and AMCP governs how agent memory is accessed across those agents.

### .persona/ ← INSTRUCTIONS.md

The `.persona/` directory is a concrete instantiation of the design described in `INSTRUCTIONS.md`. It serves as a reference implementation within this repository.

---

## AMCP Internal Architecture

```
┌─────────────────────────────────────────────┐
│  Layer 1: Core (amcp/core.py)               │
│  - MemoryRecord, ConsentGrant, AccessRequest│
│  - MemoryCustodian policy engine            │
│  - AMCPRepositoryBundle                     │
│  - No framework dependencies                │
├─────────────────────────────────────────────┤
│  Layer 2: Adapters (amcp/adapters.py)       │
│  - PydanticAI: create_pydantic_ai_amcp_agent│
│  - LangGraph: build_langgraph_amcp_app      │
│  - Framework-specific control flow mapping  │
├─────────────────────────────────────────────┤
│  Layer 3: Migration (amcp/migration.py)     │
│  - MigrationManifestV1 + EnvelopeV1        │
│  - Export/import/activate lifecycle         │
│  - Consent portability policy               │
│  - Integrity verification (SHA-256)         │
└─────────────────────────────────────────────┘
```

**Key invariant**: Policy logic lives exclusively in Layer 1. Adapters and migration never modify policy semantics — they only translate between frameworks/formats and the core policy engine.

---

## Scaffold Internal Architecture

```
┌──────────────────────────────────────────┐
│  CLI (cli.py)                            │
│  argparse entry point                    │
├──────────────────────────────────────────┤
│  Generator (generator.py)                │
│  Orchestrates profiling → rendering →    │
│  file writing with safe defaults         │
├──────────┬───────────────────────────────┤
│ Detector │  Templates (templates.py)     │
│(detector │  Loads .md from               │
│  .py)    │  template_assets/             │
│          │  Single source of truth       │
├──────────┴───────────────────────────────┤
│  Models (models.py)                      │
│  RepoProfile, ScaffoldOptions,           │
│  ScaffoldResult, RenderedArtifact        │
└──────────────────────────────────────────┘
```

---

## Design Principles

1. **Separation of concerns**: Design docs inform but do not directly couple to implementations.
2. **Policy as code**: AMCP policy is deterministic, framework-agnostic, and testable in isolation.
3. **Single source of truth**: Template content lives in `template_assets/` .md files, not in Python strings.
4. **Universal over specific**: The scaffold generator uses generic heuristics, not repo-specific hardcoding.
5. **Evidence-first**: All components are tested (81 tests across AMCP and scaffold modules).
