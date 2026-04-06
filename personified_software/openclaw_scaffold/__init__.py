"""OpenClaw-like personified scaffold toolkit for any repository."""

from .detector import detect_repo_profile
from .generator import generate_scaffold
from .models import RepoProfile, ScaffoldOptions, ScaffoldResult

__all__ = [
    "RepoProfile",
    "ScaffoldOptions",
    "ScaffoldResult",
    "detect_repo_profile",
    "generate_scaffold",
]
