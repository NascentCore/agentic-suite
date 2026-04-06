"""Template system for generating runtime agent configuration files.

Mirrors ``personified_software.openclaw_scaffold.templates`` but produces
*runtime*-oriented markdown documents:

- ``RUNTIME_TOOLS.md``  — tool manifest catalogue
- ``RUNTIME_SKILLS.md`` — runtime interaction skill contract
- ``RUNTIME_AGENTS.md`` — runtime agent boot sequence and operating loop
"""

from __future__ import annotations

from .models import RuntimeProfile


# ---------------------------------------------------------------------------
# RUNTIME_TOOLS.md
# ---------------------------------------------------------------------------

RUNTIME_TOOLS_TEMPLATE = """# RUNTIME_TOOLS.md — {APP_NAME}

> Auto-generated tool catalogue for the running application.

## Application Info
- **Name**: {APP_NAME}
- **Type**: {APP_TYPE}
- **Base URL**: {BASE_URL}
- **Health endpoint**: {HEALTH_ENDPOINT}
- **Auth method**: {AUTH_METHOD}
- **Discovered capabilities**: {CAPABILITY_COUNT}

## Tool Catalogue

{CAPABILITY_LIST}

## Usage Notes
- Tools marked **high_impact** require explicit approval before execution.
- Tools marked **read_only** are safe for autonomous execution.
- All tool invocations are recorded with provenance metadata.
"""


# ---------------------------------------------------------------------------
# RUNTIME_SKILLS.md
# ---------------------------------------------------------------------------

RUNTIME_SKILLS_TEMPLATE = """# RUNTIME_SKILLS.md — Runtime Interaction Skill Contract

## Skill Name
`runtime-interaction-skill`

## Goal
Provide a standard execution contract for agents to interact with the running
application **{APP_NAME}** on behalf of users via natural language.

## Application Profile
- App name: **{APP_NAME}**
- App type: **{APP_TYPE}**
- Base URL: {BASE_URL}
- Available tools: {CAPABILITY_COUNT}

## Input Contract
Expect:
1. User intent expressed in natural language.
2. Optional constraints (safety, scope, target resource).
3. Session context from prior turns.

## Output Contract
Return:
1. Action taken and parameters used.
2. Result or error from the application.
3. Provenance record (tool input/output, policy decisions).
4. Suggested next actions.

## Core Capabilities
### 1) Understand Intent
- Map user natural language to the most appropriate tool.
- Resolve ambiguity by asking clarifying questions.
- Respect session context and prior actions.

### 2) Execute Safely
- Evaluate policy before every tool invocation.
- Require explicit approval for high-impact operations.
- Record full provenance for audit.

### 3) Report Results
- Present results in human-readable form.
- Highlight errors and suggest remediation.
- Track state changes for multi-turn flows.

## Standard Workflow
1. **Parse** — understand user intent and extract parameters.
2. **Match** — find the best tool from the registry.
3. **Gate** — evaluate policy (RBAC, approval, rate limit).
4. **Execute** — invoke the tool handler.
5. **Report** — present results and update session state.

## Hard Guardrails
- Never execute high-impact tools without approval.
- Never fabricate tool responses.
- Never bypass policy engine.
- Record all actions for audit.
"""


# ---------------------------------------------------------------------------
# RUNTIME_AGENTS.md
# ---------------------------------------------------------------------------

RUNTIME_AGENTS_TEMPLATE = """# RUNTIME_AGENTS.md — Runtime Agent Boot Instructions

## Boot Sequence
On initial load, read in this order:
1. `RUNTIME_AGENTS.md` (this file)
2. `RUNTIME_SKILLS.md`
3. `RUNTIME_TOOLS.md`
4. Application documentation

## Operating Loop
1. Receive user message (natural language).
2. Parse intent and extract parameters.
3. Match intent to a registered tool.
4. Evaluate policy for the matched tool.
5. If approved, execute tool and return results.
6. If approval required, request human confirmation.
7. Update session state and suggest next actions.

## Application Facts
- App name: **{APP_NAME}**
- App type: **{APP_TYPE}**
- Base URL: {BASE_URL}
- Health endpoint: {HEALTH_ENDPOINT}

## Policy Summary
- **read_only** tools → auto-approved.
- **bounded_write** tools → allowed with rate limits.
- **high_impact** tools → require explicit human approval.
- All invocations produce provenance records.

## Safety Rules
- Prefer idempotent operations when possible.
- Always confirm destructive actions with the user.
- Never claim success without execution evidence.
- If uncertain, ask for clarification rather than guessing.
"""


# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------

def render_runtime_tools(profile: RuntimeProfile) -> str:
    """Render ``RUNTIME_TOOLS.md`` from a runtime profile."""
    return RUNTIME_TOOLS_TEMPLATE.format(**profile.to_template_context()).strip() + "\n"


def render_runtime_skills(profile: RuntimeProfile) -> str:
    """Render ``RUNTIME_SKILLS.md`` from a runtime profile."""
    return RUNTIME_SKILLS_TEMPLATE.format(**profile.to_template_context()).strip() + "\n"


def render_runtime_agents(profile: RuntimeProfile) -> str:
    """Render ``RUNTIME_AGENTS.md`` from a runtime profile."""
    return RUNTIME_AGENTS_TEMPLATE.format(**profile.to_template_context()).strip() + "\n"
