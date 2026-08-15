"""The fixture recorder, and the integrity of the corpus it produced.

Two halves, and they fail for different reasons.

**The recorder's rules** (first half) are what stop a *future* fixture from being wrong. The
load-bearing one is the trim rule — whole games, rows only, over the same `GAME_ID` set at both
grains. A fixture trimmed by arbitrary rows leaves a team-game with one team and a game whose
player rows do not sum to its team total, so every reconciliation downstream either fails
spuriously or passes on an empty set. The recorder is built so that rule cannot be expressed
wrongly; these tests prove that claim rather than trusting it.

**The committed corpus** (second half) is what CI actually builds from under `--target ci`.
Checking it here means an over-trimmed or half-recaptured fixture goes red in pytest with a
readable message, rather than surfacing four layers down as a dbt test that mysteriously
compares an empty set.

Both halves are offline. The corpus was captured live once, from the payloads landed under
`var/` on 2026-08-15; `reviews/endpoint-probe.md` records what was measured from them.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from nba_platform.client import GameLogResponse
from nba_platform.fixtures import (
    CellEdit,
    FixtureError,
    apply_cell_edit,
    column_index,
    fixtures_root,
    game_ids,
    headers,
    record_case,
    record_error_case,
    row_dicts,
    trim_to_games,
)

CAPTURED_AT = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)

PLAYER_HEADERS = ["GAME_ID", "PLAYER_ID", "TEAM_ID", "GAME_DATE", "PTS"]
TEAM_HEADERS = ["GAME_ID", "TEAM_ID", "GAME_DATE", "PTS", "VIDEO_AVAILABLE"]


def _envelope(header_list: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {
        "resource": "leaguegamelog",
        "parameters": {"Season": "2019-20"},
        "resultSets": [{"name": "LeagueGameLog", "headers": header_list, "rowSet": rows}],
    }


def _player_payload() -> dict[str, Any]:
    """Three games, two teams each, two players per team — 12 rows."""
    rows = [
        [game, 100 + team * 10 + player, 1610612700 + team, "2020-07-30", 10 + player]
        for game in ("0021900001", "0021900002", "0021900003")
        for team in (1, 2)
        for player in (1, 2)
    ]
    return _envelope(PLAYER_HEADERS, rows)


def _team_payload() -> dict[str, Any]:
    rows = [
        [game, 1610612700 + team, "2020-07-30", 21 + team, 1]
        for game in ("0021900001", "0021900002", "0021900003")
        for team in (1, 2)
    ]
    return _envelope(TEAM_HEADERS, rows)


def _response(grain: str, payload: dict[str, Any]) -> GameLogResponse:
    return GameLogResponse(
        season="2019-20", grain=grain, season_type="regular", payload=payload, status_code=200
    )


@pytest.fixture
def scratch_corpus(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("NBA_ENV", "local")
    monkeypatch.setenv("NBA_REPO_ROOT", str(tmp_path))
    return tmp_path / "tests" / "fixtures"


# ─── The trim rule ────────────────────────────────────────────────────────────────────


def test_trimming_keeps_every_row_of_a_kept_game() -> None:
    """Whole games: keeping one game keeps all four of its player rows, not a sample."""
    result = trim_to_games(_player_payload(), ["0021900002"])

    assert result.original_row_count == 12
    assert result.retained_row_count == 4
    assert result.game_ids == ("0021900002",)
    assert {row["GAME_ID"] for row in row_dicts(result.payload)} == {"0021900002"}
    # Both teams survive, which is what assert_every_game_has_exactly_two_teams needs.
    assert len({row["TEAM_ID"] for row in row_dicts(result.payload)}) == 2


def test_trimming_never_touches_the_envelope() -> None:
    """Only rowSet shrinks — headers, name, resource and parameters pass through intact."""
    original = _player_payload()
    trimmed = trim_to_games(original, ["0021900001"]).payload

    assert headers(trimmed) == headers(original)
    assert sorted(trimmed) == sorted(original)
    assert trimmed["resultSets"][0]["name"] == original["resultSets"][0]["name"]
    assert trimmed["resource"] == original["resource"]
    assert trimmed["parameters"] == original["parameters"]


def test_columns_resolve_by_name_not_by_position() -> None:
    """The upstream is unversioned; a reordered column must not shift every value."""
    payload = _player_payload()
    assert column_index(payload, "GAME_ID") == 0

    reordered_headers = ["PTS", "GAME_ID", "PLAYER_ID", "TEAM_ID", "GAME_DATE"]
    reordered_rows = [
        [row[4], row[0], row[1], row[2], row[3]] for row in payload["resultSets"][0]["rowSet"]
    ]
    reordered = _envelope(reordered_headers, reordered_rows)

    assert column_index(reordered, "GAME_ID") == 1
    assert trim_to_games(reordered, ["0021900002"]).retained_row_count == 4


def test_a_trim_that_would_empty_the_fixture_raises(scratch_corpus: Path) -> None:
    """An empty fixture passes every test vacuously — so it must never be written."""
    with pytest.raises(FixtureError):
        trim_to_games(_player_payload(), [])

    with pytest.raises(FixtureError):
        trim_to_games(_player_payload(), ["0029999999"])


def test_a_game_missing_from_one_grain_raises(scratch_corpus: Path) -> None:
    """The grains must cover the same games, or a reconciliation compares unequal sets."""
    short_team = _envelope(TEAM_HEADERS, _team_payload()["resultSets"][0]["rowSet"][:2])

    with pytest.raises(FixtureError):
        record_case(
            case="mismatched-grains",
            reason="both grains must cover the same games or the reconciliations are unequal",
            responses=[_response("player", _player_payload()), _response("team", short_team)],
            game_ids_kept=("0021900001", "0021900002"),
            captured_at=CAPTURED_AT,
            fixtures_root_override=scratch_corpus,
        )


def test_one_game_set_covers_both_grains(scratch_corpus: Path) -> None:
    """record_case takes ONE game set, so the grains structurally cannot diverge."""
    result = record_case(
        case="two-grains-one-game-set",
        reason="the recorder takes one game set for the whole case, so grains cannot diverge",
        responses=[_response("player", _player_payload()), _response("team", _team_payload())],
        game_ids_kept=("0021900001", "0021900003"),
        captured_at=CAPTURED_AT,
        fixtures_root_override=scratch_corpus,
    )

    assert len(result.captures) == 2
    by_grain = {capture.grain: capture for capture in result.captures}
    assert by_grain["player"].retained_row_count == 8
    assert by_grain["team"].retained_row_count == 4

    for capture in result.captures:
        landed = json.loads(capture.payload_path.read_text(encoding="utf-8"))
        assert set(game_ids(landed)) == {"0021900001", "0021900003"}


# ─── Provenance lands in the manifest, both branches ──────────────────────────────────


def test_a_recorded_fixture_carries_its_trim_provenance_in_the_manifest(
    scratch_corpus: Path,
) -> None:
    """Plan step 9: the manifest says what was kept and what was dropped."""
    result = record_case(
        case="provenance-check",
        reason="the manifest must record what was kept and what was dropped",
        responses=[_response("player", _player_payload())],
        game_ids_kept=("0021900001",),
        captured_at=CAPTURED_AT,
        fixtures_root_override=scratch_corpus,
    )

    manifest = json.loads(result.captures[0].manifest_path.read_text(encoding="utf-8"))
    provenance = manifest["provenance"]

    assert provenance is not None
    assert provenance["original_row_count"] == 12
    assert provenance["retained_row_count"] == 4
    assert provenance["game_ids"] == ["0021900001"]
    assert provenance["case"] == "provenance-check"
    assert (
        "dropped" in json.dumps(provenance)
        or provenance["original_row_count"] > provenance["retained_row_count"]
    )
    # The wire parameter dict must stay uncontaminated — bronze reads it.
    assert "original_row_count" not in manifest["parameters"]
    assert (result.captures[0].capture_dir / "trim_provenance.json").exists() is False


def test_an_untrimmed_capture_records_provenance_as_null(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A plain backfill capture has no trim to record, and says so explicitly.

    The key is always present. Absent-vs-null is the difference between "this writer did not
    know about provenance" and "this capture was not trimmed", and only one of those is true.
    """
    from nba_platform.landing import Partition, write_capture

    monkeypatch.setenv("NBA_ENV", "local")
    result = write_capture(
        partition=Partition("nba_stats", "league_game_log", "2019-20", "team", "regular"),
        payload=_team_payload(),
        captured_at=CAPTURED_AT,
        landing_root=tmp_path,
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert "provenance" in manifest
    assert manifest["provenance"] is None


# ─── The single deliberate edit ───────────────────────────────────────────────────────


def test_a_cell_edit_changes_exactly_one_value(scratch_corpus: Path) -> None:
    edited, record = apply_cell_edit(
        _team_payload(),
        CellEdit(
            match={"GAME_ID": "0021900001", "TEAM_ID": 1610612701},
            column="VIDEO_AVAILABLE",
            value=99,
            reason="sentinel",
        ),
    )

    changed = [row for row in row_dicts(edited) if row["VIDEO_AVAILABLE"] == 99]
    assert len(changed) == 1
    assert changed[0]["GAME_ID"] == "0021900001"
    assert record["value_before"] == 1
    assert record["value_after"] == 99
    # Every other row is untouched.
    assert len([row for row in row_dicts(edited) if row["VIDEO_AVAILABLE"] == 1]) == 5


def test_an_ambiguous_cell_edit_raises_rather_than_editing_several(
    scratch_corpus: Path,
) -> None:
    """A match hitting two rows would corrupt data nobody asked to change."""
    with pytest.raises(FixtureError):
        apply_cell_edit(
            _team_payload(),
            CellEdit(match={"GAME_ID": "0021900001"}, column="PTS", value=0, reason="ambiguous"),
        )


def test_an_error_case_lands_flat_and_never_in_a_partition(scratch_corpus: Path) -> None:
    """It must not be reachable by the bronze glob, and it must record its own provenance.

    The provenance matters more here than anywhere else: this is the one fixture whose whole
    point is "captured, not hand-authored", and without a record of the request that produced
    it that claim is unfalsifiable.
    """
    empty_body = _envelope(TEAM_HEADERS, [])

    result = record_error_case(
        case="empty-impossible-season",
        reason="a valid request for a season that never existed answers 200 with no rows",
        payload=empty_body,
        captured_at=CAPTURED_AT,
        parameters={"Season": "2099-00"},
        status_code=200,
        fixtures_root_override=scratch_corpus,
    )

    assert "_error_cases" in result.payload_path.as_posix()
    assert "season=" not in result.payload_path.as_posix()

    globbed = scratch_corpus.glob("*/*/season=*/grain=*/season_type=*/capture=*/payload.json")
    assert result.payload_path not in set(globbed)

    provenance = json.loads(result.provenance_path.read_text(encoding="utf-8"))
    assert provenance["parameters"]["Season"] == "2099-00"
    assert provenance["case"] == "empty-impossible-season"


# ─── The committed corpus, as CI will actually read it ────────────────────────────────

CORPUS = ("nba_stats", "league_game_log")


def _corpus_root() -> Path:
    return fixtures_root().joinpath(*CORPUS)


def _captures() -> list[Path]:
    return sorted(path.parent for path in _corpus_root().rglob("payload.json"))


def test_the_committed_corpus_exists_and_spans_the_required_cases() -> None:
    """AC 20: modern, pre-tracking, bubble, a traded player, an empty response, a recapture."""
    captures = _captures()
    assert captures, "no committed corpus - CI has nothing to build from"

    seasons = {part.split("=")[1] for path in captures for part in path.parts if "season=" in part}
    assert seasons == {"2003-04", "2019-20", "2024-25"}

    grains = {part.split("=")[1] for path in captures for part in path.parts if "grain=" in part}
    assert grains == {"player", "team"}

    error_cases = sorted((_corpus_root() / "_error_cases").glob("*.json"))
    assert error_cases, "no empty/error case captured"


def test_every_committed_fixture_holds_whole_games_at_both_grains() -> None:
    """The trim rule, verified on what actually shipped rather than on a synthetic payload.

    This is the check that catches an over-trimmed corpus. If a team-grain fixture is missing
    one side of a game, `assert_every_game_has_exactly_two_teams` fails in dbt with a message
    about the model; this fails here with a message about the fixture.
    """
    by_partition: dict[tuple[str, str], set[str]] = {}

    for capture in _captures():
        parts = {p.split("=")[0]: p.split("=")[1] for p in capture.parts if "=" in p}
        payload = json.loads((capture / "payload.json").read_text(encoding="utf-8"))
        rows = row_dicts(payload)
        assert rows, f"{capture} is empty - every fixture-backed test would pass vacuously"

        if parts["grain"] == "team":
            per_game: dict[str, int] = {}
            for row in rows:
                per_game[str(row["GAME_ID"])] = per_game.get(str(row["GAME_ID"]), 0) + 1
            wrong = {game: n for game, n in per_game.items() if n != 2}
            assert not wrong, f"{capture}: team rows per game must be exactly 2, got {wrong}"

        key = (parts["season"], parts["grain"])
        by_partition.setdefault(key, set()).update(game_ids(payload))

    # Both grains of a season must cover the same games, or the cross-grain reconciliation
    # compares populations that were never equal.
    for season in {season for season, _ in by_partition}:
        player_games = by_partition.get((season, "player"))
        team_games = by_partition.get((season, "team"))
        if player_games is None or team_games is None:
            continue
        assert player_games <= team_games, (
            f"{season}: player-grain games {player_games - team_games} have no team-grain rows"
        )


def test_the_bubble_fixture_really_carries_out_of_window_dates() -> None:
    """2019-20 was chosen for this property; a trim that lost it makes the season pointless."""
    bubble = [c for c in _captures() if "season=2019-20" in c.as_posix()]
    assert bubble

    dates: set[str] = set()
    for capture in bubble:
        payload = json.loads((capture / "payload.json").read_text(encoding="utf-8"))
        dates.update(str(row["GAME_DATE"]) for row in row_dicts(payload))

    out_of_window = {date for date in dates if date[5:7] in {"05", "06", "07", "08", "09", "10"}}
    assert out_of_window, f"no out-of-Oct-Apr dates survived the trim: {sorted(dates)}"


def test_the_corpus_contains_a_second_capture_of_one_partition() -> None:
    """AC 15's enabler: bronze's latest-capture-wins needs something to actually resolve."""
    partitions: dict[str, int] = {}
    for capture in _captures():
        partition = capture.parent.as_posix()
        partitions[partition] = partitions.get(partition, 0) + 1

    restated = {p: n for p, n in partitions.items() if n > 1}
    assert restated, (
        "no partition has two captures - assert_latest_capture_wins would pass vacuously"
    )


def test_the_pinned_trade_survives_in_the_committed_corpus() -> None:
    """AC 10's boundary dates must be IN the fixture, not merely in the probe write-up."""
    pinned_player = 1631108  # Max Christie, from the captured payload
    lakers, mavericks = 1610612747, 1610612742

    modern = [
        c
        for c in _captures()
        if "season=2024-25" in c.as_posix() and "grain=player" in c.as_posix()
    ]
    assert modern

    his_rows = [
        row
        for capture in modern
        for row in row_dicts(json.loads((capture / "payload.json").read_text(encoding="utf-8")))
        if row["PLAYER_ID"] == pinned_player
    ]
    assert his_rows, "the pinned player was trimmed out of his own fixture"

    teams = {row["TEAM_ID"] for row in his_rows}
    assert teams == {lakers, mavericks}, f"both sides of the trade must survive, got {teams}"

    last_old = max(str(r["GAME_DATE"]) for r in his_rows if r["TEAM_ID"] == lakers)
    first_new = min(str(r["GAME_DATE"]) for r in his_rows if r["TEAM_ID"] == mavericks)
    assert last_old == "2025-02-01"
    assert first_new == "2025-02-04"
    assert last_old < first_new, "the stint boundary must be unambiguous"


def test_the_error_case_sits_outside_the_partitioned_tree() -> None:
    """EXEC-02: inside it, the bronze source glob would union a zero-row season into the model."""
    error_cases = sorted((_corpus_root() / "_error_cases").glob("*.json"))
    assert error_cases

    globbed = list(_corpus_root().glob("season=*/grain=*/season_type=*/capture=*/payload.json"))
    assert globbed, "the bronze-shaped glob matched nothing"
    assert not any("_error_cases" in path.as_posix() for path in globbed)

    body = json.loads(
        next(p for p in error_cases if not p.name.endswith(".provenance.json")).read_text(
            encoding="utf-8"
        )
    )
    # Measured 2026-08-15: an empty response is a COMPLETE envelope with an empty rowSet,
    # not a headerless body. The offline error path is written against that shape.
    assert len(body["resultSets"][0]["headers"]) == 29
    assert body["resultSets"][0]["rowSet"] == []


def test_every_fixtures_manifest_agrees_with_the_bytes_beside_it() -> None:
    """The manifest is only useful if it describes the file it sits next to.

    Three claims, each checkable: the headers are present and non-empty, the landed rowSet
    length equals the retained count the provenance claims, and the retained count is genuinely
    smaller than the original — a fixture recording a trim it did not perform is a fixture
    somebody will later trust about a trim that never happened.
    """
    checked = 0
    for capture in _captures():
        payload = json.loads((capture / "payload.json").read_text(encoding="utf-8"))
        manifest = json.loads((capture / "manifest.json").read_text(encoding="utf-8"))
        provenance = manifest["provenance"]

        assert headers(payload), f"{capture}: headers missing or empty"
        assert provenance is not None, f"{capture}: a fixture must record how it was trimmed"

        landed_rows = len(payload["resultSets"][0]["rowSet"])
        assert landed_rows == provenance["retained_row_count"], (
            f"{capture}: {landed_rows} rows on disk but provenance claims "
            f"{provenance['retained_row_count']}"
        )
        assert landed_rows == manifest["row_count"]
        assert provenance["retained_row_count"] < provenance["original_row_count"], (
            f"{capture}: provenance records a trim that did not happen"
        )
        checked += 1

    assert checked >= 7, f"only {checked} captures checked - the corpus looks incomplete"


def test_the_corpus_exercises_cross_season_franchise_drift() -> None:
    """`dim_team`'s whole reason for existing must be visible to CI.

    This guard exists because the corpus once silently lacked it. The first corpus held 17
    `(team_id, team_name)` pairs over 17 team_ids — zero franchise drift, with Seattle/OKC absent
    entirely — because the games were chosen by "first N" without checking which franchises they
    contained. Every test still passed, and `dim_team`'s as-of-latest resolution was, under
    `--target ci`, indistinguishable from the naive `select distinct team_id, team_name` its own
    header calls the wrong model.

    Nothing catches that except an assertion about the corpus itself: the drift is a property of
    which GAMES were kept, so no test over the models can tell a correct model on a blind corpus
    from an incorrect one.
    """
    names_by_id: dict[int, set[str]] = {}
    for capture in _captures():
        if "grain=team" not in capture.as_posix():
            continue
        payload = json.loads((capture / "payload.json").read_text(encoding="utf-8"))
        for row in row_dicts(payload):
            names_by_id.setdefault(int(row["TEAM_ID"]), set()).add(str(row["TEAM_NAME"]))

    assert names_by_id, "no team-grain fixtures - this guard would pass vacuously"

    drifting = {tid: sorted(names) for tid, names in names_by_id.items() if len(names) > 1}
    assert drifting, (
        "NO franchise appears under two names anywhere in the fixture corpus, so dim_team's "
        "as-of-latest rule is untestable in CI and a naive `select distinct team_id, team_name` "
        "would pass every check. Keep at least one game per drifting franchise on BOTH sides of "
        "a rename — e.g. Seattle SuperSonics in 2003-04 and Oklahoma City Thunder in 2024-25."
    )

    # The naive form must be visibly wrong on this corpus, which is the property that makes the
    # uniqueness test on dim_team meaningful rather than incidental.
    pairs = sum(len(names) for names in names_by_id.values())
    assert pairs > len(names_by_id), (
        f"{pairs} (team_id, team_name) pairs over {len(names_by_id)} team_ids - a naive distinct "
        "would already satisfy unique(team_id), so the test proves nothing"
    )


def test_the_corpus_stays_small_enough_to_belong_in_git() -> None:
    """This repo redistributes no NBA data; the .gitignore carve-out is not a licence."""
    total = sum(path.stat().st_size for path in _corpus_root().rglob("*.json"))
    assert total < 512_000, f"the fixture corpus is {total} bytes - drop whole games, never rows"
