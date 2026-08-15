<!-- handoff: v1 -->

## track

feature

## built

`transform/models/silver/dim_player_team_stint.sql` — the SCD2 affiliation model, derived from
`fact_player_game` joined to `dim_game` for the date, never from bronze. Gaps-and-islands
run-collapse partitioned by `(player_id, season_id)`: `lag(team_id)` in its own CTE, a running sum
of team-change starts numbers each island, islands collapse to one row, `lead(valid_from)` supplies
the boundary. `valid_to = coalesce(first_game_new_team - 1, last_game_prior_team)` — the binding F1
rule, so a trade gap resolves to the OLD team and only a season's final stint closes at its own last
game. `is_current` is `row_number() over (partition by player_id order by valid_from desc) = 1`.

`transform/models/silver/schema.yml` — grain prose, both declared limits (gap resolves to the old
team; the containment test is vacuous between game dates), the `between valid_from and valid_to` /
never-`is_current` join rule, two uniqueness tests (`[player_id, valid_from]`, and `[player_id]`
under `config: where: is_current` for "one open interval"), `mutually_exclusive_ranges` with all
four arguments explicit and commented, and `not_null` on every column but `first_game_new_team`.
Three singular tests in `transform/tests/` (`assert_player_team_matches_open_stint`,
`assert_stints_did_not_degenerate`, `assert_known_trade_resolves_both_sides`), each with a row-count
floor, plus `transform/seeds/known_trade_expectations.csv` — 6 pinned Max Christie dates, 2 of them
inside the trade gap. `transform/models/silver/README.md:52` now lists `dim_player_team_stint` and
drops the cut `dim_date`; `transform/tests/README.md:16` points the affiliation invariant at it.

## verified

| What | Command and actual output |
|---|---|
| Both targets green | `uv run dbt build --project-dir transform --profiles-dir transform --target ci` and `--target local` → both `Done. PASS=66 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=66`, exit 0 (baseline was PASS=51) |
| Model-scoped tests | `uv run dbt test --select dim_player_team_stint ... --target local` → `Done. PASS=13 ... TOTAL=13`, exit 0 |
| Range-test arguments applied | that run names it `dbt_utils_mutually_exclusive_ranges_dim_player_team_stint_allowed__valid_from__player_id__valid_to__True` — `gaps`, `partition_by`, `zero_length` all in effect |
| Lint | `uv run sqlfluff lint transform/models transform/tests` → `All Finished!`, exit 0 |
| Python suite | `uv run pytest -m "not network"` → `102 passed, 2 deselected in 0.94s`, exit 0 |
| NEGATIVE: collapsed to one row per player-season (`case when prior_observed_team_id is null`) | `dbt build --select dim_player_team_stint --target local` → `FAIL 1 assert_stints_did_not_degenerate`, `FAIL 4964 assert_player_team_matches_open_stint`, `FAIL 4 assert_known_trade_resolves_both_sides`, `Done. PASS=11 ERROR=3` |
| NEGATIVE, the part that matters | in that same run `dbt_utils_mutually_exclusive_ranges...` and BOTH uniqueness tests still **PASS** — a degenerate collapse is invisible to every schema test |
| Reverted, green again | `git diff --stat` shows no residual model change; both `dbt build` targets back to `PASS=66` |
| Stint counts, local | `dbt show --inline` on the built model → 1,764 stints, 209 multi-stint player-seasons, 205 distinct players, 1,306 `is_current` rows over 1,306 distinct players |
| Multi-stint by season, local | 22003 → 68, 22019 → 60, 22024 → 81 — the spec's AC 11 population exactly |
| Stint counts, CI corpus | fixtures built into a scratch DuckDB (`NBA_LANDING_ROOT=tests/fixtures`, `NBA_WAREHOUSE_PATH`=scratchpad) → 258 stints, 3 multi-stint player-seasons, 216 zero-length ranges, 240 `is_current` over 240 players |
| One-day stints are three different numbers | same probe → 24 `(player, season, team)` combinations span one date, 25 STINTS do, 20 survive as zero-length RANGES after the boundary rule |
| Christie, local | 1631108: LAL 1610612747 `2024-10-22 .. 2025-02-01`, DAL 1610612742 `2025-02-04 .. 2025-04-13` — the spec's pinned values, read off the model |
| Christie, CI fixture | fixture retains only 2024-10-22, 2025-01-30, 2025-02-01, 2025-02-04, 2025-02-06, so the seed pins nothing after 2025-02-06; the trade test passes on both targets |
| One game per player per date | probe → 0 `(player_id, game_date)` pairs with two rows, 0 with two teams, so `valid_to >= valid_from` holds by construction |
| No CRLF, no mojibake | byte scan of all eight touched files → `crlf=0` on every one, `nonascii=0` on the six new ones |

## assumed

- **Seed column typing.** `as_of_date` is `cast(... as date)` in the test rather than pinned by a
  `transform/seeds/schema.yml`, which is outside my target paths. Correct either way the adapter
  infers, but the seed carries no description and no declared types.
- **Full-refresh, no `unique_key` config**, like the sibling dims. MERGE-on-key is a facts rule; the
  spec was silent and this model is a derived rebuild.
- **`is_current` is proved at most one per player**, not exactly one — a uniqueness test with
  `where: is_current` cannot see a player who has none. Equality is measured (1,306 of 1,306 local,
  240 of 240 CI) but unasserted.
- **No `relationships` tests**; both keys are already relationship-tested on `fact_player_game`,
  this model's only source. Season date ranges are assumed non-overlapping, which is what lets the
  collapse partition by season while the range test partitions by `player_id` alone.

## surprised-me

- **sqlfluff's duckdb dialect cannot parse a window function on the right-hand side of
  `is distinct from` inside a `case when`.** It reports `Found unparsable section` *plus* a phantom
  `ST03 unused CTE` naming a different CTE — the CTE error is a red herring. Hoist the `lag()` into
  its own CTE. `dbt build` was green throughout; only lint saw it.
- **`dbt show --inline` rejects a trailing `limit` in the inline SQL** — it appends its own and you
  get `Parser Error: syntax error at or near "limit"`. Filter with `where` instead.
- **The degenerate model passed every schema test.** Uniqueness and `mutually_exclusive_ranges` are
  structurally blind to a collapse emitting one row per player-season — the whole argument for
  `assert_stints_did_not_degenerate`, now demonstrated rather than asserted.
- **The CI fixture holds 216 zero-length ranges against local's 20** — trimming leaves most players
  a single game, so `zero_length_range_allowed: true` is load-bearing an order of magnitude harder
  for CI than for local. `docs-candidate`.

## could-not-do

- **`docs/decisions/0009-scd2-affiliation-interval-boundaries.md` and the `docs/decisions/README.md`
  index row already exist in the working tree and are NOT mine** — both are in my deny set and I did
  not write them. Flagging so the pre/post tree diff is not misread. I read the ADR: it matches what
  I built on all six decisions, including the boundary rule and both named limits.
- **No `transform/seeds/schema.yml`** — outside the declared target paths, so the seed is
  undocumented in dbt. Its provenance and the both-targets date constraint live in the header of
  `assert_known_trade_resolves_both_sides.sql` instead.
- Nothing else blocked. No destructive git needed, no missing packages.

## docs-delta

- **The "24 one-day stints" figure needs a qualifier** (`measured`). 24 is `(player, season, team)`
  combinations spanning one date; 25 *stints* do, because a revisit splits one combination in two;
  only **20** survive as zero-length *ranges* after the boundary rule. ADR 0009 and the plan quote
  24. The number `zero_length_range_allowed` actually governs is 20 local / 216 CI.
- **Affiliation is derivable from `leaguegamelog` alone, as-of the game date** (`verified`) — no
  roster or transactions endpoint is needed for the box-score-derived answer, and the correct join
  shape is `game_date between valid_from and valid_to`, never `is_current = true`. Candidate line
  for `docs/data-sources.md`'s gotchas.
- **CI fixture coverage for `player_id` 1631108** (`measured`): 2024-10-22, 2025-01-30, 2025-02-01,
  2025-02-04, 2025-02-06 — both trade boundaries plus one game each side, nothing after. Any future
  pinned date for this player must fall inside that window.

## still-open

- Add `transform/seeds/schema.yml` if the seed should carry a description and column types — main
  thread's, since the path was outside my allowlist.
- Consider a floor asserting **exactly** one `is_current` stint per player (current rows = distinct
  players). Only uniqueness is enforced today; measured equal on both corpora.
- `dim_player`'s description still says affiliation "lives on `fact_player_game.team_id`" — true,
  now incomplete. Left alone: the spec named only the two README lines.
- Ambiguity resolved the smaller way: `last_game_prior_team` means "last observed game *within this
  stint*" (so it equals `valid_to` on a season-final stint), not "last game with the previous team",
  which would have made the column null on every first stint.
- Off-season dates resolve to zero rows by design (season-bounded); ADR 0009 names it as a cost and
  no test asserts it. `fact_team_game.plus_minus` negating across a game is still untested from
  Phase 7, not touched here.
