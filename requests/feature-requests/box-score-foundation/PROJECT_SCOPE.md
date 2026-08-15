> **Status:** scoped · created 2026-08-14 · decided · next: plan

# Project Scope — Box-Score Foundation

## Fit Verdict

**`clean`** — unanimous across all three scopers, with two integration seams promoted to core
rather than left to be discovered during the build.

This is the roadmap's next row verbatim — `README.md:130`, *"Box-score foundation — dimensional
core, local end to end | Next"* — and the only sanctioned route by which data enters this repo.
Nothing can be broken by adding to it, because nothing exists: `git ls-files src` returns exactly
`src/nba_platform/__init__.py`, whose docstring already reserves this surface; `git ls-files
transform` returns three layer READMEs and zero `.sql`; `tests/fixtures/` holds a README and no
fixtures. Every convention the work must obey is already written and waiting, down to
`pyproject.toml`'s `network` pytest marker that nothing yet uses and `ci.yml` already excludes —
the slot was cut for this.

**No accepted ADR is contradicted.** ADR 0002 fixes the season range this works inside; ADR 0003
and 0004 are Phase 2 and fenced out; ADR 0001 authorises over-engineering the *practices* while
warning against infrastructure sized past its workload — the line this scope uses to keep
checkpoint machinery out.

**One declared divergence, stated rather than smuggled.** `CLAUDE.md`'s *"Vertical slices, not
horizontal layers"* says every phase goes source-to-published before the next widens; this slice
terminates at silver. That is a real divergence from the rule as written, and it is the right
call here — `README.md:133` stages gold marts at Phase 4. The mitigation that keeps it honest:
**no widening** — 23 seasons, playoffs, additional fact grains — until a slice actually reaches a
consumer.

## Problem

The platform cannot answer a single basketball question. There is no extraction code, no landed
data, and no dbt model, so every architectural claim in `README.md` and the seven ADRs is
untested against a real payload.

Two consequences drove the request, and **Gate 0 has now retired the first one**. The belief that
`leaguegamelog` returns an entire season per call was `unconfirmed` and worth a factor of 1000 —
~50 calls and under a minute, versus ~60,000 calls and ten hours against a source that blocks
rather than throttles. It is now **`verified`**: one call, one full season, both grains. See
[`reviews/gate-0-endpoint-probe.md`](reviews/gate-0-endpoint-probe.md).

The second stands and drives the ordering of the work. **Player–team affiliation has no source at
all.** `PERSON_ID` is stable, so identity is not the problem; trades, ten-day contracts, two-way
contracts and February buyouts mean "what team was this player on" has no answer without a date.
No endpoint returns player-team history as a time series, so it must be **derived** from box
scores: a player's `TEAM_ID` on a given game date is an *observed* affiliation, and the SCD2
intervals are reconstructed from the sequence of those observations.

That is the real reason bronze box scores must precede the dimensional core — not the textbook
"dimensions before facts" rule. Facts would load perfectly well without dimensions. The dependency
runs the other way: **the affiliation dimension cannot exist until the facts are landed, because
the facts are its source.**

## Gate 0 — already answered

The panel made a network-marked endpoint probe the first item of core scope, with a
stop-and-re-scope branch if the bulk belief failed. **It has been run.** Four calls, 0.6s pacing:

| Season | Grain | Rows | Distinct `GAME_ID` | Dupe `(GAME_ID, PLAYER_ID)` |
|---|---|---|---|---|
| 2023-24 | team | 2,460 | 1,230 | — |
| 2023-24 | player | 26,401 | 1,230 | **0** |
| 2003-04 | team | 2,378 | 1,189 | — |
| 2003-04 | player | 23,894 | 1,189 | **0** |

The stop-branch does not fire. Three data contracts are settled by measurement: the
`(GAME_ID, PLAYER_ID)` grain **holds** across a trade-heavy season; `PLUS_MINUS` is **present in
2003-04 with zero nulls**, so the 2013-14 tracking boundary **does not bite this request at all**;
and the return shape is a pandas `DataFrame` with `UPPER_SNAKE` columns.

> **A correction the plan must inherit.** The panel recorded, as `MEASURED` and independently
> reproduced, that `stats.nba.com` does not respond from this environment — and marked Gate 0, the
> backfill and the fixture capture **USER-RUN** on that basis, affecting four acceptance criteria.
> **That finding is false.** It reproduces with raw `Invoke-WebRequest`, but `nba_api` succeeds in
> 0.6s, and a control confirms general egress works. Every USER-RUN marking derived from that
> claim is void. Panel text below is carried **verbatim**, including that claim; corrections are
> marked inline as `[CORRECTED]`.

## Goals / Non-Goals

**Goals** - carried verbatim from the panel.

- GATE 0 FIRST — answer the cost question by measurement before anything is designed on it. Call leaguegamelog at PlayerOrTeam=P and PlayerOrTeam=T for the pilot seasons and record, with a `measured` label in requests/feature-requests/box-score-foundation/reviews/endpoint-probe.md: whether one call returns a whole season at each grain, the exact request issued, the response envelope shape, row count per season, the complete column list per season, whether PLUS_MINUS is present in 2003-04, whether MIN arrives as MM:SS or decimal, whether GAME_ID is a zero-padded string, whether DNP-but-active players get a row, whether (game_id, player_id) is unique in a trade-heavy season, and how many distinct (team_id, team_name) pairs appear across the span. This is a GATE with a stop-and-rescope branch, not a task — if the bulk belief fails, this request re-scopes rather than silently becoming an overnight backfill.

- Stand up the first extraction-and-landing code under src/nba_platform/: a config layer resolving the landing root, season list, pacing and retries BY NAME from the keys .env.example:8-15 already declares (NBA_ENV, NBA_REQUEST_DELAY_SECONDS=0.6, NBA_MAX_RETRIES=5) with no literal paths and no parents[N] walks outside test modules; a paced client with exponential backoff; and a write-once landing writer.

- Make the immutable landing zone auditable rather than merely asserted. Every landed payload gets a manifest record — endpoint, parameters, tz-aware captured_at, HTTP status, row count, content hash — because CLAUDE.md claims immutability is "what makes data-incident triage tractable" and transform/models/bronze/README.md:17-20 claims you can always diff against the raw, and today nothing implements the record that makes either claim executable.

- Resolve the immutable-landing vs restated-box-scores tension explicitly, in bronze. If raw is never mutated and box scores get restated (docs/data-sources.md:96-100), a re-pull produces a SECOND payload for the same partition and bronze must resolve them — latest-capture-wins on the natural key, which is exactly the deduplication transform/models/bronze/README.md:5-6 permits and nothing more. This is the architectural decision the request does not name.

- Keep `dbt build` green in CI from the first bronze model, by resolving the bronze source through ONE named seam that points at committed fixtures under --target ci and at the landing zone under --target local. This is what keeps a required check (ops/branch-protection.json:4) green and sets the pattern every future source copies.

- Build the silver dimensional core — dim_game, dim_team, dim_player, dim_player_team_stint, fact_player_game — with each model's grain stated in prose in schema.yml AND proven by a uniqueness test whose columns agree with the prose.

- Turn the traded-player requirement into a command that passes or fails rather than a lookup a human eyeballs: a singular test asserting every fact_player_game row's (player_id, game_date, team_id) falls inside exactly one matching affiliation interval, plus a fixture-pinned test asserting one specific known mid-season trade resolves correctly on BOTH sides of the trade date — the non-vacuous half, since the interval test is derived from the same observations it checks.

- Settle all five dataset contracts for exactly one endpoint family and prove each with a test rather than a claim: grain, keys, era coverage (specifically whether PLUS_MINUS has its own pre-2013-14 cliff), update semantics, and MEASURED extraction cost. +persist_docs (transform/dbt_project.yml:22-24) pushes those descriptions onto the relations themselves.

- Settle dim_team's grain against franchise-identity drift, which the request never mentions and the chosen pilot triggers: 2003-04 and 2024-25 in one dataset means Seattle/Oklahoma City, New Jersey/Brooklyn, Bobcats/Hornets and the Katrina-era New Orleans/Oklahoma City Hornets all share team_ids across differing names. A naive distinct-on-team_id-and-name either fails its own uniqueness test or gets 'fixed' with a silent arbitrary dedup.

- Commit the offline fixture set tests/fixtures/README.md:19-26 prescribes — modern season, pre-tracking season, irregular season, a mid-season-traded player, an empty/error response — as real captured payloads trimmed by ROWS only, never by structure, with trim provenance recorded. These fixtures are what makes the CI dbt job green, so they are core.

- Land the doc corrections this work actually earns and no others: promote only the docs/data-sources.md labels for endpoints actually called, leaving every untouched endpoint `unconfirmed`; correct the Phase-0 blockquotes at README.md:11-14 and in CLAUDE.md now that pipeline code exists; resolve the dangling docs/data-dictionary.md reference at docs/data-sources.md:69 (that file does not exist — verified via `git ls-files docs`, and tests/test_doc_links.py cannot catch it because the reference is backticked rather than linked); and record the landing-layout and SCD2-boundary decisions as ADRs.

- Leave the deferred decisions — MERGE, widening, playoffs, roster supplementation, checkpointing — recorded WITH their trigger conditions, so the next slice inherits a decision rather than rediscovering a trap.

**Non-Goals** - the explicit edges.

- Gold marts and anything published. This slice terminates at a tested silver layer; transform/models/gold/ keeps its README and stays empty. Phase 4 per README.md:133. This is the declared divergence from CLAUDE.md's vertical-slice rule and is stated as such.

- S3, Iceberg, Snowflake. The warehouse stays the DuckDB file at transform/profiles.yml:17; the `dev` Snowflake target at :31-41 stays unused. ADR 0003 and ADR 0004 remain accepted-and-unimplemented, Phase 2 per README.md:131. Mitigation so this stays a path swap rather than a re-land: the landing layout is S3-key-shaped prefixes resolved through the config layer.

- Orchestration. No Airflow, no DAG, no schedule — the backfill is a command a human runs. Phase 3 per README.md:132; orchestration/ does not exist.

- Play-by-play, shot detail, advanced box scores, tracking-derived stats. Phase 5 per README.md:134. This is the traditional box score only.

- Descriptive player attributes — height, weight, position, draft year, college. Those live on commonplayerinfo (~5,000 calls, FEATURE_REQUEST.md:80-82) and are not on a box score. dim_player carries identity and observed affiliation only, and its description must say so in those words.

- Roster supplementation from commonteamroster. Posture (a) from FEATURE_REQUEST.md:177-178: dim_player covers players who APPEARED, with the coverage limit documented rather than filled. ~690 calls and a second source of truth to reconcile, bought for players with zero rows in any fact table in this slice.

- Contract-type modeling. Two-way, ten-day and buyout status are not distinguishable in a box score (FEATURE_REQUEST.md:204-206, expected to stay `unconfirmed`). dim_player_team_stint must not carry a column it cannot populate honestly, and the data dictionary should record the absence so a future request does not go looking twice.

- Playoff and preseason games. Regular season only. SeasonType is a required parameter on this endpoint family (inferred, unverified) so including playoffs doubles call count and adds a population with different semantics, for zero coverage of the stated problem. dim_game carries season_type as a column from day one so playoffs arrive later as new rows, not a migration.

- A generalised extraction framework — endpoint registry, pluggable transports, retry middleware abstractions, a shared bronze casing macro across two models. One endpoint family, one module, direct calls. ADR 0001:18-21 authorises over-engineering the PRACTICES and warns explicitly that infrastructure sized past its workload reads as poor judgment.

- A standalone checkpoint store. docs/data-sources.md:34 says long backfills checkpoint, but a six-call, seconds-long backfill has no hour six to resume from. Write-once skip-if-present IS the checkpoint at this volume, for free. Build the real thing at Phase 5, which docs/data-sources.md:50-52 already names as where the rate-limit engineering earns its keep. (Note: this cuts an item the request lists at FEATURE_REQUEST.md:101 — gated below.)

- Any era-nullable column machinery — CONTINGENT non-goal. If Gate 0 confirms the traditional player log carries no tracking-derived column, the 2013-14 boundary does not touch this request at all and there is nothing to build. Do not build it speculatively; if PLUS_MINUS turns out to have its own cliff, that is a schema.yml note plus one test, not a machinery build.

- Widening past the three pilot seasons to the full 2003-04..2025-26 range, and any season before 2003-04 per ADR 0002 — not even opportunistically if the bulk endpoint makes it nearly free, because ADR 0002:47-49 defers pre-2003 era handling deliberately rather than accidentally.

- No NBA data committed beyond trimmed fixtures. README.md:62-65 states the repo redistributes no NBA data; tests/fixtures/README.md:41-44 requires trimming. A full 2019-20 player log is tens of thousands of rows and must never land in git — .gitignore:30 is a carve-out, not a licence.

- No agent-run live extraction as an acceptance gate. MEASURED and reproduced independently this session: stats.nba.com times out from this environment (Invoke-WebRequest, 20s, browser-like headers). Gate 0, the backfill and the fixture capture are USER-RUN, marked per requests/feature-requests/README.md:56-59.

- No rewrite of CLAUDE.md's rules or any accepted ADR. New decisions land as new ADRs; docs/decisions/README.md makes accepted ADRs immutable.

- No changes to the request-pipeline skills, no second subagent, no stage-4 dispatch rewiring.


## Acceptance Criteria

Numbered and objectively testable. **Four criteria were marked USER-RUN by the panel on the strength of its false unreachability finding; those markings are void** - see the correction above. Criteria that are genuinely user-run (a full-pilot run against the live API, CI green on the PR) remain so.

**1.** `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing` exits 0 on a clean checkout with no var/ directory and no network access. (Byte-identical to ci.yml:53.)

**2.** `uv run dbt build --project-dir transform --profiles-dir transform --target ci` exits 0 on that same clean checkout — bronze and silver built entirely from committed fixtures, no var/, no network. (Byte-identical to ci.yml:76; this is the required check named "dbt build" at ops/branch-protection.json:4.)

**3.** `uv run sqlfluff lint transform/models` exits 0. This step is currently skipped by the guard at ci.yml:78-85 and goes live on the first .sql file; it lints under .sqlfluff (duckdb dialect, lowercase keywords/functions/identifiers, explicit table AND column aliasing, max_line_length 100) and templates through dbt at target = ci (.sqlfluff:12-16), so it also fails on any source that does not resolve under ci.

**4.** `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy` all exit 0 with the new src/nba_platform/ modules included. Note mypy is `strict = true` over files = ["src", "tests"] (pyproject.toml:70-74) and ruff selects DTZ (:58, naive datetimes are errors) and PTH (:59, os.path is an error).

**5.** `uv sync --locked` exits 0 in CI (ci.yml:39) after the extraction dependency is added to `[project] dependencies` (pyproject.toml:9, currently `[]`) and uv.lock is regenerated in the same commit. Verified this session: uv.lock contains no nba_api, pandas or httpx entry (only a transitive `requests`), so a dependency added without re-locking is a hard red on a step unrelated to the code under review.

**6.** fact_player_game passes `dbt_utils.unique_combination_of_columns` on `[game_id, player_id]` across every pilot season including at least one containing mid-season trades, written in the `arguments:`-nested shape at transform/models/silver/README.md:19-23. (dbt 1.10+ warns on top-level generic-test args, and dbt_project.yml:51-53 sets `+severity: error`, so a warn is a red build.)

**7.** Every silver model has a schema.yml description stating its grain in prose AND a uniqueness test whose columns match that prose: dim_player unique+not_null on player_id; dim_game unique+not_null on game_id; dim_team unique on whatever key its settled grain declares; dim_player_team_stint unique_combination_of_columns on [player_id, valid_from]; fact_player_game on [game_id, player_id]. Checkable by `dbt test` and by the declared-grain-vs-test audit /update-docs performs.

**8.** `dbt_utils.mutually_exclusive_ranges` passes on dim_player_team_stint's intervals partitioned by player_id, with the gap/overlap posture matching whichever boundary rule is decided below — proving no player has two intervals that intersect and that exactly one interval is open per player. (Macro verified present in the resolved dbt_utils 1.4.1 at transform/dbt_packages/dbt_utils/macros/generic_tests/mutually_exclusive_ranges.sql; CI restores it via `dbt deps` at ci.yml:71.)

**9.** The singular test transform/tests/assert_player_team_matches_open_stint.sql returns zero rows: every fact_player_game row's (player_id, game_date) falls inside exactly one dim_player_team_stint interval whose team_id equals the fact's team_id. Named per transform/tests/README.md:28-33; this is the invariant already listed at :16.

**10.** A fixture-pinned pytest or singular test asserts that one SPECIFIC known mid-season trade resolves to the correct team on both sides of the trade date — the player chosen from the Gate 0 captured payload, never from memory. This is the non-vacuous companion to the criterion above: the interval test is derived from the same observations it checks, so on its own it proves the run-collapsing logic did not lose or reorder observations, not that the interpolated boundary is right.

**11.** A singular test asserts the SCD2 logic did not degenerate: the count of players with more than one stint inside a single pilot season is greater than zero, and no stint has valid_from > valid_to. Fails loudly if the interval builder collapses to one row per player.

**12.** `assert_every_game_has_exactly_two_teams.sql` returns zero rows, and exactly one of each game's two rows is flagged home and one away — proving the home/away derivation, which is the one inferred structure in this slice (transform/tests/README.md:13).

**13.** A landing-fidelity test asserts that for each landed payload, the bronze model's row count equals the row count in the landed JSON's result set — making executable the invariant transform/models/bronze/README.md:17 states in prose: if bronze and the landed JSON disagree, bronze is wrong.

**14.** A test asserts game_id is typed as a string in bronze and silver and that no value has lost a leading zero (every value matches a fixed-width numeric-string pattern). stats.nba.com game ids are zero-padded strings; a numeric inference in read_json_auto destroys them silently while every join still 'works' and every uniqueness test still passes.

**15.** With two captures of the same (season, grain) present in fixtures, bronze emits exactly one row per natural key and that row's values come from the later captured_at. This is the only test that exercises the immutable-landing vs restated-facts tension.

**16.** An offline pytest proves landing immutability: run the backfill twice against a stubbed client into a tmp_path, hash every file in the landing tree after run 1 and after run 2, assert the hash sets are identical and no previously-landed file's content changed. Mechanizes the invariant CLAUDE.md and docs/data-sources.md:31-33 state in prose.

**17.** An offline pytest proves pacing: with a stubbed clock, N sequential calls request no faster than NBA_REQUEST_DELAY_SECONDS (.env.example:14, default 0.6), and a simulated failure backs off exponentially up to NBA_MAX_RETRIES (:15).

**18.** An offline pytest proves resolve-by-name: the landing root resolves through the config layer from NBA_ENV, and no module under src/nba_platform/ contains a `parents[` walk or a literal 'var/' string. (tests/test_repo_structure.py:19 uses parents[1] — that is a test-file locator and must not be copied as precedent for src/.)

**19.** A fixture/schema drift guard asserts, in both directions, that the column set in each committed fixture equals the column set the corresponding bronze schema.yml declares. An upstream column added, removed or renamed reddens at the boundary rather than producing a null four layers down (transform/models/bronze/README.md:30-34).

**20.** The fixture set at tests/fixtures/nba_stats/league_game_log/ contains at least: one modern season, one 2003-04 pre-tracking case, one 2019-20 bubble case, one case containing a known mid-season-traded player, and one empty-or-error response — the applicable rows of tests/fixtures/README.md:19-26 — each a real captured payload trimmed by rows only (never by envelope structure), with trim provenance recorded alongside.

**21.** `uv run pytest tests/test_doc_links.py tests/test_repo_structure.py` exits 0 after every doc and structure edit — new relative Markdown links resolve, and transform/models/ still agrees with dbt_project.yml (test_repo_structure.py:63-85).

**22.** RECORDED-EVIDENCE — requests/feature-requests/box-score-foundation/reviews/endpoint-probe.md exists, carries a `measured` label (never `unconfirmed`), and answers by name: full-season-per-call at P and at T; the response envelope shape; row count and complete column list per pilot season; whether PLUS_MINUS is present in 2003-04; whether MIN is MM:SS or decimal; whether GAME_ID is zero-padded; whether DNP-but-active players get a row; whether (game_id, player_id) is unique in a trade-heavy season; and the count of distinct (team_id, team_name) pairs across the span.

**23.** RECORDED-EVIDENCE — docs/data-sources.md has exactly the labels this work earned promoted, each promotion naming what was run and when: the bulk-vs-per-game table (:41-48), the rate-limit paragraph (:24-27), the traditional-box-score availability row (:59). Every row for an endpoint this request did not call still reads `unconfirmed`, and the epistemic blockquote (:5-10) no longer claims no endpoint has been called. A blanket promotion is a FAILURE of this criterion.

**24.** RECORDED-EVIDENCE — the dangling docs/data-dictionary.md reference at docs/data-sources.md:69 is resolved one way or the other: either the file is created and linked as a real Markdown link (so tests/test_doc_links.py can see it) or the sentence is corrected. Verified this session via `git ls-files docs` that the file does not exist.

**25.** RECORDED-EVIDENCE — a new ADR under docs/decisions/ records the landing-zone layout, the capture manifest, and the bronze latest-capture-wins rule, with Status / Context / Decision / Consequences / Alternatives and an honestly uncomfortable cost section, and its row is added to the Index in docs/decisions/README.md.

**26.** BOOKKEEPING (greppable) — PROJECT_SCOPE.md opens `scoped · decided · next: plan`, FEATURE_REQUEST.md's status blockquote advances off `intake`, and the Index row at requests/feature-requests/README.md:91 matches. README.md:11-14's Phase-0 blockquote and :130's roadmap row, plus CLAUDE.md's "No pipeline code yet" line, no longer claim there is no pipeline code.

**27.** USER-RUN (marked per requests/feature-requests/README.md:56-59; stats.nba.com is unreachable from the agent environment — MEASURED this session) — `uv run pytest -m network` executes the Gate 0 probe against the live endpoint and prints measured call count, rows per call, wall-clock seconds and the column list per grain per pilot season.

**28.** USER-RUN — a `--dry-run` invocation of the backfill prints planned call count, pacing and estimated wall clock WITHOUT issuing a request, and that printed number equals the call count the subsequent real run makes.

**29.** USER-RUN — the pilot backfill runs against live stats.nba.com, writes payloads under var/, and then `uv run dbt build --project-dir transform --profiles-dir transform --target local` is green through silver against that real data with the same test suite. This is the criterion CI cannot claim: fixtures are trimmed samples, so a (game_id, player_id) duplicate existing only at full-season volume would pass every automated check.

**30.** USER-RUN — CI is green on the PR for all three required contexts named at ops/branch-protection.json:4: "Lint, types, tests", "dbt build", "Secret scan". Push, PR and merge stay the user's per CLAUDE.md.


## Scope (tiered)

Carried verbatim from the panel. Where a core item embeds the panel's false unreachability claim, the correction is marked `[CORRECTED]` inline rather than by rewriting the item.

### Core (must)

- GATE 0 — THE ENDPOINT PROBE, USER-RUN, BEFORE ANY MODELING. A network-marked probe calling leaguegamelog at player and team grain for the pilot seasons, regular season, recording everything listed in the Gate 0 acceptance criterion. Output: reviews/endpoint-probe.md with a `measured` label, the captured payloads that become the fixtures, and a `## docs-delta` for the main thread. DECISION POINT with a real branch: if one call does not cover a season, this request STOPS and re-scopes rather than silently becoming a ~7,000-call, hour-plus pilot. Marked user-run because stats.nba.com times out from the agent environment (MEASURED, reproduced independently this session). **[CORRECTED: false - nba_api reaches the endpoint in 0.6s; Gate 0 has been run. Not user-run.]**

- CONFIG LAYER in src/nba_platform/ — the smallest thing satisfying CLAUDE.md's resolve-by-name rule. Reads NBA_ENV / NBA_REQUEST_DELAY_SECONDS / NBA_MAX_RETRIES (.env.example:8,14,15), exposes the landing root, the warehouse path and the pilot season list by name. No literal paths, no parents[N] walks. Landing paths are S3-key-shaped prefixes (<source>/<endpoint>/season=<x>/grain=<y>/) so the Phase 2 move to S3 under ADR 0003 is a root swap, not a re-land. No settings framework, no environment class hierarchy — dev/prod branches arrive with Phase 2.

- PACED CLIENT + WRITE-ONCE LANDING WRITER. 0.6s minimum spacing and exponential backoff, both from config not literals. Write-once: a partition that already exists is skipped, not overwritten. Each write emits a manifest record — endpoint, parameters, tz-aware captured_at (ruff DTZ at pyproject.toml:58 makes naive datetimes an error), HTTP status, row count, content hash. The manifest is what makes immutability auditable and is what bronze's dedup orders by.

- LANDING LAYOUT AND RE-PULL SEMANTICS, DECIDED EXPLICITLY IN THE SCOPE, NOT LEFT TO IMPLEMENTATION. A deterministic path per (source, endpoint, season, grain, season_type) plus a capture discriminator, AND a stated rule for what bronze does when two captures of the same partition exist. Undecided, this silently doubles row counts or silently breaks immutability — both plausible choices are wrong if unstated.

- THE TARGET-AWARE BRONZE SOURCE SEAM. One named indirection — a dbt var or env_var() resolved in sources.yml — pointing the bronze source at tests/fixtures/ under --target ci and at the landing root under --target local, by name, with no literal path in a model. Non-negotiable core and completely absent from the request: ci.yml:76 builds on :memory: with var/ gitignored, ops/branch-protection.json:4 makes it a required check, and .sqlfluff:16 templates at target = ci so an unresolved source breaks linting too. This is the single seam that keeps the PR mergeable and sets the pattern every future source copies.

- BRONZE — bronze__nba_stats__league_game_log_player and bronze__nba_stats__league_game_log_team, named per transform/models/bronze/README.md:23. Typing, lowercase casing, dedup on the natural key keeping the latest capture, and nothing else: no joins, no filtering, no semantic renaming, no derived stats. Each schema.yml declares the source contract — endpoint, parameters, and not_null on the columns this project depends on the upstream promising (:30-34). The team-grain model is core despite fact_team_game being out, because it is the source of dim_game's home/away (two rows per game collapse to one, avoiding MATCHUP-string parsing) and of dim_team, for three extra API calls.

- SILVER dim_game — one row per game_id, carrying game_date, season, season_type, and home/away team ids resolved from the team-grain payload. Home/away derivation is business logic and lives in silver, never in bronze.

- SILVER dim_team — grain SETTLED against franchise-identity drift, which the request never mentions and this pilot triggers. Confirm at Gate 0 by counting distinct (team_id, team_name) pairs across the landed seasons, then decide: one row per team_id with name resolved as-of the latest observation, or one row per (team_id, season). This is a conformed-dimension decision every future model inherits, and a naive distinct-on-id-and-name either fails its own uniqueness test or gets silently 'fixed'.

- SILVER dim_player — one row per player_id, identity ONLY (id, name as observed, first and last observed game date). Its schema.yml description must state in words that coverage is players who APPEARED in a box score, so the model's name does not overclaim; +persist_docs (dbt_project.yml:22-24) carries that caveat onto the relation itself, which is the repo-native mitigation for the documentation hazard at FEATURE_REQUEST.md:181-183.

- SILVER dim_player_team_stint — the SCD2 affiliation model, one row per player per team-stint, key (player_id, valid_from), carrying team_id, valid_from, valid_to, is_current, plus the observed-boundary columns last_game_prior_team and first_game_new_team so any interpolation stays visible and falsifiable rather than fabricated. Split out of dim_player rather than folded in (gated below, recommended split).

- SILVER fact_player_game — one row per player per game, key (game_id, player_id), team_id taken from the observed box-score row so fact correctness never depends on the stint interpolation. Materialized `table` (full refresh) for the pilot with the unique key declared now, so switching to incremental+merge is configuration rather than a rewrite; the deferral and its trigger go in the model description, not left implicit.

- THE TEST SUITE this slice can afford, drawn from the list transform/tests/README.md:12-18 already publishes: grain uniqueness on every silver model; relationships from fact_player_game to dim_game, dim_player, dim_team; mutually_exclusive_ranges on the stints; assert_player_team_matches_open_stint; the fixture-pinned known-trade test; the SCD2-did-not-degenerate test; every-game-has-exactly-two-teams; FGM never exceeds FGA at any grain; the bronze-vs-landed row-count fidelity test; the game_id leading-zero test; the two-captures dedup test; and the pytest set proving immutability, pacing, and resolve-by-name.

- OFFLINE FIXTURES at tests/fixtures/nba_stats/league_game_log/ spanning the cases tests/fixtures/README.md:19-26 names, trimmed by rows only and never by envelope structure, with trim provenance recorded. These fixtures ARE the CI dataset, so they are core rather than a nicety — and every fixture-backed test needs a row-count floor assertion so it cannot pass vacuously on an over-trimmed sample.

- DEPENDENCY AND TOOLCHAIN CHANGES IN THE SAME COMMIT: the extraction library added to [project] dependencies (pyproject.toml:9, currently empty), uv.lock regenerated (uv sync --locked at ci.yml:39 fails otherwise), and the untyped third-party surface isolated behind one typed boundary module or an explicit committed mypy override (strict = true over src and tests, pyproject.toml:70-74).

- DOC LANDING, INCLUDING A MAIN-THREAD STEP THE BUILDER CANNOT PERFORM. docs/data-sources.md is in the data-engineer agent's deny set (.claude/agents/data-engineer.md:131) and facts route through `## docs-delta` (:220-225), so the label promotion MUST be an explicit main-thread /update-docs step in the plan or the request's headline success signal silently does not happen. Plus: README.md:11-14 and :130, CLAUDE.md's Phase-0 line, the dangling data-dictionary reference at docs/data-sources.md:69, and the ADR(s).

- PILOT SEASONS 2003-04, 2019-20, 2024-25 — CONFIRMED, regular season only, config-driven so widening is a parameter change. The far side of the hand-checking discontinuity, the unequal-game-count bubble, and a recent complete tracking-era season. 2011-12 and 2020-21 differ from 2019-20 only in game count, which 2019-20 already breaks harder.

### Folded in (cheap wins)

- `--dry-run` cost planner on the backfill: prints planned call count, pacing and estimated wall clock without issuing a request. CLAUDE.md makes cost a guardrail; this is the cheapest possible version of it, and it makes the cost contract checkable because the printed number and the observed number must agree.

- The extraction run manifest recording MEASURED cost — call count, elapsed wall clock, observed inter-request spacing, rows per call. Turns the whole request's central belief from asserted into measured and gives the widening a real extrapolation base. Near-zero marginal cost once the client exists.

- The fixture recorder. tests/fixtures/README.md:11-13 instructs the reader to "Capture them with the recorder" and no recorder exists (verified: src/nba_platform/ is one file). It is the paced client plus a trim-and-write step, and it makes the fixture set reproducible rather than hand-curated — which matters the first time upstream changes shape and every fixture needs recapturing.

- A `network`-marked live contract test that re-calls the endpoint and asserts the column set still matches what bronze declares. The marker already exists unused at pyproject.toml:80-82 and ci.yml:53 already excludes it — the slot was cut for exactly this. Upstream is "undocumented, unversioned, and governed by no contract" (docs/data-sources.md:17-19), so a committed fixture freezes a contract that can change silently; this is the alarm.

- The offline half of the same idea: a fixture/schema drift guard asserting fixture columns equal schema.yml columns in both directions. A dozen lines of pytest, and it catches the fixture-updated-but-schema-forgotten case that the network test cannot see in CI.

- The game_id leading-zero guard — string typing plus a fixed-width-pattern test. Cheap, and it is the classic silent-corruption failure that survives every test you would otherwise think to write.

- Season type carried on dim_game from day one with a not_null test, even though only regular season is extracted. Makes playoffs arrive later as rows rather than as a migration, and prevents a future widening from either double-counting or being silently dropped by an undocumented filter.

- A 'grain sentry' test on the bronze-to-silver row count: fact_player_game's row count equals bronze's distinct (game_id, player_id) count. Three lines of SQL, and it catches the one failure a uniqueness test cannot — silent row LOSS from an inner join to a dimension missing a key. Uniqueness catches fan-out; this catches fan-in.

- An irregular-season assertion so the pilot's own fixtures keep earning their keep: team game counts in 2019-20 are unequal, and 2019-20 contains games outside an Oct–Apr window. Pins the exact property that season was chosen for, so a future refactor that quietly filters by calendar month goes red instead of green-and-wrong.

- Two short ADRs rather than one: landing layout + capture manifest + bronze latest-capture-wins, and separately the SCD2 interval-boundary rule. Both are decisions a future reader will need legible, and docs/decisions/README.md requires the cost section be uncomfortable to write — the SCD2 one especially is.

- A landing-zone layout convention note (folded into the landing ADR rather than a separate doc). var/ is gitignored so the layout is invisible to a repo reader, and it is the structure every future extraction request must conform to. Cheapest way to stop the second dataset inventing a second layout.

- Documenting layer promotion as tagged dbt selectors — `dbt build --select tag:bronze` then `tag:silver`. dbt_project.yml:32,40,47 already assigns the tags and :18-19 already says promotion is gated on tests; this turns a comment into a runnable gate and gives the eventual Airflow DAG its natural task boundaries. A few lines of documentation.

- Team-minutes reconciliation (240 per regulation game, +25 per OT), CONDITIONAL on Gate 0 settling the MIN format. Listed at transform/tests/README.md:15, expressible on player grain alone without fact_team_game, and it doubles as the proof that the MIN parse is right.

### Gated - resolved

All eleven were disposed by the user on 2026-08-14; each is recorded with its rationale under *Decisions* below.


## Above & Beyond

The surviving ambitious proposals, carried verbatim with the panel's tiering.

- @{title=Reverse the fence and build fact_team_game in this slice; tier=gated; rationale=Strongest single call in the scope, and it reverses an explicit 'Explicitly out' line (FEATURE_REQUEST.md:78) — so it goes to the human, never folded. The case for yes is real: the team payload is landed and bronzed under core scope either way (it is the source of dim_game's home/away and dim_team), so the marginal cost is one silver model of nearly the same shape as fact_player_game. What it buys is the strongest correctness check this dataset offers. The case for no, from the minimalist, is also real: it adds a second fact grain, a second set of contracts, and a reconciliation debugging surface to a slice whose real job is proving the extraction belief and the affiliation model. MY RECOMMENDATION: yes. This slice otherwise ships with NO cross-grain proof at all, and the reconcile test is the one assertion that catches join fan-out, dedup failure and mis-resolved affiliation at once.}

- @{title=Add the player-points-reconcile-to-team-total singular test; tier=gated; rationale=Rides entirely on the item above and gated with it. ~15 lines of SQL, named verbatim as the naming example at transform/tests/README.md:30 and listed first among the invariants at :12 — and it is the repo's OWN canonical example of a testable acceptance criterion at requests/feature-requests/README.md:54. Recommend yes, with fact_team_game.}

- @{title=Team minutes reconcile to 240 per regulation game, +25 per overtime; tier=cheap_fold; rationale=Listed at transform/tests/README.md:15. Unlike the points reconcile it does NOT need fact_team_game — summing player minutes per team-game works on player grain alone. It depends on the MIN format (MM:SS vs decimal), which Gate 0 has to settle regardless, so the test doubles as the proof that the parse is right. It also surfaces the DNP question: whether the log emits rows for players who did not play materially changes fact_player_game's row count. Fold in, conditional on Gate 0.}

- @{title=Run all 23 seasons now instead of a three-season pilot, if the probe confirms bulk; tier=gated; rationale=The pilot-then-widen staging is a hedge against the endpoint not being bulk; if it is bulk the full backfill is ~46 calls and under a minute (docs/data-sources.md:44), and the staging hedges a risk already retired. Genuine judgment call, goes to the human. MY RECOMMENDATION: keep three, make the season list config-driven so widening is a parameter change. The widening does not just add calls — it drags in whatever era handling twenty unexamined seasons turn out to need, and this slice already carries the first extraction code, the first landing zone, the first bronze, five silver models and the first fixtures.}

- @{title=Add 2005-06 or 2006-07 for the Katrina-era New Orleans/Oklahoma City Hornets; tier=drop; rationale=The underlying concern is right and I have promoted it to CORE (dim_team's grain must be settled against franchise-identity drift). But the extra season is not needed to trigger it: 2003-04 and 2024-25 together already put Seattle/Oklahoma City, New Jersey/Brooklyn and Bobcats/Hornets in the same dataset under shared team_ids. Adding a season adds fixture bytes to a public repo (tests/fixtures/README.md:41-44) for a case the existing pilot already exercises. Dropped as a season; kept as a modeling requirement.}

- @{title=Build fact_player_game as incremental MERGE-on-key from day one; tier=gated; rationale=Genuine judgment call with a real repo-rule tension either way. For: CLAUDE.md's Data Layer and transform/models/silver/README.md:47-48 both state facts are MERGE-on-key, so a full-refresh first fact means the repo's first fact table contradicts its most prominently documented data rule, and /update-docs audits exactly that kind of divergence. Against: all three pilot seasons are finalized, so full-refresh is genuinely correct for them, and building the merge path now costs more in a slice already carrying a lot of firsts. MY RECOMMENDATION: defer, but record the trigger explicitly in the model description and the scope — 'the first in-progress season, or the first nightly run, requires MERGE first' — so the widening inherits a decision rather than rediscovering a trap.}

- @{title=Build the fixture recorder the repo already documents but does not have; tier=cheap_fold; rationale=tests/fixtures/README.md:11-13 instructs "Capture them with the recorder" and no recorder exists — verified drift, and this is the first request that can honestly close it because the recorder is the paced client plus a trim-and-write step. It also makes the fixture set reproducible rather than hand-curated, which matters the first time upstream changes shape and every fixture needs recapturing. Fold in.}

- @{title=Surface the capture manifest as a bronze model so lineage from a row back to its payload is queryable; tier=gated; rationale=Splits into two things with different costs. The manifest ITSELF is core in this scope — without it, bronze has nothing to order latest-capture-wins by, and CLAUDE.md's 'immutable landing makes triage tractable' claim stays unexecutable. Exposing it as a THIRD bronze model is a further step: a new model, its own schema.yml and contract, and a lineage surface with no consumer in this slice. MY RECOMMENDATION: no for this slice — the manifest lands as a written sidecar and bronze reads it; promote it to a model when requests/data-incidents/ has its first actual incident to triage.}

- @{title=--dry-run cost planner on the backfill command; tier=cheap_fold; rationale=Prints planned call count, pacing and estimated wall clock without issuing a request. CLAUDE.md makes cost a guardrail and docs/data-sources.md:41-48 frames the entire extraction design around call count; a command that can tell you it is about to make 60,000 calls before it makes them is the cheapest possible version of that guardrail. It also makes the cost contract checkable, because the printed number and the observed number must agree.}

- @{title=A network-marked live contract test asserting the column set still matches bronze's declaration; tier=cheap_fold; rationale=The `network` marker already exists unused at pyproject.toml:80-82 and ci.yml:51-53 already excludes it — the slot was cut for exactly this. Upstream is undocumented and unversioned (docs/data-sources.md:17-19), so a committed fixture is a frozen snapshot of a contract that can change silently; this turns schema drift into a one-command on-demand check instead of a data incident discovered downstream. Runs on demand, never in CI, never in a way that could get the client blocked.}

- @{title=Offline fixture/schema drift guard — fixture columns must equal schema.yml columns, both directions; tier=cheap_fold; rationale=The CI-runnable half of the item above, and the only half CI can have. transform/models/bronze/README.md:30-34 says a not_null in bronze is a statement that the upstream promised it, so the build fails loudly at the boundary; this extends that from values to the column set and catches the fixture-updated-but-schema-forgotten case. A dozen lines of pytest.}

- @{title=Prove checkpoint-and-resume with a test that interrupts a backfill mid-run; tier=drop; rationale=Dropped because the thing it tests is itself out of scope. A six-call, seconds-long backfill has no hour six to resume from, and write-once skip-if-present is the checkpoint at this volume for free. Building a checkpoint-store seam so it can be tested is exactly the infrastructure-sized-past-its-workload that ADR 0001:18-21 names as reading like poor judgment. Revisit at Phase 5 (~30,000 play-by-play calls), which docs/data-sources.md:50-52 already names as where the rate-limit engineering earns its keep.}

- @{title=A season-phase model rich enough to make 2019-20 answerable (pre-suspension / bubble, pre/post All-Star); tier=gated; rationale=Part of the dim_date decision and gated with it. The argument for is genuine — a date dimension built without a March-to-October season in front of it gets rebuilt when one arrives. The argument against is that every attribute it carries is a judgment call with no consumer in this slice able to validate it, and this repo's posture is not inventing facts. MY RECOMMENDATION: no in this slice; the irregular-season property that actually matters here is already covered by the cheap-fold assertion test on 2019-20's unequal game counts and out-of-window dates.}

- @{title=A separate ADR on SCD2 interval-boundary semantics; tier=cheap_fold; rationale=Open Question 3 is a genuine architectural decision with a cost either way, and docs/decisions/README.md requires the cost section be uncomfortable to write — this one is: snapping valid_from to the first game with the new team means an in-gap date resolves to a team the player had already left. It is also the decision most likely to be revisited when roster data makes the true transaction date knowable, which is precisely what ADRs exist to make legible later. Two short ADRs rather than one.}

- @{title=Reconcile the repo's three disagreeing epistemic-label vocabularies; tier=gated; rationale=The drift is real and verified: CLAUDE.md names five labels (measured/verified/inferred/assumed/unconfirmed), docs/data-sources.md:5-8 names three (verified/documented/unconfirmed), and the update-docs skill names a fourth set including `documented`. This request's headline deliverable is promoting labels in docs/data-sources.md, so doing it against three inconsistent vocabularies bakes the inconsistency in. But it touches CLAUDE.md and a skill file — repo governance, not pipeline — and this slice is already the largest the repo has taken. MY RECOMMENDATION: no; file it as its own tiny request, and in this slice use docs/data-sources.md's own three-label vocabulary since that is the file being edited.}

- @{title=Layer-promotion gates expressed as tagged dbt selectors; tier=cheap_fold; rationale=dbt_project.yml:32,40,47 already assigns bronze/silver/gold tags and the file's own comment at :18-19 already says promotion is gated on tests. Documenting `dbt build --select tag:bronze` then `tag:silver` as the sequence turns that comment into a runnable gate and hands the eventual Airflow DAG (Phase 3) its natural task boundaries. A few lines of documentation.}

- @{title=A shared bronze casing/typing macro instead of hand-written column lists in two models; tier=drop; rationale=Premature at two models. An abstraction introduced before its second real consumer exists tends to encode the first consumer's shape, and the next endpoint is not a leaguegamelog. It is also the infrastructure-not-practice kind of over-engineering ADR 0001:18-21 explicitly declines. Revisit at the third bronze model, when the shared shape is observed rather than predicted.}

- @{title=Build this feature through the data-engineer subagent as its first real target; tier=gated; rationale=A stage-3/4 dispatch decision with a scope-stage prerequisite, so it goes to the human. Two grounded facts either way: the agent's memory file is at 116 lines against its 120-line cap (MEASURED this session; the cap and the no-self-pruning rule are at .claude/agents/data-engineer-memory.md:56-65), so a build of this size will hit 'memory at cap, pruning needed' on the first handoff and pruning is a main-thread action; and docs/data-sources.md is in the agent's deny set, so the label promotion is a main-thread step regardless. MY RECOMMENDATION: yes, with a main-thread memory-pruning pass scheduled BEFORE the build starts, otherwise the knowledge this build generates is simply lost.}

- @{title=Call the endpoint directly with a thin typed client rather than through nba_api; tier=gated; rationale=Raised for decision, not recommended blindly, and correctly so. Real tension: README.md:29 and docs/data-sources.md:14 commit to nba_api in prose but no ADR does; nba_api brings pandas into a repo with zero runtime dependencies (verified: pyproject.toml:9 is empty and uv.lock has no nba_api/pandas/httpx); and if the landing writer stores a DataFrame round-trip, the 'immutable raw' is a re-serialization, weakening the diff-against-raw invariant at transform/models/bronze/README.md:17-20. Against that, nba_api encodes the header and parameter knowledge that keeps a client from being blocked — exactly the undocumented knowledge this project should not re-derive. MY RECOMMENDATION: keep nba_api, but land its RAW JSON response path, not the DataFrame path, and say so in the landing ADR. That resolves the invariant tension without re-deriving the header set.}

- @{title=Emit dbt docs generate lineage as a CI build artifact; tier=drop; rationale=Cheap in isolation, but it adds a CI step that can fail on the same PR that already flips sqlfluff from skipped to live and adds the repo's first runtime dependency — three new ways for a required check to redden at once. And nothing consumes the catalog until Phase 4 serving. Dropped for this slice, not on merit; it becomes near-free once the models are stable.}

- @{title=A landing-zone layout convention document under docs/; tier=cheap_fold; rationale=Right content, wrong container — fold it into the landing-layout ADR rather than a separate doc, so there is one place the decision lives and the ADR index points at it. var/ is gitignored so the layout is invisible to anyone reading the repo, and it is the one structure every future extraction request must conform to. Cheapest possible way to stop the second dataset inventing a second layout.}

- @{title=Mechanize landing immutability as a repo-level guard, not only a unit test (from the repo-fit scoper); tier=cheap_fold; rationale=tests/test_repo_structure.py:1-9 states the repo's own philosophy: invariants agents are told about in prose get violated, so they are checked mechanically. Immutability is the most load-bearing prose invariant this slice introduces. The double-run hash comparison is already a core acceptance criterion; extending it to a guard over a landed tree costs almost nothing and turns the invariant into something CI can lose sleep over.}

- @{title=Record the measured cost table as data rather than prose (from the repo-fit and minimalist scopers); tier=cheap_fold; rationale=Gate 0 already measures calls, rows and wall clock. Writing those numbers into docs/data-sources.md:41-48 as a dated, `verified` table turns the repo's single most load-bearing unconfirmed belief into a citable fact and gives the widening a real number to plan against instead of a re-guess. Near-zero marginal cost once the probe exists — but it must be a main-thread /update-docs edit, since that path is denied to the builder.}


## Risks & Unknowns

Carried verbatim. **R1 is retired by Gate 0** - the bulk-endpoint belief is now `verified`.

- R1 — THE BULK-ENDPOINT BELIEF FAILS, AND IT GATES EVERYTHING. docs/data-sources.md:46-48 is explicitly `unconfirmed` and the spread is ~50 calls versus ~60,000, ~1 minute versus ~10 hours (:41-44), against a source that BLOCKS rather than throttles (:24-27) where a block is not distinguishable from a transient failure — so a naive retry loop makes it worse. A third possibility neither the request nor the catalog considers: the endpoint may PAGINATE or cap at a `Counter` parameter, which is neither 'bulk' nor 'per-game'. Mitigation: Gate 0 with an explicit stop-and-rescope branch; do not let it run in parallel with modeling.

- R2 — MEASURED, AND THE LARGEST OPERATIONAL RISK: stats.nba.com does not respond from the agent environment. Independently reproduced this session (Invoke-WebRequest with browser-like headers, timed out at 20s) and consistent with the ambitious scoper's three curl probes returning http=000 while example.com returned 200. This does not settle reachability from the user's machine, but it means Gate 0, the backfill and the fixture capture must all be planned as USER-RUN. A plan that assumes an agent can call the endpoint stalls at step one.

- R3 — THE FIRST BRONZE MODEL REDDENS A REQUIRED CHECK IN A WAY THAT LOOKS UNRELATED. ci.yml:76 builds --target ci on in-memory DuckDB (profiles.yml:23-27) from a checkout where var/ is gitignored (.gitignore:16), and 'dbt build' is a required context (ops/branch-protection.json:4), so the PR cannot merge. The failure presents as a file-not-found naming a path CI was never going to have, and reads as a model bug rather than missing fixture plumbing. sqlfluff compounds it: it activates on the first .sql (ci.yml:78-85) and templates through dbt at target = ci (.sqlfluff:12-16), so it fails on the same unresolved source.

- R4 — THE sqlfluff STEP FLIPS FROM SKIPPED TO RUNNING against rules nothing in this repo has ever been linted under: duckdb dialect, lowercase keywords/functions/identifiers, explicit table AND column aliasing, trailing commas, 100-char lines (.sqlfluff:5-39). Expect the first red build to be style, not logic. Already recorded in the agent memory (.claude/agents/data-engineer-memory.md:79) that sqlfluff errors rather than no-ops on an empty selection, which is why the guard exists.

- R5 — dim_team IS A SECOND SCD PROBLEM HIDING BEHIND THE FIRST, AND THE REQUEST NEVER MENTIONS IT. Team identity drifts inside the chosen pilot: Seattle SuperSonics and Oklahoma City Thunder share a team_id; New Jersey became Brooklyn; Bobcats became Hornets; the Katrina-era New Orleans/Oklahoma City Hornets changed city and back. (Inferred from domain knowledge, unverified in this repo — confirm at Gate 0 by counting distinct (team_id, team_name) pairs across the landed seasons.) A dim_team built as `select distinct team_id, team_name, team_abbreviation` over a pilot spanning 2003-04 and 2024-25 emits multiple rows per team_id and either fails its uniqueness test or, worse, gets 'fixed' with an arbitrary dedup that silently picks one name.

- R6 — THE AFFILIATION CONTAINMENT TEST IS WEAKER THAN IT LOOKS, AND ALL THREE SCOPERS LEAN ON IT. dim_player_team_stint is derived from the same (game_date, team_id) observations the test then checks, so a zero-row result proves the run-collapsing logic did not lose or reorder observations — it CANNOT detect a wrong interpolation inside the trade gap, where there are no observations at all. The test is vacuous everywhere between game dates, and that limitation must be stated in the model description rather than left implicit. The fixture-pinned known-trade test is the non-vacuous companion and is why it is a separate criterion.

- R7 — SCD2 GAP SEMANTICS PRODUCE SILENTLY WRONG JOINS EITHER WAY. A trade is only known to have happened somewhere between the last game with team A and the first with team B — a window that can exceed a week across an All-Star break. Contiguous intervals make an in-gap date resolve to a team the player had already left; observation-bounded intervals make it resolve to NOTHING, which FEATURE_REQUEST.md:190-191 correctly names as the answer most likely to be silently wrong downstream. Partial mitigation baked into core: fact_player_game's team_id is taken from the observed box-score row, so the stint table is a lookup surface and never on the fact-correctness join path. Residual risk accepted: any future consumer doing an as-of join must handle its chosen failure mode, and nothing in this slice forces them to.

- R8 — dim_player WILL COVER FEWER PLAYERS THAN ITS NAME IMPLIES, AND WILL BE READ AS IF IT DOES NOT. Affiliation derived from appearances cannot see a rostered player who never played — injured all season, deep bench, G-League two-way. Narrower still: the log is believed to include only players with recorded stats, so a DNP-but-active player may also be invisible (inferred, unverified — a Gate 0 question). The hazard is naming as much as modeling, in a repo whose premise is that docs are authoritative. Mitigated by the persisted description and a first_observed_game_date column, not eliminated.

- R9 — LANDING-ZONE RE-RUN SEMANTICS ARE UNDECIDED AND BOTH PLAUSIBLE CHOICES ARE WRONG IF UNSTATED. If a re-run writes a new timestamped payload per call, bronze sees N copies of the same season and row counts silently multiply unless it dedups on the natural key with a deterministic tiebreak. If a re-run overwrites, the immutability invariant that makes incident triage tractable (CLAUDE.md; docs/data-sources.md:31-33) is broken. This is where immutability and restatement collide, and getting the tiebreak wrong means bronze silently serves a stale version of a corrected box score while the landed evidence says otherwise — precisely the bronze-is-wrong case transform/models/bronze/README.md:17-20 builds triage around.

- R10 — TOOLCHAIN BREAKAGE FROM THE FIRST RUNTIME DEPENDENCY, THREE DISTINCT WAYS. `uv sync --locked` (ci.yml:39) fails unless uv.lock is regenerated in the same commit (verified: pyproject.toml:9 is empty and uv.lock has no nba_api/pandas/httpx, only a transitive `requests`). mypy runs strict over src AND tests (pyproject.toml:70-74) with no override block present, and an untyped third-party surface — or pandas Any-leakage — errors unless isolated at one declared boundary rather than discovered as a hundred type: ignores. ruff selects DTZ (:58), so any naive datetime from date parsing or capture timestamping is a lint error, and PTH (:59) makes os.path one too.

- R11 — FIXTURE-BASED CI PROVES THE GRAIN ON A SAMPLE, NOT ON A SEASON. A (game_id, player_id) duplicate that exists only in a full 2019-20 pull would pass every automated check. This is why the full-pilot criterion is marked user-run, and why treating CI green as proof of the grain is the most dangerous mistake available in this slice.

- R12 — FIXTURE FIDELITY VERSUS FIXTURE SIZE PUTS TWO REPO RULES IN TENSION. tests/fixtures/README.md:11-13 says fixtures are real responses never hand-written; :41-44 says trim them small for a public repo. Trimming IS editing, and a trim that drops the resultSets/headers envelope produces a fixture that tests a shape the API does not return — the exact assumption most likely to be wrong. Meanwhile a trade-spanning SCD2 test needs a specific player's full season across two teams, so too-small fixtures make tests pass on empty sets. Mitigation: trim rows only never structure, record trim provenance, and give every fixture-backed test a row-count floor assertion.

- R13 — EVERY FIXTURE IS A FROZEN COPY OF AN UNVERSIONED CONTRACT. docs/data-sources.md:17-19 states endpoints change shape without notice and occasionally disappear. Fixtures make CI hermetic and simultaneously blind: the pipeline stays green for months after upstream renamed a column. The network-marked live contract test is the only counter-pressure, and it only runs when someone remembers.

- R14 — THE FULL-REFRESH TRAP, WHICH THE REQUEST ITSELF FLAGS (FEATURE_REQUEST.md:197-200). Full refresh is CORRECT for three finalized historical seasons and WRONG the moment 2025-26 is added, because box scores are restated for days (docs/data-sources.md:96-100). It also means the repo's first fact table contradicts its most prominently documented data-layer rule (CLAUDE.md; transform/models/silver/README.md:47-48), which /update-docs audits. Mitigation: record the deferral with a named trigger in both the scope and the model description.

- R15 — SEASON TYPE, IF NOT PINNED, BREAKS THE FIRST WIDENING SILENTLY. SeasonType is a required parameter on this endpoint family and game_id prefixes distinguish preseason/regular/playoff/all-star (both inferred, unverified). Unpinned in the call and uncarried as a column, a widening that adds playoffs either double-counts season totals or is silently dropped by a filter nobody documented.

- R16 — THE docs/data-sources.md RELABEL WILL SILENTLY NOT HAPPEN if the work is executed by the data-engineer agent, which is denied that path (.claude/agents/data-engineer.md:131) and routes facts through `## docs-delta` (:220-225). FEATURE_REQUEST.md:51-53 counts that relabel as an observable success signal. Related: a BLANKET promotion is the tempting mistake and would destroy the one property that file has — endpoints this request does not call must stay `unconfirmed`.

- R17 — SCOPE MASS. This is the largest single request the repo has taken: the first extraction code, the first landing zone, the first bronze models, five silver models, the first fixtures, the first singular tests, the first runtime dependency, and doc changes across four files plus new ADRs. ADR 0001 names exactly this failure — 'a platform elaborate enough to never produce an actual basketball insight would fail both goals at once' — and prescribes vertical slices. Defensible only if the ordering is strictly probe → land → bronze → one fact end-to-end → widen, each green before the next. A horizontal build that writes all five silver models before any of them has run is how this stalls.

- R18 — SCOPE CREEP BACK INTO THE CUT ITEMS. dim_date, fact_team_game, the reconcile test, the 23-season widening and checkpointing are each individually cheap-looking and collectively double this slice. The success condition is a green build and a correct traded-player lookup, not breadth.

- R19 — DOC DRIFT IS A MERGE BLOCKER HERE, NOT A CLEANUP TASK. This slice invalidates README.md:11-14's Phase-0 blockquote, :130's roadmap row, CLAUDE.md's 'No pipeline code yet' line, and docs/data-sources.md's epistemic blockquote at :5-10. Separately, docs/data-sources.md:69 references docs/data-dictionary.md which does not exist (verified via `git ls-files docs`) and tests/test_doc_links.py cannot catch it because the reference is backticked rather than linked — a silently dangling promise in the file whose entire purpose is epistemic honesty.

- R20 — THE PILOT EXERCISES NO IN-PROGRESS SEASON. 2003-04, 2019-20 and 2024-25 are all finalized, so nothing in this slice tests a partially-played season, live stat corrections, or a season whose game list grows between runs — the exact conditions that make full-refresh wrong the moment 2025-26 arrives.

- R21 — THE 2013-14 TRACKING BOUNDARY IS EXPECTED NOT TO BITE, AND THAT EXPECTATION IS UNCONFIRMED. docs/data-sources.md:59 puts traditional box scores at 1946-47 with the whole table labelled unconfirmed. If the player-grain log carries any tracking-derived or advanced column, era-nullable handling re-enters scope mid-build. PLUS_MINUS is the column most likely to have its own earlier cliff (FEATURE_REQUEST.md:140-142) and must be checked against 2003-04 by name.


## Affected Area & Pointers

What the stage-3 planning agent should read first, carried from the panel's grounding pointers.

- TARGET COMPONENTS (all currently empty or scaffold-only — verified via `git ls-files`): src/nba_platform/ (holds only __init__.py), transform/models/bronze/ and transform/models/silver/ (READMEs only, zero .sql), tests/fixtures/ (README only, zero fixtures), transform/tests/ (README only), and transform/seeds/ (does not exist yet; .gitignore:32 already whitelists its CSVs).

- requests/feature-requests/box-score-foundation/FEATURE_REQUEST.md — the request itself, in full. Its Affected Area table (:99-105), read-first ordering (:107-113), pilot-season rationale (:115-124), Data Contracts (:126-148) and seven Open Questions (:169-206) are the substrate this scope decides against.

- docs/data-sources.md — READ FIRST per the request. The catalog of beliefs this work exists to test: epistemic blockquote (:5-10), rate limiting (:22-27), the bulk-vs-per-game cost table (:37-52, the belief Gate 0 settles), era availability (:54-69, including the dangling docs/data-dictionary.md reference at :69 — that file does not exist), irregular seasons (:73-83), stat corrections (:96-100), player identity and affiliation (:102-107).

- transform/models/silver/README.md — the layer contract and the worked example this slice is written against. The grain-declaration block at :13-23 is what every silver model gets copied from, including the load-bearing `data_tests:` key and `arguments:` nesting (:29-32). The hard parts are pre-named at :36-48; the naming convention at :50-53 lists dim_player and does NOT mention a stint table, so the recommended split obliges editing this file in the same change.

- transform/models/bronze/README.md — the 1:1 rules (:8-15), the bronze-is-wrong invariant that makes incident triage tractable (:17-20), the bronze__<source>__<endpoint> naming (:23), and what must go in schema.yml as the source contract (:28-34).

- CLAUDE.md — the Data Layer section (resolve by name; landing zone immutable; bronze 1:1; silver declares AND proves its grain; facts MERGE-on-key; no bulk data in git), Project Conventions (commits through /commit only; subagents get read-only git; label your epistemics), and Constraints & Gotchas (pacing; prefer bulk endpoints; affiliation is date-dependent; renaming a CI job breaks branch protection; Windows dev / Linux CI).

- THE CI SEAM — read these four together, they are what the first model must satisfy: .github/workflows/ci.yml (:39 `uv sync --locked`, :53 pytest -m "not network", :73-76 `dbt build --target ci`, :78-85 the sqlfluff skip-guard that this slice flips live), transform/profiles.yml (:15-27, local is a var/ DuckDB file and ci is :memory:), ops/branch-protection.json (:4, the three required check display names), and .sqlfluff (:12-16 templates through dbt at target = ci; :26-39 the lint rules nothing has been linted under yet).

- transform/dbt_project.yml — layer schemas, +materialized: table, tags and +persist_docs (:20-47), and `data_tests: +severity: error` (:49-53), which makes a dbt WARNING a red build.

- transform/packages.yml and transform/package-lock.yml — dbt_utils pinned at 1.4.1 specifically because unique_combination_of_columns is how every silver model proves its grain. mutually_exclusive_ranges.sql and unique_combination_of_columns.sql are both present in the resolved package; dbt_packages/ is gitignored (.gitignore:50) and CI restores it via `dbt deps` (ci.yml:70-71).

- pyproject.toml — dependencies = [] at :9 with the comment saying extraction arrives with the source that needs it; ruff selection including DTZ and PTH (:48-64); mypy strict = true over src and tests with no override block (:69-74); the unused `network` pytest marker (:76-82).

- uv.lock — verified to contain no nba_api, pandas or httpx (only a transitive `requests`). Must be regenerated in the same commit as the dependency addition or ci.yml:39 goes red.

- .env.example — the config keys the config layer must read by name: NBA_ENV (:8), NBA_REQUEST_DELAY_SECONDS=0.6 and NBA_MAX_RETRIES=5 (:14-15), and the commented Phase-2 cloud block (:17-28) showing the shape the landing layout should anticipate.

- tests/fixtures/README.md — fixtures are real responses never hand-written (:11-13), the five cases to capture (:17-26), the <source>/<endpoint>/<descriptive-case>.json layout (:27-35), and the size discipline (:39-44).

- transform/tests/README.md — the singular-test invariants this slice draws from (:12-18, note :16 names 'dim_player's SCD2 history', which the recommended split changes), what does NOT belong here (:22-26), and the assert_<what_must_be_true>.sql naming (:28-33).

- tests/test_repo_structure.py and tests/test_doc_links.py — the structural guards that must stay green through every model and doc edit. Note test_repo_structure.py:19 uses parents[1]; that is a test-file locator and must NOT be copied as precedent for src/.

- .gitignore — var/ (:16), the blanket data ban (:18-29), and the three whitelists this slice depends on: tests/fixtures/**/*.json (:30), tests/fixtures/**/*.csv (:31), transform/seeds/**/*.csv (:32).

- docs/decisions/ — 0001 (over-engineer practices, right-size infrastructure; the vertical-slice rule and the 'never produces an insight' failure mode), 0002 (the 2003-04 floor, the one availability boundary, the three irregular seasons), 0003 and 0004 (Iceberg and Snowflake, accepted but Phase 2 — this slice's DuckDB materialization is a declared deferral, not a contradiction), 0007 (the write-capable implementation subagent), and README.md's ADR format and Index that a new ADR must join.

- .claude/agents/data-engineer.md and .claude/agents/data-engineer-memory.md — the builder's rulebook if this is dispatched to the subagent. The repo-level deny set at :123-133 (docs/data-sources.md is denied) and the docs-delta routing at :216-230 determine who performs the label promotion. The memory file is at 116 of its 120-line cap (MEASURED), and the no-self-pruning rule is at :56-65.

- README.md — the Phase-0 status blockquote (:11-14), the architecture table naming nba_api and immutable partitioned JSON (:27-34), the provenance note on redistributing no NBA data (:62-65), and the roadmap (:125-134) whose Phase 1 row this request is.

## Decisions

The disposition record. All eleven gated decisions were disposed by the user on 2026-08-14 —
four individually, six accepted en bloc at the panel's recommendation, and one resolved by Gate 0
evidence rather than judgment.

**1 — Build `fact_team_game` and the reconcile test.** Reverses the request's explicit
*"Explicitly out"* line at `FEATURE_REQUEST.md:78`, which is why it was gated rather than folded.
The request's own cut line was internally inconsistent: it fenced the fact out while requiring the
team-grain pull. The team payload is landed and bronzed regardless, so the marginal cost is one
silver model of nearly the same shape plus ~15 lines of SQL. What it buys is the **only cross-grain
correctness proof available** — for every team-game, the sum of player points equals the team total
— which catches join fan-out, dedup failure and mis-resolved affiliation in one assertion. It is
also the repo's own canonical example of a testable criterion. Without it the pilot ships with no
cross-grain check at all.

**2 — SCD2 affiliation splits into its own stint model.** The strongest convergence in the panel:
all three scopers, from three different arguments. The decisive one — a table that is sometimes
one-row-per-player and sometimes one-row-per-stint **cannot state a single true grain** in its
`schema.yml`, which is exactly the mis-documented case the declare-and-prove rule exists to catch.
A split also lets an identity lookup join without carrying a validity predicate, and the join that
forgets the predicate is the one that fans out silently. **Cost, accepted explicitly:**
`transform/models/silver/README.md:52` and `transform/tests/README.md:16` both currently assume
the other answer and must be edited **in the same change**; `/update-docs` audits exactly this.

**3 — SCD2 intervals are contiguous and gapless, with the observed boundaries carried.**
`valid_from` snaps to the first game with the new team, so an as-of join never returns zero rows —
and `last_game_prior_team` / `first_game_new_team` ride along as columns so the interpolation stays
visible and falsifiable. This split the panel; the tie-break is which failure is more dangerous.
*"Nothing"* is the answer the request itself names as most likely to be silently wrong, because an
empty as-of join disappears while a stale team at least looks like a team. Two things must be
written down alongside it: that **a date inside a trade gap deliberately resolves to the OLD team**,
and that the containment test is derived from the same observations it checks — so it proves the
run-collapsing lost or reordered nothing, but is **vacuous everywhere between game dates**. The
fixture-pinned known-trade test is what makes it non-vacuous. **This decision earns its own short
ADR.**

**4 — `dim_date` is out**, and not replaced by a hand-authored season registry either. `dim_game`
carries `game_date`, nothing in this slice consumes a date dimension, and every attribute that
would justify one — bubble flags, pre/post All-Star, season phase — is a judgment call no test in
this slice could falsify. A dimension whose columns cannot be proven wrong is not something this
repo should ship, and a seeded registry authored from memory would be fabricated facts in a repo
whose entire posture is epistemic labelling. **This contradicts the request's own Scope Signals**
(`FEATURE_REQUEST.md:73` lists it as in), so it is recorded as a deliberate cut with a trigger:
build it with the first gold mart that needs it.

**5 — Full-refresh, with the trigger named in three places** — this scope, the model description,
and the widening's follow-on. All three pilot seasons are long finalized, so restatement is not a
live concern and full-refresh is genuinely correct. But it must be said out loud that **the repo's
first fact table contradicts the repo's most prominently documented data-layer rule**, and
`/update-docs` audits exactly that kind of divergence — an undeclared one becomes debt the moment
it stops being written down. Declare `unique_key` now so the switch is a config change. The
trigger, as a sentence a future reader inherits: *the first in-progress season, or the first
nightly run, requires MERGE first.*

**6 — Keep three pilot seasons**, with the season list config-driven so widening is a parameter
change rather than a code change. Gate 0 retired the cost argument — 23 seasons is ~46 calls and
under a minute — but widening does not only add calls: it adds twenty seasons of unexamined era
behaviour, franchise identity events and column drift to a slice already carrying the first
extraction code, the first landing zone, the first bronze models, the first fixtures and the first
runtime dependency. The three are chosen to hit boundaries, not to be representative. Widen as a
follow-on with no new model code.

**7 — Cut the standalone checkpoint store**, explicitly rather than by silent omission. A
six-call, seconds-long backfill has no hour six to resume from; **write-once skip-if-present *is*
the checkpoint** at this volume, and it is free because the landing writer needs that behaviour for
immutability anyway. Building a checkpoint seam so a resume test can exist is infrastructure sized
past its workload — the precise failure ADR 0001 names as reading like poor judgment. The
counter-argument is recorded: play-by-play is ~30,000 calls, and getting the seam right against a
tiny dataset is cheaper than retrofitting — but `docs/data-sources.md` already places that
engineering at Phase 5 by name, so deferring follows the repo's own plan. Note that
`src/nba_platform/__init__.py`'s docstring promise of checkpointing stays a forward-looking
statement, not yet delivered.

**8 — Keep `nba_api`, and land its raw JSON response, not a DataFrame round-trip.** If the landed
payload is a pandas re-serialization then "immutable raw" is not raw, which weakens the
diff-against-raw invariant bronze builds incident triage on. **Gate 0 turned this from an argument
into a measurement:** raw HTTP to `stats.nba.com` times out from here while `nba_api` succeeds in
0.6s — the "undocumented header knowledge a client needs to avoid being blocked" is real, and
`nba_api` carries it. The dependency-weight objection (pandas into a repo with zero runtime
dependencies) is genuine but secondary; note it in the landing ADR.

**9 — Build through the `data-engineer` subagent, with a main-thread memory prune scheduled
first.** This is the work the agent was built for and the sequence the predecessor scope intended.
Two non-negotiable main-thread prerequisites: the memory file is at **115 of its 120-line cap** and
the agent is correctly forbidden from pruning to make room, so a build of this size would report
*"memory at cap, pruning needed"* on the first handoff and everything learned after that is lost —
**prune before the build starts**; and the `docs/data-sources.md` relabel targets a **denied path**,
so it must appear in the plan as an explicit main-thread `/update-docs` step, not a build task. One
caution carried forward: proving the agent and *then* using it here is the right order — using it
here *in order to* prove it is not.

**10 — Correct the dangling `docs/data-dictionary.md` reference; do not create the file.**
**Resolved by Gate 0 evidence rather than judgment.** The panel asked for the decision to be made
at Gate 0: create the dictionary if any landed column has its own availability cliff, correct the
sentence if none does. None does — `PLUS_MINUS` is present in 2003-04 with zero nulls and no
tracking-derived column appears in this endpoint. A dictionary recording era-bounded columns would
be a file with nothing in it. The reference is backticked rather than a Markdown link, so
`tests/test_doc_links.py` structurally cannot catch it — a silently dangling promise inside the
file whose entire purpose is epistemic honesty. **It must not survive this slice.**

**11 — File the epistemic-vocabulary reconciliation separately**, and use `docs/data-sources.md`'s
own three-label vocabulary for this slice's promotions. The drift is real and verified: `CLAUDE.md`
names five labels, `docs/data-sources.md` names three, and the `/update-docs` skill names a fourth
set including a `documented` that is not among `CLAUDE.md`'s five. But the fix touches `CLAUDE.md`
and a skill file — repo governance rather than pipeline — and this slice is already the largest the
repo has taken. Using the target file's own vocabulary means this work **adds no new
inconsistency** while it waits.

## Panel Trail

The Gate 0 probe, and the correction to the panel's unreachability finding:
[`reviews/gate-0-endpoint-probe.md`](reviews/gate-0-endpoint-probe.md) — tracked.

The raw panel output is **gitignored and machine-local**: `reviews/scope-proposals.md` (the three
divergent scopers) and `reviews/scope-adversarial.md` (the adversary findings and the convergence
map). They are referenced as inline code rather than as links precisely because they are not in a
fresh clone, and a link to a file CI does not have turns the link checker red. Everything the panel
produced that this scope depends on — goals, non-goals, acceptance criteria, the tiered scope,
above-and-beyond, risks and grounding pointers — is carried **verbatim above**, so the tracked
artifact stands alone.

Panel health: **3/3 scopers, 2/2 adversaries, no degraded lenses** — 59 findings (8 blockers, 25
majors), 13 themes with unanimous three-scoper convergence. Panel content in the trail files is
fenced because it contains Markdown link syntax that does not resolve from `reviews/`.
