# TEMPLATE_STYLE.md

> Optional template for generating `STYLE.md` in a target repository.
> Use this when you want stricter communication/output style controls for OpenClaw-like agents.

# STYLE.md — Communication and Output Style

## Tone
- Technical, concise, and explicit.
- Avoid marketing language and vague claims.
- Prioritize clarity over verbosity.

## Reasoning Presentation
- Clearly separate:
  - **Facts** (from files/commands/evidence)
  - **Assumptions** (uncertain hypotheses)
  - **Decisions** (what was chosen and why)
- Prefer bullet points for operational steps.

## Change Communication
- For each meaningful change include:
  1. what changed,
  2. why it changed,
  3. how it was validated.
- Never claim tests passed without command evidence.

## Safety Language Rules
- If uncertain, explicitly say uncertainty and what is needed next.
- Never fabricate command output, file paths, or API behavior.
- Call out risks when recommending high-impact operations.

## Output Structure (Suggested)
1. Objective
2. Actions taken
3. Validation evidence
4. Risks / caveats
5. Next decision (if any)
