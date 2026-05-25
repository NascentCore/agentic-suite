"""Map generation task names to constraint levels L0–L3 (paper Table 1)."""

from __future__ import annotations

import re

FRAMEWORKS = frozenset(
    {
        "aiohttp",
        "django",
        "fastapi",
        "flask",
        "express",
        "fastify",
        "hono",
        "koa",
    }
)

# Paper cost subset: two frameworks per runtime × four levels.
SUBSET_FRAMEWORKS = frozenset({"aiohttp", "fastapi", "express", "fastify"})


def framework_from_task(task_name: str) -> str | None:
    if "-openapi" not in task_name:
        return None
    fw = task_name.split("-openapi", 1)[0]
    return fw if fw in FRAMEWORKS else None


def is_generation_task(task_name: str, runtime: str) -> bool:
    if "openapi_small" in task_name:
        return False
    fw = framework_from_task(task_name)
    if fw is None:
        return False
    if runtime == "uv":
        return fw in {"aiohttp", "django", "fastapi", "flask"}
    if runtime == "node":
        return fw in {"express", "fastify", "hono", "koa"}
    return False


def constraint_level(task_name: str) -> int | None:
    """Return L0–L3 for an 80-task generation instance, or None if excluded."""
    if "openapi_small" in task_name:
        return None
    if task_name.endswith("-unconstrained"):
        return 0
    if re.search(
        r"-clean_architecture-(sqlite|postgres)-(sqlalchemy|sequelize)$",
        task_name,
    ):
        return 3
    if re.search(r"-clean_architecture-(sqlite|postgres)$", task_name):
        return 2
    if re.search(r"-(sqlite|postgres)-(sqlalchemy|sequelize)$", task_name) and (
        "clean_architecture" not in task_name
    ):
        return 2
    if (
        task_name.endswith("-clean_architecture")
        or task_name.endswith("-sqlite")
        or task_name.endswith("-postgres")
    ):
        return 1
    return None


def runtime_for_task(task_name: str) -> str | None:
    fw = framework_from_task(task_name)
    if fw is None:
        return None
    if fw in {"aiohttp", "django", "fastapi", "flask"}:
        return "uv"
    if fw in {"express", "fastify", "hono", "koa"}:
        return "node"
    return None


def generation_task_path(runtime: str, task_name: str) -> str:
    """Path fragment used by upstream main.py --task."""
    return f"{runtime}/{runtime}-{task_name}.json"


def build_subset_task_list() -> list[str]:
    """16-task paper subset (§4 cost-driven scope)."""
    out: list[str] = []
    for runtime in ("uv", "node"):
        frameworks = (
            ("aiohttp", "fastapi") if runtime == "uv" else ("express", "fastify")
        )
        for fw in frameworks:
            for level, suffix in (
                (0, "unconstrained"),
                (1, "clean_architecture"),
                (2, "clean_architecture-postgres"),
                (3, None),
            ):
                if level == 3:
                    orm = "sqlalchemy" if runtime == "uv" else "sequelize"
                    name = f"{fw}-openapi-clean_architecture-postgres-{orm}"
                else:
                    name = f"{fw}-openapi-{suffix}"
                out.append(generation_task_path(runtime, name))
    return out
