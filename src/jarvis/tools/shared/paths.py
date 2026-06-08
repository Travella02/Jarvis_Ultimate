"""Shared path helpers."""

from __future__ import annotations

from pathlib import Path


def project_root_from_file(file_path: str | Path) -> Path:
    path = Path(file_path).resolve()
    for parent in [path, *path.parents]:
        if (parent / "src" / "jarvis").exists():
            return parent
    return Path.cwd()
