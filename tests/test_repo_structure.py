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
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"


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


def _opens_with_frontmatter(text: str) -> str | None:
    """The raw YAML frontmatter block, or None if the file opens without one."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else None


def test_agents_directory_holds_exactly_one_definition() -> None:
    """`.claude/agents/` holds exactly one agent definition, discriminated by frontmatter.

    Frontmatter rather than file count, deliberately: the directory also carries a memory
    file and a README, so a naive "exactly one .md" would redden the moment the directory
    is complete. Verified 2026-08-14 that this matches the harness — a frontmatter-less
    .md here registers no agent type and produces no warning.

    Discovered by glob, never by hardcoded filename, so renaming the definition cannot
    turn this guard vacuous.
    """
    assert AGENTS_DIR.is_dir(), (
        f"{AGENTS_DIR.relative_to(REPO_ROOT)} must exist — it holds the repo's "
        "write-capable implementation agent and the build rulebook it owns."
    )

    definitions: list[Path] = []
    plain: list[Path] = []
    for path in sorted(AGENTS_DIR.glob("*.md")):
        block = _opens_with_frontmatter(path.read_text(encoding="utf-8"))
        (definitions if block is not None else plain).append(path)

    assert len(definitions) == 1, (
        "Expected exactly one frontmatter-bearing agent definition in "
        f"{AGENTS_DIR.relative_to(REPO_ROOT)}, found {[p.name for p in definitions]}. "
        "One definition per agent; a second agent is a separate feature request."
    )
    assert plain, (
        "The memory file and README carry no frontmatter by design, so the loader "
        "ignores them. Finding none means they are gone or have grown frontmatter."
    )

    block = _opens_with_frontmatter(definitions[0].read_text(encoding="utf-8"))
    assert block is not None
    loaded: Any = yaml.safe_load(block)
    assert isinstance(loaded, dict), (
        f"{definitions[0].name}'s frontmatter must parse to a mapping, got {type(loaded)}."
    )
    for key in ("name", "description"):
        value: Any = loaded.get(key)
        assert isinstance(value, str) and value.strip(), (
            f"{definitions[0].name}'s frontmatter needs a non-empty {key!r}. Verified "
            "2026-08-14 that this harness accepts and honours `name` and `description`; "
            "an agent without them does not register as a spawnable type."
        )


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
