"""Acceptance criterion 19 — the fixtures and bronze's declared contract cannot drift apart.

`docs/data-sources.md` calls this upstream "undocumented, unversioned, and governed by no
contract." Two things therefore rot independently: the committed fixtures freeze one snapshot of
that contract, and bronze's `schema.yml` declares another. `tests/test_live_contract.py` catches
the source moving away from both — but it is `network`-marked and excluded from CI, so it cannot
catch the case that actually happens in a pull request: someone re-records a fixture and forgets
the YAML, or edits the YAML and forgets the fixture.

That case is what this module catches, offline, in both directions and **in order**. Order is the
half that matters most and is easiest to lose: the player grain's extra columns are *interleaved*
(`PLAYER_ID` and `PLAYER_NAME` at positions 1-2, `FANTASY_PTS` second-to-last), not appended. A
model written against the appended reading misaligns every field from `TEAM_ID` onward while
passing every uniqueness test there is.

The column list is parsed out of the YAML rather than hardcoded here, so this guard cannot drift
from the thing it is guarding. Columns recovered from the landing path rather than projected from
the envelope declare `meta.endpoint_column: false` and are excluded by that property — never by a
hardcoded name, which would silently stop excluding anything if a name changed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BRONZE_SCHEMA = REPO_ROOT / "transform" / "models" / "bronze" / "schema.yml"
CORPUS = REPO_ROOT / "tests" / "fixtures" / "nba_stats" / "league_game_log"

# Measured 2026-08-15 and recorded in reviews/endpoint-probe.md.
EXPECTED_WIDTHS = {"player": 32, "team": 29}

# A floor per fixture, so an over-trimmed corpus cannot make every assertion below vacuous.
MINIMUM_ROWS = 2


def _load_schema() -> dict[str, Any]:
    with BRONZE_SCHEMA.open(encoding="utf-8") as handle:
        loaded: Any = yaml.safe_load(handle)
    assert isinstance(loaded, dict), f"{BRONZE_SCHEMA} did not parse as a mapping"
    return loaded


def _endpoint_columns(model: dict[str, Any]) -> list[str]:
    """The declared columns that come from the envelope, in declared order.

    Path-derived provenance columns opt out with `meta.endpoint_column: false`.
    """
    columns: list[str] = []
    for column in model.get("columns", []):
        meta = column.get("meta") or {}
        if meta.get("endpoint_column") is False:
            continue
        columns.append(str(column["name"]).upper())
    return columns


def _declared() -> dict[str, list[str]]:
    """Grain -> ordered endpoint column list, keyed off the model's name suffix."""
    declared: dict[str, list[str]] = {}
    for model in _load_schema().get("models", []):
        name = str(model["name"])
        grain = name.rsplit("_", 1)[-1]
        assert grain in EXPECTED_WIDTHS, f"{name} does not end in a known grain"
        declared[grain] = _endpoint_columns(model)
    return declared


def _fixtures(grain: str) -> list[Path]:
    return sorted(CORPUS.glob(f"season=*/grain={grain}/season_type=*/capture=*/payload.json"))


def test_declared_models_and_fixture_grains_cover_each_other() -> None:
    """Both directions, because each gap is silent in its own way.

    A declared model with no fixture makes every check below pass on an empty loop. A fixture
    grain with no declared model is worse: the fixture is committed, CI reads it, and nothing
    asserts its columns are what bronze believes.

    Bronze deliberately landed one model per phase — the player grain first, so the first-ever
    sqlfluff run and the source seam were absorbed on one file — so this was a one-way check
    until the team model landed alongside it.
    """
    declared = _declared()
    assert declared, "bronze declares no models - this whole module would pass vacuously"

    with_fixtures = {grain for grain in EXPECTED_WIDTHS if _fixtures(grain)}
    assert with_fixtures == set(declared), (
        f"fixture grains {sorted(with_fixtures)} and declared models {sorted(declared)} do not "
        "cover each other - a committed fixture whose columns nothing checks, or a model "
        "checked against nothing"
    )


@pytest.mark.parametrize("grain", sorted(EXPECTED_WIDTHS))
def test_declared_column_count_matches_what_was_measured(grain: str) -> None:
    """29 team / 32 player, measured. A count change is a contract change."""
    declared = _declared()
    if grain not in declared:
        pytest.skip(f"bronze declares no {grain}-grain model yet")

    assert len(declared[grain]) == EXPECTED_WIDTHS[grain], (
        f"{grain} grain declares {len(declared[grain])} endpoint columns, measured "
        f"{EXPECTED_WIDTHS[grain]}: {declared[grain]}"
    )


def test_every_fixture_matches_the_declared_columns_in_order_and_both_directions() -> None:
    """AC 19. An added, removed or renamed column reddens at the boundary, not four layers down."""
    declared = _declared()
    checked = 0

    for grain, expected in declared.items():
        fixtures = _fixtures(grain)
        assert fixtures, f"bronze declares a {grain} model but no {grain} fixture exists"

        for fixture in fixtures:
            payload = json.loads(fixture.read_text(encoding="utf-8"))
            result_set = payload["resultSets"][0]
            actual = [str(header).upper() for header in result_set["headers"]]
            where = fixture.relative_to(CORPUS).as_posix()

            # Both directions, named separately so the failure says WHICH direction broke.
            missing_from_yaml = [c for c in actual if c not in expected]
            missing_from_fixture = [c for c in expected if c not in actual]
            assert not missing_from_yaml, (
                f"{where} carries {missing_from_yaml}, which bronze's schema.yml does not "
                "declare - the upstream added a column and the model will silently drop it"
            )
            assert not missing_from_fixture, (
                f"bronze's schema.yml declares {missing_from_fixture}, absent from {where} - "
                "the model projects a column the payload no longer has"
            )

            # ORDER, checked last so the two set-differences above give the clearer message
            # when both are wrong at once.
            assert actual == expected, (
                f"{where} has the right columns in the WRONG ORDER.\n"
                f"  declared: {expected}\n  fixture : {actual}\n"
                "Bronze projects by name so it survives this, but the drift is real and the "
                "next model written from the YAML's order would misalign every field."
            )

            assert len(result_set["rowSet"]) >= MINIMUM_ROWS, (
                f"{where} holds {len(result_set['rowSet'])} rows, under the floor of "
                f"{MINIMUM_ROWS} - an over-trimmed fixture passes every test vacuously"
            )
            checked += 1

    # Three seasons per declared grain. Scales automatically when Phase 5 declares the team
    # model, so this floor cannot be satisfied by a shrinking corpus.
    assert checked >= 3 * len(declared), (
        f"only {checked} fixtures checked against {len(declared)} declared model(s) - "
        "expected at least the three pilot seasons per grain"
    )


def test_path_derived_columns_are_excluded_by_property_not_by_name() -> None:
    """The exclusion mechanism itself has to work, or the guard quietly compares the wrong list.

    If nothing opted out, `_endpoint_columns` would return provenance columns too and every
    assertion above would fail — loudly. The dangerous inverse is a model that opts a real
    endpoint column out by mistake, which would make this guard stop checking it.
    """
    for model in _load_schema().get("models", []):
        all_names = [str(column["name"]).upper() for column in model.get("columns", [])]
        endpoint = _endpoint_columns(model)
        excluded = [name for name in all_names if name not in endpoint]

        assert excluded, (
            f"{model['name']} declares no path-derived column, but bronze recovers capture "
            "provenance from the path - so either a column is missing or its meta flag is"
        )
        grain = str(model["name"]).rsplit("_", 1)[-1]
        assert len(endpoint) == EXPECTED_WIDTHS[grain], (
            f"{model['name']} excluded {excluded}, leaving {len(endpoint)} endpoint columns "
            f"against a measured {EXPECTED_WIDTHS[grain]} - a real column was opted out and "
            "this guard would have stopped checking it"
        )
