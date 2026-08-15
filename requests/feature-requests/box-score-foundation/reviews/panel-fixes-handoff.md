<!-- handoff: v1 -->

## track

feature

## built

**FIX 1 — `transform/models/silver/dim_player.sql` + `silver/schema.yml`.** Added
`first_observed_game_date` and `last_observed_game_date` (those exact names), derived as the spec
directed: `min`/`max` of `dim_game.game_date` over the player's `fact_player_game` rows, one row
per player. The name-as-of-latest logic now ends in a `latest_name` CTE and the span is **left**
joined onto it — deliberate, and explained in the model header: the name side comes from bronze
and the span side from the fact, so `inner` would silently drop any player the two disagree about,
while `left` turns a disagreement into NULLs that the two new `not_null` tests redden.
`dim_player`'s own description now carries the caveat in words — "COVERAGE IS PLAYERS WHO APPEARED
IN A BOX SCORE, AND THE MODEL'S NAME OVERCLAIMS THAT", a bench-warmer being absent entirely rather
than a row of nulls — plus an identity-only sentence; both new columns are documented as
observation bounds and explicitly **not** debut/retirement dates.

**FIX 2 — `transform/tests/assert_game_id_keeps_leading_zeros.sql`.** Extended from two bronze
models to five: both bronze grains plus `dim_game`, `fact_player_game`, `fact_team_game`. Same
`typeof(...) = 'VARCHAR'` and `^\d{10}$` predicates. The `grain` label became `model_name` holding
the actual model name, so a failure says which model and which value. `dim_player_team_stint` is
excluded and the header says why (no `game_id` column). The row-count floor is now a left join from
an explicit `expected_models` list against a `group by model_name`, so a branch deleted or
mislabelled reports zero values and reddens instead of dropping out of the assertion.

**FIX 3 — `src/nba_platform/backfill.py`.** New `PlanSurvey` dataclass and `survey_plan(plan)`,
calling the *same* `existing_capture_result` the run loop calls and splitting the plan into
`landed` / `to_issue`. `--dry-run` surveys before printing and returns
`BackfillResult(survey=..., skipped=survey.landed_count)`. Still zero requests and zero bytes
written — the survey only lists directory entries, and the client is still built inside the branch
not taken. `--recapture` reports everything as to-issue, matching what the loop does.

**Exact printed lines, for your test update.** `planned calls: <n>` is unchanged and still there.
Added, dry run only, in this order: after `planned calls:` comes
`already landed: <n> (would be skipped without a request)` — or
`already landed: 0 (--recapture ignores existing captures)` under `--recapture` — then
`requests to issue: <n>`; after the existing `estimated pacing seconds:` line comes
`estimated pacing seconds for requests to issue: <x.x> (the floor a real run would actually pay)`;
and each enumerated call line gains ` [already landed]` when it would be skipped. Without parsing
stdout: `result.survey.request_count` is the number a real run's `calls_made` must equal.

## verified

| claim | command + actual output |
|---|---|
| dbt green on fixtures | `uv run dbt build ... --target ci` → `Done. PASS=68 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=68`, exit 0 (66 → 68 = the two new `not_null` tests) |
| dbt green on real landed data | `uv run dbt build ... --target local` → `Done. PASS=68 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=68`, exit 0 |
| SQL lints | `uv run sqlfluff lint transform/models transform/tests` → `All Finished!`, exit 0 |
| offline suite | `uv run pytest -m "not network"` → `104 passed, 2 deselected in 1.09s`, exit 0 |
| lint/format/types | `uv run ruff check` → `All checks passed!`; `ruff format --check` → `77 files already formatted`; `uv run mypy` → `Success: no issues found in 17 source files`; all exit 0 |
| `dim_player` shape | read-only DuckDB probe of `var/warehouse/nba_local.duckdb`: `1306` rows, `1306` distinct `player_id`, `0` null `first_observed_game_date`, `0` null `last_observed_game_date`, `0` rows with last < first, span `2003-10-28`…`2025-04-13`, both columns `DATE` |
| span right for a known player | same probe: `2544, LeBron James, 2003-10-29, 2025-04-11` — matches the dates already in `dim_player_team_stint.sql`'s header |
| left join is a guard, not a divergence | same probe, full outer join of the model's span against `min/max(game_date)` per player from bronze → `0` disagreements |
| the caveat reached the relation | `duckdb_tables()` on `main_silver.dim_player`: comment present and matches `%APPEARED IN A BOX SCORE%` |
| silver `game_id` is VARCHAR at volume | `typeof` per model: `dim_game VARCHAR 3478`, `fact_player_game VARCHAR 72593`, `fact_team_game VARCHAR 6956` |
| FIX 2 reaches silver | compiled test under `transform/target/compiled/` names `main_silver.dim_game`, `main_silver.fact_player_game`, `main_silver.fact_team_game` beside the two bronze relations |
| FIX 2 is not vacuous | DuckDB negative controls: de-zeroing `fact_player_game.game_id` flags `72593` rows; casting `dim_game.game_id` to `BIGINT` flags `3478` on type alone; the floor's left join emits a row both for a model with zero values and for one missing from the union |
| dry run BEFORE FIX 3 | `uv run python -m nba_platform.backfill --dry-run` → `planned calls: 6` and no skip figures, while a real run against the populated zone would have made 0 |
| dry run AFTER FIX 3 | same command → `planned calls: 6`, `already landed: 6 (would be skipped without a request)`, `requests to issue: 0`, `estimated pacing seconds for requests to issue: 0.0`, all six call lines suffixed ` [already landed]`, exit 0 |
| partial and recapture branches | `--dry-run --seasons 2003-04,2011-12 --grains player` → `planned calls: 2`, `already landed: 1`, `requests to issue: 1`, marker on line 1 only. Same plus `--recapture` → `already landed: 0 (--recapture ignores existing captures)`, `requests to issue: 2` |
| a dry run still costs nothing | `tests/test_backfill_plan.py::test_a_dry_run_issues_no_requests_and_writes_no_file` passes unchanged inside the 104 — `ExplodingClient` untouched, landing tree still empty |

## assumed

- `dim_game.game_date` equals the player payload's own `GAME_DATE` for a game. Not separately
  asserted, but the full-outer-join probe measures the two spans equal for every player, which is
  the consequence that would break first.
- The 104 includes the two tests you edited in the tree (`test_fixture_recorder.py`,
  `test_live_contract.py`). You said 102; I added no pytest test, so the delta is yours.
- `survey_plan` reads the zone at plan time, so a partition landed between the dry run and the
  real run still makes the two disagree. Inherent to a preview, and not what AC 28 is about.

## surprised-me

- Three memory entries appended, 149 → 169 lines, under the 250 ceiling: the dry-run/plan
  divergence as a general design trap; `left` + `not_null` for a dimension assembled from two
  relations; and that sqlfluff's duckdb dialect cleanly lints a chain of
  `select 'literal' as col union all …`, which is what makes the per-model floor cheap.
- The floor's *duplicated* model list is a feature, not drift: because it left-joins **from** the
  expected list, a typo in a `game_ids` label makes that model report zero and go red. Folding it
  into one Jinja variable would remove that property.

## could-not-do

Nothing was blocked. No denied path needed — `tests/` and `tests/fixtures/` untouched (the fixture,
skill and `CLAUDE.md` edits in `git status` predate me), no destructive git, no missing package.

## docs-delta

- **`docs/data-sources.md`, proposed `measured`** — `dim_player.first_observed_game_date` and
  `last_observed_game_date` are bounded by what has been landed, not by a career. With the pilot's
  three non-adjacent seasons, player 2544 spans 2003-10-29 to 2025-04-11 with two decades of
  unlanded seasons inside it, so subtracting them gives a career length wrong by years. Changes an
  analyst's answer, hence here and not memory.
- **`docs/data-sources.md`, proposed `measured`** — `dim_player` coverage is players who appeared
  in a box score; a player under contract who never played has no row at all. Persisted onto the
  relation already, but the catalog is where an analyst looks first.
  **Nothing for `CLAUDE.md`** — the three build lessons are ergonomics and went to memory.

## still-open

- **`LandingError` → exit 2 is still wrong on a real run; left deliberately, per your "wider
  rework" clause.** Traced: `LandingError` comes only from `landing._reserve`, so only from
  `write_capture` (inside the loop, after a fetch succeeded) and `write_run_manifest` (after
  captures landed). `existing_capture_result` never raises it, so it can never mean "never
  started". The fix is not one line: catch it beside `ClientError` in the loop, catch it again
  around `write_run_manifest`, set `tally.error` both times so `exit_code` becomes 1, and drop it
  from `main()`'s exit-2 tuple. That changes exit-code semantics I cannot instrument (`tests/` is
  my deny set; nothing pins it today), so it would ship unasserted.
- **Ambiguity resolved the smaller way:** the existing `estimated pacing seconds:` line still
  reports the *plan* floor and I added a second, labelled line for the requests actually to be
  issued. The reading I did not take was recomputing the existing line from the survey, which
  would silently change a figure your test asserts.
- **Also smaller-interpretation:** the survey runs on the dry-run path only — a real run still
  prints skips from the loop and opens with no `requests to issue:` summary. Say the word if you
  want it to lead with the same three lines.
- `transform/models/silver/README.md` lists model names only, never the span columns — not a target path, so left alone; the doc gate may want it.
