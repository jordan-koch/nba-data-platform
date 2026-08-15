"""The offline half of acceptance criterion 28 — the dry run's count is the real run's count.

`CLAUDE.md` makes cost a guardrail, and a cost estimate nobody can check is a guess with a
number on it. The contract this module enforces is narrow and load-bearing: the call count
`--dry-run` prints must equal the number of calls a subsequent real run actually makes, and a
dry run must issue **zero** requests to say so.

The way that contract is kept is one planner with two consumers. These tests therefore assert
the planner's *output* is shared, not merely that two independently-computed numbers happen to
agree today — two code paths agreeing by coincidence is exactly the drift this criterion
exists to catch.

The live half (the printed number against a real backfill's observed count) is user-run in
Phase 9; it cannot be proven offline.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any, NoReturn

import pytest

from nba_platform.backfill import BackfillError, build_plan, main, run
from nba_platform.client import GameLogResponse
from nba_platform.config import get_settings

PLANNED_CALLS = re.compile(r"^planned calls: (\d+)$", re.MULTILINE)


def _printed_call_count(output: str) -> int:
    match = PLANNED_CALLS.search(output)
    assert match is not None, f"no 'planned calls:' line in output:\n{output}"
    return int(match.group(1))


class ExplodingClient:
    """Fails the test loudly if a dry run so much as looks at a client."""

    def fetch(self, *, season: str, grain: str, season_type: str) -> NoReturn:
        raise AssertionError(
            f"a dry run issued a request for season={season} grain={grain} "
            f"season_type={season_type}"
        )


class CountingClient:
    """Answers with a minimal envelope and counts the calls it was asked to make."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def fetch(self, *, season: str, grain: str, season_type: str) -> GameLogResponse:
        self.calls.append((season, grain, season_type))
        payload: dict[str, Any] = {
            "resource": "leaguegamelog",
            "resultSets": [
                {"name": "LeagueGameLog", "headers": ["GAME_ID"], "rowSet": [["0020300001"]]}
            ],
        }
        return GameLogResponse(
            season=season, grain=grain, season_type=season_type, payload=payload, status_code=200
        )


@pytest.fixture
def landing_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    root = tmp_path / "landing"
    monkeypatch.setenv("NBA_ENV", "local")
    monkeypatch.setenv("NBA_LANDING_ROOT", str(root))
    return root


# ─── A dry run costs nothing ──────────────────────────────────────────────────────────


def test_a_dry_run_issues_no_requests_and_writes_no_file(landing_root: Path) -> None:
    stream = io.StringIO()

    result = run(["--dry-run"], client=ExplodingClient(), stream=stream)

    assert result.dry_run is True
    assert result.calls_made == 0
    assert result.written == 0
    assert _tree_is_empty(landing_root), "a dry run wrote to the landing zone"
    assert _printed_call_count(stream.getvalue()) == 6  # 3 pilot seasons x 2 grains


def _tree_is_empty(root: Path) -> bool:
    return not root.exists() or not any(path.is_file() for path in root.rglob("*"))


def test_a_dry_run_prints_the_cost_a_human_needs_before_spending_it(
    landing_root: Path,
) -> None:
    """The estimate is a pacing floor, and it says so — an unlabelled number invites trust."""
    stream = io.StringIO()

    run(["--dry-run"], client=ExplodingClient(), stream=stream)
    output = stream.getvalue()

    assert "no requests issued" in output
    assert "request delay seconds: 0.6" in output
    assert "estimated pacing seconds: 3.0" in output  # (6 - 1) x 0.6
    assert "pacing floor only" in output


# ─── The two consumers share one planner ──────────────────────────────────────────────


def test_the_dry_run_count_equals_the_real_runs_call_count(landing_root: Path) -> None:
    """AC 28's offline half, stated exactly."""
    dry_stream = io.StringIO()
    run(["--dry-run"], client=ExplodingClient(), stream=dry_stream)

    client = CountingClient()
    real = run([], client=client, stream=io.StringIO())

    printed = _printed_call_count(dry_stream.getvalue())
    assert printed == len(client.calls) == real.calls_made == 6


def test_both_runs_iterate_the_identical_plan_not_merely_the_same_count(
    landing_root: Path,
) -> None:
    """A matching count from two different plans would satisfy the criterion and still be wrong."""
    dry = run(["--dry-run"], client=ExplodingClient(), stream=io.StringIO())
    real = run([], client=CountingClient(), stream=io.StringIO())

    assert dry.plan.calls == real.plan.calls
    assert dry.plan.seasons == real.plan.seasons
    assert dry.plan.grains == real.plan.grains


def test_the_plan_narrows_with_the_arguments_it_is_given(landing_root: Path) -> None:
    """Cost scales with the request, so the estimate has to move when the request does."""
    stream = io.StringIO()

    result = run(
        ["--dry-run", "--seasons", "2019-20", "--grains", "player"],
        client=ExplodingClient(),
        stream=stream,
    )

    assert _printed_call_count(stream.getvalue()) == 1
    assert result.plan.calls[0].season == "2019-20"
    assert result.plan.calls[0].grain == "player"
    assert result.plan.estimated_pacing_seconds == 0.0


def test_the_pilot_default_comes_from_config_not_from_the_cli(
    landing_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Widening past the pilot is a parameter change — the proof that it is."""
    monkeypatch.setenv("NBA_PILOT_SEASONS", "2011-12,2020-21,2003-04,2024-25")
    stream = io.StringIO()

    run(["--dry-run"], client=ExplodingClient(), stream=stream)

    assert _printed_call_count(stream.getvalue()) == 8  # 4 seasons x 2 grains


def test_the_planner_is_the_same_function_the_cli_uses(landing_root: Path) -> None:
    """Called directly, `build_plan` produces what the CLI produced — one planner, not two."""
    from_cli = run(["--dry-run"], client=ExplodingClient(), stream=io.StringIO()).plan
    directly = build_plan(settings=get_settings())

    assert directly.calls == from_cli.calls
    assert directly.call_count == from_cli.call_count == 6


# ─── Bad input never becomes a request ────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--seasons", "2003-2004"], "YYYY-YY"),
        (["--grains", "referee"], "grain"),
        (["--season-type", "allstar"], "season_type"),
    ],
)
def test_a_malformed_argument_fails_before_planning_completes(
    landing_root: Path, argv: list[str], expected: str
) -> None:
    with pytest.raises(BackfillError, match=expected):
        run([*argv, "--dry-run"], client=ExplodingClient(), stream=io.StringIO())


def test_main_reports_a_run_that_never_started_distinctly_from_one_that_failed(
    landing_root: Path,
) -> None:
    """Exit 2 means nothing was attempted; exit 1 would mean a call was made and failed."""
    assert main(["--grains", "referee", "--dry-run"]) == 2
    assert main(["--dry-run"]) == 0
