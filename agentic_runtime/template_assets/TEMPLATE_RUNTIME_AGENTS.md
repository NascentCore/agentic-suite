# TEMPLATE_RUNTIME_AGENTS.md

> Universal template for generating `RUNTIME_AGENTS.md` for a running application.
> Replace placeholders with actual runtime profile values.

# RUNTIME_AGENTS.md — Runtime Agent Boot Instructions

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
