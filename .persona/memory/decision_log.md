# Decision Log — agentic_suite

This log records significant architectural and design decisions for traceability.

## Format

Each entry follows:

```
## [YYYY-MM-DD] Decision Title

**Context**: Why this decision was needed.
**Decision**: What was decided.
**Rationale**: Why this option was chosen over alternatives.
**Consequences**: What changes, risks, or follow-ups result.
```

---

## [2026-04-06] Deep codebase review and improvement plan

**Context**: The repository had accumulated several structural issues since initial development: broken import paths, template duplication, hardcoded detector values, missing project configuration, and zero test coverage for the scaffold module.

**Decision**: Conducted a comprehensive review of all 16 Python files and 25 Markdown files. Created `docs/FR_IMATE_DEVELOPMENT_PLAN.md` as a formal improvement plan with prioritized tasks.

**Rationale**: A systematic review-first approach ensures fixes address root causes rather than symptoms, and the prioritized plan prevents ad-hoc changes from introducing new inconsistencies.

**Consequences**:
- P0 fixes (import paths, pyproject.toml) made the codebase runnable
- P1 fixes (deduplication, README paths, scaffold tests) established a safety net
- P2 refactors (template single-source, detector de-hardcoding) improved architecture
- P3 improvements (README, .persona/, AMCP docs) filled documentation gaps
