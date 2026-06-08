"""Minimal config helpers for Jarvis 3.

This milestone keeps config lightweight and dependency-free. Full YAML/provider
config loading can be expanded later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class JarvisConfig:
    project_root: Path = field(default_factory=lambda: Path.cwd())
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    environment: str = "development"
    debug: bool = True

    @classmethod
    def from_project_root(cls, project_root: str | Path | None = None) -> "JarvisConfig":
        root = Path(project_root) if project_root else Path.cwd()
        return cls(
            project_root=root,
            logs_dir=root / "logs",
            data_dir=root / "data",
        )
