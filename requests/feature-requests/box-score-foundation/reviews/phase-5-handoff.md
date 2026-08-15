<!-- handoff: v1 -->

# Phase 5 — bronze complete: team grain, dedup, fidelity guards

Supersedes the first Phase 5 handoff: both `--target local` blockers are fixed, green on both.

## track

feature

## built

`transform/models/bronze/bronze__nba_stats__league_game_log_team.sql` — 29 team-grain columns in
header order plus `captured_at`, same decode shape as the player model (`resultsets[1]`,
`unnest(row_set)`, `list_position` projection by name, `->> '$'` extraction, `game_id` left
VARCHAR), deduplicated latest-capture-wins on `(game_id, team_id)`.
`bronze__nba_stats__league_game_log_player.sql` — the same dedup on `(game_id, player_id)`. Both
rank **before** projecting, on the raw cells, so the key is read once and the columns written
once. A CTE, never `qualify`. `sources.yml` gains the team source table; `schema.yml` gains the
team model's contract and 30 column descriptions.

`assert_latest_capture_wins` — **rewritten generic.** The hardcoded fixture sentinel is gone. The
recaptured-key set is now derived from the source (`having count(distinct capture) > 1`), and for
every such key two things are asserted: the surviving row's `captured_at` is the maximum capture
stamp, and **every column** of it equals that capture's landed value. Provenance and payload are
separate clauses because a rewrite taking `max(captured_at)` independently of the cells would
satisfy the first while serving superseded numbers. `duplicated_keys` and `empty_population` are
untouched, and no floor requires a restatement to exist.

`assert_bronze_row_count_matches_landed` — **same logic, fixed shape.** Column positions resolve
once per source file, before the unnest; three integers ride through instead of the header array.
`assert_game_id_keeps_leading_zeros` is unchanged — it was already green on both targets.

## verified

| Claim | Command and actual output |
|---|---|
| Required check green | `uv run dbt build --project-dir transform --profiles-dir transform --target ci` → `Done. PASS=14 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=14`, `CI=0` |
| **AC 29: green on the real landing zone** | `... --target local` → `Completed successfully`, `Done. PASS=14 WARN=0 ERROR=0 ... TOTAL=14`, `LOCAL=0`, whole build `4.9s` |
| **The OOM is gone** | same run: `PASS assert_bronze_row_count_matches_landed ... in 0.19s` (was `Out of Memory Error` at 91s). `assert_latest_capture_wins ... in 0.25s`. Seconds, not minutes |
| Real-data row counts | `dbt show` (local) → `player 72593 rows / 3478 games`, `team 6956 / 3478`. 6956 = 3478 × 2 exactly |
| Fixture row counts unchanged | `dbt show` (local, `NBA_LANDING_ROOT=tests/fixtures`) → `player 305 / 14 games`, `team 28 / 14`, 30 landed rows reducing to 28 |
| **The generic clause is non-vacuous on fixtures** | inline probe of the test's own CTEs → `recaptured_keys=2, winning_rows=2, columns_compared=58` (2 keys × 29 columns actually compared, not skipped) |
| **and correctly vacuous on real data** | same probe over both grains against `var/landing` → `recaptured_keys_on_real_data = 0` |
| **Negative check: ascending dedup still FAILS** | flipped both `order by` terms to `asc`, `dbt build --select tag:bronze --target ci` → `FAIL 3 assert_latest_capture_wins`, `Got 3 results, configured to fail if != 0`, `Done. PASS=13 ... ERROR=1`. The generic rewrite kept the property the sentinel had |
| The 3 failures decompose as designed | `--store-failures`, then querying `main_dbt_test__audit.assert_latest_capture_wins` → `1610612742 provenance clause`, `1610612747 provenance clause`, `1610612742 value clause bronze=0 winning=99` |
| Same flip PASSES on real data | `... --target local` with the flip → `PASS assert_latest_capture_wins`. Correct: nothing there has been recaptured, which is exactly why `tests/test_fixture_recorder.py` guards the corpus |
| Reverted and green | `desc` restored, both targets `PASS=14 ... ERROR=0` (rows 1-2) |
| **Negative check: floors fire on empty input** | `where capture_rank = 0` in BOTH models → ci `FAIL 6` / `FAIL 2` / `FAIL 2`, `Done. PASS=11 ... ERROR=3`; identical on `--target local`. All eight `not_null` tests passed vacuously in both runs |
| Reverted; models restored | `capture_rank = 1` restored in both, both targets green per rows 1-2 |
| Style clean | `uv run sqlfluff lint transform/models` → `All Finished!`, `=0`; `uv run sqlfluff lint transform/tests` → `All Finished!`, `=0` |
| Python suite, lint, types | `uv run pytest -m "not network"` → `102 passed, 2 deselected in 0.92s`, `=0`; `uv run ruff check` → `All checks passed!`; `uv run mypy` → `Success: no issues found in 17 source files` |
| Ordered drift rehearsal, both grains | read-only parse of `schema.yml` + all 7 payloads → `player: declared=33 endpoint=32`, `team: declared=30 endpoint=29`, `ordered_equal=True` for every payload |
| I wrote only my target paths | `git status --short` → my 7 files plus memory and this handoff. `tests/test_fixture_schema_drift.py` also shows modified — **that is yours, not mine**; I have never written under `tests/` |

## assumed

- Team `min` is cast `bigint` — measured Int32 in all 30 team fixture rows and non-null across
  6,956 real rows, never `MM:SS`, never a float. Three pilot seasons is not 23.
- `fg_pct`/`fg3_pct`/`ft_pct` typed `double` and documented nullable at team grain though
  non-null everywhere measured: nullability is inherited from player grain, not proven here.
- The value comparison normalises both sides with `coalesce(cast(try_cast(v as double) as
  varchar), v)`. I did not find a landed float whose text differs from bronze's rendering, so
  the normalisation is insurance rather than a fix for something observed.
- No `dbt deps` and no live API call at any point; `--target local` read `var/landing` as it
  stood, and `transform/dbt_packages/dbt_utils` was already present.

## surprised-me

- **A broken probe nearly invented a bug.** My first non-vacuity check reported
  `recaptured_keys=1, winning_rows=0` — which reads exactly like the new test silently
  comparing nothing. The cause was PowerShell mangling `->> '$'` inside a double-quoted
  string, so every key decoded NULL and collapsed into one group. Re-run from a single-quoted
  here-string: `2 / 2 / 58`. A wrong measurement is more expensive than no measurement.
- The fixture corpus has **two** recaptured keys, not one — both sides of game `0020300003`
  appear in both captures. Only one has an edited column, so the flip produces 2 provenance
  failures and 1 value failure.
- With bronze emptied, the generic clauses go silent (nothing to join to) and only the floor
  fires — the clearest argument yet for why the floors are not decoration.

## could-not-do

None. Both blockers are fixed in my own files, no denied path was needed, and the fidelity test
fits comfortably at full volume — no memory limit raised, no sampling, nothing skipped.

## docs-delta

For `/update-docs` to route into `docs/data-sources.md`. `measured` against the real landed
pilot seasons unless noted.

- Three real pilot seasons at player grain are **72,593 rows over 3,478 games**; team grain is
  **6,956 rows over the same 3,478 games**, exactly two rows per game with no exceptions across
  2003-04, 2019-20 and 2024-25 — including the bubble season.
- `leaguegamelog` at `PlayerOrTeam=T` returns **29 columns**, identical header order in all
  three seasons: the 32-column player list minus `PLAYER_ID`, `PLAYER_NAME` and `FANTASY_PTS`,
  the rest in unchanged relative order.
- `MIN` at team grain is an integer count of **team** minutes (240 in regulation, +25 per
  overtime), not `MM:SS`. `FG_PCT`/`FG3_PCT`/`FT_PCT` are non-null in every team-grain row,
  unlike player grain where they are genuinely NULL on zero attempts.
- `GAME_ID` is 10-character zero-padded in all 335 fixture rows and all 79,549 real rows.
- Candidate for `CLAUDE.md` Constraints & Gotchas: **fixtures are trimmed samples, so a dbt
  model or test can be green in CI and fail at season volume.** The instance — broadcasting a
  header array across an unnest — is in memory as a tooling trap, tagged `docs-candidate`.

## still-open

- **Memory is at 249 of the 250 ceiling — one line of headroom.** I appended three entries, the
  guard went red at 253, and I compressed *my own new entries* to fit rather than prune anything
  older. Nothing was dropped, but Phase 6 cannot append until you sweep: treat it as blocking.
- AC 13's "winning capture" wording: recorded as accepted, per-natural-key. No action left here.
- No `unique_combination_of_columns` in `schema.yml` — `assert_latest_capture_wins` asserts the
  natural key at both grains, so a generic test would duplicate a live assertion.
- Partitions in the row-count test key on the payload's own `SEASON_ID`, not the path's
  `season=` segment — neither model carries a `season` column. Still a two-line change if wanted.
- `assert_latest_capture_wins` does not fire if bronze **lost** a recaptured key outright — the
  inner joins go silent. `assert_bronze_row_count_matches_landed` is what catches that; the two
  are load-bearing together, so do not retire either in Phase 7.
- `var/warehouse/nba_local.duckdb` also holds a `main_dbt_test__audit` schema from my
  `--store-failures` run (gitignored, regenerable, harmless).
