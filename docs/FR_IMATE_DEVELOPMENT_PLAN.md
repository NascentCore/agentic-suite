# FR_IMATE_DEVELOPMENT_PLAN — agentic_suite Deep Review & Improvement Plan

> **Status**: Active  
> **Created**: 2026-04-06  
> **Scope**: Full codebase review covering `amcp/`, `personified_software/`, and all top-level docs  
> **Method**: Line-by-line reading of all 16 Python files (~1900 LOC) and 25 Markdown files

---

## 1. Review Scope and Methodology

### Files reviewed

| Area | Files | Lines |
|------|-------|-------|
| `amcp/` (core + adapters + migration + tests + CLI) | 9 `.py` | ~1200 |
| `personified_software/openclaw_scaffold/` (models + detector + templates + generator + CLI) | 6 `.py` | ~720 |
| Top-level docs (`README.md`, `BRAIN_STORM.md`, `LICENSE`) | 3 | — |
| AMCP docs (`amcp/README.md`, `amcp/ROADMAP.md`) | 2 | — |
| Scaffold docs (README, instantiation guide, checklist, INSTRUCTIONS) | 5 | — |
| Template assets (`template_assets/*.md`) | 7 | — |
| Example outputs (`examples/generated_for_*`) | 9 | — |
| Config (`.gitignore`) | 1 | — |

### Review criteria

1. **Correctness** — can the code actually run?
2. **Architecture** — are components well-separated and maintainable?
3. **Documentation** — do docs match reality?
4. **Testing** — is there a safety net for changes?
5. **Universality** — does the "universal scaffold toolkit" work on arbitrary repos?

---

## 2. Findings

### 🔴 Critical — Code Cannot Run

#### C1: AMCP import paths are broken — all CLI, tests, and examples fail

**Affected files** (5):
- `amcp/main.py` — `from research.amcp.core import ...`
- `amcp/langgraph_example.py` — `from research.amcp.adapters import ...`
- `amcp/test_pydanticai_amcp.py` — `from research.amcp.adapters import ...` / `from research.amcp.core import ...`
- `amcp/test_langgraph_amcp.py` — `from research.amcp.adapters import ...` / `from research.amcp.core import ...`
- `amcp/test_migration_manifest.py` — `from research.amcp.core import ...` / `from research.amcp.migration import ...`

**Root cause**: The package lives at `amcp/`, not `research/amcp/`. The `research/` prefix is a leftover from a previous directory structure that no longer exists.

**Impact**: Every executable entry point in the AMCP module is broken. `python -m pytest amcp/` fails with `ModuleNotFoundError`.

**Internal modules** (`adapters.py`, `migration.py`) correctly use relative imports (`from .core import ...`) and are unaffected.

**Fix**: Change all 5 files to use relative imports (consistent with the rest of the package).

#### C2: No project configuration — packages are not installable

**Problem**: The repository has no `pyproject.toml`, `setup.py`, or `setup.cfg`.

**Impact**:
- Cannot `pip install -e .` for development
- Cannot run `python -m pytest` from root without `sys.path` hacks
- `personified_software/` has zero dependency declarations
- `amcp/requirements.txt` exists but cannot be consumed by standard tooling

**Fix**: Create a top-level `pyproject.toml` declaring both packages, their dependencies, and tool configuration.

---

### 🟠 High — Architectural Issues

#### H1: Template dual-maintenance — hardcoded in Python AND on disk

**Problem**:
- `templates.py` contains all 5 templates as Python multi-line f-strings (~243 lines of template content)
- `template_assets/` contains the same templates as standalone `.md` files
- **The code never reads `template_assets/`** — they are dead documentation artifacts
- The two versions have subtle content differences (e.g., SOUL.md "Identity" section wording differs)

**Impact**: Any template edit must be made in two places, and they are already out of sync.

**Fix**: Refactor `templates.py` to load templates from `template_assets/` at runtime using `Path(__file__).parent / "template_assets"`. Remove all hardcoded template strings. `template_assets/` becomes the single source of truth.

#### H2: Detector hardcodes this repository's directory names

**Problem**: `detector.py` bakes in repository-specific names that break the "universal toolkit" premise:

```python
source_dirs = _detect_named_dirs(target_repo, ("src", "app", "lib", "amcp"))
test_dirs = _detect_named_dirs(target_repo, ("tests", "test", "spec", "amcp"))
docs_dirs = _detect_named_dirs(target_repo, ("docs", "doc", "personified_software"))
```

Additionally:
- `_detect_entrypoints()` explicitly checks `(root / "amcp" / "main.py").exists()`
- `_detect_run_commands()` explicitly checks `(root / "amcp" / "main.py").exists()`

**Impact**: Running the scaffold on any external repo that happens to have an `amcp/` or `personified_software/` directory will produce incorrect results. More importantly, the "universal" toolkit silently injects repo-specific assumptions.

**Fix**: Remove `"amcp"` and `"personified_software"` from candidate lists. Replace `amcp/main.py` checks with generic Python package detection (e.g., find directories containing `__init__.py` and `__main__.py`).

#### H3: Scaffold module has zero test coverage

**Problem**: `personified_software/openclaw_scaffold/` has no test files at all.

**Affected modules** (5):
- `models.py` — dataclasses and helper functions, untested
- `detector.py` — complex filesystem traversal and heuristic logic, untested
- `templates.py` — template rendering, untested
- `generator.py` — end-to-end generation, untested
- `cli.py` — argument parsing and output, untested

**Impact**: Refactoring (H1, H2) has no safety net. Regressions will be silent.

**Fix**: Create comprehensive test suite:
- `tests/test_scaffold_models.py` — profile serialization, helper functions
- `tests/test_scaffold_detector.py` — filesystem heuristics with `tmp_path`
- `tests/test_scaffold_templates.py` — template rendering correctness
- `tests/test_scaffold_generator.py` — end-to-end scaffold generation
- `tests/test_scaffold_cli.py` — CLI argument parsing

#### H4: `utc_now()` and `canonical_json()` are duplicated

**Problem**:
- `amcp/core.py` defines `utc_now()` and `canonical_json()`
- `amcp/migration.py` defines identical copies of both functions

**Fix**: Remove duplicates from `migration.py`; import from `core.py` instead.

---

### 🟡 Medium — Documentation and Feature Gaps

#### M1: Root `README.md` is nearly empty

**Problem**: Contains only 2 lines:
```markdown
# agentic_suite
A suite of highly-complimentary protocols, design principles, and paradigms for building agentic software
```

No project structure, no getting-started instructions, no component descriptions.

**Fix**: Expand with project vision, component overview, quick-start instructions, and project layout.

#### M2: `.persona/` structure is designed but not implemented

**Problem**: `INSTRUCTIONS.md` describes a rich directory structure (`.persona/identity/`, `.persona/memory/`, signals, diagnosis, retrospectives) and a full self-evolution loop. None of this exists in the repo.

**Fix**: Create minimal seed structure:
- `.persona/identity/mission.md`
- `.persona/memory/decision_log.md`

#### M3: AMCP README references wrong paths

**Problem**: `amcp/README.md` uses `research/amcp/` prefix throughout:
- `File: research/amcp/main.py`
- `research/amcp/.venv/bin/python -m pytest -q research/amcp/test_pydanticai_amcp.py`
- `python research/amcp/main.py demo`

These paths do not exist.

**Fix**: Replace all `research/amcp/` with `amcp/` throughout the README.

#### M4: `MemoryRecord.cid` is non-deterministic by design but undocumented

**Problem**: The `cid` property hashes the entire model dump, including auto-generated `memory_id` (uuid4) and `created_at` (now). Two identical-content records will always produce different CIDs.

**Fix**: Add docstring clarifying that CID is instance-specific (not content-addressable in the traditional sense), or refactor to hash only business-content fields.

#### M5: AMCP architecture description omits migration module

**Problem**: The README describes 3 layers (Core / Adapter Ports / Runtime Adapters) mapping to 2 files (`core.py` / `adapters.py`). The `migration.py` module (212 lines, significant functionality) is not mentioned in the architecture section.

**Fix**: Add migration as a fourth architectural component in the README.

---

### 🟢 Low — Quality and Enhancement

#### L1: No CI/CD configuration

No `.github/workflows/` directory. No automated testing, linting, or type checking.

**Fix**: Create minimal GitHub Actions workflow running `pytest`, `ruff check`, and `mypy`.

#### L2: No code quality tool configuration

No ruff, mypy, or pre-commit configuration.

**Fix**: Add `[tool.ruff]` and `[tool.mypy]` sections to `pyproject.toml`.

#### L3: `STYLE.md` template exists but generation is not supported

`template_assets/TEMPLATE_STYLE.md` exists, but `generator.py` and `cli.py` do not support generating `STYLE.md`.

**Fix**: Add `--include-style` CLI option and generation logic.

#### L4: Scaffold detector does not parse existing project metadata

The detector only examines filesystem structure. It does not read `pyproject.toml` (project name, description), `package.json`, or `README.md` content.

**Fix**: Enhance detector to extract metadata from common project config files.

#### L5: No top-level architecture document

`BRAIN_STORM.md` is a brainstorming document, not an architecture overview. There is no document describing how the three components (AMCP, Personified Software, design docs) relate.

**Fix**: Create `docs/ARCHITECTURE.md` with component relationship diagram.

---

## 3. Implementation Priority

| Priority | Task | Dependencies | Effort |
|----------|------|-------------|--------|
| **P0** | C1: Fix AMCP import paths | None | Small |
| **P0** | C2: Create `pyproject.toml` | None | Small |
| **P1** | H4: Remove `utc_now`/`canonical_json` duplication | C1 | Tiny |
| **P1** | M3: Fix AMCP README paths | None | Tiny |
| **P1** | H3: Add scaffold tests | C2 | Medium |
| **P2** | H1: Template single-source refactor | H3 | Medium |
| **P2** | H2: Remove detector hardcoding | H3 | Medium |
| **P3** | M1: Expand root README | None | Small |
| **P3** | M2: Seed `.persona/` structure | None | Small |
| **P3** | M5: Update AMCP architecture docs | None | Small |
| **P4** | L1–L5: CI, quality tools, enhancements | C2 | Medium |

**Recommended execution order**: P0 → P1 → P2 → P3 → P4 (strictly sequential within priority, parallelizable across priorities where deps allow).

---

## 4. Acceptance Criteria

1. **C1 done**: `python -m pytest amcp/` discovers and runs all 3 test files (14+ tests) with zero import errors.
2. **C2 done**: `pip install -e .` succeeds; `python -m pytest` discovers tests from both packages.
3. **H1 done**: `template_assets/` is the only source of template content; `templates.py` contains no template strings.
4. **H2 done**: Running scaffold on an external repo produces zero references to `amcp` or `personified_software`.
5. **H3 done**: Scaffold module has test files covering models, detector, templates, generator, and CLI.
6. **H4 done**: `amcp/migration.py` contains no local `utc_now` or `canonical_json` definitions.
7. **All P0–P1 done**: `python -m pytest` runs all tests and exits with code 0.

---

## 5. Out of Scope

- AMCP cryptographic signature implementation (tracked in `amcp/ROADMAP.md` P0.1)
- Full `.persona/` self-evolution loop automation
- Multi-language scaffold support (e.g., TypeScript, Rust project detection)
- BRAIN_STORM.md component implementations beyond AMCP
