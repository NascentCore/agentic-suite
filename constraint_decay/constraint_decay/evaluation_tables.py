"""Reproduce paper Tables 1–3 and marginal effects (§5)."""

from __future__ import annotations

import argparse
from pathlib import Path

from constraint_decay.evaluation import (
    aggregate_generation,
    framework_a_pct,
    iter_run_records,
    marginal_constraint_effects,
    mean_level_a_pct,
    pass_at_1_by_level,
)
from constraint_decay.evaluation_feature import feature_pass_at_1_table

CAPABLE_L0_THRESHOLD = 50.0
EXCLUDE_MODELS = frozenset({"devstral-small"})

DISPLAY_NAMES = {
    "mini_swe_sdk": "Mini-SWE",
    "openhands_sdk": "OpenHands",
    "gpt-5-mini": "GPT-5-mini",
    "qwen3-coder-next": "Qwen3-Coder-Next",
    "qwen3-235b-a22b": "Qwen3-235B-A22B",
    "minimax-m2.5": "MiniMax-M2.5",
    "kimi-k2.5": "Kimi-K2.5",
    "gpt-5.2": "GPT-5.2",
}


def _results_root(path: Path) -> Path:
    if (path / "results").is_dir():
        return path / "results"
    return path


def format_table1(records, *, raw: bool = False) -> str:
    gen = aggregate_generation(records, apply_verifier=not raw)
    pass1 = pass_at_1_by_level(records)
    lines = []
    title = "Table 1-raw (no verifiers)" if raw else "Table 1: A% and pass@1 by constraint level"
    lines.append(title)
    lines.append(f"{'Agent':<12} {'Model':<22} {'L0':>6} {'L1':>6} {'L2':>6} {'L3':>6}  "
                 f"{'p@1 L0':>7} {'p@1 L3':>7} {'ΔA%':>7}")
    capable_deltas: list[float] = []

    for (agent, model), levels in sorted(gen.items()):
        if model in EXCLUDE_MODELS:
            continue
        means = mean_level_a_pct(levels)
        p1 = pass_at_1_by_level(records)[(agent, model)]
        p1_means = mean_level_a_pct(p1)
        delta = means.get(3, float("nan")) - means.get(0, float("nan"))
        if means.get(0, 0) > CAPABLE_L0_THRESHOLD:
            capable_deltas.append(delta)
        ag = DISPLAY_NAMES.get(agent, agent)
        mo = DISPLAY_NAMES.get(model, model)
        lines.append(
            f"{ag:<12} {mo:<22} "
            f"{means.get(0, float('nan')):6.1f} {means.get(1, float('nan')):6.1f} "
            f"{means.get(2, float('nan')):6.1f} {means.get(3, float('nan')):6.1f}  "
            f"{p1_means.get(0, float('nan')):7.1f} {p1_means.get(3, float('nan')):7.1f} "
            f"{delta:+7.1f}"
        )
    if capable_deltas:
        avg = sum(capable_deltas) / len(capable_deltas)
        lines.append(f"\nCapable configs (L0>{CAPABLE_L0_THRESHOLD}%): mean ΔA%(L3-L0) = {avg:+.1f} pp (n={len(capable_deltas)})")
    lines.append(
        "\nNote: HF results export has no verifier sidecars; A% is from Newman CSV only "
        "(paper Table 1-raw; full Table 1 differs by ≤2.7 pp)."
    )
    return "\n".join(lines)


def format_table2a(records) -> str:
    effects = marginal_constraint_effects(records)
    lines = ["Table 2a: Marginal constraint effects (matched-pair ΔA%, pp)"]
    for name in (
        "Clean architecture",
        "PostgreSQL",
        "SQLite",
        "SQLAlchemy",
        "Sequelize",
    ):
        if name not in effects:
            continue
        mean, sem = effects[name]
        lines.append(f"  {name:<22} {mean:+.1f} ± {sem:.1f}")
    return "\n".join(lines)


def format_table3(records) -> str:
    fw_data = framework_a_pct(records)
    lines = ["Table 3: A% by framework (aggregated across levels)"]
    focus_models = ("gpt-5-mini", "qwen3-coder-next", "qwen3-235b-a22b")
    for model in focus_models:
        lines.append(f"\nModel: {DISPLAY_NAMES.get(model, model)}")
        lines.append(f"{'Framework':<12} {'Mini-SWE':>10} {'OpenHands':>10}")
        frameworks = sorted(
            {
                fw
                for (agent, m), fws in fw_data.items()
                if m == model
                for fw in fws
            }
        )
        for fw in frameworks:
            m_rate = _fw_mean(fw_data, "mini_swe_sdk", model, fw)
            o_rate = _fw_mean(fw_data, "openhands_sdk", model, fw)
            lines.append(f"{fw:<12} {m_rate:10.1f} {o_rate:10.1f}")
    return "\n".join(lines)


def _fw_mean(fw_data, agent: str, model: str, fw: str) -> float:
    rates = fw_data.get((agent, model), {}).get(fw, [])
    return sum(rates) / len(rates) if rates else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results_path", type=Path)
    parser.add_argument("--latex", action="store_true", help="Also write .tex snippets")
    parser.add_argument("--raw", action="store_true", help="Table 1 without verifiers only")
    args = parser.parse_args()

    root = _results_root(args.results_path)
    records = iter_run_records(root)
    reports_dir = Path(__file__).resolve().parents[1] / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    sections = []
    if not args.raw:
        sections.append(format_table1(records, raw=False))
        sections.append("")
        sections.append(format_table2a(records))
        sections.append("")
        sections.append(feature_pass_at_1_table(records))
        sections.append("")
    sections.append(format_table1(records, raw=True))
    sections.append("")
    sections.append(format_table3(records))

    output = "\n".join(sections)
    print(output)

    (reports_dir / "evaluation_tables.txt").write_text(output, encoding="utf-8")
    if args.latex:
        (reports_dir / "evaluation_tables.tex").write_text(
            "% LaTeX export placeholder — extend with booktabs as needed.\n"
            + output.replace("%", "\\%"),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
