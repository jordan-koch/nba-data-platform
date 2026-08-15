"""The backfill command a human runs — one planner, two consumers, no drift.

    uv run python -m nba_platform.backfill --dry-run

**The planner is the point.** `build_plan()` returns the list of calls the run will make;
`--dry-run` counts and prints exactly that list, and the real run iterates exactly that
list. Two code paths that happen to agree today is precisely the drift the dry run exists to
catch, so there is only one. A dry run issues **zero** requests and constructs **no** client:
the client is built inside the branch that is not taken.

**Cost is checkable before it is spent.** The dry run prints the planned call count, the
configured pacing, and the pacing floor in wall-clock seconds. A real run writes a run
manifest recording what it actually cost — call count, elapsed seconds, observed spacing
between issued requests, and rows per call — so the estimate can be audited against the
measurement rather than believed.

**Re-running is safe and cheap.** A completed capture of a partition is detected *before*
the request is issued, so resuming a half-finished backfill costs nothing at the API. That
skip-if-present check is this project's whole checkpoint mechanism at six calls per pilot
run; there is deliberately no checkpoint store. `--recapture` lands a new capture beside the
existing one and never touches it.

Injection seams, all parameters of `run()` rather than module-level globals:

| seam | type | default |
|---|---|---|
| `client` | anything with `fetch(*, season, grain, season_type)` | a real `GameLogClient` |
| `stream` | text stream | `sys.stdout` |
| `now` | `Callable[[], datetime]` — tz-aware | `datetime.now(UTC)` |
| `monotonic` | `Callable[[], float]` | `time.monotonic` |
| `environ` | mapping or `None` | the live process environment |

Exit codes: 0 success, 1 the run started and a call failed, 2 the run never started
(bad arguments, bad configuration, or a refused write).
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, TextIO

from nba_platform.client import (
    CLIENT_NAME,
    DEFAULT_GRAINS,
    DEFAULT_SEASON_TYPE,
    ENDPOINT_NAME,
    GRAIN_ABBREVIATIONS,
    SEASON_TYPES,
    SOURCE_NAME,
    ClientError,
    GameLogClient,
    GameLogResponse,
    client_version,
)
from nba_platform.config import SEASON_PATTERN, ConfigError, Settings, get_settings
from nba_platform.landing import (
    MANIFEST_VERSION,
    CaptureResult,
    LandingError,
    Partition,
    existing_capture_result,
    write_capture,
    write_run_manifest,
)

__all__ = [
    "BackfillError",
    "BackfillPlan",
    "BackfillResult",
    "GameLogFetcher",
    "PlannedCall",
    "build_parser",
    "build_plan",
    "main",
    "plan_calls",
    "run",
    "utc_now",
]


class BackfillError(RuntimeError):
    """The requested backfill cannot be planned — a season, grain or season type is wrong."""


class GameLogFetcher(Protocol):
    """All the backfill needs from a client, so an offline stub is three lines long."""

    def fetch(self, *, season: str, grain: str, season_type: str) -> GameLogResponse: ...


def utc_now() -> datetime:
    """The default capture clock. Tz-aware by construction — ruff DTZ forbids the naive one."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class PlannedCall:
    """One request the run intends to make, and the partition it will land under."""

    season: str
    grain: str
    season_type: str
    source: str = SOURCE_NAME
    endpoint: str = ENDPOINT_NAME

    @property
    def partition(self) -> Partition:
        return Partition(
            source=self.source,
            endpoint=self.endpoint,
            season=self.season,
            grain=self.grain,
            season_type=self.season_type,
        )

    @property
    def label(self) -> str:
        return f"season={self.season} grain={self.grain} season_type={self.season_type}"


@dataclass(frozen=True, slots=True)
class BackfillPlan:
    """Every call the run will make, plus the pacing it will make them at."""

    calls: tuple[PlannedCall, ...]
    seasons: tuple[str, ...]
    grains: tuple[str, ...]
    season_type: str
    landing_root: Path
    request_delay_seconds: float
    max_retries: int
    recapture: bool

    @property
    def call_count(self) -> int:
        return len(self.calls)

    @property
    def estimated_pacing_seconds(self) -> float:
        """The pacing floor: the first call waits for nothing, every later one waits a delay.

        A floor, not a forecast — it excludes however long the source takes to answer, which
        is exactly what the run manifest measures.
        """
        return max(self.call_count - 1, 0) * self.request_delay_seconds


@dataclass(frozen=True, slots=True)
class BackfillResult:
    """What a run did, in the shape a test can assert against without parsing stdout."""

    plan: BackfillPlan
    dry_run: bool
    captures: tuple[CaptureResult, ...] = ()
    calls_made: int = 0
    written: int = 0
    skipped: int = 0
    elapsed_seconds: float = 0.0
    spacing_seconds: tuple[float, ...] = ()
    run_manifest_path: Path | None = None
    error: str | None = None

    @property
    def exit_code(self) -> int:
        return 1 if self.error is not None else 0


def plan_calls(
    *, seasons: Sequence[str], grains: Sequence[str], season_type: str
) -> tuple[PlannedCall, ...]:
    """The cross product of seasons and grains, seasons outermost and order preserved."""
    return tuple(
        PlannedCall(season=season, grain=grain, season_type=season_type)
        for season in seasons
        for grain in grains
    )


def _unique(values: Sequence[str]) -> tuple[str, ...]:
    """Order-preserving de-duplication — a repeated season is a typo, not two calls."""
    return tuple(dict.fromkeys(value.strip() for value in values if value.strip()))


def build_plan(
    *,
    settings: Settings,
    seasons: Sequence[str] | None = None,
    grains: Sequence[str] | None = None,
    season_type: str = DEFAULT_SEASON_TYPE,
    recapture: bool = False,
) -> BackfillPlan:
    """Resolve arguments against config and validate them before anything is issued.

    Defaults come from the config layer (`pilot_seasons`, the delay, the retry ceiling), so
    widening the backfill past the pilot is an environment change and not a code change.
    """
    chosen_seasons = _unique(seasons) if seasons else settings.pilot_seasons
    chosen_grains = _unique(grains) if grains else DEFAULT_GRAINS

    malformed = [season for season in chosen_seasons if not SEASON_PATTERN.match(season)]
    if malformed:
        raise BackfillError(
            f"{malformed!r} is not the NBA season format YYYY-YY (for example 2003-04). "
            "The endpoint takes that string verbatim."
        )
    unknown_grains = [grain for grain in chosen_grains if grain not in GRAIN_ABBREVIATIONS]
    if unknown_grains:
        raise BackfillError(
            f"{unknown_grains!r} is not a known grain. Choose from {sorted(GRAIN_ABBREVIATIONS)}."
        )
    if season_type not in SEASON_TYPES:
        raise BackfillError(
            f"season_type={season_type!r} is unknown. Choose from {sorted(SEASON_TYPES)}."
        )

    return BackfillPlan(
        calls=plan_calls(seasons=chosen_seasons, grains=chosen_grains, season_type=season_type),
        seasons=chosen_seasons,
        grains=chosen_grains,
        season_type=season_type,
        landing_root=settings.landing_root,
        request_delay_seconds=settings.request_delay_seconds,
        max_retries=settings.max_retries,
        recapture=recapture,
    )


def build_parser() -> argparse.ArgumentParser:
    """The CLI surface. Every default is resolved later, from config, never here."""
    parser = argparse.ArgumentParser(
        prog="python -m nba_platform.backfill",
        description=(
            "Land raw leaguegamelog captures in the immutable landing zone. Existing "
            "captures are skipped rather than overwritten; --recapture lands a new one "
            "beside them."
        ),
    )
    parser.add_argument(
        "--seasons",
        type=_split_list,
        default=None,
        help="comma-separated NBA seasons, e.g. 2003-04,2019-20 (default: the pilot seasons)",
    )
    parser.add_argument(
        "--grains",
        type=_split_list,
        default=None,
        help=f"comma-separated grains (default: {','.join(DEFAULT_GRAINS)})",
    )
    parser.add_argument(
        "--season-type",
        default=DEFAULT_SEASON_TYPE,
        help=f"one of {','.join(sorted(SEASON_TYPES))} (default: {DEFAULT_SEASON_TYPE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the plan and its estimated cost, issue zero requests, write nothing",
    )
    parser.add_argument(
        "--recapture",
        action="store_true",
        help="deliberately re-pull: land a new capture beside the existing one, never over it",
    )
    return parser


def _split_list(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _emit(stream: TextIO, line: str) -> None:
    """Every printed line goes through here, and every one of them is plain ASCII.

    Deliberate: this output gets piped and redirected on a Windows box whose console
    encoding is not UTF-8, and a decorative dash is not worth a UnicodeEncodeError in the
    middle of a backfill.
    """
    print(line, file=stream)


def _print_plan(plan: BackfillPlan, *, dry_run: bool, stream: TextIO) -> None:
    _emit(stream, "backfill plan (dry run - no requests issued)" if dry_run else "backfill plan")
    _emit(stream, f"landing root: {plan.landing_root}")
    _emit(stream, f"seasons: {', '.join(plan.seasons)}")
    _emit(stream, f"grains: {', '.join(plan.grains)}")
    _emit(stream, f"season type: {plan.season_type}")
    _emit(stream, f"planned calls: {plan.call_count}")
    _emit(stream, f"request delay seconds: {plan.request_delay_seconds}")
    _emit(stream, f"max retries: {plan.max_retries}")
    _emit(
        stream,
        f"estimated pacing seconds: {plan.estimated_pacing_seconds:.1f}"
        " (pacing floor only, excludes server response time)",
    )
    _emit(stream, f"recapture: {plan.recapture}")
    for index, call in enumerate(plan.calls, start=1):
        _emit(stream, f"  {index}. {call.label}")


@dataclass(slots=True)
class _RunTally:
    """Mutable bookkeeping for one run, kept out of `run()` so the loop stays readable."""

    captures: list[CaptureResult] = field(default_factory=list)
    records: list[dict[str, Any]] = field(default_factory=list)
    issued_at: list[float] = field(default_factory=list)
    calls_made: int = 0
    written: int = 0
    skipped: int = 0
    error: str | None = None

    @property
    def spacing_seconds(self) -> tuple[float, ...]:
        return tuple(
            later - earlier
            for earlier, later in zip(self.issued_at, self.issued_at[1:], strict=False)
        )


def run(
    argv: Sequence[str] | None = None,
    *,
    client: GameLogFetcher | None = None,
    stream: TextIO | None = None,
    now: Callable[[], datetime] = utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    environ: Mapping[str, str] | None = None,
) -> BackfillResult:
    """Plan the backfill, print it, and — unless this is a dry run — execute it."""
    args = build_parser().parse_args(argv)
    out = sys.stdout if stream is None else stream

    settings = get_settings(environ)
    plan = build_plan(
        settings=settings,
        seasons=args.seasons,
        grains=args.grains,
        season_type=args.season_type,
        recapture=args.recapture,
    )
    _print_plan(plan, dry_run=args.dry_run, stream=out)

    if args.dry_run:
        # The client is constructed inside the branch not taken, so a dry run cannot issue
        # a request even by accident.
        return BackfillResult(plan=plan, dry_run=True)

    fetcher: GameLogFetcher = GameLogClient(environ=environ) if client is None else client
    tally = _RunTally()
    started_at = now()
    started = monotonic()

    for index, call in enumerate(plan.calls, start=1):
        position = f"[{index}/{plan.call_count}]"
        if not plan.recapture:
            already = existing_capture_result(call.partition, landing_root=plan.landing_root)
            if already is not None:
                tally.captures.append(already)
                tally.skipped += 1
                _emit(
                    out,
                    f"{position} {call.label} skipped, already landed at "
                    f"{already.capture_dir.name}",
                )
                continue

        issued = monotonic()
        try:
            response = fetcher.fetch(
                season=call.season, grain=call.grain, season_type=call.season_type
            )
        except ClientError as exc:
            tally.error = str(exc)
            _emit(out, f"{position} {call.label} FAILED: {exc}")
            break

        tally.issued_at.append(issued)
        tally.calls_made += 1
        result = write_capture(
            partition=call.partition,
            payload=response.payload,
            captured_at=now(),
            parameters=response.parameters,
            status_code=response.status_code,
            elapsed_seconds=response.elapsed_seconds,
            request_url=response.request_url,
            client_name=CLIENT_NAME,
            client_version=response.client_version,
            landing_root=plan.landing_root,
            recapture=plan.recapture,
        )
        tally.captures.append(result)
        if result.written:
            tally.written += 1
            _emit(
                out,
                f"{position} {call.label} landed {result.row_count} rows "
                f"in {response.elapsed_seconds:.2f}s at {result.capture_dir.name}",
            )
        else:
            tally.skipped += 1
            _emit(out, f"{position} {call.label} skipped at {result.capture_dir.name}")
        tally.records.append(
            {
                "season": call.season,
                "grain": call.grain,
                "season_type": call.season_type,
                "attempts": response.attempts,
                "http_status": response.status_code,
                "row_count": result.row_count,
                "elapsed_seconds": response.elapsed_seconds,
                "capture": result.capture_dir.name,
                "written": result.written,
            }
        )

    elapsed = monotonic() - started
    run_manifest_path = None
    if tally.written:
        run_manifest_path = write_run_manifest(
            _run_manifest(
                plan=plan,
                tally=tally,
                started_at=started_at,
                finished_at=now(),
                elapsed_seconds=elapsed,
            ),
            started_at=started_at,
            landing_root=plan.landing_root,
        )

    _emit(out, f"calls made: {tally.calls_made}")
    _emit(out, f"captures written: {tally.written}")
    _emit(out, f"captures skipped: {tally.skipped}")
    _emit(out, f"elapsed seconds: {elapsed:.2f}")
    if run_manifest_path is not None:
        _emit(out, f"run manifest: {run_manifest_path}")

    return BackfillResult(
        plan=plan,
        dry_run=False,
        captures=tuple(tally.captures),
        calls_made=tally.calls_made,
        written=tally.written,
        skipped=tally.skipped,
        elapsed_seconds=elapsed,
        spacing_seconds=tally.spacing_seconds,
        run_manifest_path=run_manifest_path,
        error=tally.error,
    )


def _run_manifest(
    *,
    plan: BackfillPlan,
    tally: _RunTally,
    started_at: datetime,
    finished_at: datetime,
    elapsed_seconds: float,
) -> dict[str, Any]:
    """The measured half of the dry run's estimate, recorded so the two can be compared."""
    return {
        "manifest_version": MANIFEST_VERSION,
        "source": SOURCE_NAME,
        "endpoint": ENDPOINT_NAME,
        "started_at": started_at.astimezone(UTC).isoformat(),
        "finished_at": finished_at.astimezone(UTC).isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "planned_calls": plan.call_count,
        "calls_made": tally.calls_made,
        "captures_written": tally.written,
        "captures_skipped": tally.skipped,
        "recapture": plan.recapture,
        "request_delay_seconds": plan.request_delay_seconds,
        "estimated_pacing_seconds": plan.estimated_pacing_seconds,
        "observed_spacing_seconds": list(tally.spacing_seconds),
        "max_retries": plan.max_retries,
        "client": CLIENT_NAME,
        "client_version": client_version(),
        "error": tally.error,
        "calls": tally.records,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Console entry point: 0 green, 1 a call failed, 2 the run never started."""
    try:
        result = run(argv)
    except (BackfillError, ClientError, ConfigError, LandingError) as exc:
        print(f"backfill did not start: {exc}", file=sys.stderr)
        return 2
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
