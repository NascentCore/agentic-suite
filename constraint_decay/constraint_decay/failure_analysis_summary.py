"""RQ3 summary when upstream judge CSVs are unavailable."""

from __future__ import annotations

from pathlib import Path


def summarize_rq3(data_dir: Path) -> str:
    """Check for precomputed judge outputs; document gap if missing."""
    candidates = [
        data_dir / "failure_analysis_qwen3-coder-next.csv",
        data_dir / "failure_analysis_minimax-m2.5.csv",
        data_dir / "logic_subcategories.csv",
    ]
    found = [p for p in candidates if p.is_file()]
    lines = ["RQ3: Failure taxonomy"]
    if found:
        lines.append("Precomputed judge files present:")
        for p in found:
            lines.append(f"  - {p.name} ({p.stat().st_size} bytes)")
        lines.append(
            "TODO(phase-3): run upstream failure_analysis.py when vendor repo is available."
        )
    else:
        lines.append(
            "Precomputed failure_analysis_*.csv not in HuggingFace results.zip only."
        )
        lines.append(
            "Paper claim: ~45% of logic errors are data-layer (ORM/query) — reproduce "
            "via upstream failure_analysis_logic.py after cloning constraint-decay."
        )
        lines.append(
            "TODO(phase-3): download judge CSVs from full repo or re-run LLM judge."
        )
    return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("data_path", type=Path)
    args = parser.parse_args()
    print(summarize_rq3(args.data_path))


if __name__ == "__main__":
    main()
