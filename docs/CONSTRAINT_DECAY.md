# Constraint Decay evaluation replication

Paper: [Constraint Decay: The Fragility of LLM Agents in Backend Code Generation](https://arxiv.org/pdf/2605.06445)

## Phase 0 (essential) — completed in-repo

Reproduce paper tables from HuggingFace results (no new LLM spend).

```bash
# One-time: results live under constraint_decay/data/results/ (gitignored, ~3GB)
./scripts/constraint_decay_eval.sh phase-0
```

Artifacts:

- [`constraint_decay/reports/evaluation_tables.txt`](../constraint_decay/reports/evaluation_tables.txt)
- [`constraint_decay/reports/VERIFICATION.md`](../constraint_decay/reports/VERIFICATION.md)
- [`constraint_decay/VENDOR_PIN.txt`](../constraint_decay/VENDOR_PIN.txt)

### HuggingFace download

```bash
pip install huggingface_hub
python3 -c "
from huggingface_hub import hf_hub_download
import zipfile, pathlib
z = hf_hub_download('constraint/constraint_decay', 'results.zip', repo_type='dataset')
pathlib.Path('constraint_decay/data').mkdir(parents=True, exist_ok=True)
zipfile.ZipFile(z).extractall('constraint_decay/data/')
"
```

Dataset: https://huggingface.co/datasets/constraint/constraint_decay/tree/main

### Vendor upstream (blocked)

Official repo: https://anonymous.4open.science/r/constraint-decay — returned HTTP 403 during setup. Local harness: [`constraint_decay/constraint_decay/`](../constraint_decay/constraint_decay/).

## Phase 1 — smoke (optional)

**Requires:** Docker, `LLM_API_KEY`, upstream `main.py` from vendor repo.

```bash
export LLM_API_KEY=...
./scripts/constraint_decay_eval.sh phase-1
```

`# TODO(phase-1)` in [`scripts/constraint_decay_eval.sh`](../scripts/constraint_decay_eval.sh)

## Phase 2 — 16-task subset (optional)

48 runs per model–agent (16 tasks × 3). Task list: [`constraint_decay/SUBSET_TASKS.txt`](../constraint_decay/SUBSET_TASKS.txt).

```bash
export AGENT=mini_swe_sdk
./scripts/constraint_decay_eval.sh phase-2
```

Do **not** use `main.py --task uv` alone — that runs all 40 Python tasks.

## Phase 3 — full study (optional)

~5B tokens; re-run `failure_analysis.py`, `tokens.py` from upstream when available.

`# TODO(phase-3)` in script and [`eval_harness/constraint_decay/__init__.py`](../eval_harness/constraint_decay/__init__.py)

## Metrics (RQ summary)

| RQ | Claim | Phase 0 status |
|----|-------|----------------|
| RQ1 | ~30 pp A% drop L0→L3 | Replicated (−27.6 pp capable mean, Newman-only) |
| RQ2 | Framework disparity | Replicated qualitatively in Table 3 |
| RQ3 | ~45% data-layer logic errors | Needs upstream judge CSVs or phase-3 |

## Environment

Copy [`constraint_decay/.env.template`](../constraint_decay/.env.template) → `constraint_decay/.env` for Phase 1+.
