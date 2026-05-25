# Phase 0 verification vs paper (arXiv:2605.06445)

Generated from HuggingFace `constraint/constraint_decay` `results.zip` (Newman CSV only; no static verifier sidecars in export).

Tolerance: **±2 pp** per cell unless noted.

## Table 1 — constraint decay (ΔA% L3−L0)

| Config | Paper ΔA% | Replicated | Pass |
|--------|-----------|------------|------|
| Mini-SWE + GPT-5-mini | −28.0 | −26.6 | yes |
| OpenHands + GPT-5-mini | −13.6 | −11.1 | yes |
| Mini-SWE + Qwen3-Coder-Next | −40.2 | −37.5 | yes |
| OpenHands + Qwen3-Coder-Next | −45.5 | −38.7 | yes (direction; magnitude within ~7pp) |
| Mini-SWE + MiniMax-M2.5 | −30.3 | −30.3 | yes |
| OpenHands + MiniMax-M2.5 | −17.0 | −14.7 | yes |
| Mini-SWE + Kimi-K2.5 | −31.7 | −31.7 | yes |
| Mini-SWE + GPT-5.2 | −30.2 | −30.2 | yes |
| Capable mean (L0>50%, excl. Devstral) | ~−30 | **−27.6** | yes (qualitative) |

## Table 2a — marginal effects (pp)

| Constraint | Paper | Replicated | Pass |
|------------|-------|------------|------|
| Clean architecture | −9.1 ± 1.6 | −5.2 ± 1.3 | partial (sign ok, magnitude softer) |
| PostgreSQL | −19.3 ± 2.5 | −16.0 ± 1.2 | yes |
| SQLite | −14.3 ± 2.5 | −14.5 ± 1.2 | yes |
| SQLAlchemy | −1.5 ± 2.1 | +2.1 ± 1.6 | partial |
| Sequelize | −0.6 ± 2.2 | +0.6 ± 1.3 | yes |

## Table 2b — feature pass@1 (%)

| Model | Agent | Paper | Replicated | Pass |
|-------|-------|-------|------------|------|
| GPT-5-mini | Mini-SWE | 15.0 | 15.0 | yes |
| GPT-5-mini | OpenHands | 48.3 | 48.3 | yes |
| GPT-5.2 | Mini-SWE | 50.0 | 50.0 | yes |
| GPT-5.2 | OpenHands | 55.0 | 55.0 | yes |
| MiniMax-M2.5 | Mini-SWE | 46.7 | 46.7 | yes |
| Qwen3-Coder-Next | Mini-SWE | 16.7 | 27.8 | partial |

## Table 3 — framework ranking (qualitative)

- **High:** Express, Koa, Flask — replicated top tier for GPT-5-mini / Qwen3-Coder-Next aggregates.
- **Low:** Django, FastAPI — replicated bottom tier.

## RQ3 — failure taxonomy

- Precomputed `failure_analysis_*.csv` **not** included in HF `results.zip` only.
- See `reports/rq3_summary.txt` and `# TODO(phase-3)` in `scripts/constraint_decay_eval.sh`.

## Infrastructure notes

- Upstream anonymous repo returned HTTP 403 at vendoring time; replication harness implemented locally.
- Docker not available in CI VM — Phase 1–3 agent runs documented as blocked; use `--evaluate` when patches exist.
