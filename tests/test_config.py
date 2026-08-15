"""Guards for the config layer, and the purity guard that keeps `src/` honest.

`src/nba_platform/config.py` is the only place this package learns a path, a season, a delay
or a retry count. That rule is worth nothing unless something enforces it, so the last two
tests here walk every module under `src/nba_platform/` and fail if one spells a path itself.

This mechanizes acceptance criterion 18 *before* the modules that could violate it exist —
the same posture as `tests/test_repo_structure.py`, which asserts config and filesystem agree
rather than trusting that they do.

Note the asymmetry, which is deliberate: this file resolves the repo root with a fixed-index
`parents[1]` walk, which is exactly what it forbids under `src/`. A test module's location
relative to the repo is fixed by pytest's own layout; a library module's is not, and the
moment one moves a directory a fixed-index walk points somewhere wrong while still resolving.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml

from nba_platform.config import ConfigError, get_settings, landing_key

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PACKAGE = REPO_ROOT / "src" / "nba_platform"

# The two spellings the purity guard hunts for. `parents[` is the fixed-index walk; the
# quoted `var` forms are the gitignored local-state directory, which exactly one documented
# line in config.py is allowed to name.
FIXED_INDEX_PARENT_WALK = "parents["
LOCAL_STATE_LITERALS = ('"var/"', "'var/'", '"var"', "'var'")

# Every environment key that can leak in from the developer's own shell and change what a
# test resolves. Cleared per-test so a populated .env or exported override cannot mask a bug.
CONFIG_ENV_KEYS = (
    "NBA_ENV",
    "NBA_REQUEST_DELAY_SECONDS",
    "NBA_MAX_RETRIES",
    "NBA_LANDING_ROOT",
    "NBA_WAREHOUSE_PATH",
    "NBA_PILOT_SEASONS",
    "NBA_REPO_ROOT",
)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """A process environment with every config key removed."""
    for key in CONFIG_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


def _python_modules() -> list[Path]:
    modules = sorted(SRC_PACKAGE.rglob("*.py"))
    assert modules, f"No Python modules found under {SRC_PACKAGE} — the guard would pass vacuously."
    return modules


# ─── Resolve-by-name (AC 18, first half) ──────────────────────────────────────────────


def test_landing_root_resolves_through_the_config_layer(clean_env: pytest.MonkeyPatch) -> None:
    """With only NBA_ENV set, the landing root comes from the config layer, not a literal."""
    clean_env.setenv("NBA_ENV", "local")
    settings = get_settings()

    assert settings.env == "local"
    # Built from the resolved repo root rather than a hand-written string: Path.resolve()
    # reports the filesystem's own casing on Windows, so a string comparison passes in CI
    # and fails locally.
    assert settings.landing_root == settings.repo_root / "var" / "landing"
    assert settings.repo_root == REPO_ROOT


def test_an_overriding_env_var_wins(clean_env: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """NBA_LANDING_ROOT beats the derived default — relocating is a parameter change."""
    clean_env.setenv("NBA_ENV", "local")
    clean_env.setenv("NBA_LANDING_ROOT", str(tmp_path))

    settings = get_settings()

    assert settings.landing_root == tmp_path.resolve()
    assert settings.landing_root != settings.repo_root / "var" / "landing"


def test_warehouse_path_agrees_with_the_dbt_profile(clean_env: pytest.MonkeyPatch) -> None:
    """config and transform/profiles.yml must name the same DuckDB file.

    Two sources of truth for the warehouse location is how a backfill lands in one file and
    `dbt build --target local` reads another, with both looking green.
    """
    clean_env.setenv("NBA_ENV", "local")

    with (REPO_ROOT / "transform" / "profiles.yml").open(encoding="utf-8") as fh:
        loaded: Any = yaml.safe_load(fh)
    assert isinstance(loaded, dict)
    profile_path = loaded["nba_platform"]["outputs"]["local"]["path"]

    # profiles.yml paths are written relative to the dbt project dir, not the repo root.
    from_profile = (REPO_ROOT / "transform" / profile_path).resolve()

    assert get_settings().warehouse_path == from_profile


def test_pacing_and_retries_come_from_the_environment(clean_env: pytest.MonkeyPatch) -> None:
    """Both values are config-driven, so a literal in the client would fail this."""
    clean_env.setenv("NBA_ENV", "local")
    assert get_settings().request_delay_seconds == pytest.approx(0.6)  # .env.example:14
    assert get_settings().max_retries == 5  # .env.example:15

    clean_env.setenv("NBA_REQUEST_DELAY_SECONDS", "1.25")
    clean_env.setenv("NBA_MAX_RETRIES", "9")
    settings = get_settings()

    assert settings.request_delay_seconds == pytest.approx(1.25)
    assert settings.max_retries == 9


def test_pilot_seasons_default_to_decision_6_and_are_overridable(
    clean_env: pytest.MonkeyPatch,
) -> None:
    """Widening past the pilot is a parameter change, not a code change."""
    clean_env.setenv("NBA_ENV", "local")
    assert get_settings().pilot_seasons == ("2003-04", "2019-20", "2024-25")

    clean_env.setenv("NBA_PILOT_SEASONS", "2011-12, 2020-21")
    assert get_settings().pilot_seasons == ("2011-12", "2020-21")


def test_a_malformed_season_is_rejected_rather_than_passed_through(
    clean_env: pytest.MonkeyPatch,
) -> None:
    """The endpoint takes the season string verbatim, so a bad one must fail here."""
    clean_env.setenv("NBA_ENV", "local")
    clean_env.setenv("NBA_PILOT_SEASONS", "2003-2004")

    with pytest.raises(ConfigError, match="YYYY-YY"):
        get_settings()


def test_a_cloud_env_refuses_to_guess_a_landing_root(clean_env: pytest.MonkeyPatch) -> None:
    """NBA_ENV=dev has no built-in landing zone — S3 is a later phase, so it raises."""
    clean_env.setenv("NBA_ENV", "dev")

    with pytest.raises(ConfigError, match="NBA_LANDING_ROOT"):
        get_settings()


# ─── landing_key shape (AC 18, second half) ───────────────────────────────────────────

CAPTURE_STAMP = re.compile(r"^\d{8}T\d{6}Z$")


def test_landing_key_is_colon_free_and_hive_shaped() -> None:
    """The four trailing segments are `key=value` pairs DuckDB projects as columns."""
    key = landing_key(
        source="nba_stats",
        endpoint="league_game_log",
        season="2003-04",
        grain="player",
        season_type="regular",
        captured_at=datetime(2026, 8, 15, 13, 45, 6, tzinfo=UTC),
    )

    # A colon is illegal in a Windows path; the tz-aware ISO stamp lives in the manifest.
    assert ":" not in key
    assert key.endswith("/")

    segments = key.rstrip("/").split("/")
    assert segments[:2] == ["nba_stats", "league_game_log"]

    partitions = dict(segment.split("=", 1) for segment in segments[2:])
    assert partitions["season"] == "2003-04"
    assert partitions["grain"] == "player"
    assert partitions["season_type"] == "regular"
    assert CAPTURE_STAMP.match(partitions["capture"])


def test_landing_key_renders_the_stamp_in_utc() -> None:
    """A non-UTC capture time normalises rather than landing under local-clock time."""
    eastern = timezone(timedelta(hours=-4))
    key = landing_key(
        source="nba_stats",
        endpoint="league_game_log",
        season="2024-25",
        grain="team",
        season_type="regular",
        captured_at=datetime(2026, 8, 15, 9, 45, 6, tzinfo=eastern),
    )

    assert "capture=20260815T134506Z/" in key


def test_landing_key_rejects_a_naive_timestamp() -> None:
    """ruff DTZ bans naive datetimes in this repo; the boundary enforces it at runtime too."""
    with pytest.raises(ConfigError, match="timezone-aware"):
        landing_key(
            source="nba_stats",
            endpoint="league_game_log",
            season="2024-25",
            grain="player",
            season_type="regular",
            captured_at=datetime(2026, 8, 15, 13, 45, 6),  # noqa: DTZ001 — the point of the test
        )


# ─── The purity guard (AC 18) ─────────────────────────────────────────────────────────


def test_no_module_under_src_walks_parents_by_index() -> None:
    """A fixed-index parent walk resolves to the wrong directory the moment a module moves.

    `tests/test_repo_structure.py:19` uses `parents[1]`, and so does this file — both are
    test-file locators, whose depth pytest fixes. Neither is precedent for `src/`.
    """
    offenders = [
        module.relative_to(REPO_ROOT).as_posix()
        for module in _python_modules()
        if FIXED_INDEX_PARENT_WALK in module.read_text(encoding="utf-8")
    ]

    assert not offenders, (
        f"{FIXED_INDEX_PARENT_WALK!r} found in {offenders}. Resolve the repo root by walking "
        "up to the directory containing pyproject.toml, or from NBA_REPO_ROOT by name."
    )


def test_only_config_names_the_local_state_directory() -> None:
    """Exactly one documented line in config.py may spell the gitignored `var/` root.

    Every other module resolves it through the config layer. One carve-out is a decision;
    two is a hardcoded path, and the second one is always the one that breaks elsewhere.
    """
    counts = {
        module.relative_to(REPO_ROOT).as_posix(): sum(
            module.read_text(encoding="utf-8").count(literal) for literal in LOCAL_STATE_LITERALS
        )
        for module in _python_modules()
    }

    config_key = "src/nba_platform/config.py"
    assert counts.pop(config_key) == 1, (
        f"{config_key} must spell the local-state directory exactly once, in its documented "
        "resolution helper."
    )

    offenders = {path: count for path, count in counts.items() if count}
    assert not offenders, (
        f"{offenders} name the gitignored local-state directory directly. Ask the config layer "
        "for landing_root or warehouse_path instead."
    )
