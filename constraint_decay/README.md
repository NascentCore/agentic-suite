# Constraint Decay — replication harness

Replication of evaluation metrics for [*Constraint Decay: The Fragility of LLM Agents in Backend Code Generation*](https://arxiv.org/pdf/2605.06445).

Upstream vendor repo ([anonymous.4open.science](https://anonymous.4open.science/r/constraint-decay)) was unavailable (HTTP 403) at vendoring time; this directory contains a compatible aggregation harness and HuggingFace `data/results/`.

See [../docs/CONSTRAINT_DECAY.md](../docs/CONSTRAINT_DECAY.md) for the full roadmap.

**TODO (new experiments):** [PHASES_TODO.md](PHASES_TODO.md) — Phases 1–3 checklist (Docker, API key, vendor `main.py`).

```bash
pip install -e .
python3 -m constraint_decay.evaluation_tables data
```
