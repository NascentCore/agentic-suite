"""Feature-implementation task pass@1 (paper Table 2b)."""

from __future__ import annotations

from collections import defaultdict

from constraint_decay.evaluation import pass_at_k
from constraint_decay.evaluation import iter_run_records as _iter  # noqa: F401

FEATURE_RUNTIMES = frozenset({"aiohttp", "express", "fastapi", "flask", "honojs"})


def feature_pass_at_1_table(records) -> str:
    by_task: dict[tuple[str, str, str], list[bool]] = defaultdict(list)
    for r in records:
        if r.runtime not in FEATURE_RUNTIMES:
            continue
        by_task[(r.agent, r.model, r.task)].append(r.passed)

    per_config: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (agent, model, _task), passes in by_task.items():
        n = len(passes)
        c = sum(1 for p in passes if p)
        per_config[(agent, model)].append(100.0 * pass_at_k(n, c, 1))

    lines = ["Table 2b: Feature implementation pass@1 (%)"]
    lines.append(f"{'Model':<22} {'Mini-SWE':>10} {'OpenHands':>10}")
    models = sorted({m for _, m in per_config})
    for model in models:
        m_vals = per_config.get(("mini_swe_sdk", model), [])
        o_vals = per_config.get(("openhands_sdk", model), [])
        m_avg = sum(m_vals) / len(m_vals) if m_vals else float("nan")
        o_avg = sum(o_vals) / len(o_vals) if o_vals else float("nan")
        lines.append(f"{model:<22} {m_avg:10.1f} {o_avg:10.1f}")
    return "\n".join(lines)


def main() -> None:
    import argparse
    from pathlib import Path

    from constraint_decay.evaluation import iter_run_records

    parser = argparse.ArgumentParser()
    parser.add_argument("results_path", type=Path)
    args = parser.parse_args()
    root = args.results_path
    if (root / "results").is_dir():
        root = root / "results"
    records = iter_run_records(root)
    print(feature_pass_at_1_table(records))


if __name__ == "__main__":
    main()
