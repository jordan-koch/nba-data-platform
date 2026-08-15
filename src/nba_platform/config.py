"""Configuration — the one place this package learns a path, a season, or a pacing value.

Everything downstream (the paced client, the landing writer, the backfill CLI, the fixture
recorder) asks this module instead of spelling a path, a delay or a retry count of its own.
That is the resolve-by-name rule applied to Python: a literal path inside an extraction
module is a defect that only surfaces on someone else's machine, and a literal delay is one
that only surfaces as a block from `stats.nba.com`.

**Repo-root resolution — which of the two allowed strategies this module uses.** It walks
*upward from this file until it finds the directory holding `pyproject.toml`*. It does not
take a fixed-index `parents` subscript: that form silently points one directory too high or
too low the moment a module moves a level, and it is banned everywhere under `src/`. The
walk stops at the filesystem root rather than looping. `NBA_REPO_ROOT` overrides it by name
for callers running from an installed wheel, where no `pyproject.toml` sits on disk.

**Environment keys, all read by name.** The first three are documented in `.env.example`
(`:8`, `:14`, `:15`); the last four are overrides that exist so widening or relocating is a
parameter change rather than a code change.

| key | default | what it controls |
|---|---|---|
| `NBA_ENV` | `local` | which environment's paths resolve; one of local/dev/prod |
| `NBA_REQUEST_DELAY_SECONDS` | `0.6` | minimum seconds between source-API requests |
| `NBA_MAX_RETRIES` | `5` | retry ceiling for exponential backoff |
| `NBA_LANDING_ROOT` | derived | absolute or repo-relative landing-zone root |
| `NBA_WAREHOUSE_PATH` | derived | DuckDB file; agrees with `transform/profiles.yml:17` |
| `NBA_PILOT_SEASONS` | three seasons | comma-separated `YYYY-YY` list |
| `NBA_REPO_ROOT` | discovered | escape hatch for the upward walk |

Resolution is eager and uncached: `get_settings()` re-reads the environment on every call, so
a monkeypatched key takes effect immediately and no test can be poisoned by an earlier one.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

__all__ = [
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_PILOT_SEASONS",
    "DEFAULT_REQUEST_DELAY_SECONDS",
    "ConfigError",
    "Settings",
    "get_settings",
    "landing_key",
]


class ConfigError(RuntimeError):
    """Configuration is missing, malformed, or asks for something not built yet."""


# ─── Environment keys — every one of them resolved by name, never inlined ─────────────
ENV_KEY = "NBA_ENV"
REQUEST_DELAY_KEY = "NBA_REQUEST_DELAY_SECONDS"
MAX_RETRIES_KEY = "NBA_MAX_RETRIES"
LANDING_ROOT_KEY = "NBA_LANDING_ROOT"
WAREHOUSE_PATH_KEY = "NBA_WAREHOUSE_PATH"
PILOT_SEASONS_KEY = "NBA_PILOT_SEASONS"
REPO_ROOT_KEY = "NBA_REPO_ROOT"

# ─── Defaults ─────────────────────────────────────────────────────────────────────────
DEFAULT_ENV = "local"
KNOWN_ENVIRONMENTS = frozenset({"local", "dev", "prod"})

# 0.6s is not a tuning knob. stats.nba.com blocks impolite clients rather than throttling
# them, and a block is hard to tell apart from a transient failure. See docs/data-sources.md
# before raising the request rate; the client pairs this with exponential backoff.
DEFAULT_REQUEST_DELAY_SECONDS = 0.6
DEFAULT_MAX_RETRIES = 5

# Decision 6: three pilot seasons chosen to span the discontinuities — 2003-04 is pre-tracking
# and pre-hand-check-ban, 2019-20 is the bubble (unequal game counts, July-October dates), and
# 2024-25 is modern. Widening the backfill sets NBA_PILOT_SEASONS; it does not edit this file.
DEFAULT_PILOT_SEASONS: tuple[str, ...] = ("2003-04", "2019-20", "2024-25")

# The NBA's own season string, passed to the endpoint verbatim: four-digit start year, hyphen,
# two-digit end year. "2003-2004" is not the same string and the endpoint rejects it.
SEASON_PATTERN = re.compile(r"^\d{4}-\d{2}$")

PROJECT_MARKER = "pyproject.toml"

# These two must agree with the `local` target's path at transform/profiles.yml:17, which is
# written relative to the dbt project dir and resolves to the same file this composes. If that
# profile moves the warehouse, these move with it — read it, do not assume it.
WAREHOUSE_DIRNAME = "warehouse"
WAREHOUSE_FILENAME = "nba_local.duckdb"
LANDING_DIRNAME = "landing"

# ─── The one hardcoded path fragment allowed anywhere under src/ ──────────────────────
# This module is the only one permitted to spell the repo's gitignored local-state directory
# (IMPLEMENTATION_PLAN.md §7), and the line below is the only place in it that does. That
# directory is ignored wholesale at .gitignore:16 and holds regenerable state only: the local
# landing zone, the DuckDB warehouse, caches, run state. Both `landing_root` and
# `warehouse_path` hang off it and both are overridable by name, so nothing downstream ever
# needs to repeat it — and the purity guard in tests/ fails the build if anything does.
_LOCAL_STATE_ROOT = "var/"

# Compact UTC, deliberately colon-free: `:` is illegal in a Windows path and this is a
# Windows-dev / Linux-CI repo. The true tz-aware ISO timestamp lives in the capture manifest,
# where it can carry punctuation safely.
CAPTURE_STAMP_FORMAT = "%Y%m%dT%H%M%SZ"


def _lookup(environ: Mapping[str, str], key: str) -> str | None:
    """The value of `key`, or None when it is unset or blank.

    Blank is treated as unset on purpose: an exported-but-empty variable is a shell accident,
    not a request for an empty path.
    """
    value = environ.get(key)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _anchor(candidate: str, repo_root: Path) -> Path:
    """Resolve an override to an absolute path, anchoring relatives at the repo root.

    Anchoring at the repo root rather than the process working directory means a backfill run
    from `transform/` and one run from the repo top land in the same place.
    """
    path = Path(candidate).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _resolve_repo_root(environ: Mapping[str, str]) -> Path:
    override = _lookup(environ, REPO_ROOT_KEY)
    if override is not None:
        return Path(override).expanduser().resolve()

    current = Path(__file__).resolve().parent
    while True:
        if (current / PROJECT_MARKER).is_file():
            return current
        nxt = current.parent
        if nxt == current:  # filesystem root — stop rather than spin
            raise ConfigError(
                f"Walked up from {Path(__file__).resolve()} without finding {PROJECT_MARKER}. "
                f"Set {REPO_ROOT_KEY} to the repo root (expected when running from a wheel)."
            )
        current = nxt


def _resolve_env(environ: Mapping[str, str]) -> str:
    value = (_lookup(environ, ENV_KEY) or DEFAULT_ENV).lower()
    if value not in KNOWN_ENVIRONMENTS:
        known = ", ".join(sorted(KNOWN_ENVIRONMENTS))
        raise ConfigError(
            f"{ENV_KEY}={value!r} is not a known environment. Expected one of: {known}."
        )
    return value


def _resolve_landing_root(environ: Mapping[str, str], env: str, repo_root: Path) -> Path:
    override = _lookup(environ, LANDING_ROOT_KEY)
    if override is not None:
        return _anchor(override, repo_root)
    if env != DEFAULT_ENV:
        raise ConfigError(
            f"{ENV_KEY}={env!r} has no built-in landing zone — cloud targets are a later phase. "
            f"Set {LANDING_ROOT_KEY} by name to point at the bucket prefix or mount."
        )
    return repo_root / _LOCAL_STATE_ROOT / LANDING_DIRNAME


def _resolve_warehouse_path(environ: Mapping[str, str], env: str, repo_root: Path) -> Path:
    override = _lookup(environ, WAREHOUSE_PATH_KEY)
    if override is not None:
        return _anchor(override, repo_root)
    if env != DEFAULT_ENV:
        raise ConfigError(
            f"{ENV_KEY}={env!r} warehouses to Snowflake, not to a file on disk. "
            f"Set {WAREHOUSE_PATH_KEY} by name if a local file is genuinely wanted."
        )
    return repo_root / _LOCAL_STATE_ROOT / WAREHOUSE_DIRNAME / WAREHOUSE_FILENAME


def _resolve_pilot_seasons(environ: Mapping[str, str]) -> tuple[str, ...]:
    raw = _lookup(environ, PILOT_SEASONS_KEY)
    if raw is None:
        return DEFAULT_PILOT_SEASONS

    seasons = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not seasons:
        raise ConfigError(f"{PILOT_SEASONS_KEY}={raw!r} is set but names no season.")

    malformed = [season for season in seasons if not SEASON_PATTERN.match(season)]
    if malformed:
        raise ConfigError(
            f"{PILOT_SEASONS_KEY} holds {malformed!r}, which is not the NBA season format "
            "YYYY-YY (for example 2003-04). The endpoint takes that string verbatim."
        )
    return seasons


def _resolve_positive_float(environ: Mapping[str, str], key: str, default: float) -> float:
    raw = _lookup(environ, key)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{key}={raw!r} is not a number.") from exc
    if value <= 0:
        raise ConfigError(f"{key}={value!r} must be greater than zero.")
    return value


def _resolve_non_negative_int(environ: Mapping[str, str], key: str, default: int) -> int:
    raw = _lookup(environ, key)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{key}={raw!r} is not an integer.") from exc
    if value < 0:
        raise ConfigError(f"{key}={value!r} must not be negative.")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """Every path, season and pacing value this package uses, resolved once and frozen.

    Frozen because a setting that can be mutated mid-run is a setting that can be mutated
    between the dry-run cost estimate and the run that spends it.
    """

    env: str
    repo_root: Path
    landing_root: Path
    warehouse_path: Path
    pilot_seasons: tuple[str, ...]
    request_delay_seconds: float
    max_retries: int

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Resolve settings from `environ`, defaulting to the live process environment.

        Accepting a mapping keeps this testable without touching global state; every key is
        read by name, so nothing here changes when a path moves.
        """
        source = os.environ if environ is None else environ
        env = _resolve_env(source)
        repo_root = _resolve_repo_root(source)
        return cls(
            env=env,
            repo_root=repo_root,
            landing_root=_resolve_landing_root(source, env, repo_root),
            warehouse_path=_resolve_warehouse_path(source, env, repo_root),
            pilot_seasons=_resolve_pilot_seasons(source),
            request_delay_seconds=_resolve_positive_float(
                source, REQUEST_DELAY_KEY, DEFAULT_REQUEST_DELAY_SECONDS
            ),
            max_retries=_resolve_non_negative_int(source, MAX_RETRIES_KEY, DEFAULT_MAX_RETRIES),
        )


def get_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """The entry point every other module uses to learn a path, a season or a delay.

    Deliberately uncached: the environment is re-read on every call, so a monkeypatched key
    takes effect at once and no test inherits a neighbour's resolution. Resolution is cheap —
    a few `dict` lookups and one upward directory walk.
    """
    return Settings.from_env(environ)


def _component(label: str, value: str) -> str:
    """Validate and normalise one path segment of a landing key."""
    normalised = value.strip().lower()
    if not normalised:
        raise ConfigError(f"landing_key() got an empty {label}.")
    for illegal in ("/", "\\", "=", ":"):
        if illegal in normalised:
            raise ConfigError(
                f"landing_key() got {label}={value!r}, which contains {illegal!r}. "
                "That breaks the key=value partition shape, and ':' is illegal in a "
                "Windows path."
            )
    return normalised


def landing_key(
    source: str,
    endpoint: str,
    season: str,
    grain: str,
    season_type: str,
    captured_at: datetime,
) -> str:
    """The S3-key-shaped relative prefix one capture lands under, ending in `/`.

    Shape, exactly::

        nba_stats/league_game_log/season=2003-04/grain=player/season_type=regular/capture=<stamp>/

    The four trailing segments are Hive-style `key=value` pairs on purpose: DuckDB projects
    them as columns under `hive_partitioning = true`, which is how bronze recovers capture
    provenance from the *path* instead of joining to the manifest sidecar — a join the bronze
    layer contract forbids. Do not add segments and do not reorder them.

    `captured_at` must be timezone-aware; it is rendered as compact UTC with no `:`, because
    a colon is illegal in a Windows path. The full ISO timestamp belongs in the manifest.

    Every component is lowercased, so `grain=Player` and `grain=player` cannot become two
    partitions holding the same rows.
    """
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise ConfigError(
            "landing_key() needs a timezone-aware captured_at. A naive timestamp lands one "
            "capture under whatever the writer's local clock happened to say."
        )

    stamp = captured_at.astimezone(UTC).strftime(CAPTURE_STAMP_FORMAT)
    segments = (
        _component("source", source),
        _component("endpoint", endpoint),
        f"season={_component('season', season)}",
        f"grain={_component('grain', grain)}",
        f"season_type={_component('season_type', season_type)}",
        f"capture={stamp}",
    )
    return "/".join(segments) + "/"
