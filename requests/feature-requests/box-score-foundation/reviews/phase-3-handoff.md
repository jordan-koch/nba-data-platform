<!-- handoff: v1 -->

## track

feature

## built

`src/nba_platform/fixtures.py` — the recorder `tests/fixtures/README.md:11-13` already tells the
reader to use. It never touches the network: it trims `GameLogResponse` objects the caller already
fetched and lands them via `landing.write_capture`, so the trim rule is provable offline. `git status
--short` shows one untracked file; my memory file gained two entries.

The trim rule is enforced by the API's shape: `record_case()` takes **one** `game_ids_kept` argument
for the whole case, so the two grains cannot cover different games, and `trim_to_games()` raises on a
game absent from a payload. Nothing means "keep the first N rows". Every column lookup funnels
through `column_index()`, reading the envelope's own `headers`; no ordinal literal exists. Structure
is shallow-copied, so key order, `resource`, `parameters`, the result set `name` and `headers` pass
through untouched and retained rows are the original objects — only `rowSet` shrinks. Provenance is a
sibling `trim_provenance.json`, written only for a capture this call made. `record_error_case()`
writes the body verbatim under `.../_error_cases/` plus a sidecar — the only path not using
`write_capture`, since that flat shape sits deliberately outside the partitioned tree (EXEC-02).

## api-surface

`payload` is `Mapping[str, Any]`; `case` is a slug (`^[a-z0-9][a-z0-9._-]*$`), prose goes in `reason`. Case (f) is `record_case(..., responses=[one], edits=[CellEdit(...)], recapture=True)`.

```python
FixtureError(RuntimeError)
TrimResult(payload, game_ids, original_row_count, retained_row_count)
CellEdit(match: Mapping[str, Any], column: str, value: Any, reason: str)
FixtureCapture(grain, season, season_type, capture_dir, payload_path, manifest_path, provenance_path: Path|None, original_row_count, retained_row_count, payload_bytes, written)
CaseResult(case, reason, season, season_type, game_ids, captures)  # + .retained_row_count .payload_bytes
ErrorCaseResult(case, payload_path, provenance_path)
fixtures_root(*, settings: Settings | None = None) -> Path
headers(payload) -> tuple[str, ...]
column_index(payload, column: str) -> int
row_values(payload) -> tuple[list[Any], ...]   # width-checked; row_dicts() gives name -> value
game_ids(payload) -> tuple[str, ...]           # distinct, first-seen order
first_games(payload, count: int) -> tuple[str, ...]
games_where(payload, predicate: Callable[[Mapping[str, Any]], bool]) -> tuple[str, ...]
trim_to_games(payload, game_ids_kept: Sequence[str]) -> TrimResult
apply_cell_edit(payload, edit: CellEdit) -> tuple[dict[str, Any], dict[str, Any]]
record_case(*, case: str, reason: str, responses: Sequence[GameLogResponse], game_ids_kept: Sequence[str], captured_at: datetime,
    edits: Sequence[CellEdit] = (), source: str = SOURCE_NAME, endpoint: str = ENDPOINT_NAME, fixtures_root_override: Path | None = None, recapture: bool = False) -> CaseResult
record_error_case(*, case: str, reason: str, payload: Any, captured_at: datetime, parameters: Mapping[str, str] | None = None,
    status_code: int | None = None, request_url: str | None = None, source: str = SOURCE_NAME, endpoint: str = ENDPOINT_NAME, fixtures_root_override: Path | None = None) -> ErrorCaseResult
```

## verified

"proof" rows ran `prove_trim.py` in this session's scratchpad — a synthetic two-grain envelope over 3 games, written only into that scratch directory.

| Claim | Command and actual output |
|---|---|
| Lint, format, types | `uv run ruff check` -> `All checks passed!`; `uv run ruff format --check` -> `67 files already formatted`; `uv run mypy` -> `Success: no issues found in 15 source files` |
| Suite green, module uncovered | `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing` -> `78 passed, 2 deselected in 0.94s`; `fixtures.py 245 stmts, 245 miss, 0%` |
| Guards green, dry run unaffected | `uv run pytest tests/test_agent_contract.py tests/test_doc_links.py -q` -> `24 passed`; `uv run python -m nba_platform.backfill --dry-run` -> `planned calls: 6`, `request delay seconds: 0.6` |
| Whole games at both grains over one set; no game loses a team | proof -> `grain=player original=18 retained=12`, `grain=team original=6 retained=4`, both `games=['0021900001','0021900002']`; `teams per retained game: {'0021900001': 2, '0021900002': 2}` |
| Envelope intact; resolved by name not ordinal | proof -> `player headers equal: True`, `team headers equal: True`, `top-level keys: ['resource','parameters','resultSets']`, `result set keys: ['name','headers','rowSet']`; moving `GAME_ID` from ordinal 2 to 0 -> both `retained 12` |
| Empty/broken trims raise | proof -> six `FixtureError`s: empty selection, game absent from payload, game absent from one grain, predicate matched nothing, headers missing, not an envelope |
| Provenance lands in the capture | proof -> `capture=20260815T120000Z/trim_provenance.json` with `original_row_count: 18`, `retained_row_count: 12`, `game_ids: ['0021900001','0021900002']`, plus `case`/`parameters`/`captured_at`; `manifest row_count: 12` agrees |
| Write-once holds; recapture lands beside | proof -> re-recording -> `written flags: [False, False]`, `files unchanged: True`; then `capture=20260815T120005Z` beside `...120000Z`, the first capture's cell still `20` |
| One cell edited, nothing else | proof -> `rows unchanged: True`, provenance `value_before: 20, value_after: 99`; a match hitting 6 rows raises |
| Traded player trimmed around; error case outside the glob | proof -> `games with player 2545: 3; retained rows 18; his own rows 3`; `_error_cases/empty-response.json`, bronze-shaped glob sees 3 files, `error case among them: False` |
| RUF100 fires on a non-enabled noqa | `uv run ruff check --isolated --select "E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF" <scratch>` -> `RUF100 Unused noqa directive (non-enabled: PLC2701)` |

## assumed

- `GAME_ID` is a zero-padded string upstream (`reviews/gate-0-endpoint-probe.md:146`, not re-measured),
  so `str()` normalisation is identity; it is applied to both sides of every comparison anyway.
- `leaguegamelog` returns one result set; a hypothetical second passes through untrimmed.
- `tests/fixtures/` is the corpus root, spelled as `FIXTURES_DIRNAMES` off `get_settings().repo_root`
  since `config.py` is outside my target path. It arguably belongs in config.
- The spec is silent on the error case needing provenance (nothing is trimmed there); I wrote the
  sidecar anyway — without it, "captured, not hand-authored" is unfalsifiable. All three written
  filenames land tracked under `.gitignore:30`: read from it, not proven by a `git add`.

## surprised-me

- `write_capture` opens its manifest `"xb"` and builds it from a fixed key list, so per-capture extra metadata can be neither passed in nor appended; appending would itself mutate a landed file.
- RUF100 rejects a `# noqa` naming a rule the repo does not `select`, so a pylint code cannot be
  pre-silenced. A deliberate private cross-module import gets a comment, not a noqa.
- PowerShell `Measure-Object -Line` undercounts a Markdown file by every blank line in it (92 vs the guard's 119). Do not check a line budget with it.

## could-not-do

- **Tests for `fixtures.py`.** `tests/` is repo-root-denied, so it ships at **0% coverage**. No `fail_under` exists so the suite is green, but the module stays unguarded until the main thread ports the proof script into `tests/test_fixture_recorder.py`.
- **The corpus itself** — live call plus a denied path; plan steps 8, 10 and 11 are main-thread.
- **Provenance inside `manifest.json`**, as plan step 9 words it. `write_capture` exposes no free-form
  field and `parameters` is the wire parameter dict — folding trim metadata in would corrupt what
  bronze reads. Tidy fix: one keyword (`provenance: Mapping[str, Any] | None = None`) on
  `write_capture`. **SUPERSEDED — accepted and built in `phase-3b-handoff.md`; the sibling file is
  gone and this bullet's sibling-file description no longer describes the code.**

## docs-delta

- No data facts to route: I issued no request. The `GAME_ID` and envelope claims I relied on sit in
  `reviews/gate-0-endpoint-probe.md` and still need their Phase 10 `/update-docs` promotion.
- Candidate for `docs/data-sources.md` once the corpus lands: *why* an error body must sit outside the
  partitioned tree is a DuckDB glob-unification fact a reader would otherwise re-derive the hard way
  — proposed label `inferred` until a `dbt build` over the corpus demonstrates it.
- Memory is at 134 lines after my two entries: over the ~120 curation target, far under the 250
  ceiling. Flagged for the pre-merge sweep, not a request for a mid-build prune.

## still-open

- **Ambiguity resolved small (1).** The dispatch listed case (f) but scoped me to plan steps 7 and 9.
  I built `CellEdit` / `apply_cell_edit` (~40 lines); the reading I did not take leaves that edit to be
  made by hand — but then step 9's "exactly what was changed" has no recorder to record it.
- **Ambiguity resolved small (2).** `games_where` takes a predicate; the reading I did not take was
  three named wrappers, for date windows, player pins and team pins.
- **Driving it live:** compute the game-id set once from the *player* grain (the only one that can
  pin a traded player) and pass the same tuple for both. For the bubble, select with
  `games_where(payload, lambda row: row["GAME_DATE"] >= "2020-07-01")` to keep July-October dates.
  `CaseResult.payload_bytes` reports corpus size per case; no ceiling is enforced, and if `/commit`'s
  bulk-data refusal fires, drop whole games rather than rows.
- Phase 4's bronze source glob must name `payload.json` explicitly — `manifest.json` and
  `trim_provenance.json` sit beside it, and `capture=*/*.json` would swallow all three.
