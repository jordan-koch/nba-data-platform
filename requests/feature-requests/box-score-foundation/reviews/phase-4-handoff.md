<!-- handoff: v1 -->

# Phase 4 — bronze walking skeleton

## track

feature

## built

Three new files, all inside the declared target paths.

`transform/models/bronze/sources.yml` — one source, `nba_stats_landing.league_game_log_player`,
reading the landing zone in place via a table-level `meta.external_location` whose root is an
inline Jinja conditional (`tests/fixtures` at `--target ci`, else
`env_var('NBA_LANDING_ROOT', 'var/landing')`). No `vars:` block, per EXEC-03. `payload.json` is
globbed by name so sibling manifests cannot enter the model, and the glob starts at `season=`
so `_runs/` is unreachable. **One binding correction to the spec: the roots carry no `../`** —
see `could-not-do`.

`transform/models/bronze/bronze__nba_stats__league_game_log_player.sql` — decodes the
column-store envelope (`resultsets[1].headers` + `unnest(rowset)`), projects all 32 player-grain
columns **by name** through `list_position(headers, ...)`, unwraps every value with `->> '$'`
(never `cast(... as varchar)`), casts explicitly, keeps `game_id`/`season_id` VARCHAR, and
recovers `captured_at` from the path's `capture=` segment. No dedup, no join, no filter, no
rename beyond casing, no derived stat.

`transform/models/bronze/schema.yml` — source contract (endpoint, all nine call parameters),
all 32 endpoint columns described **in header order**, then `captured_at`, plus `not_null` on
`game_id`, `player_id`, `team_id`, `game_date`, `plus_minus`. Records the era finding: no
tracking-derived column exists on this endpoint, so 2013-14 does not bite here.

## verified

| Claim | Command and actual output |
|---|---|
| CI build is green, byte-identical to `ci.yml:76` | `uv run dbt build --project-dir transform --profiles-dir transform --target ci` → `Done. PASS=6 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=6`, `Completed successfully` |
| The `bronze` tag works as a promotion gate | `uv run dbt build --select tag:bronze --target ci --project-dir transform --profiles-dir transform` → same `PASS=6 ... TOTAL=6`, `EXIT=0` |
| Seam resolves differently per target | `dbt compile` twice, then reading `transform/target/compiled/.../bronze__nba_stats__league_game_log_player.sql`: LOCAL → `read_json_auto('var/landing/nba_stats/...` ; CI → `read_json_auto('tests/fixtures/nba_stats/...` |
| Row count, game count, id width | `dbt show --inline "select count(*) ... from {{ ref(...) }}"` (local target, `NBA_LANDING_ROOT=../tests/fixtures`) → `model_rows=305, distinct_games=14, min_id_len=10, max_id_len=10, captures=1, first_game=2003-10-28` |
| `->> '$'` unwraps rather than quoting; NULL survives | `dbt show` sample → `game_id = 0020300001` (bare, 10 chars, leading zeros intact) and `fg_pct` empty for players with no attempt |
| The model is style-clean under the repo's intended rules | `uv run sqlfluff lint transform/models --ignore-local-config --disregard-sqlfluffignores --config <repaired copy of .sqlfluff>` → `All Finished!`, `EXIT=0`. Repaired copy differs from `.sqlfluff` by one line only |
| `.sqlfluff` as committed cannot be loaded at all | `uv run sqlfluff lint transform/models` → `configparser.ParsingError: Source contains parsing errors: '<string>' [line 10]: ']\n'`, `SQLFLUFF_LITERAL_EXIT=1` |
| Ordered schema-drift check (rehearsal of the guard) | read-only script parsing `schema.yml` + all three player fixtures → `declared endpoint : 32 columns`, `ordered-equal-both-ways=True` for 2003-04/2019-20/2024-25, `total fixture rows : 305` |
| Python suite, lint, format, types unaffected | `uv run pytest -m "not network" -q` → 97 passed, `PYTEST=0`; `uv run ruff check` → `All checks passed!`; `uv run ruff format --check` → `69 files already formatted`; `uv run mypy` → `Success: no issues found in 16 source files` |
| Working tree holds only the three declared files | `git status --short` → three `??` entries under `transform/models/bronze/`, nothing else |

## assumed

- `plus_minus` is cast to `bigint`. Measured across all 305 fixture rows it arrives as a JSON
  **integer** literal, never `8.0`. If a season ever sends it as a float the cast may raise —
  which is the right failure mode (loud, at the boundary) but is not something I proved.
- `strptime(capture_stamp, '%Y%m%dT%H%M%SZ')` yields a naive TIMESTAMP that is UTC by
  construction, because `config.CAPTURE_STAMP_FORMAT` says so. Not made TIMESTAMPTZ: that
  would be a semantic decision, and silver is where those get documented.
- No uniqueness test on `(game_id, player_id)`. The rulebook's grain contract binds **silver**;
  this bronze model is deliberately pre-dedup this phase, so asserting a natural key here would
  claim a property Phase 5 exists to establish. Flagged rather than silently skipped.
- `env_var('NBA_LANDING_ROOT', 'var/landing')` assumes a relative override is repo-root-relative
  — which is how `src/nba_platform/config.py` anchors one. An absolute override sidesteps it.

## surprised-me

- **dbt does not chdir into `--project-dir`.** This is the single fact the phase turned on and
  it is the opposite of what the plan recorded. Also explains a latent bug in `profiles.yml`.
- **`.sqlfluff` has never been loadable** — TOML list syntax in an INI file. The repo's first
  `.sql` file was always going to redden CI, but for a config reason, not a style one.
- DuckDB struct-field access is case-insensitive, so the whole envelope decode can be written
  lowercase and satisfy `capitalisation.identifiers = lower` with no quoting and no `noqa`.
- Zero style violations on the first-ever sqlfluff run. The predicted "first red is style" did
  not happen; the first red was infrastructure.

## could-not-do

- **BLOCKER, and it will redden the required check.** `uv run sqlfluff lint transform/models`
  cannot run: `.sqlfluff:7-10` writes `exclude_rules` as a TOML-style bracketed list, and the
  file is parsed by `configparser`, which raises on the closing `]`. `ci.yml:78-85` starts
  running sqlfluff on this commit, inside the `dbt build` job that
  `ops/branch-protection.json:4` requires. `.sqlfluff` is outside my declared target paths so I
  did not touch it. **The whole fix is to replace those four lines with one comment line plus
  `exclude_rules = ST06`** — I verified exactly that content lints the model clean at exit 0.
- Could not run `dbt build --target local` from the repo root at all: `profiles.yml:17`'s
  `../var/warehouse/nba_local.duckdb` resolves to a path *outside* the repo. Worked around for
  verification by invoking from `transform/`; `profiles.yml` is outside my target paths.

## docs-delta

For `/update-docs` to route into `docs/data-sources.md`, all `measured` against the committed
fixtures (2003-04, 2019-20, 2024-25, player grain, 305 rows):

- `leaguegamelog` answers column-store: `resultSets[0].headers` plus `resultSets[0].rowSet`,
  values as native JSON scalars. Player grain is 32 columns, `PLAYER_ID`/`PLAYER_NAME` at
  positions 2-3 and `FANTASY_PTS` second-to-last — it is **not** the team list with three
  columns appended.
- `MIN` at player grain is an **integer count of minutes**, not `MM:SS`. No string parser needed.
- `GAME_ID` is a 10-character zero-padded string; `SEASON_ID` is 5 characters (`22003`).
- `FG_PCT`, `FG3_PCT`, `FT_PCT` carry genuine NULLs when nothing was attempted. `PLUS_MINUS`
  and `FANTASY_PTS` are non-null in every fixture row; `PLUS_MINUS` arrives as an integer.
- Candidate for `CLAUDE.md` Constraints & Gotchas (repo-wide scar tissue, binds every agent):
  `dbt --project-dir X` does not chdir into X, so every relative path in dbt config resolves
  against the process CWD. Tagged `docs-candidate`; also in memory as a tooling trap.

## still-open

- **Fix `.sqlfluff` before this branch merges.** One line. See `could-not-do`.
- Fix `profiles.yml:17` to be repo-root-relative (`var/warehouse/nba_local.duckdb`) so
  `--target local` works from the sanctioned working directory. Not urgent for CI.
- For the main thread's `tests/test_fixture_schema_drift.py`: `schema.yml` declares 33 columns.
  The 32 endpoint columns are in exact header order; `captured_at` is last and carries
  `meta: {endpoint_column: false}` so the guard can exclude provenance columns **by property
  rather than by name**. My rehearsal used that predicate and passed both directions.
- Ambiguity I under-built deliberately: "carry `captured_at`" is the only path-derived column
  I added. I did **not** carry `season`, `grain`, `season_type` or a `capture_id`, though
  Phase 5's dedup tiebreak and `assert_bronze_row_count_matches_landed` both look like they
  will want them. Adding them is a two-line change in the first CTE.
- `var/warehouse/nba_local.duckdb` now exists from my local verification build (gitignored,
  regenerable). I did not delete it.
- Phase 5 should confirm the team-grain glob unions cleanly with the second 2003-04 team
  capture, which is the first time two captures of one partition meet in a model.
