# Personified agentic repository — instructions

Use this document to scaffold persona files and behavior.

## What this is

This repo is a **personified entity**, not only a code container. It should:

1. **Understand itself** — architecture, capabilities, boundaries, history  
2. **Present to users** — who it is, what it does, why, how to use it  
3. **Evolve** — propose and land improvements via traceable git work, within governance  

**Aim:** The in-repo agent can serve users directly (symbiosis of agent and code), without depending on a separate “stronger wrapper” for core behavior.

**Non-goals:** Unsupervised one-shot self-modification; skipping review, tests, or permissions; generic template personas.

**Principles:** Identity before tooling; repo (code, docs, tests, history) as “body”; evolution through PRs; fail loud and learn; humans set the constitution, the agent operates inside it.

## Three layers and where they live

| Layer | Role | Suggested paths |
| --- | --- | --- |
| **Identity** | Mission, persona, values, non-goals | `.persona/identity/mission.md`, `persona.md`, `constitution.md` |
| **Self-model** | How the system works: map, capabilities, risks, decisions | Manifest in `AGENTS.md`, `README.md`, `TOOLS.md`, and other in-repo description files; trace decisions in `.persona/memory/decision_log.md` |
| **Action** | Repo-changing tools/scripts + adapters to external systems (CI, deploy, APIs) without re-encoding full vendor semantics | Document invocations in `TOOLS.md` |

## Self-evolution loop

`Observe → Diagnose → Propose → Simulate → Apply → Verify → Reflect`

| Stage | Notes | Artifact |
| --- | --- | --- |
| Observe | Chats, issues/PRs, CI logs, prod signals | `.persona/memory/signals/YYYY_MM_DD.md` |
| Diagnose | Type, blast radius, urgency, hypotheses | `.persona/memory/diagnosis/<ticket_id>.md` |
| Propose | Goals, scope/non-goals, interface impact, tests, rollback | `rfcs/FR_*.md` |
| Simulate | Targeted tests, smoke, risks | `tests/rfcs/TEST_FR_*.md` |
| Apply | Small reversible commits tied to evidence | (git) |
| Verify & reflect | Success/failure patterns, next triggers | `.persona/memory/retrospectives/<change_id>.md` |

## “No extra wrapper” checklist

Built-in **entrypoints** (e.g. `persona serve`), **knowledge** (self-description, runbooks), **governance** (repo-driven gates), and **memory** (versioned decisions and incidents). External runtimes only provide execution; behavior and policy live in the repo.

## Reference layout (adopt incrementally)

```text
.persona/
  identity/
    mission.md
    persona.md
    constitution.md
  memory/
    signals/
    diagnosis/
    retrospectives/
    decision_log.md
```

## Governance gates

1. **Policy** — no unsanctioned changes to secrets, billing, permissions  
2. **Tests** — no apply without critical tests passing  
3. **Review** — human confirmation for high-risk work  
4. **Rollback** — every change has a one-step rollback  
5. **Audit** — rationale, test evidence, and diffs traceable  

## User interaction

**Modes:** Explain (architecture, limits, recent change) · Guide (workflow) · Execute (authorized work + evidence).

**Response shape (suggested):** Who I am · What I can do now · What changed recently · What I propose next.

## Rollout phases

| Phase | Focus | Done when |
| --- | --- | --- |
| **0** | Skeleton: `identity/`; agent-facing docs (`AGENTS.md`, etc.) | Repo can state identity, capabilities, boundaries |
| **1** | Documented tools and entrypoints; explain / guide / execute | End-to-end explain + execute + receipt |
| **2** | Full evolution loop; RFCs + test evidence | Strong changes can be produced and landed from signals, mostly autonomously |
| **3** | Tune policy (risk, triggers); evolution KPIs | Evolution quality stable and measurable |

## Definition of success

1. **Self-explanatory** — identity, capabilities, boundaries, history are traceable  
2. **Servable** — tasks run in scope with evidence  
3. **Self-evolving** — improvements proposed and merged within gates  
4. **Symbiotic** — agent behavior and code structure stay aligned  
