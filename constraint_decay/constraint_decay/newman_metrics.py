"""Parse Newman CSV reports into assertion pass rates."""

from __future__ import annotations

import csv
import io
from pathlib import Path


def assertion_pass_rate_from_csv(path: Path) -> float | None:
    """Return A% in [0, 100] from a Newman run report CSV."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.strip() or "iteration,collectionName" not in text.split("\n", 1)[0]:
        return None
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return None
    passed = 0
    total = 0
    for row in rows:
        try:
            passed += int(row.get("executedCount") or 0)
            total += int(row.get("totalAssertions") or 0)
        except (TypeError, ValueError):
            continue
    if total <= 0:
        return None
    return 100.0 * passed / total


def run_passed(rate: float | None, *, full_pass_threshold: float = 100.0) -> bool:
    return rate is not None and rate >= full_pass_threshold
