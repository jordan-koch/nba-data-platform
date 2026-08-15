<!-- handoff: v1 -->

# Phase 7 — conformed dimensions + the cross-grain proof

## track

feature

## built

`transform/models/silver/dim_team.sql` — one row per `team_id`; name and abbreviation resolved
as-of the latest observation via `row_number()` over `(game_date desc, game_id desc)`, both read
off the **same** observed row so a (name, abbreviation) pair that never existed cannot be
assembled. `transform/models/silver/dim_player.sql` — same rule on `player_id`, and it carries
**no team column** on purpose. `transform/models/silver/fact_team_game.sql` — straight projection
of the already-deduplicated team bronze; `min` renamed to `minutes_played` to match Phase 6,
`unique_key` declared for the eventual merge switch, `video_available` deliberately unread.

`transform/tests/assert_player_points_reconcile_to_team.sql` unpivots both grains to long form and
full-outer-joins them, so a failure names the measure and the team-game rather than saying
"something differs". Fourteen measures; `tov` excluded with the basketball reason in the header.
`transform/tests/assert_team_turnovers_never_below_player_sum.sql` is the inequality that is true.
Both carry row-count floors. `transform/models/silver/schema.yml` was extended, never rewritten:
three new model blocks with prose grain, plus five `relationships` tests on Phase 6's
`fact_player_game` columns.

## verified

| Claim | Command and actual output |
|---|---|
| CI target green | `uv run dbt build --project-dir transform --profiles-dir transform --target ci` → `Done. PASS=51 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=51`, exit 0 |
| Local target green, real data | same with `--target local` → `PASS=51 WARN=0 ERROR=0 ... TOTAL=51`, exit 0 |
| Silver tests green | `uv run dbt test --select silver ... --target local` → `PASS=31 WARN=0 ERROR=0 ... TOTAL=31`, exit 0; log shows `PASS assert_player_points_reconcile_to_team`, `PASS assert_team_turnovers_never_below_player_sum`, `PASS unique_dim_team_team_id`, `PASS unique_dim_player_player_id`, `PASS dbt_utils_unique_combination_of_columns_fact_team_game_game_id__team_id`, `PASS relationships_fact_team_game_{game_id,team_id}...` |
| Lint clean | `uv run sqlfluff lint transform/models transform/tests` → `All Finished!`, exit 0 |
| Offline pytest green | `uv run pytest -m "not network"` → `102 passed, 2 deselected` |
| Row counts | `dbt show --inline`, `--target local`: `dim_team_rows 30`, `dim_player_rows 1306`, `fact_team_game_rows 6956`, `games 3478`, `fact_player_game_rows 72593` |
| Reconciliation is real | `dbt show --inline`, `--target local`: `team_games 6956`, `pts_ok 6956`, `tov_eq 3541`, `tov_hi 3415`, `tov_lo 0`; the other thirteen measures all reconcile |
| Dimension drift measured | `dbt show --inline`: `team_ids 30`, `team_pairs 34`, `team_abbr_pairs 33`, `player_ids 1306`, `player_pairs 1309` |
| As-of-latest picks the right rows | `dbt show --inline` on `dim_team`: `New Orleans Pelicans / LA Clippers / Brooklyn Nets / Oklahoma City Thu...`; on `dim_player`: `Jonas Valančiūnas`, `Bobby Portis`, `Vlatko Čančar` (accents survive the round trip) |
| Negative check fails for exactly one team-game | Fixture tree copied to scratchpad, one player row (`2584 Willie Green`, PHI, `0020300001`) removed from the copy, built with `NBA_LANDING_ROOT` pointed at the copy → `FAIL 6 assert_player_points_reconcile_to_team`, `Got 6 results, configured to fail if != 0`, `Done. PASS=50 ... ERROR=1 TOTAL=51`. All six rows are `game_id 0020300001`, `team_id 1610612755`: `dreb 26/27`, `fga 71/75`, `fgm 29/33`, `pf 16/19`, `pts 81/89`, `reb 38/39` — exactly the removed line. `assert_team_turnovers_never_below_player_sum` stayed `PASS` (that player had 0 turnovers) |
| Green after the negative check | Repo fixtures never touched; both `dbt build` targets re-run at `PASS=51 ERROR=0` |

## assumed

- **"As-of the latest observation" needed an ordering; the spec gave none.** I used `game_date
  desc, game_id desc`. The tiebreak makes the ordering total, so two builds of identical data
  cannot disagree — without it the output depends on scan order.
- Silver's grain contract was applied to all three new models whether or not the spec named it
  per-model: prose grain in `schema.yml` **and** a uniqueness test matching that prose.
- `dim_player` carries no `team_id` because affiliation is date-dependent. The spec did not say to
  omit it; the rulebook does.
- The reconciliation uses a **full outer** join: "for every team-game" has to include a team-game
  whose player rows all vanished, which an inner join would pass vacuously.
- `ruff`/`mypy` were not run — no Python changed, and they are not in the acceptance list. No
  `dbt deps`, `uv lock/sync`, `sqlfluff fix`, or network call.

## surprised-me

- **sqlfluff LT02 rejects a dbt `{% for %}` loop that generates select-list lines even when the
  compiled SQL is flawless.** My first reconcile test looped over a measure list; `target/compiled/`
  output was perfectly indented and lint still emitted 24 `layout.indent` failures against the
  templated source. `sqlfluff fix` is forbidden and fighting the mapping is a rabbit hole.
- **DuckDB `unpivot <cte> on a, b, c into name x value y` parses cleanly under sqlfluff's duckdb
  dialect** and works as a CTE body — the lintable way to compare many measures across two grains
  without fourteen near-identical union branches. The most useful thing I learned this phase.
- **`dbt show --inline` cannot run on `--target ci`** — same `:memory:` reason the spec gives for
  `dbt test`. Probe on `--target local`.
- **You can build the committed fixtures into a real file database** with `--target local` plus
  `NBA_LANDING_ROOT=tests/fixtures` and a scratch `NBA_WAREHOUSE_PATH`. That is how the negative
  check ran without touching `tests/`.
- The fixture corpus is **not** a weak version of the real one here: 28 team-games, `pts`
  reconciles 28/28, and 11 already carry a team-turnover excess — so the `tov` exclusion is
  load-bearing in CI, not only at full volume.

## could-not-do

- **The required negative check told me to mutate `tests/fixtures/...` and revert. `tests/` is in
  my absolute deny set**, above any spec instruction, so I did not write there. I ran the
  equivalent against a scratchpad copy of the fixture tree — same evidence, no repo mutation, no
  revert to get wrong. If you want the in-repo version, that is a main-thread action.
- I did not add a test for the `plus_minus` negation invariant that bronze's `schema.yml` says
  belongs on silver's fact — it needs a seventh file outside my declared target paths.

## docs-delta

For `/update-docs` to route into `docs/data-sources.md`. All four are data facts, not ergonomics.

1. **`TOV` at team grain includes team turnovers charged to no player** — shot-clock violation,
   five-second inbound. `team.tov >= sum(player.tov)` always, never below. Measured 6,956
   team-games: 3,541 equal, 3,415 higher (excess 0–7, mean 0.70), 0 lower; by season 0.68 / 0.63 /
   0.80, so not era-specific. Proposed label: **verified**.
2. **`TEAM_NAME` is not stable per `TEAM_ID`** — 34 distinct pairs over 30 ids. `TEAM_ABBREVIATION`
   gives 33, because 1610612746 changed display name only under an unchanged `LAC`. **verified**.
3. **`PLAYER_NAME` is not stable per `PERSON_ID`** — 1,309 distinct pairs over 1,306 ids;
   diacritics get added over time (202685, 1628427). **verified**.
4. **Correction to a measured claim in my spec:** the Bobby Portis (1626171) drift runs the other
   way. Per-spelling `min(game_date)` in bronze: `Bobby Portis Jr.` spans 2019-10-23 to 2020-03-11,
   `Bobby Portis` spans 2024-10-23 to 2025-04-11 — **the suffix was dropped, not added**. No
   lexical rule ("prefer the longer spelling") picks the right name; only a date does. **verified**.
   Also a `docs-candidate` memory note. I corrected the model comment and persisted description.

## still-open

- **`wl` is not carried on `fact_team_game`, the smaller of two readings.** It is a genuine
  team-game attribute, but `fact_player_game`'s schema already assigns `wl` to game attributes and
  the winner is derivable from the two sides' `pts`. The reading I did not take was to add it.
- **`team_abbreviation` on `dim_team` is slightly more than the spec asked for** — carried from the
  same latest row because the spec's own `LAC` reasoning makes it relevant. Drop it if that reads
  as over-building.
- The `plus_minus` negation invariant is still unasserted; `fact_team_game`'s description says so.
- `git status` also shows `.../box-score-foundation/reviews/endpoint-probe.md` as modified (54
  lines added). **That is not mine** — I wrote only the six target paths, this handoff, and my
  memory file. Flagging it so the tree comparison is not misread.
- Both facts remain `table` / full refresh with `unique_key` declared; the merge switch is not
  this phase's. `dim_player_team_stint` untouched, and `dim_player` leaves affiliation to Phase 8.
