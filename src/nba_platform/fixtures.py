"""The fixture recorder — turns captured payloads into the committed offline corpus.

`tests/fixtures/README.md` already tells the reader to "capture them with the recorder".
This is that recorder. It does **not** talk to the network: a live call is the caller's job
(the paced `GameLogClient` in `client.py`), and everything here operates on a
`GameLogResponse` that already exists. That split is deliberate — it means the trim rule,
which is the part that can silently corrupt a whole test suite, is provable offline against
a synthetic envelope.

**The trim rule, stated once: WHOLE GAMES, ROWS ONLY.** You choose a set of `GAME_ID`s and
every row carrying one of them is kept, at every grain, over the *same* set. There is no
parameter anywhere in this module that means "keep the first N rows", because a fixture
trimmed by rows is the specific failure this module exists to prevent: it leaves a game with
one team instead of two, or a game whose player rows no longer sum to its team total. Every
downstream reconciliation then either fails spuriously or — far worse — passes vacuously on
an empty set. If a caller cannot express row-trimming, a caller cannot do it by accident.

`first_games()` and `games_where()` both select at *game* granularity, never row
granularity, and `record_case()` takes **one** `game_ids` argument for the whole case, so the
player-grain and team-grain fixtures of a case cannot be trimmed over different sets.

**Columns resolve by name, never by ordinal.** The upstream is undocumented and unversioned,
so `GAME_ID`'s position inside `headers` is not a contract. Every lookup here goes through
`column_index()`, which reads the envelope's own `headers` list — the same thing bronze will
do with `list_position`. An integer literal index would bake in today's column order and
shift every value the day upstream reorders one.

**The envelope survives, in shape.** `resource`, `parameters`, and `resultSets[0]` with its
`name` / `headers` / `rowSet` all come through; key order is preserved; the `headers` list is
passed through untouched, never reordered and never subset; retained rows are the original
row objects, so no cell can drift in transit. Only `rowSet` shrinks.

**Failing loudly is the point.** A trim to zero rows, a requested game that is not in the
payload, an envelope with no `headers`, an edit that matches no row or more than one — all
raise `FixtureError` before anything is written. Every data-level check runs across every
response *before* the first byte lands, so a failure cannot leave a case half-written with
one grain on disk and the other missing.

**Writing goes through the landing writer.** `record_case()` calls
`landing.write_capture()`, so fixtures land in the identical `season=/grain=/season_type=/
capture=/` shape as real captures, with the same write-once guarantees: nothing here can
overwrite a fixture that already exists. A second capture of an already-captured partition
(the dedup fixture) passes `recapture=True` and lands *beside* the first.

**Trim provenance rides inside the capture's own manifest.** `write_capture(provenance=...)`
nests it under the manifest's `provenance` key, so a capture is still two files and a reader
asking "what was dropped from these rows" never has to know a further filename exists. The
nested document carries only what the manifest does not already say one level up — the case
name and reason, the trim rule in words, original and retained row counts, the retained
`GAME_ID`s, and any deliberate edit — because `parameters`, `captured_at`, `season`, `grain`
and the rest are right there beside it.

**The one shape the landing writer cannot express: the error case.** An empty-or-error body
lands OUTSIDE the partitioned tree, under
`_error_cases/`, whose leading underscore marks it "not a landing partition, never globbed by
a source" — the same convention the landing zone uses for run manifests. Inside the tree the
bronze source glob would match it, and DuckDB unifies schema across a glob, so a payload with
no `resultSets[0].headers` either fails unification or injects a null-headers row and turns
the required `dbt build` check red. The error path is exercised by offline pytest only, never
by dbt.

Every fixture this module writes is `.json`, which is the only extension the `.gitignore`
carve-out whitelists under the fixture tree. That carve-out is a narrow exception for test
data, not a licence to redistribute: keep the corpus to the few whole games each case needs.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from nba_platform.client import CLIENT_NAME, ENDPOINT_NAME, SOURCE_NAME, GameLogResponse
from nba_platform.config import Settings, get_settings
from nba_platform.landing import (
    RESULT_SETS_KEY,
    ROW_SET_KEY,
    Partition,
    _serialize,
    row_count,
    write_capture,
)

# `_serialize` is imported deliberately, private name and all: it is one serializer for the
# whole package, and the alternative is a second copy of the same compact-UTF-8-with-trailing-
# newline policy — exactly the two-answers drift this repo removes wherever it finds it. The
# coupling is loud rather than silent: a rename in the landing writer is an ImportError here,
# not a quiet divergence in fixture bytes. Promoting it to a public name in `landing.py` would
# retire this note, and that is a main-thread edit.

__all__ = [
    "ERROR_CASES_DIRNAME",
    "FIXTURES_DIRNAMES",
    "GAME_ID_COLUMN",
    "HEADERS_KEY",
    "PROVENANCE_VERSION",
    "TRIM_RULE",
    "CaseResult",
    "CellEdit",
    "ErrorCaseResult",
    "FixtureCapture",
    "FixtureError",
    "TrimResult",
    "apply_cell_edit",
    "column_index",
    "first_games",
    "fixtures_root",
    "game_ids",
    "games_where",
    "headers",
    "record_case",
    "record_error_case",
    "row_dicts",
    "row_values",
    "trim_to_games",
]


class FixtureError(RuntimeError):
    """A capture cannot be trimmed or recorded without producing a misleading fixture."""


# ─── Envelope vocabulary ──────────────────────────────────────────────────────────────
# `resultSets` and `rowSet` are imported from the landing writer so the envelope's key names
# keep one owner. `headers` has no owner yet because nothing before this needed to read it.
HEADERS_KEY: Final = "headers"

# The column every trim pivots on. Named here once; resolved through the envelope's own
# `headers` list at every use, never by position.
GAME_ID_COLUMN: Final = "GAME_ID"

# Recorded into every provenance document so a future reader of a fixture learns the rule
# from the fixture itself rather than from a module they may never open.
TRIM_RULE: Final = (
    "whole games, rows only: a set of GAME_IDs is chosen and EVERY row carrying one of them "
    "is retained, at every grain, over the same set. Rows are never trimmed individually and "
    "the resultSets/headers/rowSet envelope is never trimmed at all."
)

# Relative to the repo root, which the config layer resolves. Spelled as segments rather than
# as a path string so this stays platform-neutral.
FIXTURES_DIRNAMES: Final[tuple[str, ...]] = ("tests", "fixtures")

# Leading underscore, exactly as the landing zone marks its run-manifest directory: this is
# not a landing partition and no dbt source glob may ever reach it.
ERROR_CASES_DIRNAME: Final = "_error_cases"

# Only the error case needs a provenance file of its own: it lands outside the partitioned
# tree and so has no capture manifest to nest inside. Every partitioned fixture's provenance
# rides in its own `manifest.json` under the landing writer's `provenance` key.
PROVENANCE_SUFFIX: Final = ".provenance.json"
PROVENANCE_VERSION: Final = 1
JSON_SUFFIX: Final = ".json"

# A case name becomes a filename for error cases and a manifest field for everything else, so
# it is held to one conservative shape in both places: lowercase, digit, dot, hyphen,
# underscore. That rules out a separator, a drive-letter colon and a parent-directory hop
# without needing to reason about which platform is writing.
CASE_NAME_PATTERN: Final = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


# ─── Reading an envelope, always by name ──────────────────────────────────────────────


def _first_result_set(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """The envelope's first result set, or a `FixtureError` naming what is wrong with it."""
    result_sets = payload.get(RESULT_SETS_KEY)
    if not isinstance(result_sets, list) or not result_sets:
        raise FixtureError(
            f"payload has no non-empty {RESULT_SETS_KEY!r} list, so it is not a result "
            "envelope this recorder can trim. An error or empty body belongs in "
            f"{ERROR_CASES_DIRNAME!r} via record_error_case()."
        )
    first = result_sets[0]
    if not isinstance(first, Mapping):
        raise FixtureError(f"{RESULT_SETS_KEY}[0] is {type(first).__name__}, not an object.")
    return first


def headers(payload: Mapping[str, Any]) -> tuple[str, ...]:
    """The first result set's column names, in the order the endpoint returned them.

    This list is the only contract available for column position, which is why it is read
    here rather than assumed anywhere.
    """
    raw = _first_result_set(payload).get(HEADERS_KEY)
    if not isinstance(raw, list) or not raw:
        raise FixtureError(
            f"{RESULT_SETS_KEY}[0].{HEADERS_KEY} is missing or empty. A fixture without "
            "headers cannot be typed by bronze and would poison a schema-unified glob."
        )
    return tuple(str(name) for name in raw)


def column_index(payload: Mapping[str, Any], column: str) -> int:
    """The position of `column` within the envelope's own `headers`.

    Every ordinal in this module comes from here. Writing one as a literal would freeze
    today's column order into the recorder and shift every value the day upstream reorders.
    """
    names = headers(payload)
    try:
        return names.index(column)
    except ValueError:
        raise FixtureError(
            f"{column!r} is not among the {len(names)} columns this payload returned: "
            f"{list(names)!r}."
        ) from None


def row_values(payload: Mapping[str, Any]) -> tuple[list[Any], ...]:
    """The first result set's rows, validated to be as wide as `headers` says they are."""
    raw = _first_result_set(payload).get(ROW_SET_KEY)
    if not isinstance(raw, list):
        raise FixtureError(f"{RESULT_SETS_KEY}[0].{ROW_SET_KEY} is missing or is not a list.")
    width = len(headers(payload))
    rows: list[list[Any]] = []
    for position, row in enumerate(raw):
        if not isinstance(row, list):
            raise FixtureError(f"{ROW_SET_KEY}[{position}] is {type(row).__name__}, not a list.")
        if len(row) != width:
            raise FixtureError(
                f"{ROW_SET_KEY}[{position}] has {len(row)} values but {HEADERS_KEY} names "
                f"{width} columns. A ragged envelope cannot be resolved by name."
            )
        rows.append(row)
    return tuple(rows)


def row_dicts(payload: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Every row as a `column name -> value` mapping — the shape predicates read."""
    names = headers(payload)
    return tuple(dict(zip(names, row, strict=True)) for row in row_values(payload))


def _game_id(value: Any) -> str:
    """One canonical spelling for a game id, used on both sides of every comparison.

    `GAME_ID` is a zero-padded ten-character string upstream, so this is the identity there;
    normalising anyway means a selection and a trim can never disagree about a value's type.
    """
    return str(value)


def game_ids(payload: Mapping[str, Any]) -> tuple[str, ...]:
    """Every distinct `GAME_ID` in the payload, in first-seen order."""
    index = column_index(payload, GAME_ID_COLUMN)
    return tuple(dict.fromkeys(_game_id(row[index]) for row in row_values(payload)))


# ─── Choosing games — never rows ──────────────────────────────────────────────────────


def first_games(payload: Mapping[str, Any], count: int) -> tuple[str, ...]:
    """The first `count` distinct `GAME_ID`s, in payload order.

    Game granularity, not row granularity: the caller gets identifiers, and `trim_to_games`
    then keeps *every* row of each. Raises rather than quietly returning fewer, so an
    over-small fixture is discovered here instead of in a vacuously-passing test.
    """
    if count < 1:
        raise FixtureError(f"first_games() needs a positive count, got {count!r}.")
    available = game_ids(payload)
    if len(available) < count:
        raise FixtureError(
            f"first_games() was asked for {count} games but the payload holds "
            f"{len(available)}. Trimming to fewer games than a case needs is how a fixture "
            "starts passing vacuously."
        )
    return available[:count]


def games_where(
    payload: Mapping[str, Any], predicate: Callable[[Mapping[str, Any]], bool]
) -> tuple[str, ...]:
    """The `GAME_ID`s of every game with at least one row satisfying `predicate`.

    The predicate sees a row as a `column name -> value` mapping, so it is written against
    column names and never against positions. This is how the interesting cases are pinned:
    a traded player's whole season is
    `games_where(player_payload, lambda row: row["PLAYER_ID"] == pinned_id)`, and a date
    window is a comparison on `row["GAME_DATE"]`. Whichever rows match, whole games come
    back — so the rows *around* the match survive the trim too.
    """
    index = column_index(payload, GAME_ID_COLUMN)
    names = headers(payload)
    matched = [
        _game_id(row[index])
        for row in row_values(payload)
        if predicate(dict(zip(names, row, strict=True)))
    ]
    if not matched:
        raise FixtureError(
            "games_where() matched no row. A fixture selected from an empty match trims to "
            "nothing, which is the failure this recorder exists to make impossible."
        )
    return tuple(dict.fromkeys(matched))


# ─── The trim ─────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TrimResult:
    """A trimmed envelope plus the counts that prove what the trim did."""

    payload: dict[str, Any]
    game_ids: tuple[str, ...]
    original_row_count: int
    retained_row_count: int


def trim_to_games(payload: Mapping[str, Any], game_ids_kept: Sequence[str]) -> TrimResult:
    """Keep every row of every named game, and change nothing else about the envelope.

    Structure is preserved rather than rebuilt: top-level keys keep their order and their
    values, the result set keeps its `name`, the `headers` list is passed through as-is, and
    retained rows are the original row objects. Only `rowSet` is replaced.

    Raises when a requested game is absent from this payload. That check is what keeps the
    two grains of a case honest — if the team-grain payload lacks a game the player-grain
    payload had, the pair would silently no longer describe the same set of games.
    """
    wanted = tuple(dict.fromkeys(_game_id(value) for value in game_ids_kept))
    if not wanted:
        raise FixtureError(
            "trim_to_games() was given no GAME_IDs. An empty selection trims the fixture to "
            "zero rows, and a suite that reconciles zero rows against zero rows is green and "
            "worthless."
        )

    index = column_index(payload, GAME_ID_COLUMN)
    all_rows = row_values(payload)
    wanted_set = set(wanted)
    kept = [row for row in all_rows if _game_id(row[index]) in wanted_set]

    present = {_game_id(row[index]) for row in kept}
    missing = [value for value in wanted if value not in present]
    if missing:
        raise FixtureError(
            f"{missing!r} were asked for but appear in no row of this payload. Recording the "
            "grains of one case over different game sets breaks every cross-grain "
            "reconciliation, so this raises instead of trimming to what happens to be there."
        )
    if not kept:
        raise FixtureError(
            f"trimming to {list(wanted)!r} retained zero of {len(all_rows)} rows. Nothing was "
            "written; a zero-row fixture makes a whole suite pass vacuously."
        )

    result_sets = payload[RESULT_SETS_KEY]
    first = result_sets[0]
    # A shallow copy, so key order survives and `headers` is passed through as the very same
    # list object it arrived as — never rebuilt, never reordered, never subset.
    trimmed_first = dict(first)
    trimmed_first[ROW_SET_KEY] = kept
    trimmed_result_sets = list(result_sets)
    trimmed_result_sets[0] = trimmed_first
    trimmed: dict[str, Any] = dict(payload)
    trimmed[RESULT_SETS_KEY] = trimmed_result_sets

    return TrimResult(
        payload=trimmed,
        game_ids=tuple(sorted(wanted)),
        original_row_count=len(all_rows),
        retained_row_count=len(kept),
    )


# ─── The one deliberate edit: the second-capture fixture ──────────────────────────────


@dataclass(frozen=True, slots=True)
class CellEdit:
    """One deliberate single-cell change, for the two-captures-of-one-partition fixture.

    That fixture is the only one in the corpus that may be edited rather than captured — it
    exists to prove latest-capture-wins deduplication, which needs two captures that disagree
    about exactly one value. `match` names the row by column values (for example
    `{"GAME_ID": "0021900002", "PLAYER_ID": 2544}`) and must select exactly one row.
    """

    match: Mapping[str, Any]
    column: str
    value: Any
    reason: str


def _same_cell(left: Any, right: Any) -> bool:
    """Equality that survives a string/number spelling difference in a match value."""
    return bool(left == right) or str(left) == str(right)


def apply_cell_edit(
    payload: Mapping[str, Any], edit: CellEdit
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Change one cell of one row, and hand back the change as provenance.

    The row count does not move and no structure is touched — this is a value edit, never a
    trim. An edit matching zero rows or more than one raises, because "I changed one value"
    is only a useful thing to record if it is true.
    """
    if not edit.match:
        raise FixtureError("CellEdit.match is empty, so it selects every row rather than one.")
    if not edit.reason.strip():
        raise FixtureError(
            "CellEdit.reason is empty. An edited fixture whose provenance does not say what "
            "was changed and why is indistinguishable from a hand-authored one."
        )

    target = column_index(payload, edit.column)
    match_indices = {name: column_index(payload, name) for name in edit.match}
    all_rows = row_values(payload)
    hits = [
        position
        for position, row in enumerate(all_rows)
        if all(
            _same_cell(row[match_indices[name]], expected) for name, expected in edit.match.items()
        )
    ]
    if len(hits) != 1:
        raise FixtureError(
            f"{dict(edit.match)!r} matched {len(hits)} rows; an edit must name exactly one. "
            "Editing several rows at once cannot be described honestly in provenance."
        )

    position = hits[0]
    before = all_rows[position][target]
    edited_row = list(all_rows[position])
    edited_row[target] = edit.value

    edited_rows = list(all_rows)
    edited_rows[position] = edited_row

    result_sets = payload[RESULT_SETS_KEY]
    first = result_sets[0]
    edited_first = dict(first)
    edited_first[ROW_SET_KEY] = edited_rows
    edited_result_sets = list(result_sets)
    edited_result_sets[0] = edited_first
    edited_payload: dict[str, Any] = dict(payload)
    edited_payload[RESULT_SETS_KEY] = edited_result_sets

    record = {
        "match": {name: str(value) for name, value in edit.match.items()},
        "row_position": position,
        "column": edit.column,
        "value_before": before,
        "value_after": edit.value,
        "reason": edit.reason,
    }
    return edited_payload, record


# ─── Where fixtures live ──────────────────────────────────────────────────────────────


def fixtures_root(*, settings: Settings | None = None) -> Path:
    """The committed fixture corpus root, hung off the repo root the config layer resolves.

    Resolved rather than spelled: no absolute literal, and no fixed-index parent walk — the
    guard under `tests/` fails the build for either. This is the one path fragment this
    module knows, and it is overridable at every call site through a `fixtures_root`
    argument, so relocating the corpus is a parameter change.
    """
    resolved = get_settings() if settings is None else settings
    return resolved.repo_root.joinpath(*FIXTURES_DIRNAMES)


def _resolve_fixtures_root(fixtures_root_override: Path | None) -> Path:
    return fixtures_root() if fixtures_root_override is None else fixtures_root_override


def _check_case_name(case: str) -> str:
    """A case name is a slug; the sentence explaining it belongs in `reason`."""
    if not CASE_NAME_PATTERN.match(case):
        raise FixtureError(
            f"case={case!r} is not a fixture case slug. Use lowercase letters, digits, dots, "
            "hyphens and underscores, for example '2019-20-bubble-restart'. The prose that "
            "says why the case is interesting goes in `reason`."
        )
    return case


def _check_reason(reason: str) -> str:
    if not reason.strip():
        raise FixtureError(
            "reason is empty. The fixtures README requires a future reader to learn WHY a "
            "case was captured, and the partitioned layout leaves the manifest as the only "
            "place that can carry it."
        )
    return reason


def _check_aware(captured_at: datetime) -> datetime:
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise FixtureError(
            "captured_at must be timezone-aware. A naive timestamp records the writer's "
            "local clock as if it were UTC."
        )
    return captured_at


def _write_once(path: Path, document: Any) -> Path:
    """Write one JSON document, refusing to touch a file that already exists.

    Exclusive-create binary, the same posture as the landing writer: an existing fixture
    raises rather than being truncated, so re-running a capture can never quietly rewrite
    committed bytes. `document` is deliberately untyped — an error-case body is whatever came
    back, which is the whole reason that case is worth committing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(_serialize(document))
    except FileExistsError as exc:
        raise FixtureError(
            f"{path} already exists. Fixtures are write-once; delete it deliberately by hand "
            "or record the case under a different name."
        ) from exc
    return path


# ─── Recording a case ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class FixtureCapture:
    """One grain of one recorded case, and what landed on disk for it.

    `provenance` is the document that went into this capture's `manifest.json`, or None when
    the capture was skipped because a completed one already existed — in which case this call
    recorded nothing and will not claim credit for someone else's manifest.
    """

    grain: str
    season: str
    season_type: str
    capture_dir: Path
    payload_path: Path
    manifest_path: Path
    provenance: dict[str, Any] | None
    original_row_count: int
    retained_row_count: int
    payload_bytes: int | None
    written: bool


@dataclass(frozen=True, slots=True)
class CaseResult:
    """Everything one `record_case()` call produced, in a shape a test can assert on."""

    case: str
    reason: str
    season: str
    season_type: str
    game_ids: tuple[str, ...]
    captures: tuple[FixtureCapture, ...]

    @property
    def retained_row_count(self) -> int:
        return sum(capture.retained_row_count for capture in self.captures)

    @property
    def payload_bytes(self) -> int:
        return sum(capture.payload_bytes or 0 for capture in self.captures)


@dataclass(frozen=True, slots=True)
class ErrorCaseResult:
    """Where an error-case body and its provenance landed, outside the partitioned tree."""

    case: str
    payload_path: Path
    provenance_path: Path


def record_case(
    *,
    case: str,
    reason: str,
    responses: Sequence[GameLogResponse],
    game_ids_kept: Sequence[str],
    captured_at: datetime,
    edits: Sequence[CellEdit] = (),
    source: str = SOURCE_NAME,
    endpoint: str = ENDPOINT_NAME,
    fixtures_root_override: Path | None = None,
    recapture: bool = False,
) -> CaseResult:
    """Trim every grain of one case to the same whole games and land them as fixtures.

    `game_ids_kept` is a single argument for the whole call, which is what makes the
    player-grain and team-grain fixtures structurally incapable of covering different games.
    Pick it with `first_games()` or `games_where()` against one payload — usually the player
    grain, which is the one that can pin a traded player — and pass the same tuple here.

    Every check runs across every response before the first byte is written, so a case is
    never left half-recorded because the second grain turned out to be wrong.

    `edits` is for the one fixture that proves latest-capture-wins deduplication: a second
    capture of an already-captured partition, differing in exactly one cell. It is only
    accepted for a single-response call, because "the row I changed" has no unambiguous
    meaning across grains. Pair it with `recapture=True`, which lands a new capture beside
    the existing one and never touches it.
    """
    _check_case_name(case)
    _check_reason(reason)
    _check_aware(captured_at)
    if not responses:
        raise FixtureError("record_case() was given no responses, so it has nothing to record.")

    seasons = {response.season for response in responses}
    season_types = {response.season_type for response in responses}
    if len(seasons) != 1 or len(season_types) != 1:
        raise FixtureError(
            f"one case is one (season, season_type) at one or more grains, but got "
            f"seasons={sorted(seasons)!r} season_types={sorted(season_types)!r}. Record them "
            "as separate cases so each carries its own game set."
        )
    grains = [response.grain for response in responses]
    if len(set(grains)) != len(grains):
        raise FixtureError(f"grains {grains!r} repeat; each grain is recorded once per case.")
    if edits and len(responses) != 1:
        raise FixtureError(
            f"edits were given with {len(responses)} responses. The edited fixture is a single "
            "(season, grain) recapture, so an edit is only unambiguous against one response."
        )

    # Trim (and edit) everything first: nothing below this block can fail on the data.
    trimmed: list[tuple[GameLogResponse, TrimResult, list[dict[str, Any]]]] = []
    for response in responses:
        trim = trim_to_games(response.payload, game_ids_kept)
        payload = trim.payload
        records: list[dict[str, Any]] = []
        for edit in edits:
            payload, record = apply_cell_edit(payload, edit)
            records.append(record)
        if records:
            trim = TrimResult(
                payload=payload,
                game_ids=trim.game_ids,
                original_row_count=trim.original_row_count,
                retained_row_count=trim.retained_row_count,
            )
        trimmed.append((response, trim, records))

    root = _resolve_fixtures_root(fixtures_root_override)
    captures: list[FixtureCapture] = []
    for response, trim, records in trimmed:
        partition = Partition(
            source=source,
            endpoint=endpoint,
            season=response.season,
            grain=response.grain,
            season_type=response.season_type,
        )
        provenance = _provenance_document(
            case=case, reason=reason, trim=trim, edits=records, recapture=recapture
        )
        result = write_capture(
            partition=partition,
            payload=trim.payload,
            captured_at=captured_at,
            parameters=response.parameters,
            status_code=response.status_code,
            elapsed_seconds=response.elapsed_seconds,
            request_url=response.request_url,
            client_name=CLIENT_NAME,
            client_version=response.client_version,
            provenance=provenance,
            landing_root=root,
            recapture=recapture,
        )
        captures.append(
            FixtureCapture(
                grain=response.grain,
                season=response.season,
                season_type=response.season_type,
                capture_dir=result.capture_dir,
                payload_path=result.payload_path,
                manifest_path=result.manifest_path,
                # A skip wrote no manifest, so this call recorded no provenance either.
                provenance=provenance if result.written else None,
                original_row_count=trim.original_row_count,
                retained_row_count=trim.retained_row_count,
                payload_bytes=result.payload_bytes,
                written=result.written,
            )
        )

    first_response = responses[0]
    return CaseResult(
        case=case,
        reason=reason,
        season=first_response.season,
        season_type=first_response.season_type,
        game_ids=trimmed[0][1].game_ids,
        captures=tuple(captures),
    )


def _provenance_document(
    *,
    case: str,
    reason: str,
    trim: TrimResult,
    edits: Sequence[Mapping[str, Any]],
    recapture: bool,
) -> dict[str, Any]:
    """The nested `provenance` block one trimmed capture's manifest carries.

    Deliberately narrow. The manifest one level up already records the source, endpoint,
    season, grain, season type, capture stamp, request `parameters`, request URL, HTTP status,
    client and version — repeating any of them here would be two answers to one question in a
    single file. What only the recorder knows goes in: which case this is and why, the trim
    rule in words, what the trim cost, which games survived, and what was deliberately edited.

    `original_row_count` and `retained_row_count` are both present even when equal, so
    "trimmed, and it happened to retain everything" reads differently from a capture whose
    manifest carries no provenance at all.
    """
    return {
        "provenance_version": PROVENANCE_VERSION,
        "case": case,
        "reason": reason,
        "trim_rule": TRIM_RULE,
        "original_row_count": trim.original_row_count,
        "retained_row_count": trim.retained_row_count,
        "game_ids": list(trim.game_ids),
        "game_count": len(trim.game_ids),
        "recapture": recapture,
        "edits": [dict(edit) for edit in edits],
    }


def record_error_case(
    *,
    case: str,
    reason: str,
    payload: Any,
    captured_at: datetime,
    parameters: Mapping[str, str] | None = None,
    status_code: int | None = None,
    request_url: str | None = None,
    source: str = SOURCE_NAME,
    endpoint: str = ENDPOINT_NAME,
    fixtures_root_override: Path | None = None,
) -> ErrorCaseResult:
    """Land an empty-or-error body under `_error_cases/`, never in the partitioned tree.

    The body is written verbatim, whatever shape it has — that is the point of the case, and
    it is why this path exists at all: a payload with no `resultSets[0].headers` sitting
    inside the partitioned tree gets matched by the bronze source glob, and DuckDB unifies
    schema across a glob, so it either fails unification or injects a null-headers row and
    turns the required `dbt build` check red. Nothing under the underscore-prefixed directory
    is ever globbed by a source; the error path is offline-pytest-only.

    Provenance goes in a sibling `<case>.provenance.json` rather than inside the body, since
    the body must stay exactly what came back.
    """
    _check_case_name(case)
    _check_reason(reason)
    _check_aware(captured_at)

    directory = (
        _resolve_fixtures_root(fixtures_root_override) / source / endpoint / ERROR_CASES_DIRNAME
    )
    payload_path = _write_once(directory / f"{case}{JSON_SUFFIX}", payload)
    provenance_path = _write_once(
        directory / f"{case}{PROVENANCE_SUFFIX}",
        {
            "provenance_version": PROVENANCE_VERSION,
            "case": case,
            "reason": reason,
            "source": source,
            "endpoint": endpoint,
            "captured_at": captured_at.astimezone(UTC).isoformat(),
            "parameters": dict(parameters or {}),
            "request_url": request_url,
            "http_status": status_code,
            "client": CLIENT_NAME,
            "row_count": row_count(payload) if isinstance(payload, Mapping) else 0,
            "partitioned": False,
            "why_not_partitioned": (
                f"{ERROR_CASES_DIRNAME!r} is not a landing partition and is never globbed by a "
                "dbt source: a body without resultSets[0].headers breaks schema unification "
                "across the bronze glob."
            ),
            "payload_filename": f"{case}{JSON_SUFFIX}",
        },
    )
    return ErrorCaseResult(case=case, payload_path=payload_path, provenance_path=provenance_path)
