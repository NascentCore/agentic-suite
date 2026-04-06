# Template Assets

This directory is the **single source of truth** for all scaffold templates.

The `templates.py` module loads these files at runtime and renders them with repository profile values. **Do not duplicate template content in Python code** — edit the `.md` files here instead.

## Files

| Template | Generates | Placeholders |
|----------|-----------|-------------|
| `TEMPLATE_SOUL.md` | `SOUL.md` | `{REPO_NAME}`, `{PRIMARY_LANGUAGE}`, `{ADDITIONAL_LANGUAGES}`, `{PACKAGE_MANAGERS}`, `{SOURCE_DIRS}`, `{TEST_DIRS}`, `{DOCS_DIRS}`, `{ENTRYPOINT_CANDIDATES}`, `{RISK_NOTES}` |
| `TEMPLATE_SKILLS.md` | `skills.md` | Same as SOUL + `{TEST_COMMANDS}`, `{RUN_COMMANDS}` |
| `TEMPLATE_AGENTS.md` | `AGENTS.md` | `{REPO_NAME}`, `{PRIMARY_LANGUAGE}`, `{PACKAGE_MANAGERS}`, `{SOURCE_DIRS}`, `{TEST_DIRS}`, `{DOCS_DIRS}` |
| `TEMPLATE_TOOLS.md` | `TOOLS.md` | `{RAW_TEST_COMMANDS}`, `{RAW_RUN_COMMANDS}` |
| `TEMPLATE_SKILL_ALIAS.md` | `SKILL.md` | None (static) |
| `TEMPLATE_STYLE.md` | `STYLE.md` (optional) | None (static) |

## Placeholder values

All placeholders are populated by `models.RepoProfile.to_template_context()`. The `RAW_TEST_COMMANDS` and `RAW_RUN_COMMANDS` placeholders are computed directly from the profile's command lists.
