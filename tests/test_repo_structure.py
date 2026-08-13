"""Structural guards.

These assert that the repo's configuration and its filesystem agree. They exist because
this repo is written mostly by agents against docs that are treated as authoritative —
so a config claiming a layer that doesn't exist, or a layer nobody configured, is a real
failure mode rather than a theoretical one.

Cheap, fast, and they run on every PR.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TRANSFORM = REPO_ROOT / "transform"


def _load_dbt_project() -> dict[str, Any]:
    with (TRANSFORM / "dbt_project.yml").open(encoding="utf-8") as fh:
        loaded: Any = yaml.safe_load(fh)
    assert isinstance(loaded, dict)
    return loaded


def _configured_layers() -> set[str]:
    """Medallion layers declared under `models: nba_platform:` in dbt_project.yml."""
    project = _load_dbt_project()
    models: Any = project["models"]["nba_platform"]
    return {
        key for key, value in models.items() if not key.startswith("+") and isinstance(value, dict)
    }


def _layer_directories() -> set[str]:
    """Subdirectories actually present under transform/models/."""
    models_dir = TRANSFORM / "models"
    return {path.name for path in models_dir.iterdir() if path.is_dir()}


def test_package_imports_and_declares_a_version() -> None:
    import nba_platform

    assert nba_platform.__version__


def test_package_version_matches_pyproject() -> None:
    import nba_platform

    with (REPO_ROOT / "pyproject.toml").open("rb") as fh:
        pyproject = tomllib.load(fh)

    assert nba_platform.__version__ == pyproject["project"]["version"], (
        "src/nba_platform/__init__.py and pyproject.toml disagree about the version."
    )


def test_every_configured_layer_has_a_directory() -> None:
    missing = _configured_layers() - _layer_directories()
    assert not missing, (
        f"dbt_project.yml configures layer(s) with no transform/models/ directory: {sorted(missing)}"
    )


def test_every_layer_directory_is_configured() -> None:
    unconfigured = _layer_directories() - _configured_layers()
    assert not unconfigured, (
        f"transform/models/ has directory(ies) absent from dbt_project.yml: {sorted(unconfigured)}. "
        "An unconfigured layer silently inherits default materialization and schema."
    )


def test_every_layer_documents_itself() -> None:
    """Each medallion layer carries a README stating what belongs in it."""
    undocumented = [
        layer
        for layer in _layer_directories()
        if not (TRANSFORM / "models" / layer / "README.md").is_file()
    ]
    assert not undocumented, f"Layer(s) missing a README.md: {sorted(undocumented)}"


def test_dotenv_is_ignored_and_an_example_is_committed() -> None:
    """The repo is public. A committed .env would be a credential leak.

    Gitleaks catches secrets by content in CI; this catches the structural mistake
    locally and instantly.
    """
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "\n.env\n" in gitignore, ".env must be gitignored — this repo is public."
    assert (REPO_ROOT / ".env.example").is_file(), (
        ".env.example must be committed so a fresh clone knows what configuration is expected."
    )
    assert not (REPO_ROOT / ".env").is_file() or ".env" in gitignore
