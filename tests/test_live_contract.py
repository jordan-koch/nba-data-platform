"""The live column-set contract — the only counter-pressure against a frozen fixture lying.

`docs/data-sources.md` calls this upstream "undocumented, unversioned, and governed by no
contract." Every committed fixture is therefore a frozen copy of a contract that can change
without notice, and CI — which builds entirely from fixtures — would stay green for months
after the source renamed a column. This module is the alarm that does not depend on fixtures.

It is marked `network` and is **excluded from CI** by `.github/workflows/ci.yml:53`; the marker
is declared at `pyproject.toml:80-82`. Run it deliberately:

    uv run pytest -m network

**What it asserts against.** Binding correction SEQ-01 has two halves. The first: while Phase 3
gated the model phases, this test asserted against the measured column lists in
`reviews/endpoint-probe.md`, because depending on a file a later phase creates would have made
the gate hit a `FileNotFoundError` or skip vacuously. The second, executed here: now that
`transform/models/bronze/schema.yml` exists, this test reads its column list **from the YAML**,
so there is exactly one declaration of the contract rather than three.

That closes the loop with `tests/test_fixture_schema_drift.py`, which asserts fixtures equal the
same YAML. Live matches YAML, YAML matches fixtures — so a source change reddens here, a fixture
re-record without a YAML edit reddens there, and neither can drift silently past the other. The
hardcoded lists below are retained only as a **cross-check on the parse itself**: if the YAML
reader ever returns something empty or reordered, comparing against it alone would pass.

Cost: six calls at the configured pacing, roughly six seconds. It satisfies AC 27 by printing
the measured call count, rows per call, wall-clock seconds, and the ordered column list per
grain per pilot season — through `capsys.disabled()`, so the figures appear on a plain
`pytest -m network` without anyone needing to remember `-s`.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest
import yaml

from nba_platform.client import GameLogClient
from nba_platform.config import get_settings

# MEASURED 2026-08-15 and recorded in reviews/endpoint-probe.md. Identical across 2003-04,
# 2019-20 and 2024-25 at both grains. Note the player list is NOT the team list with three
# columns appended - PLAYER_ID and PLAYER_NAME are interleaved at positions 1-2 and
# FANTASY_PTS sits second-to-last. Assuming otherwise misaligns every later field.
TEAM_COLUMNS: tuple[str, ...] = (
    "SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "TEAM_NAME", "GAME_ID", "GAME_DATE",
    "MATCHUP", "WL", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A", "FG3_PCT", "FTM", "FTA",
    "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "PLUS_MINUS",
    "VIDEO_AVAILABLE",
)  # fmt: skip

PLAYER_COLUMNS: tuple[str, ...] = (
    "SEASON_ID", "PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION", "TEAM_NAME",
    "GAME_ID", "GAME_DATE", "MATCHUP", "WL", "MIN", "FGM", "FGA", "FG_PCT", "FG3M", "FG3A",
    "FG3_PCT", "FTM", "FTA", "FT_PCT", "OREB", "DREB", "REB", "AST", "STL", "BLK", "TOV",
    "PF", "PTS", "PLUS_MINUS", "FANTASY_PTS", "VIDEO_AVAILABLE",
)  # fmt: skip

RECORDED_COLUMNS = {"team": TEAM_COLUMNS, "player": PLAYER_COLUMNS}

BRONZE_SCHEMA = (
    Path(__file__).resolve().parents[1] / "transform" / "models" / "bronze" / "schema.yml"
)


def _declared_columns() -> dict[str, tuple[str, ...]]:
    """Grain -> ordered endpoint columns, read from bronze's own schema.yml.

    SEQ-01's second half: the YAML is the single declaration of this contract. Columns recovered
    from the landing path rather than projected from the envelope opt out via
    `meta.endpoint_column: false`, so provenance columns are excluded by property, not by name.
    """
    with BRONZE_SCHEMA.open(encoding="utf-8") as handle:
        loaded: Any = yaml.safe_load(handle)
    declared: dict[str, tuple[str, ...]] = {}
    for model in loaded["models"]:
        grain = str(model["name"]).rsplit("_", 1)[-1]
        declared[grain] = tuple(
            str(column["name"]).upper()
            for column in model.get("columns", [])
            if (column.get("meta") or {}).get("endpoint_column") is not False
        )
    return declared


def test_the_declared_contract_still_matches_what_was_measured() -> None:
    """Guard the parse itself, offline-checkable, so the live test cannot pass vacuously.

    If `_declared_columns()` ever returned empty or reordered lists, asserting the live response
    against it alone would succeed while proving nothing.
    """
    declared = _declared_columns()
    assert declared.keys() == RECORDED_COLUMNS.keys()
    for grain, recorded in RECORDED_COLUMNS.items():
        assert declared[grain] == recorded, (
            f"bronze/schema.yml's {grain} column list no longer matches the list measured in "
            f"reviews/endpoint-probe.md.\n  yaml    : {declared[grain]}\n  measured: {recorded}"
        )


EXPECTED_COLUMNS = _declared_columns()

# A floor, not the measured count: these are real seasons and a response an order of magnitude
# short of this is a truncated or paginated answer, which is the failure mode that would make
# every downstream count quietly wrong.
MINIMUM_ROWS = {"team": 2_000, "player": 20_000}


def _result_set(payload: Any) -> dict[str, Any]:
    result_sets = payload["resultSets"]
    assert isinstance(result_sets, list) and result_sets, "envelope carried no result set"
    first: dict[str, Any] = result_sets[0]
    return first


@pytest.mark.network
def test_the_live_column_contract_still_matches_what_was_measured(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Six live calls; the ordered column list must still be what the probe recorded."""
    settings = get_settings()
    client = GameLogClient()
    started = time.monotonic()
    measurements: list[tuple[str, str, int, int]] = []

    for season in settings.pilot_seasons:
        for grain in ("player", "team"):
            payload = client.fetch(season=season, grain=grain, season_type="regular").payload
            result_set = _result_set(payload)
            headers = tuple(result_set["headers"])
            rows = result_set["rowSet"]

            assert headers == EXPECTED_COLUMNS[grain], (
                f"UPSTREAM COLUMN DRIFT at season={season} grain={grain}.\n"
                f"  expected: {EXPECTED_COLUMNS[grain]}\n"
                f"  received: {headers}\n"
                "Every committed fixture is now stale, and bronze's schema.yml with them. "
                "Re-record the fixtures before trusting a green CI run."
            )
            assert len(rows) >= MINIMUM_ROWS[grain], (
                f"season={season} grain={grain} returned {len(rows)} rows, under the "
                f"{MINIMUM_ROWS[grain]} floor - a truncated or paginated response."
            )
            measurements.append((season, grain, len(rows), len(headers)))

    elapsed = time.monotonic() - started

    # AC 27: print the measured figures. capsys.disabled() makes them appear without `-s`.
    with capsys.disabled():
        print(f"\n{'=' * 70}")
        print("LIVE CONTRACT - measured this run")
        print(f"{'=' * 70}")
        print(f"calls made          : {client.request_count}")
        print(f"wall clock seconds  : {elapsed:.2f}")
        print(f"configured pacing   : {settings.request_delay_seconds}s")
        print(f"observed spacing    : {[round(g, 2) for g in client.observed_spacing_seconds]}")
        print(f"{'season':<10}{'grain':<9}{'rows':>8}{'cols':>7}")
        for season, grain, rows_count, cols in measurements:
            print(f"{season:<10}{grain:<9}{rows_count:>8}{cols:>7}")
        print(f"\nteam   columns ({len(TEAM_COLUMNS)}): {', '.join(TEAM_COLUMNS)}")
        print(f"player columns ({len(PLAYER_COLUMNS)}): {', '.join(PLAYER_COLUMNS)}")
        print(f"{'=' * 70}")

    assert client.request_count == len(settings.pilot_seasons) * 2 == 6
    assert len(measurements) == 6


@pytest.mark.network
def test_the_endpoint_still_answers_an_impossible_season_with_an_empty_envelope() -> None:
    """The empty-response shape AC 20's fixture is built on, re-checked live.

    Measured 2026-08-15: a structurally valid request for a season that never existed returns
    HTTP 200 with a *complete* envelope - all 29 headers present, `rowSet` empty. That is what
    makes the empty case safe to hold as a fixture, and it is worth re-checking, because if the
    source ever starts answering with a truncated body instead, the offline error-path tests
    are testing a shape that no longer occurs.
    """
    from nba_api.stats.library.http import NBAStatsHTTP

    impossible_season = {
        "Counter": "0", "Direction": "ASC", "LeagueID": "00", "PlayerOrTeam": "T",
        "Season": "2099-00", "SeasonType": "Regular Season", "Sorter": "DATE",
        "DateFrom": "", "DateTo": "",
    }  # fmt: skip

    response = NBAStatsHTTP().send_api_request(
        endpoint="leaguegamelog", parameters=impossible_season
    )

    payload = response.get_dict()
    result_set = _result_set(payload)

    assert tuple(result_set["headers"]) == TEAM_COLUMNS, (
        "an empty response no longer carries the full header list - the offline error-path "
        "fixtures now describe a shape the source does not return"
    )
    assert result_set["rowSet"] == []
