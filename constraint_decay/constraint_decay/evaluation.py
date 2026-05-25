"""Aggregate Newman results into A% and pass@k (paper §4)."""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from constraint_decay.newman_metrics import assertion_pass_rate_from_csv, run_passed
from constraint_decay.task_levels import (
    constraint_level,
    framework_from_task,
    is_generation_task,
)

GENERATION_RUNTIMES = ("uv", "node")
FEATURE_RUNTIMES = ("aiohttp", "express", "fastapi", "flask", "honojs")
AGENTS = ("mini_swe_sdk", "openhands_sdk")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator (Chen et al., 2021)."""
    if n < k:
        return float("nan")
    if c == 0:
        return 0.0
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


@dataclass
class RunRecord:
    runtime: str
    agent: str
    model: str
    task: str
    run_id: str
    a_pct: float
    passed: bool


def _find_newman_csv(run_dir: Path) -> Path | None:
    for p in sorted(run_dir.glob("newman-run-report-*.csv")):
        if p.name.startswith("._"):
            continue
        return p
    return None


def iter_run_records(results_root: Path) -> list[RunRecord]:
    records: list[RunRecord] = []
    if not results_root.is_dir():
        return records
    for runtime_dir in sorted(results_root.iterdir()):
        if not runtime_dir.is_dir():
            continue
        runtime = runtime_dir.name
        for agent_dir in runtime_dir.iterdir():
            if not agent_dir.is_dir() or agent_dir.name not in AGENTS:
                continue
            agent = agent_dir.name
            for model_dir in agent_dir.iterdir():
                if not model_dir.is_dir():
                    continue
                model = model_dir.name
                for task_dir in model_dir.iterdir():
                    if not task_dir.is_dir():
                        continue
                    task = task_dir.name
                    for date_dir in task_dir.iterdir():
                        if not date_dir.is_dir():
                            continue
                        for run_dir in date_dir.iterdir():
                            if not run_dir.is_dir() or not run_dir.name.startswith(
                                "run_"
                            ):
                                continue
                            csv_path = _find_newman_csv(run_dir)
                            if csv_path is None:
                                continue
                            rate = assertion_pass_rate_from_csv(csv_path)
                            if rate is None:
                                continue
                            records.append(
                                RunRecord(
                                    runtime=runtime,
                                    agent=agent,
                                    model=model,
                                    task=task,
                                    run_id=run_dir.name,
                                    a_pct=rate,
                                    passed=run_passed(rate),
                                )
                            )
    return records


def aggregate_generation(
    records: list[RunRecord],
    *,
    apply_verifier: bool = False,
) -> dict[tuple[str, str], dict[int, list[float]]]:
    """Map (agent, model) -> level -> list of per-task mean A%."""
    # task -> list of run rates
    by_task: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for r in records:
        if r.runtime not in GENERATION_RUNTIMES:
            continue
        if not is_generation_task(r.task, r.runtime):
            continue
        by_task[(r.agent, r.model, r.runtime, r.task)].append(r.a_pct)

    out: dict[tuple[str, str], dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for (agent, model, runtime, task), rates in by_task.items():
        level = constraint_level(task)
        if level is None:
            continue
        mean_rate = sum(rates) / len(rates)
        # Without verifier artifacts in HF export, apply_verifier is a no-op placeholder.
        if apply_verifier:
            pass
        out[(agent, model)][level].append(mean_rate)
    return out


def mean_level_a_pct(
    level_map: dict[int, list[float]],
) -> dict[int, float]:
    return {lv: sum(v) / len(v) if v else float("nan") for lv, v in level_map.items()}


def pass_at_1_by_level(
    records: list[RunRecord],
) -> dict[tuple[str, str], dict[int, list[float]]]:
    """Per-task pass@1 (%), grouped by constraint level."""
    by_task_runs: dict[tuple[str, str, str, str], list[bool]] = defaultdict(list)
    for r in records:
        if r.runtime not in GENERATION_RUNTIMES:
            continue
        if not is_generation_task(r.task, r.runtime):
            continue
        by_task_runs[(r.agent, r.model, r.runtime, r.task)].append(r.passed)

    out: dict[tuple[str, str], dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for (agent, model, runtime, task), passes in by_task_runs.items():
        level = constraint_level(task)
        if level is None:
            continue
        n = len(passes)
        c = sum(1 for p in passes if p)
        out[(agent, model)][level].append(100.0 * pass_at_k(n, c, 1))
    return out


def framework_a_pct(
    records: list[RunRecord],
) -> dict[tuple[str, str], dict[str, list[float]]]:
    out: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for r in records:
        if r.runtime not in GENERATION_RUNTIMES:
            continue
        if not is_generation_task(r.task, r.runtime):
            continue
        fw = framework_from_task(r.task)
        if fw is None:
            continue
        out[(r.agent, r.model)][fw].append(r.a_pct)
    return out


def marginal_constraint_effects(
    records: list[RunRecord],
) -> dict[str, tuple[float, float]]:
    """Matched-pair ΔA% per constraint axis (Table 2a). Simplified SEM."""
    task_means: dict[tuple[str, str, str, str], float] = {}
    by_task_runs: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for r in records:
        if r.runtime not in GENERATION_RUNTIMES:
            continue
        if not is_generation_task(r.task, r.runtime):
            continue
        by_task_runs[(r.agent, r.model, r.runtime, r.task)].append(r.a_pct)
    for key, vals in by_task_runs.items():
        task_means[key] = sum(vals) / len(vals)

    pairs: dict[str, list[float]] = defaultdict(list)

    def add_pair(name: str, with_c: float, without_c: float) -> None:
        pairs[name].append(with_c - without_c)

    for (agent, model, runtime, task), a in task_means.items():
        fw = framework_from_task(task)
        if fw is None:
            continue
        level = constraint_level(task)
        if level is None:
            continue
        # Match tasks differing by one constraint — compare means across configs.
        _ = agent, model, runtime, fw, level, a

    # Explicit matched pairs from task naming (same framework, one constraint flip).
    all_tasks = {
        (agent, model, runtime, task): a
        for (agent, model, runtime, task), a in task_means.items()
    }

    def find_task(fw: str, runtime: str, suffix: str) -> str:
        return f"{fw}-openapi-{suffix}"

    for (agent, model, runtime, task), a_with in all_tasks.items():
        fw = framework_from_task(task)
        if fw is None:
            continue
        orm_py, orm_node = "sqlalchemy", "sequelize"
        orm = orm_py if runtime == "uv" else orm_node

        candidates = [
            (
                "Clean architecture",
                find_task(fw, runtime, "clean_architecture"),
                find_task(fw, runtime, "unconstrained"),
            ),
            (
                "PostgreSQL",
                find_task(fw, runtime, "postgres"),
                find_task(fw, runtime, "unconstrained"),
            ),
            (
                "SQLite",
                find_task(fw, runtime, "sqlite"),
                find_task(fw, runtime, "unconstrained"),
            ),
            (
                "SQLAlchemy" if runtime == "uv" else "Sequelize",
                find_task(fw, runtime, f"postgres-{orm}"),
                find_task(fw, runtime, "postgres"),
            ),
        ]
        for cname, with_name, without_name in candidates:
            key_with = (agent, model, runtime, with_name)
            key_without = (agent, model, runtime, without_name)
            if key_with in all_tasks and key_without in all_tasks:
                add_pair(cname, all_tasks[key_with], all_tasks[key_without])

    result: dict[str, tuple[float, float]] = {}
    for name, deltas in pairs.items():
        if not deltas:
            continue
        mean = sum(deltas) / len(deltas)
        if len(deltas) > 1:
            var = sum((d - mean) ** 2 for d in deltas) / (len(deltas) - 1)
            sem = math.sqrt(var / len(deltas))
        else:
            sem = 0.0
        result[name] = (mean, sem)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate constraint-decay results")
    parser.add_argument("results_path", type=Path)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--agent", default=None)
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    root = args.results_path
    if (root / "results").is_dir():
        root = root / "results"
    records = iter_run_records(root)
    if args.agent:
        records = [r for r in records if r.agent == args.agent]
    if args.model:
        records = [r for r in records if r.model == args.model]

    gen = aggregate_generation(records)
    print(f"Loaded {len(records)} runs with Newman CSVs")
    if not args.summary:
        return

    print(f"Generation task means by level:")
    for (agent, model), levels in sorted(gen.items()):
        means = mean_level_a_pct(levels)
        parts = [f"L{lv}={means.get(lv, float('nan')):.1f}" for lv in range(4)]
        d = means.get(3, float("nan")) - means.get(0, float("nan"))
        print(f"  {agent} / {model}: {', '.join(parts)}  Δ(L3-L0)={d:+.1f}pp")


if __name__ == "__main__":
    main()
