#!/usr/bin/env bash
# Constraint Decay evaluation wrapper (Agentic Suite)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CDIR="${ROOT}/constraint_decay"
DATA="${CDIR}/data"
RESULTS="${DATA}/results"

phase0_tables() {
  cd "${CDIR}"
  python3 -m constraint_decay.evaluation_tables data "$@"
  python3 -m constraint_decay.failure_analysis_summary "${DATA}" > reports/rq3_summary.txt
}

# TODO(phase-0): default entry — regenerate paper tables from HF results
if [[ "${1:-phase-0}" == "phase-0" ]]; then
  phase0_tables
  exit 0
fi

# TODO(phase-1): smoke run — requires Docker + LLM_API_KEY + upstream main.py
if [[ "$1" == "phase-1" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "SKIP phase-1: docker not available"
    exit 2
  fi
  if [[ -z "${LLM_API_KEY:-}" ]]; then
    echo "SKIP phase-1: set LLM_API_KEY"
    exit 2
  fi
  if [[ ! -f "${CDIR}/main.py" ]]; then
    echo "SKIP phase-1: upstream main.py missing (vendor repo 403); cannot run agent"
    exit 2
  fi
  cd "${CDIR}"
  uv run main.py --agent mini_swe_sdk --task uv/uv-flask-openapi-unconstrained.json
  exit 0
fi

# TODO(phase-2): 16-task subset — loop SUBSET_TASKS.txt
if [[ "$1" == "phase-2" ]]; then
  if [[ ! -f "${CDIR}/main.py" ]]; then
    echo "SKIP phase-2: upstream main.py missing"
    exit 2
  fi
  AGENT="${AGENT:-mini_swe_sdk}"
  cd "${CDIR}"
  while read -r task; do
    [[ "$task" =~ ^#|^$ ]] && continue
    uv run main.py --agent "${AGENT}" --task "$task" --runs 3
  done < SUBSET_TASKS.txt
  exit 0
fi

# TODO(phase-3): full study + failure judges + tokens.py
if [[ "$1" == "phase-3" ]]; then
  echo "SKIP phase-3: requires upstream repo, ~5B tokens, Docker — see docs/CONSTRAINT_DECAY.md"
  exit 2
fi

echo "Usage: $0 [phase-0|phase-1|phase-2|phase-3]"
exit 1
