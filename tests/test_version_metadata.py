from __future__ import annotations

import tomllib
from pathlib import Path

from lean_hybrid_reasoner import __version__


def test_package_version_matches_pyproject() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = repo_root / "pyproject.toml"
    payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project_version = payload["project"]["version"]
    assert __version__ == project_version
