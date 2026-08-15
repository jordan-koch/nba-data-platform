<!-- handoff: v1 -->

## track

`feature` — box-score-foundation, Phase 2 (paced client, landing writer, manifest, backfill CLI).

## built

`src/nba_platform/{client,landing,backfill}.py` — the three target paths, nothing else; three
entries were also appended to my memory file (now 115/120 lines).

**client.py** wraps `LeagueGameLog`, always `get_request=False`, with the network moment split out as
one named `endpoint.get_request()` line inside `nba_api_transport`. Delay and retry ceiling come from
`get_settings()` **inside every `fetch()`**, never at import; the `nba_api` import is local to that
transport, so importing the module — or a dry run — loads neither nba_api nor pandas. Raw envelope
out, no `get_data_frames()` path at all.

**landing.py** owns every write under the landing root, and immutability is structural: a capture dir
is claimed with `mkdir(exist_ok=False)` and both files open `"xb"` (exclusive-create, binary — also
why no CRLF appears on Windows), so an overwrite raises instead of succeeding. A capture is present
only once `manifest.json` exists. `existing_capture_result()` is the skip-if-present check, exposed
so the backfill skips *before* spending a request; `--recapture` lands a new `capture=` dir beside
the old, advancing the stamp on a one-second collision rather than touch a landed byte.

**backfill.py** has one planner: `build_plan()` returns the call list, `--dry-run` prints and counts
it, the real run iterates it, and the client is built inside the branch a dry run does not take. A
run writing ≥1 capture emits a run manifest of measured cost under `_runs/run=<stamp>/`; a run that
lands nothing writes nothing, which is what keeps a re-run byte-identical.

## API surface

```
client.GameLogClient(*, transport=None, clock=time.monotonic, sleep=time.sleep, environ=None)
    transport: Callable[[Mapping[str, str]], RawResponse]      # single positional arg
    .fetch(*, season: str, grain: str, season_type: str) -> GameLogResponse
    .issued_at -> tuple[float, ...]  .request_count -> int  .observed_spacing_seconds -> tuple
client.RawResponse(payload, status_code=None, parameters={}, request_url=None)
client.GameLogResponse(season, grain, season_type, payload, parameters={}, status_code=None,
    request_url=None, elapsed_seconds=0.0, attempts=1, client_version=<installed nba_api>)
client.BACKOFF_FACTOR = 2.0   # attempts = max_retries + 1; sleep after failure i = delay * 2**i
landing.Partition(source, endpoint, season, grain, season_type)
landing.write_capture(*, partition, payload, captured_at, parameters=None, status_code=None,
    elapsed_seconds=0.0, request_url=None, client_name="", client_version="", landing_root=None,
    recapture=False) -> CaptureResult                          # .written is False on a skip
landing.existing_captures / existing_capture_result(partition, *, landing_root=None)
backfill.run(argv=None, *, client=None, stream=None, now=utc_now, monotonic=time.monotonic,
    environ=None) -> BackfillResult  # .plan .calls_made .written .skipped .error .exit_code
backfill.GameLogFetcher  # Protocol: fetch(*, season, grain, season_type) -> GameLogResponse
backfill.main(argv=None) -> int      # 0 green, 1 a call failed, 2 the run never started
# the dry run prints exactly one line matching `planned calls: <n>`
```

## verified

| Claim | Command | Actual output |
|---|---|---|
| Lint, format, types — no nba_api/pandas leak | `uv run ruff check` · `ruff format --check` · `uv run mypy` | `All checks passed!` · `60 files already formatted` · `Success: no issues found in 10 source files` · all exit 0 |
| CI pytest line (AC 1), incl. AC-18 purity guards over all three modules; agent contract after the memory append | `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing` | `52 passed in 0.64s` · exit 0 · new modules 0% (their tests are main-thread, landing next) · `test_agent_contract` green at 115 memory lines |
| Dry run plans 6 and builds no client | `uv run python -m nba_platform.backfill --dry-run` | `planned calls: 6`, `estimated pacing seconds: 3.0`, 6 enumerated calls · exit 0 |
| AC 17 pacing + backoff, stubbed clock/transport, env-set values | scratchpad `prove_phase2.py` | gaps `(0.25, 0.25, 0.25)`; delay raised mid-run → next gap `1.5`; `NBA_MAX_RETRIES=3` → 4 attempts, slept `[0.25, 0.5, 1.0]`; HTTP 429 retried to the ceiling then `ClientError` |
| AC 16 two runs then `--recapture` | same script | run 1 → 13 files; run 2 → **0 requests**, 6 skips, hash sets identical, no run manifest; recapture → 6 new capture dirs, every run-1 file byte-identical. The stamp collision fired for real (`…135153Z` then `…135154Z`) |
| Overwrite is impossible, not merely avoided | same script | reopening a landed `payload.json` `"xb"` raises `FileExistsError`; two `write_capture` calls at one timestamp land in two dirs |
| AC 28 one planner; manifest completeness | same script | printed `planned calls: 6` == 6 stub fetches == `result.calls_made` 6; every required manifest field present, `payload_sha256` matches the bytes on disk, `row_count` 5, tz-aware ISO `captured_at`, `http_status` 200, nba_api version, no CRLF |
| Resume semantics; bad args; the boundary holds | same script and `prove_cli_validation.py` | failure at call 3 → exit 1, 2 landed, next run re-requests only the 4 missing; malformed season/grain/season-type each raise `BackfillError` and `main()` returns 2; `nba_api`/`pandas` **not** in `sys.modules` after importing all three modules |
| Seams type-check from a test author's side; nothing written outside target paths | `uv run mypy --strict` on a scratch stub (MYPYPATH=src) · `git status --short` | `Success: no issues found in 1 source file` — a stub class satisfies `GameLogFetcher` structurally; tree shows only my three `src/nba_platform/*.py` as `??` plus the main thread's own ADR 0008 files |

`prove_phase2.py` ran 43 checks, all PASS, exit 0, into a scratch dir outside the repo. Evidence, not a deliverable: `tests/` is denied to me.

## assumed

- **`counter` is not passed** to `LeagueGameLog`; nba_api's own `0` applies. The manifest records it
  anyway: on a real call the parameter dict is `endpoint.parameters` (the wire dict), falling back to
  my kwargs only for a stub. **HTTP status comes from the private `NBAResponse._status_code`**, read
  defensively, degrading to `None`. Both measured from the installed 1.11.4 source, neither live.
  Timeout is nba_api's 30s default — `config.py` has no timeout key and is not my path.
- Invariants the spec did not restate but that bind (case 2): resolve by name, `pathlib` only,
  tz-aware only, no `parents` subscript, no literal delay/retry, no checkpoint store, nothing bulk in
  git. The delay is **not** clamped to 0.6s, per `.env.example:17-20`.

## surprised-me

- **`LeagueGameLog.get_request()` is two things.** It sends *and* runs `load_response()`, which
  indexes `resultSets['LeagueGameLog']` — a non-conforming body raises inside the call instead of
  being returned, so this transport can never *land* an error response. Relatedly, `NBAResponse`
  exposes no public status accessor at all. Both in memory.
- **The one-second stamp collision is not theoretical** — my own two-run proof hit it. In memory.
- The installed package has **no `py.typed`**, so mypy skips `nba_platform` outside its configured `files` unless `MYPYPATH` names `src/`. Harmless for CI; cost me 15 minutes.

## could-not-do

- **The three pytest modules** are repo-root `tests/` — denied. I built to their described API and
  proved it offline; the API-surface block is what they should be written against.
- **ADR 0008 and the decisions index** are denied and already present from the main thread. I read
  0008; my implementation agrees with all five of its parts.
- No `uv lock`/`uv sync`/`dbt deps`, nothing against `stats.nba.com`, no `.sql` to lint, no
  destructive git; `--dry-run` was the only CLI backfill invocation.

## docs-delta

- `docs/data-sources.md`, proposed `measured` (2026-08-15, by source reading, not by a call), under
  the `nba_api` section: **`LeagueGameLog.get_request()` also parses**, so an error or empty body
  raises rather than returning — capturing one needs `NBAStatsHTTP.send_api_request`. This is the
  constraint Phase 3's AC-20 fixture runs into. `docs-candidate`; also in memory.
- ADR 0008's cost bullet *"two captures inside the same second are ordered by the directory name
  tiebreak"* is partly retired: they can no longer share a name, because the stamp advances on
  collision. The clock-stepping-backwards hazard stands. One line, when 0008 is next touched.

## still-open

1. **Ambiguity resolved by under-building (case 3).** `--seasons`/`--grains` take one comma-separated
   string, matching `NBA_PILOT_SEASONS`; the reading I did *not* take is `nargs="+"`.
2. **The DataFrame accessor the plan says the client "may" expose was not built** — nothing landed
   needs it and it cannot be exercised without a live call or a fixture. Phase 3's recorder is home.
3. **`_runs/` is new under the landing root**, leading underscore per the Phase-3 `_error_cases`
   convention, so no source glob reaches it. A run that writes nothing emits no run manifest —
   deliberate, and what lets `test_landing_immutability` compare hash sets across runs.
4. **An aborted capture leaves an orphan `payload.json` with no manifest.** Ignored as a checkpoint,
   but a bronze glob would read it; removing it is a human action. Sweep before `--target local`.
5. **Memory is at 115/120 again**; room for one more entry at most, so a prune is due before Phase 3.
6. **User-run, never me:** the first real `uv run python -m nba_platform.backfill` — six live calls, ~4s of pacing plus response time — is what proves the transport end to end.
