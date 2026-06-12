"""Safe read-only file helpers for Jarvis abilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

IGNORED_DIR_NAMES = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", "logs", "data"}


@dataclass(slots=True)
class FileSearchMatch:
    path: str
    name: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "name": self.name, "size_bytes": self.size_bytes}


def safe_project_root(root: str | Path | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def iter_project_files(root: str | Path | None = None):
    project_root = safe_project_root(root)
    for path in project_root.rglob("*"):
        if any(part in IGNORED_DIR_NAMES for part in path.relative_to(project_root).parts):
            continue
        if path.is_file():
            yield path


def search_project_files(root: str | Path | None, query: str, *, max_results: int = 12) -> list[FileSearchMatch]:
    project_root = safe_project_root(root)
    q = str(query or "").strip().lower()
    if not q:
        return []
    matches: list[FileSearchMatch] = []
    for path in iter_project_files(project_root):
        relative = path.relative_to(project_root)
        haystack = str(relative).lower()
        if q in haystack:
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            matches.append(FileSearchMatch(str(relative), path.name, size))
            if len(matches) >= max_results:
                break
    return matches


def project_status(root: str | Path | None = None) -> dict[str, Any]:
    project_root = safe_project_root(root)
    src_dir = project_root / "src" / "jarvis"
    tests_dir = project_root / "tests"
    app_shell_dir = project_root / "app_shell"
    test_files = list(tests_dir.rglob("test_*.py")) if tests_dir.exists() else []
    agent_dirs = [path for path in (src_dir / "agents").iterdir() if path.is_dir() and not path.name.startswith("_")] if (src_dir / "agents").exists() else []
    return {
        "project_root": str(project_root),
        "src_exists": src_dir.exists(),
        "tests_exists": tests_dir.exists(),
        "app_shell_exists": app_shell_dir.exists(),
        "test_file_count": len(test_files),
        "agent_count": len(agent_dirs),
        "agents": sorted(path.name for path in agent_dirs),
    }
