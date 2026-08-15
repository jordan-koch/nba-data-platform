<!-- handoff: v1 -->

# Phase 6 — the vertical slice: dim_game + fact_player_game

## track

feature

## built

`transform/models/silver/dim_game.sql` — one row per `game_id`, collapsed from the team-grain
bronze by grouping on `(game_id, game_date, season_id)`, not `game_id` alone, so two rows that ever
disagree emit two rows and redden `unique` instead of being resolved by a silent `min()`. Home/away
derives from `MATCHUP`'s ` vs. ` / ` @ ` token; `is_neutral_site` is true when both rows read ` @ `
and both ids are then NULL — as for any other row shape, rather than letting `max()` invent a side.

`transform/models/silver/fact_player_game.sql` — one row per `(game_id, player_id)`, a straight
projection of the player-grain bronze with `team_id` read off the observed box-score row and no
join to anything. `unique_key` declared in config now; `min` renamed `minutes_played`. Not carried:
`game_date`/`season_id`/`wl` (dim_game's), names (Phase 7's), and `video_available` — that last one
**must** stay unread downstream or `assert_latest_capture_wins`'s sentinel argument dies.

`transform/models/silver/schema.yml` — prose grain plus proof for both. Five singular tests under
`transform/tests/`, each with a row-count floor: the amended two-teams check, the grain sentry,
FGM<=FGA at both grains, the team-minutes residue, the 2019-20 out-of-window floor.

## verified

| Claim | Command and actual output |
|---|---|
| Required check green | `uv run dbt build --project-dir transform --profiles-dir transform --target ci` → `Completed successfully`, `Done. PASS=31 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=31`, `CI=0` |
| Green on the REAL landing zone | same command `--target local` → `Completed successfully`, `PASS=31 WARN=0 ERROR=0 ... TOTAL=31`, `LOCAL=0`, whole build `1.49s` |
| **THE BASKETBALL FACT** | `dbt show` (local), `fact_player_game` → `dim_game` → bronze for the label: `LeBron James \| 2003-10-29 \| pts 25 \| reb 6 \| ast 9 \| minutes_played 42`. Same row: `away_team_id 1610612739` (CLE), `home_team_id 1610612758` (SAC) — his NBA debut, at Sacramento. 25/6/9 matches the public record, so landing→bronze→silver→join is externally checkable, not merely self-consistent |
| dim_game shape at full volume | `dbt show` (local) → `games 3478, neutral_games 5, null_home_team 5, null_away_team 5, seasons 3, season_types 1` |
| Per season, matching the spec's measurements | `dbt show` (local) → `22003 Regular Season 1189 games / 0 neutral / 0 out-of-window`; `22019 1059 / 0 / 88`; `22024 1230 / 5 / 0` |
| The five neutral games are the five named | `dbt show` (local) → `0022400147 2024-11-02`, `0022400621 2025-01-23`, `0022400633 2025-01-25`, `0022401229 2024-12-14`, `0022401230 2024-12-14`, all with empty home and away team ids |
| Grain sentry numbers | `dbt show` (local) → `fact_rows 72593, bronze_distinct_keys 72593, fact_games 3478, dim_games 3478, teams 30` |
| Test selection passes | `uv run dbt test --select fact_player_game --project-dir transform --profiles-dir transform --target local` → `Done. PASS=6 WARN=0 ERROR=0 ... TOTAL=6` (the `--target ci` form is impossible — see could-not-do) |
| **Negative: flag every game neutral** | `is_neutral_site` set to `(away_row_count >= 1)`, `--target ci` → `FAIL 39 assert_every_game_has_exactly_two_teams`, `Got 39 results`. The vacuity the spec warned about is caught |
| **Negative: silent row LOSS** | one game filtered out of the fact, `--target ci` → `FAIL 23 assert_fact_player_game_row_count_matches_bronze` while `PASS dbt_utils_unique_combination_of_columns...` and all three `not_null_fact_player_game_*` still passed. The sentry's whole argument, demonstrated |
| **Negative: the floor fires on BOTH targets** | out-of-window games filtered from the test's own input → ci `FAIL 2` (season absent *and* floor), local `FAIL 1` (floor only, season still present). Both clauses work and are distinct |
| **Negative: the minutes residue is real** | `% 25` → `% 24`, `--target local` → `FAIL 400 assert_team_minutes_are_regulation_plus_overtime` — the 400 overtime team-games. Also `SKIP=9`: the layer gate held, silver never built on failed bronze |
| **Negative: adjacent-column swap** | `fgm`/`fga` swapped in the fact, `--target local` → `FAIL 65653 assert_fgm_never_exceeds_fga` |
| All four negative checks reverted | after reverting: `--target ci` and `--target local` both `Completed successfully`, `PASS=31 ... ERROR=0` |
| `unique_key` really is on the node | read-only parse of `transform/target/manifest.json` → `materialized= table`, `unique_key= ['game_id', 'player_id']`, `persist_docs= {'relation': True, 'columns': True}`. dbt raised no warning for the unused key |
| `persist_docs` carried the caveats onto the relations | `duckdb_tables()` (local) → `dim_game` comment 1434 chars, `fact_player_game` 1523; `comment like '%REQUIRES MERGE%'` True on the fact; `comment ilike '%scheduling designation%'` and `'%neutral%'` True on dim_game |
| Style clean, including the directory CI never lints | `uv run sqlfluff lint transform/models transform/tests` → `All Finished!`, `SQLFLUFF=0` |
| Python suite unaffected | `uv run pytest -m "not network"` → `102 passed, 2 deselected in 1.05s`, `PYTEST=0` |
| I wrote only my target paths | `git status --short` → my 8 files as `??`, plus memory and this handoff. `endpoint-probe.md` shows ` M` — **that is yours, not mine**; I never opened it for writing |

## assumed

- `4` → `Playoffs` in the `season_type` decode is **inferred** from stats.nba.com convention and
  unverified, since no playoff game has been landed. `2` → `Regular Season` is verified for this
  corpus. Every other leading digit resolves to NULL on purpose, so `not_null` turns an
  unrecognised season type into a red build rather than a guessed label.
- The spec handed me the neutral counts, the 58.5% minutes figure and the 88 out-of-window games as
  measured. I re-derived all but the 58.5% from the built models (rows above).
- No `dbt deps`, `uv lock`/`uv sync`, `sqlfluff fix`, or call to stats.nba.com at any point.
  `--target local` read `var/landing` as it stood; `transform/dbt_packages/` was already present.

## surprised-me

- **The CI fixture already contains a neutral-site game.** `0022400621` (SAS/IND, 2025-01-23) is
  one of the five, so the positively-asserted neutral branch is live in CI and not only against
  `var/landing`. That was luck, not design — worth pinning before anyone re-trims the fixtures.
- **The row-loss negative check is the most convincing thing here.** Dropping 22 player rows left a
  table still perfectly unique, still not-null on every key, green on every generic test, and 22
  rows short. Only the sentry moved.
- A wrong overtime period length fails 400 of 6,956 team-games — far more sensitive than "does
  `MIN` look like a number", which is what makes it a real replacement for the dropped reconcile.

## could-not-do

- **`uv run dbt test --select fact_player_game ... --target ci` cannot pass, and not because of
  anything in this phase.** `ci` is `:memory:`, so a test-only process has no relations: all six
  ERROR with `Table ... does not exist because schema "main_silver" does not exist`. `dbt build
  --select +fact_player_game --target ci` does not rescue it — indirect test selection is eager, so
  singular tests referencing unselected models get pulled in and error. **This reproduces on Phase
  5 code alone**: `dbt build --select bronze__nba_stats__league_game_log_player --target ci` errors
  `assert_game_id_keeps_leading_zeros`, `assert_bronze_row_count_matches_landed` and
  `assert_latest_capture_wins` identically. I ran the `--target local` form (PASS=6) and the full
  `--target ci` build (PASS=31) instead. Correct the acceptance line before Phase 7 inherits it.
- Nothing else was blocked; no denied path was needed.

## docs-delta

For `docs/data-sources.md`; `measured` against the real landed pilot seasons unless labelled.

- **`MATCHUP`'s home designation is a scheduling fact, not a venue fact.** All 1,059 2019-20 games
  were physically played at one neutral site in Orlando and every one still carries a designated
  home team. Any model reading home/away as "in their own arena" is wrong for all 1,059.
- **Five 2024-25 games carry ` @ ` on BOTH team rows** — no home team designated at all:
  `0022400147`, `0022400621`, `0022400633`, `0022401229`, `0022401230`. Zero such games in 2003-04
  or 2019-20. Distinct from the bubble case: here the source declines to name a host.
- **`SEASON_ID`'s leading digit encodes season type.** `2` → Regular Season, verified for this
  corpus; `4` → Playoffs is `inferred` and unverified until a playoff pull lands.
- **Player `MIN` is rounded to whole minutes at the source**, so `sum(player.min) = team.min` for
  only 4,069 of 6,956 team-games (58.5%) and no parse recovers it. Team `MIN` is exact: 6,956 of
  6,956 are `240 + 25n`.
- **2019-20 has 88 DISTINCT games outside an Oct-Apr calendar** (8 July, 80 August). The 176 in the
  plan and in Gate 0 counted team ROWS.
- Pilot totals at silver: 3,478 games, 72,593 player-games, 30 distinct `team_id`.

## still-open

- `assert_fgm_never_exceeds_fga` and `assert_team_minutes_are_regulation_plus_overtime` read the
  **bronze** team model for their team-grain half, since `fact_team_game` does not exist yet.
  Repoint both in Phase 7 — the invariants do not change. Each file's header says so.
- **Ambiguity, smaller reading taken.** No `player_name`, `wl` or `season_id` on the fact, so the
  basketball query joined bronze for the display name. The larger reading — a degenerate
  `player_name` on the fact — makes that query two-table but creates a second answer to "what is
  this player called" once `dim_player` lands. Revisit in Phase 7 if the join proves annoying.
- **`min` is renamed `minutes_played` in silver** (the spec left the rename to silver's judgment);
  Phase 7's `fact_team_game` should match or the two facts disagree. And `fg3m <= fg3a` / `ftm <=
  fta` are **not** covered — I did not widen the test past its own name. Cheap Phase 7 adds.
- The unequal-team-game-count half of the 2019-20 property stays deferred to `--target local` per
  Phase 5; no fixture-backed version was snuck in. `var/warehouse/nba_local.duckdb` now holds
  `main_silver` beside `main_bronze` (gitignored).
- Memory: three entries appended, file at 159 lines against the 250 ceiling. No pruning needed.
