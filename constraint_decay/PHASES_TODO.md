# TODO: Run Phases 1–3 (new experiments)

Phase 0 (analyze HuggingFace results only) is done. Use this checklist for **new agent runs**.

## Prerequisites (all phases)

- [ ] **TODO:** Clone vendor repo when available: https://anonymous.4open.science/r/constraint-decay → `constraint_decay/main.py`, `runtime/`, `data/tasks/`
- [ ] **TODO:** Install Docker + Docker Compose; verify `docker compose version`
- [ ] **TODO:** Install `uv` (Python 3.12+): `cd constraint_decay && uv sync`
- [ ] **TODO:** Copy `.env.template` → `.env` and set paths + API (see OpenRouter below)
- [ ] **TODO:** Record vendor commit in `VENDOR_PIN.txt`

### OpenRouter (optional provider)

```bash
# constraint_decay/.env
LLM_API_KEY=<OPENROUTER_API_KEY>
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini   # or paper model if available on OpenRouter
```

LiteLLM must accept the model id you choose.

---

## Phase 1 — smoke (1 task, 1 run)

**Goal:** End-to-end agent → patch → Newman + verifiers on one L0 task.

- [ ] **TODO:** Set `LLM_API_KEY` (and `LLM_BASE_URL` if using OpenRouter)
- [ ] **TODO:** Vendor upstream `main.py` + `runtime/flask` Docker compose
- [ ] **TODO:** Run: `./scripts/constraint_decay_eval.sh phase-1`
  - Equivalent: `uv run main.py --agent mini_swe_sdk --task uv/uv-flask-openapi-unconstrained.json`
- [ ] **TODO:** Confirm output under `data/results/uv/mini_swe_sdk/<model>/flask-openapi-unconstrained/.../run_0/`
- [ ] **TODO:** Re-score only: `uv run main.py --agent mini_swe_sdk --task uv/uv-flask-openapi-unconstrained.json --evaluate`
- [ ] **TODO:** Do not modify upstream `runtime/agents/` prompts (Appendix J fidelity)

**Blockers if SKIP exit 2:** no Docker, no API key, no `main.py`.

---

## Phase 2 — 16-task cost subset (48 runs per model–agent)

**Goal:** Reproduce decay *trends* on paper subset (aiohttp, fastapi, express, fastify × L0–L3).

- [ ] **TODO:** Complete Phase 1 successfully
- [ ] **TODO:** Choose `AGENT` (`mini_swe_sdk` or `openhands_sdk`) and model in `.env`
- [ ] **TODO:** Review task list: `constraint_decay/SUBSET_TASKS.txt` (16 paths, not `--task uv`)
- [ ] **TODO:** Run: `AGENT=mini_swe_sdk ./scripts/constraint_decay_eval.sh phase-2`
- [ ] **TODO:** Budget: 16 tasks × 3 runs × token cost per agent step
- [ ] **TODO:** After runs: `./scripts/constraint_decay_eval.sh phase-0` to refresh tables
- [ ] **TODO:** Compare subset ΔA% to paper Appendix A (expect r ≈ 0.98 vs full 80 tasks if you later run Phase 3)

---

## Phase 3 — full replication + RQ3

**Goal:** 80 greenfield + 20 feature tasks; failure taxonomy; token tables (~5B tokens paper-scale).

- [ ] **TODO:** Explicit budget sign-off before starting
- [ ] **TODO:** Generation (Python): `uv run main.py --agent <agent> --task uv --runs 3`
- [ ] **TODO:** Generation (Node): `uv run main.py --agent <agent> --task node --runs 3`
- [ ] **TODO:** Feature tasks per framework dir, e.g. `uv run main.py --agent <agent> --task express --runs 3`
- [ ] **TODO:** RQ3 coarse: `uv run failure_analysis.py data/results --agent ... --model ... --output data/failure_analysis_<model>.csv`
- [ ] **TODO:** RQ3 logic subcategories: `uv run failure_analysis_logic.py ... --output data/logic_subcategories.csv`
- [ ] **TODO:** Token appendix: `uv run tokens.py data/results --agent mini_swe_sdk` (and `openhands_sdk`)
- [ ] **TODO:** Update `reports/VERIFICATION.md` with judge CSV data-layer share (~45% target)
- [ ] **TODO:** Optional CI workflow (Docker + secrets) — separate from main Agentic Suite pytest

---

## Quick commands

| Phase | Command |
|-------|---------|
| 0 | `./scripts/constraint_decay_eval.sh phase-0` |
| 1 | `export LLM_API_KEY=... && ./scripts/constraint_decay_eval.sh phase-1` |
| 2 | `export LLM_API_KEY=... AGENT=mini_swe_sdk ./scripts/constraint_decay_eval.sh phase-2` |
| 3 | See checklist above; `./scripts/constraint_decay_eval.sh phase-3` is a stub until upstream is vendored |
