#!/usr/bin/env bash
# Constraint Decay evaluation wrapper (Agentic Suite)
#
# Phase 0: analyze pre-published HuggingFace results (no LLM).
# Phases 1-3: run new agent experiments — see constraint_decay/PHASES_TODO.md
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CDIR="${ROOT}/constraint_decay"
DATA="${CDIR}/data"
RESULTS="${DATA}/results"
PHASES_TODO="${CDIR}/PHASES_TODO.md"

phase0_tables() {
  cd "${CDIR}"
  python3 -m constraint_decay.evaluation_tables data "$@"
  python3 -m constraint_decay.failure_analysis_summary "${DATA}" > reports/rq3_summary.txt
}

require_phase_prereqs() {
  local phase="$1"
  if ! command -v docker >/dev/null 2>&1; then
    echo "SKIP phase-${phase}: docker not available (TODO: install Docker — see ${PHASES_TODO})"
    return 2
  fi
  if [[ -z "${LLM_API_KEY:-}" ]]; then
    echo "SKIP phase-${phase}: set LLM_API_KEY (TODO: OpenRouter or provider key in constraint_decay/.env)"
    return 2
  fi
  if [[ ! -f "${CDIR}/main.py" ]]; then
    echo "SKIP phase-${phase}: upstream main.py missing (TODO: vendor constraint-decay repo — ${PHASES_TODO})"
    return 2
  fi
  if [[ ! -f "${CDIR}/.env" ]] && [[ -f "${CDIR}/.env.template" ]]; then
    echo "WARN phase-${phase}: copy constraint_decay/.env.template to .env and set TASKS/RESULTS paths"
  fi
  return 0
}

# Phase 0 — default: regenerate tables from HF results (no API key)
if [[ "${1:-phase-0}" == "phase-0" ]]; then
  phase0_tables
  exit 0
fi

# TODO(phase-1): Smoke — 1 task, 1 run; validate Docker + agent + Newman pipeline
#   ./scripts/constraint_decay_eval.sh phase-1
#   Checklist: constraint_decay/PHASES_TODO.md § Phase 1
if [[ "$1" == "phase-1" ]]; then
  require_phase_prereqs 1 || exit $?
  cd "${CDIR}"
  # TODO(phase-1): pin Mini-SWE / OpenHands versions in VENDOR_PIN.txt after first success
  uv run main.py --agent "${AGENT:-mini_swe_sdk}" \
    --task uv/uv-flask-openapi-unconstrained.json
  # TODO(phase-1): run phase-0 after to compare new run vs HF baseline
  exit 0
fi

# TODO(phase-2): Paper 16-task subset — 48 runs per model–agent (SUBSET_TASKS.txt)
#   AGENT=mini_swe_sdk LLM_API_KEY=... ./scripts/constraint_decay_eval.sh phase-2
#   Do NOT use: main.py --task uv  (runs all 40 Python tasks)
if [[ "$1" == "phase-2" ]]; then
  require_phase_prereqs 2 || exit $?
  AGENT="${AGENT:-mini_swe_sdk}"
  cd "${CDIR}"
  while read -r task; do
    [[ "$task" =~ ^#|^$ ]] && continue
    # TODO(phase-2): add --evaluate to re-score existing patches without re-agent
    uv run main.py --agent "${AGENT}" --task "$task" --runs "${RUNS:-3}"
  done < SUBSET_TASKS.txt
  # TODO(phase-2): ./scripts/constraint_decay_eval.sh phase-0
  exit 0
fi

# TODO(phase-3): Full study — 80 greenfield + 20 feature tasks, ~5B tokens
#   See PHASES_TODO.md for: --task uv|node|express|..., failure_analysis*.py, tokens.py
if [[ "$1" == "phase-3" ]]; then
  require_phase_prereqs 3 || exit $?
  cat <<EOF
phase-3 is not fully scripted here (too large for one command).

TODO(phase-3):
  1. uv run main.py --agent \$AGENT --task uv --runs 3
  2. uv run main.py --agent \$AGENT --task node --runs 3
  3. uv run main.py --agent \$AGENT --task express  (and flask, fastapi, aiohttp, honojs) --runs 3
  4. uv run failure_analysis.py / failure_analysis_logic.py (RQ3)
  5. uv run tokens.py data/results
  6. ./scripts/constraint_decay_eval.sh phase-0

Full checklist: ${PHASES_TODO}
EOF
  exit 2
fi

echo "Usage: $0 [phase-0|phase-1|phase-2|phase-3]"
echo "Phase 1-3 TODOs: ${PHASES_TODO}"
exit 1
