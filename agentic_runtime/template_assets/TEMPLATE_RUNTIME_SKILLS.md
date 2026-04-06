# TEMPLATE_RUNTIME_SKILLS.md

> Universal template for generating `RUNTIME_SKILLS.md` for a running application.
> Replace placeholders with actual runtime profile values.

# RUNTIME_SKILLS.md — Runtime Interaction Skill Contract

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
