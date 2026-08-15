> **Status:** implemented · created 2026-08-15 · decided · next: commit

# Implementation Report — Box-Score Foundation

> **One-line outcome:** the repo's first vertical data slice runs end to end — `nba_api` → an
> immutable, manifest-audited landing zone → 2 bronze models → 6 silver models, **72,593
> player-games across 3,478 games and three pilot seasons**, green on committed fixtures *and* on
> real full-season data. · **Acceptance:** 29/30 criteria met, 1 outstanding (CI on the PR, which
> only exists once the branch is pushed). · **Branch:** `feature/box-score-foundation`

**The first basketball fact this repository has ever produced:** LeBron James, 2003-10-29 — **25
points, 6 rebounds, 9 assists in 42 minutes**, Cleveland away at Sacramento. His NBA debut. That
line matches the public record, so source → landing → bronze → silver → join is externally
checkable rather than merely self-consistent.

## 1. Acceptance ledger

Every row was verified by **running** it, not by asserting it. Commands are as CI runs them.

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | `pytest -m "not network" --cov` exits 0 | **met** | 102 passed, 2 deselected |
| 2 | `dbt build --target ci` exits 0 from fixtures | **met** | `PASS=66 WARN=0 ERROR=0` |
| 3 | `sqlfluff lint transform/models` exits 0 | **met** | `All Finished!` — first successful run in repo history; the config had never parsed |
| 4 | `ruff check` / `ruff format --check` / `mypy` | **met** | 0 / 76 files formatted / 17 source files clean |
| 5 | `uv sync --locked` exits 0 | **met** | 85 packages checked; `nba_api 1.11.4` locked with pyproject in one commit |
| 6 | `fact_player_game` unique on `[game_id, player_id]` | **met** | 72,593 rows = 72,593 distinct keys; passes across a season with 81 mid-season trades |
| 7 | Every silver model: prose grain + matching uniqueness test | **met** | `dbt test --select silver --target local` → `PASS=31`; all six models |
| 8 | `mutually_exclusive_ranges` on stints | **met** | Both arguments explicit; 0 overlapping intervals over 1,764 stints |
| 9 | `assert_player_team_matches_open_stint` zero rows | **met** | Green on both targets |
| 10 | Known trade resolves on both sides | **met** | Max Christie (1631108) pinned from the captured payload; asserts a date **inside** the gap |
| 11 | `assert_stints_did_not_degenerate` | **met** | 209 multi-stint player-seasons (68/60/81); proven able to fail |
| 12 | `assert_every_game_has_exactly_two_teams` | **met (amended)** | 3,473 games one-home-one-away; 5 neutral-site games asserted positively. See §3 |
| 13 | Bronze row count matches landed | **met** | Green at full volume in 0.19s |
| 14 | `game_id` keeps leading zeros | **met** | Width exactly 10 in every row of all six payloads |
| 15 | Latest-capture-wins | **met** | 58 column values compared across 2 recaptured keys; ascending flip → FAIL 3 |
| 16 | Offline landing-immutability pytest | **met** | `tests/test_landing_immutability.py`, 6 tests |
| 17 | Offline pacing/backoff pytest | **met** | `tests/test_client_pacing.py`, 9 tests, stubbed clock |
| 18 | Offline resolve-by-name + src purity guard | **met** | `tests/test_config.py`, 12 tests; proven able to fail |
| 19 | Fixture/schema ordered drift guard | **met** | `tests/test_fixture_schema_drift.py`, both grains, both directions; proven able to fail |
| 20 | Fixture corpus spans the required cases | **met** | 17 files, 78 KB, `.json` only, all git-tracked |
| 21 | `test_doc_links` + `test_repo_structure` green | **met** | Green after every doc edit |
| 22 | `reviews/endpoint-probe.md`, `measured` | **met** | Every AC-22 question answered by name |
| 23 | `docs/data-sources.md` promotions, no blanket | **met** | Bulk table extended to 4 seasons; era row promoted for the pilot; play-by-play, shot chart, advanced box scores **all still `unconfirmed`**; rate-limit paragraph deliberately still `unconfirmed` |
| 24 | Dangling `docs/data-dictionary.md` resolved | **met** | Sentence corrected, file not created; `grep -r data-dictionary docs/` returns nothing |
| 25 | ADR for landing layout + manifest + dedup | **met** | ADR 0008, five sections, Index row |
| 26 | Bookkeeping | **met** | `grep 'No pipeline code yet'` returns nothing; Index row `implemented`; all status blockquotes advanced |
| 27 | `pytest -m network` prints measured figures | **met** | 2 passed; 6 calls, 3.36s, observed spacing `[0.86, 0.59, 0.59, 0.59, 0.61]`, full ordered column lists |
| 28 | Dry-run count equals the real run's | **met** | Offline: identical plan objects. Live: printed 6, observed 6 |
| 29 | Pilot backfill + `--target local` green | **met** | 6 calls / 6.06s; `--target local` `PASS=66`; re-run made **0 calls** and left all 13 files byte-identical |
| 30 | CI green on the PR, three required contexts | **outstanding — yours** | Requires the branch pushed and a PR opened. See §6 |

**29 of 30 met.** The one outstanding criterion cannot be met before a PR exists.

## 2. What shipped

Ten commits on `feature/box-score-foundation`, one per phase plus one governance change.

**Extraction** — `src/nba_platform/`: `config.py` (the only module that learns a path, a season, a
delay or a retry count), `client.py` (the single untyped boundary over `nba_api`, paced and
backing off from config on every call), `landing.py` (write-once, structurally: `mkdir(exist_ok=
False)` plus `"xb"`, so an overwrite raises rather than succeeding), `backfill.py` (one planner,
two consumers), `fixtures.py` (the recorder whose API makes the trim rule inexpressible wrongly).

**Transformation** — `transform/models/bronze/`: the target-aware source seam plus two models
decoding `headers`+`rowSet` by name with latest-capture-wins dedup.
`transform/models/silver/`: `dim_game`, `dim_team`, `dim_player`, `dim_player_team_stint`,
`fact_player_game`, `fact_team_game`. `transform/tests/`: twelve singular tests, each with a
row-count floor. `transform/seeds/known_trade_expectations.csv`.

**Guards** — six pytest modules under `tests/` (main-thread throughout; `tests/` is the build
agent's deny set) and the 17-file fixture corpus that *is* the CI dataset.

**Docs** — ADR 0008, ADR 0009, `docs/data-sources.md` promotions, `README.md`, `CLAUDE.md`,
`tests/fixtures/README.md`, both layer READMEs, and eight `reviews/` evidence artifacts.

Final row counts, `--target local`:

| Model | Rows |
|---|---|
| `bronze__…_player` / `fact_player_game` | 72,593 |
| `bronze__…_team` / `fact_team_game` | 6,956 |
| `dim_game` | 3,478 |
| `dim_player_team_stint` | 1,764 |
| `dim_player` | 1,306 |
| `dim_team` | 30 |

## 3. Deviations from the plan

Every one was forced by a measurement, and each is recorded where it binds rather than only here.

**AC 12 was amended — five games have no home team.** Both `MATCHUP` rows read ` @ ` for two NBA
Cup semifinals, two Paris games and one other. `dim_game` gained `is_neutral_site` with
`home_team_id`/`away_team_id` NULL for exactly those five. Disposed by the user on 2026-08-15. The
control that makes it interesting: every 2019-20 bubble game, all played at one neutral site, still
carries a designated home team — `MATCHUP`'s "home" is a **scheduling designation, not a venue
fact**.

**The team-minutes reconciliation was dropped and replaced.** `PROJECT_SCOPE.md:280` makes it
conditional on the `MIN` format. Measured: `sum(player.min) = team.min` in only 4,069 of 6,956
team-games. `MIN` is an integer at *both* grains, so player minutes arrive pre-rounded and no
parser recovers the fractions. Replaced with a team-grain `(min - 240) % 25 = 0` check, which holds
6,956/6,956 and still catches a `MM:SS` misread.

**`tov` is excluded from the reconciliation.** It agrees in only 3,541 of 6,956 — but `team.tov` is
**never** lower than the player sum, and higher in 3,415 by 0–7 (mean 0.70), stably across eras.
That is the *team turnover*, basketball rather than a defect. Asserted as `>=` in its own test.

**`dim_player` needed `dim_team`'s as-of rule, which the plan never mentions.** 1,306 player_ids
against 1,309 `(player_id, player_name)` pairs. The directions disagree — one player *lost* a
suffix while two *gained* diacritics — so no lexical tie-break works and only as-of-date does.

**Four numbers in the plan were wrong and are corrected.** 2019-20 has **88** games outside an
Oct–Apr window, not 176 (that counted team rows, and every game has two). The zero-length-stint
figure is **20**, not 24 (24 combinations span one date, 25 stints do, 20 survive as zero-length
*ranges*). The plan's `../`-prefixed paths resolve outside the repo. And its §4 lists
`dbt test --select <model> --target ci` as a spot check, which cannot pass — `:memory:` gives a
test-only process an empty database.

**Two latent config defects were fixed.** `.sqlfluff` wrote `exclude_rules` as a TOML list inside
an INI file, so `configparser` rejected it and **no sqlfluff command could run at all** — invisible
because the CI step is guarded to skip while no `.sql` exists. `transform/profiles.yml` pointed the
local warehouse at `../var/warehouse/`, which resolves to a *sibling of the repo*; `--target local`
had never been able to open its database.

**`pyproject.toml`/`uv.lock` moved to main-thread.** The plan put them on the build agent's
surface, but regenerating the lock resolves against PyPI — the same class of network call its
rulebook forbids.

**The memory budget became two-tier**, at the user's direction mid-build: ~120 lines is a curation
target swept before merge, 250 is the mechanically enforced ceiling. This supersedes the plan's
Phase 10 step 9. Final state 149 lines, 16 entries.

**Phase 9's extraction ran on the main thread**, because Phase 3 needs real payloads to trim
fixtures from and the plan puts that work there. What remained genuinely user-run is in §6.

## 4. Verification & edge cases

**Both targets, every phase.** Phase 5 proved why: two singular tests were green on fixtures and
broken at full volume — one hardcoded a fixture-only sentinel row so it could never pass on real
data, the other exhausted memory after 91 seconds. Neither was visible under `--target ci`. Every
phase since ran both.

**Seven deliberate negative checks**, each run once and reverted, because a test that cannot fail
is not a test:

| Check | Result |
|---|---|
| `parents[` + a second `var/` in `src/` | both purity guards red |
| Rename one declared bronze column | drift guard red, naming the fixture and direction |
| Flip dedup ordering to ascending | `assert_latest_capture_wins` FAIL 3 |
| Empty both bronze models | 3 singular tests red **while all 8 `not_null` passed vacuously** |
| Flag every game neutral | FAIL 39 |
| Drop one game's 22 player rows | grain sentry FAIL 23 **while uniqueness and every `not_null` passed** |
| Collapse stints to one row per player-season | population floor FAIL 1 **while `mutually_exclusive_ranges` and both uniqueness tests PASSED** |

The last three are the point of the whole exercise: **uniqueness catches fan-out, and nothing else
catches fan-in or degeneration.** A one-stint-per-player model is trivially unique and trivially
non-overlapping.

**Edge cases exercised:** the 2019-20 bubble (64–75 games per team, 9 distinct values, against an
82/82 control); games in July and August; a mid-season trade with an interpolated gap; a player in
three non-adjacent seasons; 20 zero-length stints; players returning to a former team mid-season;
DNP rows carrying `MIN = 0`; `FG_PCT` genuinely null for players who took no shots; and a
deliberately restated capture.

## 5. Findings resolved

Beyond the deviations above: an empty API response is **HTTP 200 with a complete envelope** (29
headers, empty `rowSet`), which falsifies the stated premise of binding correction EXEC-02 — its
conclusion was kept for a different, measured reason. `LeagueGameLog.get_request()` sends *and*
parses, so it can never land an error response. `cast(json as varchar)` keeps the JSON quotes,
giving `game_id` width 12. And the build agent **correctly refused** a negative check I specified
that would have mutated `tests/fixtures/` — its deny set outranked my instruction, and it produced
equivalent evidence against a scratch copy instead.

## 6. Manual gates & user-run steps

1. **Push and open the PR** — `git push -u origin feature/box-score-foundation`. **AC 30** needs CI
   green on all three required contexts: `Lint, types, tests`, `dbt build`, `Secret scan`.
2. **Merge stays yours.** `main` is protected.
3. **Optional re-verification** — everything in §1 is reproducible from a clean checkout;
   `--target local` additionally needs `mkdir -p var/warehouse` and a backfill run, both now in
   `README.md`.

## 7. Hand-off

Next: `/commit` for the Phase 10 doc landing, then your push and PR.

**Deferred decisions, with their triggers, so the next slice inherits a decision rather than
rediscovering a trap:**

- **`MERGE` on facts** — triggered by the first in-progress season **or** the first nightly run.
  `unique_key` is already declared, so it is a config change.
- **Widening past three seasons** — a parameter change (`NBA_PILOT_SEASONS`), ~46 calls total.
- **Playoffs** — `season_type` is carried on `dim_game` from day one, so they arrive as rows.
  `SeasonType=Playoffs` has still never been called.
- **Roster supplementation** — `dim_player` covers players who *appeared*; filling it needs
  `commonteamroster` and a second source of truth to reconcile.
- **A checkpoint store** — revisit at the ~30,000 play-by-play calls; skip-if-present suffices at 6.
- **NBA Cup labelling** — group-stage games are ordinary regular-season games and count normally,
  but **nothing in this endpoint identifies them**. Answering "how did we do in group play" needs
  another source. The Cup Final is already excluded upstream (every team shows exactly 82).
- **The rate-limit paragraph stays `unconfirmed`** — 22 polite calls say nothing about sustained
  behaviour, and the failure mode is a block rather than a 429.
- **`_done/` relocation** — the artifacts read `implemented`, but the directory stays at the track
  root until the PR merges. Moving it now would claim completion of steps that have not run.
