"""Acceptance criterion 16 — the landing zone is immutable, proven by hashing it twice.

`CLAUDE.md` calls immutability "what makes data-incident triage tractable," and
`transform/models/bronze/README.md:17-19` rests the diff-against-raw invariant on it. Both
were prose until this module. The proof is deliberately blunt: run the backfill, hash every
byte under the landing root, run it again, hash again, and compare the whole mapping — not
just the file names, and not just a count.

Comparing the full path-to-digest mapping is stronger than the "hash sets are identical"
wording the criterion uses, and catches the failure that wording would miss: a second run
that rewrote a file with different content but left the *set* of digests unchanged by also
rewriting another one.

Everything runs against a stubbed client into `tmp_path`. Nothing here touches the network,
and nothing writes to the real `var/`.
"""

from __future__ import annotations

import hashlib
import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from nba_platform.backfill import BackfillResult, run
from nba_platform.client import GameLogResponse

# A fixed capture clock. Every partition in one run therefore renders the same capture
# stamp — which is fine, they are different directories — while a --recapture of an
# already-landed partition collides on purpose, exercising the writer's advance-the-stamp
# path rather than pretending second-resolution collisions do not happen.
FROZEN_NOW = datetime(2026, 8, 15, 13, 45, 6, tzinfo=UTC)

SEASONS = "2003-04,2019-20"
GRAINS = "player,team"
EXPECTED_CALLS = 4  # two seasons x two grains


def _envelope(season: str, grain: str) -> dict[str, Any]:
    """An envelope shaped like the real one — `resultSets[0]` with headers and rowSet."""
    headers = ["SEASON_ID", "TEAM_ID", "GAME_ID", "GAME_DATE", "PTS"]
    return {
        "resource": "leaguegamelog",
        "parameters": {"Season": season, "PlayerOrTeam": grain[0].upper()},
        "resultSets": [
            {
                "name": "LeagueGameLog",
                "headers": headers,
                "rowSet": [
                    [f"2{season[:4]}", 1610612747, f"002{index:07d}", "2003-10-28", 20 + index]
                    for index in range(3)
                ],
            }
        ],
    }


class StubClient:
    """Satisfies the `GameLogFetcher` protocol and records every call it was asked to make."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def fetch(self, *, season: str, grain: str, season_type: str) -> GameLogResponse:
        self.calls.append((season, grain, season_type))
        return GameLogResponse(
            season=season,
            grain=grain,
            season_type=season_type,
            payload=_envelope(season, grain),
            parameters={"Season": season, "PlayerOrTeam": grain[0].upper()},
            status_code=200,
            request_url="https://stats.nba.com/stats/leaguegamelog",
            elapsed_seconds=0.42,
            attempts=1,
            client_version="1.11.4",
        )


@pytest.fixture
def landing_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point the config layer at a throwaway landing zone, by name."""
    root = tmp_path / "landing"
    monkeypatch.setenv("NBA_ENV", "local")
    monkeypatch.setenv("NBA_LANDING_ROOT", str(root))
    return root


def _tree_digests(root: Path) -> dict[str, str]:
    """Every file under `root`, as relative path to sha256 of its bytes."""
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _backfill(client: StubClient, *extra: str) -> BackfillResult:
    return run(
        ["--seasons", SEASONS, "--grains", GRAINS, *extra],
        client=client,
        stream=io.StringIO(),
        now=lambda: FROZEN_NOW,
    )


# ─── The criterion ────────────────────────────────────────────────────────────────────


def test_a_second_run_lands_nothing_and_changes_no_landed_byte(landing_root: Path) -> None:
    """The core of AC 16: run twice, and the landing tree is byte-for-byte what it was."""
    first_client = StubClient()
    first = _backfill(first_client)

    after_first = _tree_digests(landing_root)
    assert first.written == EXPECTED_CALLS
    assert len(first_client.calls) == EXPECTED_CALLS
    assert after_first, "the first run landed nothing — the rest of this test would be vacuous"

    second_client = StubClient()
    second = _backfill(second_client)
    after_second = _tree_digests(landing_root)

    # Skip-if-present is the checkpoint: the second run must not even spend the request.
    assert second_client.calls == [], "a re-run issued requests for already-landed partitions"
    assert second.calls_made == 0
    assert second.written == 0
    assert second.skipped == EXPECTED_CALLS

    assert after_second == after_first, "a re-run changed the landing zone"


def test_recapture_lands_beside_the_original_without_touching_it(landing_root: Path) -> None:
    """Immutability and restatement coexist: the correction is a new directory, not an edit."""
    _backfill(StubClient())
    after_first = _tree_digests(landing_root)

    recapture_client = StubClient()
    result = _backfill(recapture_client, "--recapture")
    after_recapture = _tree_digests(landing_root)

    assert len(recapture_client.calls) == EXPECTED_CALLS, "--recapture must re-issue the requests"
    assert result.written == EXPECTED_CALLS

    # Every originally-landed file survives untouched, with the same content.
    for path, digest in after_first.items():
        assert path in after_recapture, f"{path} disappeared on recapture"
        assert after_recapture[path] == digest, f"{path} was mutated on recapture"

    # And new capture directories appeared beside them.
    new_paths = set(after_recapture) - set(after_first)
    assert new_paths, "--recapture wrote no new capture"
    new_captures = {Path(path).parent.as_posix() for path in new_paths if "capture=" in path}
    assert len(new_captures) == EXPECTED_CALLS


def test_an_overwrite_raises_rather_than_succeeding_quietly(landing_root: Path) -> None:
    """Immutability is structural, not conventional — the files open exclusive-create."""
    _backfill(StubClient())
    payloads = sorted(landing_root.rglob("payload.json"))
    assert payloads, "nothing landed"

    with pytest.raises(FileExistsError):
        with payloads[0].open("xb") as handle:
            handle.write(b"overwritten")


# ─── The manifest is what makes immutability auditable ────────────────────────────────


def test_every_capture_carries_a_manifest_that_describes_its_payload(
    landing_root: Path,
) -> None:
    """A hash nobody checks is decoration. Check it against the bytes actually on disk."""
    _backfill(StubClient())

    manifests = sorted(landing_root.rglob("manifest.json"))
    assert len(manifests) == EXPECTED_CALLS

    required = {
        "endpoint",
        "parameters",
        "captured_at",
        "http_status",
        "row_count",
        "payload_sha256",
        "client_version",
        "elapsed_seconds",
    }

    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        missing = required - set(manifest)
        assert not missing, f"{manifest_path} is missing {sorted(missing)}"

        payload_bytes = (manifest_path.parent / manifest["payload_filename"]).read_bytes()
        assert manifest["payload_sha256"] == hashlib.sha256(payload_bytes).hexdigest()
        assert manifest["row_count"] == 3
        assert manifest["http_status"] == 200
        assert manifest["client_version"] == "1.11.4"

        # Tz-aware, per ruff DTZ — a naive stamp here would make captures unorderable.
        captured_at = datetime.fromisoformat(manifest["captured_at"])
        assert captured_at.tzinfo is not None
        assert captured_at.utcoffset() is not None


def test_the_landed_payload_round_trips_to_what_the_client_returned(
    landing_root: Path,
) -> None:
    """Landing is verbatim: no reshaping, no DataFrame round-trip, no lost leading zeros."""
    _backfill(StubClient())

    player_payloads = [
        path for path in landing_root.rglob("payload.json") if "grain=player" in path.as_posix()
    ]
    assert len(player_payloads) == 2

    landed = json.loads(player_payloads[0].read_text(encoding="utf-8"))
    result_set = landed["resultSets"][0]

    assert result_set["headers"] == ["SEASON_ID", "TEAM_ID", "GAME_ID", "GAME_DATE", "PTS"]
    assert len(result_set["rowSet"]) == 3
    # The classic silent corruption: game ids are zero-padded strings and must stay strings.
    assert result_set["rowSet"][0][2] == "0020000000"
    assert isinstance(result_set["rowSet"][0][2], str)


def test_a_run_that_lands_nothing_writes_no_run_manifest(landing_root: Path) -> None:
    """Otherwise a re-run would add a file and the byte-for-byte comparison above could not hold."""
    first = _backfill(StubClient())
    assert first.run_manifest_path is not None

    second = _backfill(StubClient())

    assert second.run_manifest_path is None
    assert second.written == 0
