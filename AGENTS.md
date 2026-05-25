# Building agentic software

- [Source control](https://jorijn.com/en/blog/leaving-github-for-forgejo/): local self-contained source code management tool.
- [Pi](https://pi.dev/): minimalistic coding agent

## Cursor Cloud specific instructions

### Overview

Pure Python library (Python 3.11+, hatchling build system). No databases, Docker, or web servers required. All state is in-memory or file-based.

### Key commands

- **Install**: `pip install -e ".[all]"` (includes `amcp`, `dev` extras)
- **Lint**: `python3 -m ruff check .` (see `pyproject.toml [tool.ruff]` for rule config)
- **Test**: `python3 -m pytest -v` (test paths: `amcp`, `tests`, `agentic_runtime`, `agentic_devops`)
- **CLI modules**: see `README.md` for per-module CLI usage

### Gotchas

- The AMCP CLI must be invoked as `python3 -m amcp.main` (not `python3 amcp/main.py`), since it uses relative imports.
- The scaffold CLI (`python3 -m personified_software.openclaw_scaffold.cli /path/to/repo`) writes files into the target repo by default; use `--dry-run` to preview without writing.
- `pytest-asyncio` is pinned at 1.3.0 and uses `mode=Mode.STRICT`; async tests require the `@pytest.mark.asyncio` decorator.
