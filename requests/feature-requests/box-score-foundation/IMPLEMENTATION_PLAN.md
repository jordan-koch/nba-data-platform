> **Status:** implemented · created 2026-08-15 · decided · next: commit
>
> Built 2026-08-15. Outcome, deviations and the acceptance ledger are in
> [`IMPLEMENTATION_REPORT.md`](IMPLEMENTATION_REPORT.md). Four numbers in this plan were corrected
> by measurement during the build — see the report's Deviations section.

# Implementation Plan — Box-Score Foundation

> **One-line goal:** the repo's first vertical data slice — `nba_api` → an immutable,
> manifest-audited landing zone under `var/` → two `leaguegamelog` bronze models behind **one**
> target-aware source seam → six silver models, each declaring its grain in prose and proving it
> with a test. · **Target component:** `src/nba_platform/` (net-new), `transform/models/bronze/`
> and `transform/models/silver/` (net-new), `tests/` + `tests/fixtures/`, `docs/`.

**Gold stays empty.** This slice terminates at a tested silver layer — a declared divergence from
*"vertical slices, not horizontal layers"*, recorded in the scope and not re-opened here.

## 0. Before you start — four things that will bite you

Read these before Phase 0. Each is measured, not inferred, and each was found by an adversary
rather than by the planners.

**1. The agent's memory file is full.** `.claude/agents/data-engineer-memory.md` is at **115 of
its 120-line cap** (measured 2026-08-15; the guard is `tests/test_agent_contract.py`). The agent
is *correctly forbidden* from pruning to make room, so on a build this size its first handoff
reports *"memory at cap, pruning needed"* and **everything it learns after that is lost**.
Decision 9 makes a main-thread prune a non-negotiable prerequisite — it is Phase 0, step 1, and
it is not optional.

**2. `docs/data-sources.md` is partly done already, and its line numbers moved.** The
`leaguegamelog` bulk claim was promoted `unconfirmed` → `verified` during the scoping commit, and
two falsified statements were corrected there (that file's Phase 0 blockquote, and `CLAUDE.md`'s
copy of the same claim). **Do not re-do those.** Still outstanding: decision 10's dangling
`docs/data-dictionary.md` reference, now at **`:85`, not `:69`** — the scope's citation is stale
because the promotion shifted the file. Every write to that path is **main-thread**; it is
write-denied to the agent, which reads it freely.

**3. Gate 0 is complete, but only after a correction.** The first probe called 2003-04 and
**2023-24 — not a pilot season** — and never called 2019-20. A completion probe on 2026-08-15
closed the gap: all three pilot seasons now measured, plus the envelope questions
(`GAME_ID` is a zero-padded **string**, `MIN` is **`int64`** not `MM:SS`, DNP rows exist carrying
`MIN == 0`, and Decision 8's raw-JSON accessor is confirmed via `get_dict()`). See
[`reviews/gate-0-endpoint-probe.md`](reviews/gate-0-endpoint-probe.md). **Phase 3 is
correspondingly smaller than the panel drafted it** — the reachability and column-contract
questions are settled; what remains there is playoffs, the trade pin, and the fixture corpus.

**4. Four blocker corrections are applied inline below.** Where a phase step carries a
**`[CORRECTED — binding]`** clause, that clause supersedes the sentence before it. They are not
suggestions; each is a case where following the drafted text produces a red required check or
silently reverses a disposed decision.

## 1. Onboarding — read these first

The platform can answer zero basketball questions today: `git ls-files src transform tests` returns one Python module, four READMEs under transform/, four dbt config files, four guard-test modules and a fixtures README — zero .sql, zero fixtures, zero extraction code. This slice creates all of it, end to end, for one endpoint family (`leaguegamelog`) across three pilot seasons. Its real purpose is the affiliation model: no endpoint returns player-team history as a time series, so `dim_player_team_stint` must be DERIVED from observed box-score rows — which is why facts must land before the dimensional core, and why the pinned known-trade test (AC 10) is the only non-vacuous proof the derivation is right. Everything in PROJECT_SCOPE.md is DECIDED (fit `clean`, 30 acceptance criteria, 11 disposed decisions); this plan consumes it and does not reopen it.

| Path | Why |
|---|---|
| `requests/feature-requests/box-score-foundation/PROJECT_SCOPE.md` | The decided upstream artifact. Goals/Non-Goals :88-149, the 30 numbered acceptance criteria :151-213, tiered Core :220-252, cheap folds :254-280, risks R1-R21 :338-383, Affected Area & Pointers :385-425, and the eleven disposed Decisions :427-534. Decisions 1-11 are settled — fact_team_game IN, stints split out of dim_player, contiguous+gapless intervals with observed boundaries carried, dim_date OUT, full-refresh with a named MERGE trigger, three config-driven pilot seasons, no checkpoint store, nba_api landing RAW JSON, subagent build after a memory prune, correct-don't-create the data-dictionary reference, defer the vocabulary reconciliation. |
| `requests/feature-requests/box-score-foundation/reviews/gate-0-endpoint-probe.md` | The only measured endpoint evidence. Read all 117 lines. :3-5 the bulk belief is `verified`; :52-57 measured rows/games/dupes; :72-75 (GAME_ID, PLAYER_ID) has zero duplicates in both probed seasons; :77-81 PLUS_MINUS present in 2003-04 with zero nulls so the 2013-14 boundary does not bite; :83-86 the return shape is a pandas DataFrame via `get_data_frames()[0]`; :95-99 the exact 29-column team / 32-column player lists; :104-116 WHAT IT DID NOT SETTLE — 2019-20 never called, playoffs never called, nothing about rate limiting, no files written. |
| `transform/models/bronze/README.md` | The bronze layer contract, 33 lines. :10 'No joins. A bronze model reads exactly one source' — this is what forces capture provenance to come from the PATH rather than a join to the manifest sidecar. :11-15 no business logic / no renaming beyond casing / no filtering. :17-19 the bronze-is-wrong invariant AC 13 mechanizes. :23 the `bronze__<source>__<endpoint>` naming. :30-33 what schema.yml must declare as the source contract. |
| `transform/models/silver/README.md` | The template every silver model is copied from. The grain-declaration block :13-23, and the two load-bearing details at :28-32 — the key is `data_tests:` (renamed from `tests:` in dbt 1.8) and generic-test arguments nest under `arguments:`. Hard parts pre-named :38-48, including :47-48 'Facts here are MERGE-on-key, not append-only' which this slice deliberately diverges from. :52 lists dim_player/dim_team/dim_game/dim_date and names no stint table — Decision 2 obliges editing that line in the same change. |
| `transform/tests/README.md` | The singular-test invariant menu this slice draws from (:12-18), what does NOT belong here (:22-26), and the `assert_<what_must_be_true>.sql` naming with `assert_player_points_reconcile_to_team.sql` as the canonical example (:28-33). :16 says the SCD2 history lives in `dim_player` — stale under Decision 2 and must be edited alongside the stint model. |
| `.github/workflows/ci.yml` | The gates, 99 lines. Three job display names pinned by ops/branch-protection.json:4 — `Lint, types, tests` (:27), `dbt build` (:56), `Secret scan` (:88). `uv sync --locked` (:39). The pytest command AC 1 must match byte-for-byte (:53). `dbt deps` (:70-71). The dbt command AC 2 must match (:76). The sqlfluff skip-guard (:78-85) that this slice flips from skipped to live on the first .sql file. |
| `transform/profiles.yml` | Two targets that differ exactly where the first bronze model breaks: `local` is a DuckDB file at `../var/warehouse/nba_local.duckdb` (:15-22, path at :17) under the gitignored var/ root, and `ci` is `:memory:` (:24-27). CI has no var/, so the bronze source MUST resolve to committed fixtures under `--target ci`. |
| `pyproject.toml` | Every toolchain constraint the first runtime dependency trips. `dependencies = []` at :9 with the now-false comment at :11-13; ruff selects DTZ (:58, naive datetimes are errors) and PTH (:59, os.path is an error); mypy `strict = true` over `files = ["src", "tests"]` at :70-74 with NO override block; the unused `network` marker at :80-82 that the completion probe and live contract test claim. |
| `tests/fixtures/README.md` | Fixtures are real responses never hand-written (:11-13), the five cases to span (:19-25), the FLAT `<source>/<endpoint>/<descriptive-case>.json` layout (:27-34) that cannot express AC 15's two-captures-of-one-partition case and must be edited, and the size discipline (:39-44). |
| `.env.example` | The three keys the config layer must resolve BY NAME: NBA_ENV (:8), NBA_REQUEST_DELAY_SECONDS=0.6 (:14), NBA_MAX_RETRIES=5 (:15). The commented Phase-2 cloud block (:17-28) is the shape the S3-key-shaped landing prefixes anticipate. |
| `.claude/agents/data-engineer.md` | Decides who can build what, 277 lines. Write allowlist :115-121; repo-level deny :123-133 (tests/, .github/, ops/, .claude/ except its own memory, CLAUDE.md, docs/data-sources.md at :131, docs/decisions/); stop-and-report at :140-141; tool allowlist :143-155; and :157-159, which forbids anything that hits stats.nba.com live and names `dbt deps` as a network call to report rather than run. Docs-delta routing at :216-235. |
| `docs/data-sources.md` | The belief catalog, 148 lines. READ THE CURRENT LINE NUMBERS, not the scope's — this file moved in the scoping commit. Epistemic blockquote :5-11 (already corrected). Rate limiting still `unconfirmed` at :23-28. Bulk-vs-per-game table :42-45 with the `verified` verdict and measured table at :47-64. Era availability :74-80, traditional-box-score row at :76. THE DANGLING `docs/data-dictionary.md` REFERENCE IS AT :85. Stat corrections :112-116; player affiliation :118-123. |
| `transform/dbt_packages/dbt_utils/macros/generic_tests/mutually_exclusive_ranges.sql` | Read :1 and :6-30 BEFORE writing AC 8's test. Signature at :1 is `(model, lower_bound_column, upper_bound_column, partition_by=None, gaps='allowed', zero_length_range_allowed=False)`. `gaps` outside {'not_allowed','allowed','required'} raises a compiler error (:15-18). And `zero_length_range_allowed=False` selects a strict `<` at :20-22 — so a single-game stint (valid_from == valid_to), exactly what a ten-day contract with one appearance produces, FAILS on the default. |
| `tests/test_repo_structure.py` | The structural guards that must stay green through every edit: version pinning (:52-60), layer-directory/dbt_project.yml agreement in both directions (:63-77), per-layer README (:78-85). Note :19 uses `parents[1]` — that is a TEST-file locator and AC 18 forbids copying it into src/. |

## 2. Architecture map

CURRENT STRUCTURE (verified 2026-08-14 via `git ls-files src transform tests`). The touched area is empty or scaffold-only in all four subsystems, so there is nothing to refactor — only seams to hook into.

1) PYTHON PACKAGE. `src/nba_platform/__init__.py` is the ONLY tracked file under src/. Its docstring (:1-10) already reserves exactly this surface — "talking to source APIs, enforcing polite request pacing, checkpointing long backfills, and writing immutable raw payloads to the landing zone" — and `__version__ = "0.1.0"` at :12 is pinned against pyproject.toml:3 by tests/test_repo_structure.py:52-60. New submodules attach here. The checkpointing clause stays a forward-looking promise (Decision 7 cut the standalone store).

2) DBT PROJECT. `transform/models/{bronze,silver,gold}/` hold a README each and ZERO .sql / schema.yml / sources.yml. `transform/tests/` holds a README and zero .sql. `transform/seeds/` DOES NOT EXIST (verified `Test-Path transform/seeds` → False) although dbt_project.yml:10 declares `seed-paths: ["seeds"]` and .gitignore:32 already whitelists `transform/seeds/**/*.csv`. Layer config exists already: `+persist_docs` relation+columns (dbt_project.yml:22-24), bronze schema/table/tag (:26-32), silver (:34-40), gold (:42-47), and `data_tests: +severity: error` (:49-53) — which makes any dbt WARN a RED build, and is why the `arguments:`-nested generic-test shape at transform/models/silver/README.md:19-23 is mandatory rather than stylistic. dbt_utils resolves to 1.4.1 (transform/package-lock.yml); `mutually_exclusive_ranges.sql` and `unique_combination_of_columns.sql` are both confirmed present in transform/dbt_packages/dbt_utils/macros/generic_tests/.

3) THE LOAD-BEARING SEAM — THE BRONZE SOURCE. ci.yml:76 runs `dbt build --target ci` against `:memory:` (profiles.yml:24-27) on a checkout where `var/` is gitignored (.gitignore:16), and "dbt build" is a required context (ops/branch-protection.json:4). So bronze must resolve to committed fixtures under `--target ci` and to the landing root under `--target local`, through ONE named indirection with no literal path in any model. The mechanism is VERIFIED in the resolved adapter: `DuckDBRelation.create_from_source` (.venv/Lib/site-packages/dbt/adapters/duckdb/relation.py:31-77) reads `external_location` from the source config (:58-59), interpolates it with `str.format_map(source_config.as_dict())` under the default `newstyle` formatter (:60-62), and — because the rendered string contains `(` — emits it UNQUOTED (:73-74). So `{{ source('nba_stats_landing', 'league_game_log_player') }}` compiles to `read_json_auto('<root>/...')`. Drive `<root>` from a dbt var defaulted per target in transform/dbt_project.yml, never from a literal in a model. TWO GOTCHAS: the `format_map` at :62 means any LITERAL `{` or `}` in a glob raises at parse time; and .sqlfluff:12-16 templates through dbt at `target = ci`, so an unresolved source reddens sqlfluff AND dbt build — one root cause, two required checks (R3/R4).

4) WHAT GETS LANDED, AND WHY BRONZE UNNESTS. Decision 8 requires landing nba_api's RAW JSON response, not a DataFrame round-trip. The raw envelope is `resultSets[0].headers` (an ordered name list) plus `resultSets[0].rowSet` (positional arrays). Bronze therefore decodes headers-plus-rowSet into columns. THE OBVIOUS WAY IS WRONG: indexing `rowSet[i][3]` bakes column ORDER into SQL against an explicitly unversioned upstream (docs/data-sources.md:18-21), so a reordered column shifts every value one field over while every uniqueness test still passes. Resolve BY NAME with `list_position(headers, 'PLAYER_ID')` — the same rule CLAUDE.md states for paths, applied to columns. That decode is decoding, not business logic, and stays inside transform/models/bronze/README.md:10-15's rules; say so in the bronze schema.yml description and in ADR 0008.

5) LANDING LAYOUT, S3-KEY-SHAPED SO PHASE 2 IS A ROOT SWAP (non-goal at PROJECT_SCOPE.md:120):
   `<landing_root>/nba_stats/league_game_log/season=<2003-04>/grain=<player|team>/season_type=regular/capture=<YYYYMMDDTHHMMSSZ>/payload.json` + `manifest.json` beside it.
   Every segment is a Hive-style key=value pair on purpose, so DuckDB can project them as columns and bronze gets `captured_at` WITHOUT a join to the manifest — which transform/models/bronze/README.md:10 forbids. WINDOWS GOTCHA: the capture stamp must be COLON-FREE (`:` is illegal in a Windows path; CLAUDE.md says Windows dev / Linux CI); the true tz-aware ISO timestamp lives inside manifest.json, where ruff DTZ (pyproject.toml:58) still enforces awareness.

6) FIXTURES ARE THE CI DATASET. `var/` is gitignored (.gitignore:16) and the blanket data ban at :18-29 is carved out only by :30-32 (`tests/fixtures/**/*.json`, `tests/fixtures/**/*.csv`, `transform/seeds/**/*.csv`). Note `*.jsonl` and `*.ndjson` are ignored at :28-29 with NO counter-whitelist — fixtures must be `.json` or they are silently uncommitted and CI fails on a missing file.

7) DISPATCH SEAM. Decision 9 sends the build to the `data-engineer` subagent, but .claude/agents/data-engineer.md:123-133 makes `tests/`, `.github/`, `ops/`, `.claude/`, `CLAUDE.md`, `docs/data-sources.md` and `docs/decisions/` a repo-level deny, :140-141 tells the agent to STOP rather than build a spec targeting them, and :157-159 forbids hitting stats.nba.com live and running `dbt deps`. Consequence baked into Phase 0: the agent's buildable surface is `src/nba_platform/`, `transform/models/`, `transform/tests/`, `transform/seeds/`, `pyproject.toml`/`uv.lock` and its own reviews/ handoff; the pytest suite, the fixture capture (a live call), `dbt deps`, the ADRs, the docs relabel and all bookkeeping are MAIN-THREAD.

END-TO-END HOOK-IN: nba_api LeagueGameLog → `src/nba_platform/client.py` (paced + backoff, both from config) → `src/nba_platform/landing.py` (write-once, S3-key-shaped prefix, manifest sidecar) → `transform/models/bronze/sources.yml` (the ONE target-aware indirection) → two bronze models (decode/type/case/dedup only) → silver dim_game, dim_team, dim_player, fact_player_game, fact_team_game, dim_player_team_stint → `transform/tests/assert_*.sql`. Nothing reaches gold; `transform/models/gold/` keeps its README and stays empty.

## 3. Phased implementation

Eleven phases, in order. Each ends green locally, then lands via `/commit` — the only sanctioned committer. Never `git commit` ad hoc; never merge, push, or amend.

Where a step carries a **[CORRECTED — binding]** clause, that clause supersedes the sentence before it. See section 5.

### Phase 0 — Pre-flight and dispatch gate (main thread, no code)

**Goal.** Clear the two prerequisites Decision 9 makes non-negotiable, settle the one deny-set ambiguity in writing, and record a green baseline so any later red is attributable.

**Steps.**

1. MEASURE the memory file, do not assume: `python -c "import pathlib;print(len(pathlib.Path('.claude/agents/data-engineer-memory.md').read_text(encoding='utf-8').splitlines()))"`. MEASURED at planning time: 115 physical lines against the 120 cap at tests/test_agent_contract.py:40, counted as `len(text.splitlines())` per the comment at :35 and the helper at :133. That is ~5 lines of headroom and a memory entry is four to five lines. DO NOT use PowerShell's `Measure-Object -Line` — it skips blank lines and undercounts this file by 25.

2. PRUNE the memory file on the main thread to ~95-100 lines, leaving room for at least four new entries. The agent is correctly forbidden from self-pruning (.claude/agents/data-engineer-memory.md:56-63, '**At cap, append nothing.** Do not delete an older entry to make room'), so this cannot be delegated. Preserve the entries this build actually needs — the nba_api-returns-a-DataFrame casing entry and the dbt `arguments:`-nesting entry.

3. RESOLVE THE DENY-SET AMBIGUITY IN WRITING, in the spec handed to the agent: does the bare `tests/` token at .claude/agents/data-engineer.md:126 cover `transform/tests/` (the dbt singular tests) or only repo-root `tests/`? Recommendation and default: repo-root only — the deny comment reads 'the guards that catch you', and dbt singular tests are model work. Write the answer into the spec's target-path list so the agent never has to guess at :140-141.

4. WRITE THE DISPATCH SPLIT into the spec explicitly, criterion by criterion. AGENT-BUILDABLE: src/nba_platform/, transform/models/, transform/tests/, transform/seeds/, pyproject.toml, uv.lock, its own reviews/ handoff. MAIN-THREAD ONLY: everything under tests/ including tests/fixtures/ (AC 10, 16-20), the live probe and fixture capture (.claude/agents/data-engineer.md:157-158 forbids hitting stats.nba.com), `dbt deps` (:158-159), docs/data-sources.md, docs/decisions/, CLAUDE.md, README.md, requests/ bookkeeping. No acceptance criterion may be left unassigned.

5. MAIN-THREAD: run `uv run dbt deps --project-dir transform --profiles-dir transform` once so transform/dbt_packages/ is populated for the agent (dbt_utils 1.4.1 per transform/package-lock.yml).

6. RECORD THE BASELINE, all green BEFORE any change: `uv run pytest -m "not network"`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, `uv run dbt build --project-dir transform --profiles-dir transform --target ci`.

7. USER-RUN: confirm the working branch is a feature branch off main with a clean tree. Agents never run checkout — subagents get read-only git.

**Acceptance.**

- `uv run pytest tests/test_agent_contract.py` exits 0 and the memory file is at or under 100 physical lines, verified by the splitlines command above (not by Measure-Object).
- `transform/dbt_packages/dbt_utils/macros/generic_tests/mutually_exclusive_ranges.sql` and `unique_combination_of_columns.sql` both exist on disk.
- The spec document names, for each of acceptance criteria 1-30, whether it is agent-built, main-thread-built, or user-run — with no criterion unassigned and the `transform/tests/` question answered in words.
- The baseline five commands are all green and the result is recorded.

**Commit note.** green locally (pytest) → /commit. Message: 'chore(agents): prune data-engineer memory to make room for the box-score build'. Docs-only change; say in the message that the prune is a prerequisite of this build, not routine housekeeping, so the pruned entries stay recoverable from history.

### Phase 1 — Toolchain and the resolve-by-name config layer

**Goal.** Land the repo's first runtime dependency without reddening a check, and stand up the config layer that is the only way any later module learns a path, a season, a delay or a retry count. No network, no models — so the three distinct toolchain failure modes (R10) are isolated in one small reversible change.

**Steps.**

1. Add `nba_api` to `[project] dependencies` at pyproject.toml:9 (currently `[]`) and rewrite the now-false comment at :11-13. REGENERATE uv.lock IN THE SAME COMMIT — verified today that uv.lock contains no nba_api, pandas or httpx entry (only a transitive `requests` at :1550), and ci.yml:39 runs `uv sync --locked` and fails otherwise (AC 5).

2. Add a scoped `[[tool.mypy.overrides]]` block for `module = "nba_api.*"` (and `pandas.*` if it leaks) with `ignore_missing_imports = true`. pyproject.toml:70-74 is `strict = true` over `files = ["src", "tests"]` with NO override block today, so this must be one committed, declared boundary — not a hundred discovered `# type: ignore`s. Confine every nba_api and pandas import to `src/nba_platform/client.py`.

3. Create `src/nba_platform/config.py`: a frozen settings object read from the environment BY NAME — NBA_ENV (.env.example:8), NBA_REQUEST_DELAY_SECONDS default 0.6 (:14), NBA_MAX_RETRIES default 5 (:15). It exposes `landing_root`, `warehouse_path`, `pilot_seasons` (default 2003-04, 2019-20, 2024-25 per Decision 6, overridable so widening is a parameter change), `request_delay_seconds`, `max_retries`.

4. Add `landing_key(source, endpoint, season, grain, season_type, captured_at)` returning the S3-key-shaped relative prefix `nba_stats/league_game_log/season=<s>/grain=<g>/season_type=regular/capture=<YYYYMMDDTHHMMSSZ>/`. THE CAPTURE STAMP IS COLON-FREE: `:` is illegal in a Windows path and this is a Windows-dev / Linux-CI repo; the true tz-aware ISO timestamp lives in the manifest.

5. NO literal `'var/'` string and NO `parents[N]` walk anywhere under src/ (AC 18). tests/test_repo_structure.py:19 uses `parents[1]` but that is a test-file locator and is explicitly not precedent. Resolve the repo root from an env var with a documented default, or by walking up to the directory containing pyproject.toml, and say which in the module docstring. Use `pathlib` only — ruff PTH (pyproject.toml:59) makes `os.path` an error.

6. MAIN-THREAD: write `tests/test_config.py` — (a) the landing root resolves through the config layer from NBA_ENV via monkeypatched env; (b) an overriding env var wins; (c) `landing_key` output contains no `:` and matches the `key=value/` prefix shape; (d) THE PURITY GUARD: walk every `.py` under `src/nba_platform/` and assert none contains `parents[` and none contains a literal `'var/'` or `"var/"` outside config.py's single documented resolution helper. This mechanizes AC 18 before any code exists that could violate it, in the spirit of tests/test_repo_structure.py:1-9.

**Acceptance.**

- `uv sync --locked` exits 0 (AC 5).
- `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` all exit 0 with src/nba_platform/config.py in scope (AC 4).
- `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing` exits 0 — byte-identical to ci.yml:53 (AC 1).
- The purity guard in tests/test_config.py fails if a `parents[` or a literal `var/` is introduced anywhere under src/nba_platform/ (AC 18).
- `uv run pytest tests/test_repo_structure.py tests/test_doc_links.py` exits 0 (AC 21).

**Commit note.** green locally (pytest + ruff + ruff format + mypy) → /commit. Stage pyproject.toml AND uv.lock together — splitting them reddens ci.yml:39 on a step unrelated to the code under review. Reverting this commit restores an empty dependency list; nothing else imports it yet.

### Phase 2 — Paced client, write-once landing writer, capture manifest, backfill CLI, ADR 0008

**Goal.** Make the immutable landing zone real and auditable rather than asserted, make its cost checkable before it is spent, and record the layout/manifest/dedup decision as an ADR BEFORE anything reads it. Everything provable offline against a stubbed transport.

**Steps.**

1. Create `src/nba_platform/client.py` — the ONE untyped boundary. It wraps `nba_api`'s LeagueGameLog, enforces a minimum inter-request gap and exponential backoff, BOTH read from config and never literals, via an injectable clock/sleep. It returns the RAW response body (Decision 8) — never a `get_data_frames()` round-trip, because a pandas re-serialization means 'immutable raw' is not raw and weakens the diff-against-raw invariant at transform/models/bronze/README.md:17-19. It may expose a separate DataFrame accessor for inspection only.

2. VERIFY THE RAW ACCESSOR AGAINST THE INSTALLED PACKAGE BEFORE WRITING ANYTHING THAT DEPENDS ON ITS SHAPE. Gate 0 only exercised `get_data_frames()[0]` (gate-0-endpoint-probe.md:83-86) and nba_api is NOT installed today (verified: `importlib.util.find_spec('nba_api')` is None before Phase 1). The raw accessor's name and the envelope it returns are `unconfirmed`. Believed to be a `get_dict()`/`get_json()`-style accessor returning `{"resultSets":[{"headers":[...],"rowSet":[[...]]}]}` — CONFIRM by introspection now, record what you find, and if no accessor returns the raw body, serialize the response's own JSON dict rather than a DataFrame and say so honestly in ADR 0008.

3. Create `src/nba_platform/landing.py`: `write_capture(...)` is WRITE-ONCE. If a capture already exists under the (source, endpoint, season, grain, season_type) prefix it is SKIPPED and never overwritten — this skip-if-present IS the checkpoint at this volume (Decision 7); do not build a checkpoint store. A deliberate re-pull is a separate `--recapture` flag that writes a NEW `capture=<ts>/` directory beside the first and never touches it. That is how immutability and restatement (docs/data-sources.md:112-116) coexist, and it is the concrete resolution of R9.

4. Each capture writes `payload.json` (raw envelope, verbatim, UTF-8) and `manifest.json` beside it carrying: endpoint, the full parameter dict, tz-aware `captured_at` (ruff DTZ at pyproject.toml:58 makes a naive one a lint error), HTTP status, row count, sha256 of payload.json, the nba_api version, and elapsed seconds.

5. Create `src/nba_platform/backfill.py`: the command a human runs. `--seasons`, `--grains`, `--season-type`, `--dry-run`, `--recapture`. `--dry-run` prints planned call count, pacing and estimated wall clock and issues ZERO requests (AC 28); the printed count must come from the same planner the real run consumes, so the two cannot drift. A real run emits a run manifest recording MEASURED cost — call count, elapsed wall clock, observed inter-request spacing, rows per call.

6. MAIN-THREAD pytest (tests/ is a denied path for the agent): `tests/test_landing_immutability.py` — AC 16: run the backfill twice against a stubbed client into `tmp_path`, hash every file in the landing tree after run 1 and run 2, assert the hash SETS are identical and no previously-landed file's content changed; then run once more with `--recapture` and assert the run-1 files are still byte-identical while a new capture directory appeared.

7. MAIN-THREAD pytest: `tests/test_client_pacing.py` — AC 17: with a stubbed clock, N sequential calls request no faster than NBA_REQUEST_DELAY_SECONDS, and a simulated failure backs off exponentially up to NBA_MAX_RETRIES. Both values are set via env so the test proves they are config-driven, not literals.

8. MAIN-THREAD pytest: `tests/test_backfill_plan.py` — `--dry-run` makes zero client calls and its printed call count equals the number of calls a subsequent stubbed real run makes (the offline half of AC 28).

9. MAIN-THREAD (docs/decisions/ is a denied path): write `docs/decisions/0008-landing-layout-and-capture-manifest.md` — Status / Context / Decision / Consequences / Alternatives per docs/decisions/README.md:19-25 — covering the S3-key-shaped layout, the colon-free path stamp, the capture manifest, path-carried provenance, the raw-JSON-not-DataFrame choice, and the bronze latest-capture-wins rule (decided here, implemented in Phase 5). Fold the landing-layout convention note in rather than making a separate doc. Per docs/decisions/README.md:34-35 the cost section must be uncomfortable: name the pandas-into-a-zero-runtime-dependency-repo weight, and name that a re-pull permanently doubles disk under var/. Add its Index row at docs/decisions/README.md:39-47 (the Index currently ends at 0007 on :47).

**Acceptance.**

- `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing` exits 0 with all three new test modules green (AC 1, 16, 17).
- `uv run mypy` exits 0 — no nba_api or pandas `Any`-leakage escapes client.py.
- `uv run python -m nba_platform.backfill --dry-run` prints a planned call count of 6 (3 pilot seasons × 2 grains) and constructs no client.
- The `--recapture` path adds a capture directory without mutating one (R9's resolution, proven offline).
- `docs/decisions/0008-*.md` exists with all five required sections and a non-empty cost section, and has a row in the Index; `uv run pytest tests/test_doc_links.py` exits 0 (AC 21).
- The raw-accessor finding is recorded in writing with a `verified` label.

**Commit note.** green locally (pytest + ruff + mypy) → /commit. Stage src/nba_platform/{client,landing,backfill}.py, the three test modules, the ADR and the Index row. Nothing under var/ may appear in /commit's staged list — inspect it by eye, not just its refusal logic.

### Phase 3 — VERIFICATION PHASE: complete Gate 0 and capture the fixture corpus (network)

**Goal.** Retire every remaining unconfirmed claim this build stands on BEFORE any model is designed against it — including the two pilot seasons Gate 0 never called — and turn the captured payloads into the committed fixture corpus that IS the CI dataset. Nothing downstream may proceed until this phase's stop-conditions are cleared.

**Steps.**

1. READ FIRST: gate-0-endpoint-probe.md:104-116. Gate 0 called 2003-04 and 2023-24. The pilot is 2003-04, 2019-20 and 2024-25 (PROJECT_SCOPE.md:252), so TWO OF THREE PILOT SEASONS HAVE NEVER BEEN CALLED — and 2019-20 is the one most likely to break a calendar assumption. Cross-check its Results (:52-66) and Columns (:93-102) against AC 22's list (PROJECT_SCOPE.md:197): the probe does NOT report MIN's format, whether DNP-but-active players get a row, whether GAME_ID is zero-padded and at what width, or the distinct (team_id, team_name) pair count. Four AC-22 answers are missing plus one unprobed pilot season.

2. WHO RUNS THIS: reachability is settled — gate-0-endpoint-probe.md:28-46 shows nba_api succeeds in 0.6s from this environment while raw Invoke-WebRequest times out. So this is MAIN-THREAD agent work or user-run, but NEVER subagent work: .claude/agents/data-engineer.md:157-158 forbids the data-engineer from anything that hits stats.nba.com live.

3. MAIN-THREAD: write `tests/test_live_contract.py` marked `@pytest.mark.network` (the marker at pyproject.toml:80-82 is unused and ci.yml:53 already excludes it — the slot was cut for this). It calls leaguegamelog at P and T for all three pilot seasons at 0.6s pacing and asserts the returned ORDERED column list equals what bronze's schema.yml declares.

   **[CORRECTED — binding]** Do NOT assert against `transform/models/bronze/schema.yml` here: Phase 4 creates it, so a cold agent hits a FileNotFoundError, or writes a vacuously-skipping test, in the phase whose whole job is to gate the model phases (SEQ-01). In THIS phase, assert the live ordered column list against the 29/32-column lists recorded in `reviews/gate-0-endpoint-probe.md`, so the probe evidence IS the contract. Phase 4 re-points it at the YAML as an explicit step.

4. RUN THE COMPLETION PROBE and record, with a `measured` label and the date, in `requests/feature-requests/box-score-foundation/reviews/endpoint-probe.md` (AC 22): full-season-per-call at P and T for 2019-20 and 2024-25; the exact raw-response envelope and the accessor that returns it un-round-tripped; row count and ORDERED column list per season per grain, diffed against the 29/32 lists at gate-0-endpoint-probe.md:95-99; MIN's exact repr and dtype; whether any row exists for a DNP-but-active player; GAME_ID's dtype, exact character width, and whether leading zeros survive; the count of distinct (team_id, team_name) pairs across all three seasons and WHICH team_ids carry more than one name; 2019-20's GAME_DATE min/max and per-team game-count spread; duplicate (GAME_ID, PLAYER_ID) count per season; whether MATCHUP carries both a ' vs. ' and an ' @ ' token; and what an empty-or-error response actually looks like.

5. STOP-AND-ESCALATE BRANCH — do not build around any of these silently: a different column set in 2019-20 or 2024-25 changes bronze's column list and reopens the era-nullable contingent non-goal (PROJECT_SCOPE.md:138); a duplicate (GAME_ID, PLAYER_ID) changes the grain test; an unparseable MIN cancels the team-minutes reconciliation (a conditional cheap fold at :280, not core); a missing MATCHUP token removes dim_game's only home/away signal.

6. PIN THE TRADE FROM THE PAYLOAD, NEVER FROM MEMORY (AC 10): query the captured player payload for a PLAYER_ID with two or more distinct TEAM_IDs inside one season, and record his player_id, name, both team_ids, the date of his last game with the old team and the date of his first game with the new one.

7. Create `src/nba_platform/fixtures.py` — the recorder tests/fixtures/README.md:11-13 already instructs the reader to use and which does not exist (verified drift). THE TRIM RULE IS LOAD-BEARING AND IS 'WHOLE GAMES, ROWS ONLY': choose a set of GAME_IDs and keep EVERY row for those games at BOTH grains, preserving the resultSets/headers/rowSet envelope byte-for-byte in shape (R12, PROJECT_SCOPE.md:246). Trimming by arbitrary rows silently breaks assert_every_game_has_exactly_two_teams, the team-minutes reconcile and the points reconcile. Never trim structure.

8. CAPTURE THE CORPUS under `tests/fixtures/nba_stats/league_game_log/`, in the SAME `season=/grain=/season_type=/capture=` partition layout as the landing zone: (a) 2024-25 modern, both grains; (b) 2003-04 pre-tracking, both grains; (c) 2019-20 bubble, both grains, DELIBERATELY retaining July-October 2020 game dates; (d) the pinned traded player's FULL set of rows across BOTH teams, at both grains — trim around him, never through him; (e) an empty-or-error response, captured not hand-authored; (f) A SECOND CAPTURE of one already-captured (season, grain) partition under a later `capture=` stamp with at least one row's value deliberately changed. Case (f) is the AC-15 enabler the fixtures README table does not list, and it is the only fixture that may be edited rather than captured — its provenance must state exactly what was changed and why.

   **[CORRECTED — binding]** Land the empty/error capture (AC 20) OUTSIDE the landing-shaped tree, at `tests/fixtures/nba_stats/league_game_log/_error_cases/<case>.json`, with the leading underscore documented as "not a landing partition, never globbed by a source" (EXEC-02). Inside the partitioned tree it is matched by the Phase 4 source glob, and DuckDB unifies schema across a glob — a payload with no `resultSets[0].headers` either fails unification or injects a null-headers row, turning the REQUIRED `dbt build` check red. The error path is exercised only by offline pytest against the client and landing writer, never by dbt. Repeat the note in the edited `tests/fixtures/README.md` Layout section so the next capture does not re-break it.

9. Write per-capture trim provenance into each capture's `manifest.json`: request parameters, capture timestamp, original row count, retained row count, the GAME_IDs kept, and the descriptive case name (relocated from the filename).

10. EDIT `tests/fixtures/README.md`'s Layout section (:27-34) from the flat `<source>/<endpoint>/<descriptive-case>.json` shape to the partitioned capture layout, stating the reason inline: a flat name cannot express two captures of one partition, which AC 15 requires. Keep the 'the case name should say what makes the fixture interesting' requirement by relocating it into the manifest's provenance field.

11. CONFIRM every fixture is `.json` — .gitignore:28-29 ignores `*.jsonl` and `*.ndjson` with NO counter-whitelist, and :30 whitelists only `tests/fixtures/**/*.json`. Confirm total fixture bytes stay small (tests/fixtures/README.md:39-44; README.md:11-14 and the provenance note say this repo redistributes no NBA data — .gitignore:30 is a carve-out, not a licence).

**Acceptance.**

- `uv run pytest -m network` exits 0 and prints measured call count, rows per call, wall-clock seconds and the ordered column list per grain per pilot season (AC 27).
- `reviews/endpoint-probe.md` exists, carries a `measured` label, and answers every AC-22 question BY NAME — including the four Gate 0 left open (AC 22).
- `tests/fixtures/nba_stats/league_game_log/` contains at least the six cases above; every non-empty case has a player-grain and a team-grain file over the SAME GAME_ID set (AC 20).
- Every fixture's `resultSets[0].headers` is present and non-empty, and each fixture's rowSet count equals the retained count in its provenance — asserted by the recorder, not by eye.
- `git status` shows every fixture as TRACKED, not ignored — proving the .gitignore:30 whitelist actually caught them.
- The pinned traded player is recorded with player_id, both team_ids and both boundary dates, sourced from a captured payload.
- `uv run pytest -m "not network"` and `uv run pytest tests/test_doc_links.py` both exit 0 after the fixtures README edit.

**Commit note.** green locally (pytest, both markers) → /commit. Stage tests/fixtures/**, src/nba_platform/fixtures.py, tests/test_live_contract.py, reviews/endpoint-probe.md and the fixtures README edit PER PATH. This is the commit where /commit's bulk-data refusal is most likely to fire; if it does, the fixtures are over-trimmed in the wrong direction and must lose whole games, not rows.

### Phase 4 — Bronze walking skeleton: the target-aware source seam, ONE model, and the sqlfluff shakedown

**Goal.** Prove the single seam that keeps a required check green, and absorb the first-ever sqlfluff run, on the smallest possible surface — before nine more .sql files ride on it. This is the highest-risk phase and the highest-value rollback point.

**Steps.**

1. SPIKE FIRST, MODEL SECOND (throwaway, 15 minutes): open a committed fixture in DuckDB and nail the exact expression that unnests `resultSets[0].rowSet`, projects columns BY NAME via `list_position(headers, 'PLAYER_ID')` with explicit casts, and recovers the capture path. Verify whether `read_json_auto(<glob>, hive_partitioning = true)` projects the `season=`, `grain=`, `season_type=` and `capture=` segments as columns — this is INFERRED, not verified; the documented fallback is `filename = true` plus `regexp_extract` over the path. Record which won, because ADR 0008 must say. Do not write the model until the expression returns rows.

2. Add a `vars:` block to `transform/dbt_project.yml` declaring `nba_landing_root`, defaulted per target — fixtures under `--target ci`, the config-layer landing root under `--target local`. Paths resolve relative to the dbt project dir (transform/), so the CI default carries `../tests/fixtures`.

   **[CORRECTED — binding]** Do NOT use a `vars:` block (EXEC-03). dbt's `vars:` is a flat mapping with no target-scoping syntax, and whether `{{ target.name }}` renders while `dbt_project.yml` is parsed depends on `DbtProjectYamlRenderer` constructing a `TargetContext` — verified at `.venv/Lib/site-packages/dbt/config/renderer.py:123`, an implementation detail rather than a contract. Put the conditional in `transform/models/bronze/sources.yml`, where the full Jinja context is guaranteed, and keep `vars:` out of it entirely. The `external_location` value takes the shape `read_json_auto('<conditional-root>/nba_stats/league_game_log/season=*/grain=player/season_type=*/capture=*/payload.json', hive_partitioning = true)`, where the conditional root is an inline Jinja `if target.name == 'ci'` selecting `../tests/fixtures`, else `env_var('NBA_LANDING_ROOT', '../var/landing')`. Prove it by running `dbt compile` against BOTH targets and diffing `transform/target/compiled/` — the two roots must differ.

3. Create `transform/models/bronze/sources.yml` with ONE named indirection: a table-level `meta.external_location` built from `{{ var('nba_landing_root') }}` and rendering as `read_json_auto('<root>/...', ...)`. Mechanism VERIFIED in the resolved adapter — dbt-duckdb reads `external_location` from the source config (relation.py:58-59), interpolates it with `format_map` under the default `newstyle` formatter (:60-62), and emits it UNQUOTED because it contains `(` (:73-74). TWO TRAPS: any LITERAL `{` or `}` in a glob raises at parse time under `format_map`, so double it or set `formatter: template`; and confirm with `dbt compile --target ci` that a parent-level meta key actually reaches the table's SourceConfig — if it does not, repeat `nba_landing_root` on each table's meta (two lines).

4. Write `transform/models/bronze/bronze__nba_stats__league_game_log_player.sql`, named per transform/models/bronze/README.md:23. Decode the envelope, project the 32 ordered player-grain columns from gate-0-endpoint-probe.md:99 BY NAME, lowercase them, cast explicitly, CAST game_id AS VARCHAR (never let inference eat the leading zero), and carry `captured_at` recovered from the path. NO dedup yet — that arrives in Phase 5 with the two-captures fixture that proves it. No joins, no filtering, no semantic renaming, no derived stats (transform/models/bronze/README.md:10-15).

5. Write `transform/models/bronze/schema.yml` declaring the source contract per transform/models/bronze/README.md:30-33: the endpoint, its parameters, every column described, and `not_null` on the columns this project depends on the upstream promising — game_id, player_id, team_id, game_date, plus_minus. Record in the description that Gate 0 measured plus_minus present in 2003-04 with zero nulls and that no tracking-derived column appears in this endpoint, so the 2013-14 boundary does not apply here. Use `data_tests:` with args nested under `arguments:` (transform/models/silver/README.md:28-32); dbt_project.yml:51-53 sets `+severity: error`, so a warn is a RED build.

6. RUN `uv run sqlfluff lint transform/models` LOCALLY AND FIX THE STYLE SHAKEDOWN HERE, ON ONE FILE. This command has never run in this repo: the guard at ci.yml:78-85 skips while no .sql exists and goes live on this commit, against duckdb dialect and 100-char lines (.sqlfluff:5-6), lowercase keywords/functions/identifiers (:26-33), explicit table AND column aliasing (:35-39) and trailing commas (:23-24). Expect the first red to be style, not logic (R4).

7. MAIN-THREAD pytest: `tests/test_fixture_schema_drift.py` — for each committed fixture, assert its `resultSets[0].headers` equals, IN ORDER and in BOTH directions, the column list declared in transform/models/bronze/schema.yml, parsed from YAML rather than hardcoded (AC 19). Add a row-count floor so the guard cannot pass on an empty fixture.

**Acceptance.**

- `uv run dbt build --project-dir transform --profiles-dir transform --target ci` exits 0 on a checkout with no var/ and no network — bronze built entirely from committed fixtures. Byte-identical to ci.yml:76 and the required check named 'dbt build' at ops/branch-protection.json:4 (AC 2).
- `uv run sqlfluff lint transform/models` exits 0 (AC 3) — the first time this command has ever run in this repo.
- `uv run dbt build --select tag:bronze --target ci` selects and builds the model, proving the tag at dbt_project.yml:32 works as a promotion gate.
- `uv run pytest -m "not network"` exits 0 including the ordered drift guard (AC 19).
- `uv run pytest tests/test_repo_structure.py` exits 0 — transform/models/ still agrees with dbt_project.yml (:63-77).

**Commit note.** green locally (pytest + dbt build --target ci + sqlfluff) → /commit. If the seam is wrong, exactly one model, one sources.yml and one vars block are in the blast radius — which is the entire point of landing one model here rather than four.

### Phase 5 — Bronze complete: team grain, latest-capture-wins, and the fidelity guards

**Goal.** Finish bronze and make the immutable-landing-versus-restated-facts tension executable rather than asserted.

**Steps.**

1. Write `transform/models/bronze/bronze__nba_stats__league_game_log_team.sql` in the same shape, projecting the 29 ordered team-grain columns from gate-0-endpoint-probe.md:95-97. This model is CORE even though its fact arrives in Phase 7: it is the source of dim_game's home/away and of dim_team, for three extra API calls (PROJECT_SCOPE.md:232).

2. Add latest-capture-wins dedup to BOTH bronze models: a `row_number() over (partition by <natural key> order by captured_at desc, capture_id desc)` CTE filtered to 1. Natural key is (game_id, player_id) at player grain and (game_id, team_id) at team grain. The capture_id tiebreak makes it deterministic when two captures share a second. Use a CTE rather than `qualify` — unambiguously lintable under .sqlfluff's duckdb dialect. This is the dedup transform/models/bronze/README.md:5-6 permits and nothing more, and it is the rule ADR 0008 already recorded.

3. Add `transform/tests/assert_bronze_row_count_matches_landed.sql` (AC 13): for each (season, grain) partition, the bronze row count equals the rowSet row count of the WINNING capture read straight from the source. This makes executable the invariant transform/models/bronze/README.md:17 states in prose.

4. Add `transform/tests/assert_latest_capture_wins.sql` (AC 15): with the Phase-3 second-capture fixture present, exactly one row exists per natural key and the changed column carries the LATER capture's value.

5. Add `transform/tests/assert_game_id_keeps_leading_zeros.sql` (AC 14): game_id is typed VARCHAR and every value matches a fixed-width numeric-string pattern using the WIDTH MEASURED IN PHASE 3 — do not guess it. stats.nba.com game ids are zero-padded; a numeric inference destroys the padding while every join still 'works' and every uniqueness test still passes.

6. Give every fixture-backed test a row-count FLOOR assertion so an over-trimmed fixture cannot make it pass vacuously (R12).

7. Extend `tests/test_fixture_schema_drift.py` to cover BOTH bronze schema.yml column lists.

**Acceptance.**

- `uv run dbt build --project-dir transform --profiles-dir transform --target ci` exits 0 with both bronze models and all three new singular tests green (AC 2, 13, 14, 15).
- `uv run sqlfluff lint transform/models` exits 0 (AC 3).
- DELIBERATE NEGATIVE CHECK, run once by hand and then reverted: flipping the dedup ordering to ascending makes assert_latest_capture_wins FAIL. A test that cannot fail is not a test.
- `uv run dbt build --select tag:bronze --target ci` is green as a standalone layer gate (dbt_project.yml:18-19, :32).
- `uv run pytest -m "not network"` exits 0.

**Commit note.** green locally (pytest + dbt build --target ci + sqlfluff) → /commit. Bronze is frozen after this commit; any later red in bronze is a regression, not a build error.

### Phase 6 — First vertical slice: dim_game + fact_player_game

**Goal.** Get ONE fact from source to a tested silver table before anything widens — the ordering R17 says this slice is only defensible under, and the phase that must have landed if the plan is ever cut short.

**Steps.**

1. Write `transform/models/silver/dim_game.sql`: one row per game_id from the TEAM-grain bronze (two rows per game collapse to one), carrying game_date, season, season_type, home_team_id and away_team_id. HOME/AWAY IS THE ONE INFERRED STRUCTURE IN THIS SLICE and the scope is only half right about it: collapsing the two team rows avoids parsing the OPPONENT out of MATCHUP, but MATCHUP's ' vs. ' / ' @ ' token remains the only home/away signal in the payload. Derive `is_home` from that token using the Phase-3 confirmation that both tokens appear, guard it with not_null, and let AC 12's test be the real proof. Home/away derivation is business logic and lives here, never in bronze.

2. Carry `season_type` as a column from day one with a not_null test even though only regular season is extracted, so playoffs later arrive as ROWS rather than as a migration (R15).

3. Write `transform/models/silver/fact_player_game.sql`: one row per (game_id, player_id). `team_id` comes from the OBSERVED bronze box-score row and from nowhere else — never from a join to the stint model or to dim_team — so fact correctness never depends on the interpolation built in Phase 8 (R7's baked-in mitigation). Materialized `table` per dbt_project.yml:34-40, with `unique_key = ['game_id','player_id']` DECLARED NOW so the switch to incremental+merge is configuration rather than a rewrite (Decision 5). Parse MIN using the format MEASURED in Phase 3.

4. Write the MERGE deferral into the model description as a sentence a future reader inherits: facts here are MERGE-on-key by rule (CLAUDE.md; transform/models/silver/README.md:47-48) and this one is full-refresh because all three pilot seasons are long finalized — *the first in-progress season, or the first nightly run, requires MERGE first.* Declaring the divergence out loud is what keeps /update-docs from reading it as drift; `+persist_docs` (dbt_project.yml:22-24) carries it onto the relation itself.

5. Create `transform/models/silver/schema.yml` with each model's grain stated in PROSE and proven: `dbt_utils.unique_combination_of_columns` on `[game_id, player_id]` for fact_player_game, in the `arguments:`-nested shape at transform/models/silver/README.md:19-23 (AC 6); `unique` + `not_null` on dim_game.game_id and `not_null` on season_type (AC 7).

6. Add `transform/tests/assert_every_game_has_exactly_two_teams.sql` (AC 12) — zero rows, AND exactly one of each game's two rows is flagged home and one away.

7. Add `transform/tests/assert_fact_player_game_row_count_matches_bronze.sql` — THE GRAIN SENTRY: fact_player_game's row count equals bronze's distinct (game_id, player_id) count. Uniqueness catches fan-OUT; only this catches silent row LOSS from an inner join to a dimension missing a key.

8. Add `transform/tests/assert_fgm_never_exceeds_fga.sql` (transform/tests/README.md:17). Add `transform/tests/assert_team_minutes_reconcile.sql` (240 per regulation game, +25 per OT, summed from player minutes — expressible on player grain alone) ONLY IF Phase 3 showed MIN is parseable with overtime recoverable; it is a conditional cheap fold (PROJECT_SCOPE.md:280), so if the format makes OT unrecoverable, SKIP it and say so in writing rather than skipping it quietly.

9. Add `transform/tests/assert_2019_20_has_out_of_window_games.sql`: the 2019-20 fixture contains games outside an Oct-Apr calendar window, with a row-count floor. NOTE the unequal-team-game-count half of that property CANNOT survive whole-games fixture trimming and is deferred to the `--target local` run in Phase 9 — do NOT write a fixture-backed version that passes vacuously.

**Acceptance.**

- `uv run dbt build --project-dir transform --profiles-dir transform --target ci` exits 0 with dim_game, fact_player_game and their tests (AC 2, 6, 7 partial).
- `uv run dbt test --select fact_player_game` passes, including unique_combination_of_columns on [game_id, player_id] against a fixture set containing a mid-season trade (AC 6).
- `assert_every_game_has_exactly_two_teams.sql` returns zero rows and each game has exactly one home and one away (AC 12).
- The grain sentry, FGM<=FGA and the out-of-window assertion all return zero rows, each with a row-count floor confirming a non-empty evaluation.
- A BASKETBALL QUESTION IS ANSWERABLE: a one-line query joining fact_player_game to dim_game returns a named player's points for a specific game date. Run it once and record the answer in the commit message — this is the first basketball fact this repo has ever produced.
- `uv run sqlfluff lint transform/models` and `uv run pytest -m "not network"` both exit 0.

**Commit note.** green locally (pytest + dbt build --target ci + sqlfluff) → /commit. If the plan is ever cut short, THIS is the phase that must have landed — it is the vertical slice CLAUDE.md's 'vertical slices, not horizontal layers' rule is protecting.

### Phase 7 — Conformed dimensions and the cross-grain proof: dim_team, dim_player, fact_team_game

**Goal.** Add the dimensions the facts join to — with dim_team's grain settled against franchise-identity drift from a counted number rather than a silent dedup — and buy the only cross-grain correctness proof this dataset offers (Decision 1).

**Steps.**

1. Write `transform/models/silver/dim_team.sql` with the grain SETTLED using the distinct (team_id, team_name) pair count MEASURED IN PHASE 3 (R5 flags this as inferred-from-domain-knowledge and unverified in this repo). RECOMMENDED: one row per team_id with team_name and team_abbreviation resolved as-of the LATEST observation, plus first/last observed season. Rejected alternative: one row per (team_id, season), which forces every fact join to carry season. Whichever is chosen, the schema.yml prose and the uniqueness test's columns must agree EXACTLY — a naive `select distinct team_id, team_name, team_abbreviation` over a pilot spanning 2003-04 and 2024-25 either fails its own test or gets silently 'fixed' with an arbitrary dedup.

2. WRITE THE AS-OF HAZARD INTO dim_team's PERSISTED DESCRIPTION: with the recommended grain, a fact-to-dim_team join renders a 2003-04 Seattle game under today's franchise name. This is the same as-of-today-versus-as-of-game-date bug docs/data-sources.md:120-123 names for players, in the dimension nobody flags it for. The historical name stays recoverable from bronze.

3. Write `transform/models/silver/dim_player.sql`: one row per player_id, IDENTITY ONLY — player_id, player_name as observed, first and last observed game date. No height, weight, position, draft year or college; those live on commonplayerinfo and are a declared non-goal (PROJECT_SCOPE.md:126). Its description must state IN WORDS that coverage is players who APPEARED in a box score, so the model's name does not overclaim (R8); `+persist_docs` carries that caveat onto the relation.

4. Write `transform/models/silver/fact_team_game.sql`: one row per (game_id, team_id) from the team-grain bronze model, per Decision 1. Same materialization posture and the same MERGE-deferral sentence in its description. This phase is deliberately small because the payload is already landed and bronzed.

5. Extend `transform/models/silver/schema.yml`: `unique` + `not_null` on dim_player.player_id; a uniqueness test on dim_team whose columns match its settled prose grain; `dbt_utils.unique_combination_of_columns` on `[game_id, team_id]` for fact_team_game; and `relationships` tests from fact_player_game to dim_game, dim_player and dim_team, and from fact_team_game to dim_game and dim_team (AC 7).

6. Add `transform/tests/assert_player_points_reconcile_to_team.sql` — for every team-game, the sum of fact_player_game points equals fact_team_game's team total. This is the repo's OWN canonical naming example (transform/tests/README.md:30), the first invariant it lists (:12), and its canonical example of a testable acceptance criterion (requests/feature-requests/README.md). Give it a row-count floor.

7. IF THE RECONCILE FAILS, suspect the fixture trim before the model: a fixture trimmed by rows rather than by whole games is the most likely cause. That is exactly why Phase 3's trim rule is 'whole games, rows only'.

**Acceptance.**

- `uv run dbt build --project-dir transform --profiles-dir transform --target ci` exits 0 with all three models and their tests (AC 2, 7).
- `uv run dbt test --select silver` passes: every silver model added so far has a prose grain in schema.yml and a uniqueness test whose columns match it (AC 7) — checkable by the declared-grain-vs-test audit /update-docs performs.
- dim_team emits exactly one row per its declared key across a fixture set spanning 2003-04 and 2024-25, with the franchise-drift cases PRESENT rather than trimmed away.
- `assert_player_points_reconcile_to_team.sql` returns zero rows and its floor confirms it compared a non-empty set of team-games.
- DELIBERATE NEGATIVE CHECK, run once and reverted: dropping one player row from the player-grain fixture makes the reconcile test FAIL for exactly that team-game.
- The five relationships tests return zero failures; `uv run sqlfluff lint transform/models` and `uv run pytest -m "not network"` exit 0.

**Commit note.** green locally (pytest + dbt build --target ci + sqlfluff) → /commit. Record dim_team's settled grain and its rationale in the model description, not only in the commit message.

### Phase 8 — dim_player_team_stint: the SCD2 affiliation model, its four tests, and ADR 0009

**Goal.** Derive the model this whole request exists for, with the interpolation visible and falsifiable rather than fabricated, and prove it with the one test that is NOT derived from the same observations it checks.

**Steps.**

1. Write `transform/models/silver/dim_player_team_stint.sql`: one row per player per team-stint, key (player_id, valid_from), carrying team_id, season_id, valid_from, valid_to, is_current, PLUS the observed-boundary columns `last_game_prior_team` and `first_game_new_team` so the interpolation stays visible (Decision 3). Build it by ordering each player's observed (game_date, team_id) pairs from fact_player_game and collapsing runs of the same team.

2. PARTITION THE RUN-COLLAPSE BY (player_id, season_id) — SEASON-BOUNDED STINTS. The pilot's three seasons are NOT adjacent (2003-04, 2019-20, 2024-25) and this is not hypothetical: LeBron James appears in all three and the repo is anchored to his rookie year. A global collapse produces a stint spanning 2004 to 2020. Decision 3's 'contiguous and gapless' means contiguous WITHIN a season — the only coherent reading given a non-contiguous pilot — and it merges naturally when widening makes the seasons contiguous. Close each season's final stint at that season's last observed game date; set `is_current` on the stint containing the player's globally-latest observation. See gated decision 2 below.

3. SET BOTH mutually_exclusive_ranges ARGUMENTS EXPLICITLY, WITH A COMMENT SAYING WHY — read transform/dbt_packages/dbt_utils/macros/generic_tests/mutually_exclusive_ranges.sql:1 and :6-30 first. `partition_by: player_id`, `lower_bound_column: valid_from`, `upper_bound_column: valid_to`, `gaps: 'allowed'` (season-bounded stints have real gaps between non-adjacent pilot seasons; anything outside {'not_allowed','allowed','required'} raises a compiler error at :15-18), and `zero_length_range_allowed: true` (the default False selects a strict `<` at :20-22, so a one-game stint — exactly what a ten-day contract with a single appearance produces — FAILS on correct data). Written in the `arguments:`-nested shape (AC 8).

4. Keep `valid_to` non-null everywhere (closed at the last observed game within the season) rather than null or a 9999 sentinel — the macro compares bounds directly and a null upper bound produces a meaningless comparison. Express 'exactly one open interval per player' as an is_current uniqueness test instead.

   **[CORRECTED — binding]** As drafted this reverses disposed Decision 3 (F1). Closing `valid_to` at the last observed game leaves the trade gap uncovered, so an as-of join for a date inside it returns ZERO rows — the observation-bounded behaviour Decision 3 explicitly rejected, while the plan's own prose documents the contiguous rule. Instead: within a `(player_id, season_id)` partition, each stint's `valid_to` is the day BEFORE the next stint's `valid_from` (which is the first game with the new team); only the season's FINAL stint closes at that season's last observed game. Keep `last_game_prior_team` and `first_game_new_team` alongside so the interpolated span stays visible and falsifiable. A date inside a trade gap deliberately resolves to the OLD team. `gaps: 'allowed'` remains the correct macro setting — not because intra-season gaps exist, but because the non-adjacent pilot seasons create real between-season gaps (P2, season-bounded).

5. Add `dbt_utils.unique_combination_of_columns` on `[player_id, valid_from]` (AC 7).

6. Add `transform/tests/assert_player_team_matches_open_stint.sql` (AC 9, named per transform/tests/README.md:28-33): every fact_player_game row's (player_id, game_date) falls inside exactly one stint whose team_id equals the fact's team_id.

7. Add `transform/tests/assert_stints_did_not_degenerate.sql` (AC 11): the count of players with more than one stint inside a single pilot season is > 0, and no stint has valid_from > valid_to. This fails loudly if the run-collapsing collapses to one row per player — the silent failure a passing containment test cannot see.

8. Create `transform/seeds/known_trade_expectations.csv` (the directory does not exist yet; .gitignore:32 already whitelists it) holding the pinned player_id, both team_ids and a game date on each side of the trade, VALUES TAKEN FROM THE PHASE-3 CAPTURED PAYLOAD, NEVER FROM MEMORY. Add `transform/tests/assert_known_trade_resolves_both_sides.sql` (AC 10) joining the stints to that seed and asserting the correct team on BOTH sides of the trade date, with a floor asserting the seed has > 0 rows. THIS IS THE NON-VACUOUS COMPANION.

9. WRITE THE TWO LIMITS INTO THE MODEL DESCRIPTION AND INTO ADR 0009: (a) a date inside a trade gap DELIBERATELY resolves to the OLD team (Decision 3); (b) the containment test is derived from the same observations it checks, so it proves the run-collapsing lost and reordered nothing but is VACUOUS everywhere between game dates (R6). Also state that any future as-of join must join on `game_date between valid_from and valid_to` and NEVER on `is_current = true` — resolving as-of today instead of as-of the game date is what docs/data-sources.md:120-123 names as the single most likely source of silently wrong joins in this project.

10. EDIT THE TWO READMEs THE SPLIT INVALIDATES, IN THIS SAME CHANGE (Decision 2 accepts this cost explicitly): `transform/models/silver/README.md:52` lists dim_player/dim_team/dim_game/dim_date and names no stint table (dim_date is also cut by Decision 4); `transform/tests/README.md:16` still says the invariant is against `dim_player`'s SCD2 history. /update-docs audits exactly this divergence.

11. MAIN-THREAD: write `docs/decisions/0009-scd2-affiliation-interval-boundaries.md` — the contiguous-gapless-within-a-season rule, the season-bounded vs global choice and why, the gap/zero-length macro posture, the deliberate resolve-to-the-OLD-team consequence, and the containment test's vacuity limit. Per docs/decisions/README.md:34-35 the cost section must be uncomfortable, and this is the one that earns it. Add its Index row.

**Acceptance.**

- `uv run dbt build --project-dir transform --profiles-dir transform --target ci` exits 0 end to end — bronze + silver + seed + every test (AC 2).
- `uv run dbt test --select dim_player_team_stint` passes, including mutually_exclusive_ranges partitioned by player_id with both arguments set explicitly (AC 8) and unique_combination_of_columns on [player_id, valid_from] (AC 7).
- `assert_player_team_matches_open_stint.sql` returns zero rows (AC 9).
- `assert_known_trade_resolves_both_sides.sql` returns zero rows, names a real player id drawn from the captured payload, and its seed has > 0 rows (AC 10).
- `assert_stints_did_not_degenerate.sql` returns zero rows AND the >0-multi-stint-players clause is genuinely satisfied by the trade fixture (AC 11).
- transform/models/silver/README.md:52 and transform/tests/README.md:16 both name dim_player_team_stint; `uv run pytest tests/test_doc_links.py tests/test_repo_structure.py` exits 0 (AC 21).
- docs/decisions/0009-*.md exists with all five sections and an Index row; `uv run sqlfluff lint transform/models` exits 0.

**Commit note.** green locally (pytest + dbt build --target ci + sqlfluff) → /commit. Stage the two README edits and the ADR IN THE SAME COMMIT as the model — splitting them leaves the repo documenting a model shape it no longer has, which is exactly what /update-docs flags.

### Phase 9 — Live pilot backfill and the --target local proof (USER-RUN)

**Goal.** Prove what fixtures structurally cannot: that the grain, the reconciliation and the affiliation model hold at ~26,000 rows per season rather than on a trimmed sample (R11).

**Steps.**

1. USER-RUN: `uv run python -m nba_platform.backfill --dry-run`. Record the printed call count, pacing and estimated wall clock (AC 28). Expect 6 calls at 0.6s.

2. USER-RUN: run the real pilot backfill against live stats.nba.com for 2003-04, 2019-20 and 2024-25 at both grains, regular season, writing under var/. Confirm the observed call count EQUALS the dry-run number — that equality is the whole point of the cost guardrail. No cloud money is spent (NBA_ENV=local, DuckDB, no credentials), so CLAUDE.md's user-run-for-billable rule is satisfied vacuously here; state that explicitly so the widening does not inherit a false precedent.

3. USER-RUN: `uv run dbt build --project-dir transform --profiles-dir transform --target local` — the same models and the same test suite, now against real full-season data through the landing-root seam rather than the fixture seam (AC 29).

4. USER-RUN: run the DEFERRED irregular-season assertion here — 2019-20 team game counts are UNEQUAL. That property cannot survive whole-games fixture trimming, so it lives on the local target only. Record the observed spread.

5. USER-RUN: re-run the backfill a second time and confirm write-once skip-if-present makes zero API calls, creates no new capture directory, and leaves every previously-landed file byte-identical — the live counterpart of AC 16 and proof that skip-if-present is a real checkpoint at this volume (Decision 7).

6. Record the MEASURED cost table (calls, rows per call, wall clock, observed inter-request spacing, per season and grain) and the 2019-20 observations into `reviews/endpoint-probe.md` with a `measured` label and a date, as the `## docs-delta` input to Phase 10 and the extrapolation base for the widening.

**Acceptance.**

- The dry-run's printed call count equals the real run's observed call count (AC 28).
- `uv run dbt build --project-dir transform --profiles-dir transform --target local` exits 0 through silver against the real three-season pilot, with every grain, containment, reconcile and SCD2 test green (AC 29).
- The second backfill run makes zero API calls and changes no landed file's content hash.
- The 2019-20 unequal-game-count assertion holds against the landed season and the observed spread is recorded.
- `uv run pytest -m network` exits 0 and prints the measured figures (AC 27).
- `uv run pytest -m "not network"` and `uv run dbt build --target ci` are STILL green — the local run must not have required a model change.

**Commit note.** green locally → /commit, staging ONLY the reviews/ evidence file. NOTHING under var/ may be staged: a full 2019-20 player log is tens of thousands of rows and .gitignore:16 is the only thing between it and a public repo. Inspect /commit's staged list by eye.

### Phase 10 — Docs, epistemic promotion and bookkeeping (MAIN THREAD), then the PR

**Goal.** Land exactly the doc corrections this work earned and no others, in the one place a build subagent structurally cannot do it (R16), and hand the PR to the user.

**Steps.**

1. MAIN-THREAD ONLY: docs/data-sources.md is denied to the data-engineer at .claude/agents/data-engineer.md:131 and facts route through `## docs-delta` (:216-235). Collect the docs-delta blocks from Phases 3 and 9 and route them here. Run `/update-docs` as the judgment gate.

2. EDIT BY CONTENT MATCH, NEVER BY THE SCOPE'S LINE OFFSETS — that file moved in the scoping commit. Current state: the epistemic blockquote at :5-11 is ALREADY corrected (it already says one endpoint has been called); the bulk-vs-per-game section at :38-68 is ALREADY promoted to `verified` with the measured table at :51-56 and the honest two-seasons caveat at :62-64. WHAT THIS WORK EARNS: extend the measured table to all three pilot seasons with the Phase-9 numbers, and promote the traditional-box-score availability row at :76 for the pilot range. Use docs/data-sources.md's OWN three-label vocabulary — verified / documented / unconfirmed (Decision 11) — not CLAUDE.md's five.

3. DO NOT BLANKET-PROMOTE. Every row for an endpoint this request did not call — play-by-play, shot chart detail, advanced box scores, the 2015-16 SportVU note — stays `unconfirmed`; AC 23 says a blanket promotion is a FAILURE of the criterion. On the rate-limit paragraph at :23-28, see gated decision 3: the recommendation is to record the measured six-call observation inside the paragraph while LEAVING the label `unconfirmed`, because gate-0-endpoint-probe.md:113-114 says four calls settle nothing about sustained-backfill behaviour and a six-call pilot barely improves on that.

4. AC 24 — resolve the dangling `docs/data-dictionary.md` reference. IT IS AT LINE 85 ('...and `docs/data-dictionary.md` records which columns are era-bounded'), NOT :69 as the scope says in three places. Per Decision 10 CORRECT THE SENTENCE; do not create the file — no landed column has its own availability cliff, so the dictionary would be empty. tests/test_doc_links.py structurally cannot catch this because the reference is backticked rather than linked (fenced/inline handling at :55, :69, :86), so it is a manual edit verified by grep.

5. AC 26 — correct the Phase-0 claims: README.md:11-14's status blockquote ('No pipeline code yet') and :130's roadmap row ('Box-score foundation — dimensional core, local end to end | Next'); CLAUDE.md:11's copy of the same claim, plus its Project Map now that src/nba_platform/, transform/models/, transform/tests/ and transform/seeds/ have contents. CLAUDE.md is 132 physical lines against the 200 cap at tests/test_agent_contract.py:41, so there is room.

6. AC 26 bookkeeping — advance PROJECT_SCOPE.md's and FEATURE_REQUEST.md's status blockquotes, set IMPLEMENTATION_PLAN.md's own status, and update the Index row at requests/feature-requests/README.md:100 (currently Stage `scoped`) to match. Status grammar is `intake` → `scoped` → `planned` → `implemented`.

7. Document layer promotion as tagged dbt selectors — `dbt build --select tag:bronze` then `--select tag:silver`. dbt_project.yml:32 and :40 already assign the tags and :18-19 already says promotion is gated on tests; this turns a comment into a runnable gate and gives the eventual Airflow DAG its task boundaries.

8. Record the deferred decisions WITH their trigger conditions so the next slice inherits a decision rather than rediscovering a trap: MERGE (the first in-progress season, or the first nightly run), widening past three seasons, playoffs, roster supplementation from commonteamroster, and the checkpoint store (revisit at Phase 5's ~30,000 play-by-play calls, which docs/data-sources.md:66-68 already names).

9. MAIN-THREAD: append what the build learned to `.claude/agents/data-engineer-memory.md` — the entries Phase 0's prune made room for. Respect the 120-line cap; if it is reached, report rather than prune.

**Acceptance.**

- `uv run pytest tests/test_doc_links.py tests/test_repo_structure.py` exits 0 after every doc edit (AC 21).
- `uv run pytest tests/test_agent_contract.py` exits 0 — CLAUDE.md under 200 physical lines, memory under 120.
- `grep -rn 'data-dictionary' docs/` returns nothing, or a real Markdown link to a real file (AC 24).
- grep confirms every endpoint row this request did not call still reads `unconfirmed`, spot-checked BY NAME rather than by count (AC 23).
- `grep -rn 'No pipeline code yet' README.md CLAUDE.md` returns nothing (AC 26).
- requests/feature-requests/README.md:100's Stage cell matches the artifacts' own status blockquotes (AC 26).
- Both new ADRs exist under docs/decisions/ with all five sections and non-empty cost sections, and both have Index rows (AC 25).
- `uv run pytest -m "not network"` and `uv run dbt build --target ci` are both still green.
- USER-RUN (AC 30): CI is green on the PR for all three required contexts at ops/branch-protection.json:4 — 'Lint, types, tests', 'dbt build', 'Secret scan'.

**Commit note.** green locally (doc-link + structure + agent-contract tests) → /commit. Expect /commit to run the full doc panel rather than the proportional one — this is the commit /update-docs exists for. Then STOP: the agent does not push, does not open the PR, and does not merge. Push, PR and merge stay the user's.

## 4. Testing & verification

FOUR PROOF SURFACES, AND THE PLAN MUST KEEP STRAIGHT WHICH ONE PROVES WHAT.

(1) OFFLINE PYTEST — `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing`, byte-identical to ci.yml:53. Covers the extraction half, which dbt cannot see: double-run landing immutability by hashing the whole landed tree before and after (AC 16, tests/test_landing_immutability.py); pacing and exponential backoff against a stubbed clock driven from config (AC 17, tests/test_client_pacing.py); resolve-by-name plus the src-purity grep for `parents[` and literal `var/` (AC 18, tests/test_config.py); dry-run/real call-count agreement (AC 28 offline half, tests/test_backfill_plan.py); and the ORDERED fixture-headers-vs-schema.yml drift guard in both directions (AC 19, tests/test_fixture_schema_drift.py). ALL of these live under `tests/`, a repo-level deny for the data-engineer subagent (.claude/agents/data-engineer.md:126) — main-thread work.

(2) DBT TESTS ON FIXTURES — `uv run dbt build --project-dir transform --profiles-dir transform --target ci`, byte-identical to ci.yml:76, the required check at ops/branch-protection.json:4. `data_tests: +severity: error` (dbt_project.yml:51-53) means a dbt WARNING is a RED build, so the `data_tests:` key and `arguments:`-nested generic-test args (transform/models/silver/README.md:28-32) are load-bearing, not stylistic.
  SELECTORS TO RUN AS LAYER GATES AND SPOT CHECKS:
  - `dbt build --select tag:bronze --target ci` then `--select tag:silver --target ci` — the promotion gate dbt_project.yml:18-19 describes in prose and :32/:40 already tags.
  - `dbt test --select source:nba_stats_landing+` — the bronze source contract (not_null on the columns the upstream promised, transform/models/bronze/README.md:30-33).
  - `dbt test --select fact_player_game` — unique_combination_of_columns [game_id, player_id] (AC 6) plus its relationships to dim_game / dim_player / dim_team.
  - `dbt test --select fact_team_game` — unique_combination_of_columns [game_id, team_id].
  - `dbt test --select dim_game dim_player dim_team` — unique + not_null on each declared key, not_null on season_type (AC 7).
  - `dbt test --select dim_player_team_stint` — unique_combination_of_columns [player_id, valid_from] and dbt_utils.mutually_exclusive_ranges partitioned by player_id with `gaps: 'allowed'` and `zero_length_range_allowed: true` (AC 8).
  - `dbt test --select test_type:singular` — the whole singular suite in one command.
  - `dbt test --select test_type:generic --target ci` — every schema test.

(3) DBT SINGULAR TESTS under transform/tests/, named `assert_<what_must_be_true>.sql` (transform/tests/README.md:28-33), each returning zero rows on pass: assert_bronze_row_count_matches_landed (AC 13), assert_latest_capture_wins (AC 15), assert_game_id_keeps_leading_zeros (AC 14), assert_every_game_has_exactly_two_teams plus the one-home-one-away check (AC 12), assert_fact_player_game_row_count_matches_bronze (the fan-IN sentry uniqueness structurally cannot catch), assert_fgm_never_exceeds_fga, assert_team_minutes_reconcile (conditional on the Phase-3 MIN finding), assert_2019_20_has_out_of_window_games, assert_player_points_reconcile_to_team (Decision 1's payoff), assert_player_team_matches_open_stint (AC 9), assert_stints_did_not_degenerate (AC 11), assert_known_trade_resolves_both_sides (AC 10).

(4) LIVE, NEVER IN CI — `uv run pytest -m network` (the marker at pyproject.toml:80-82; ci.yml:53 already excludes it): the Phase-3 completion probe and the column-set contract test that re-calls the endpoint and asserts the ordered column set still matches what bronze declares. This is the ONLY counter-pressure against R13 — every fixture is a frozen copy of an unversioned contract (docs/data-sources.md:18-21), so CI stays green for months after upstream renames a column. And `dbt build --target local` against the real pilot (Phase 9) is the only run that proves the grain at full-season volume (AC 29, R11).

NON-VACUITY DISCIPLINE — the thing most likely to make this suite lie.
  - EVERY fixture-backed test carries a ROW-COUNT FLOOR assertion so an over-trimmed sample cannot pass it on an empty set (R12, PROJECT_SCOPE.md:246).
  - The fixture trim rule is WHOLE GAMES, ROWS ONLY, over the same GAME_ID set at both grains. Trimming by arbitrary rows silently breaks the two-teams test, the team-minutes reconcile and the points reconcile.
  - The affiliation containment test is derived from the same observations it checks and is VACUOUS everywhere between game dates (R6); the seed-pinned known-trade test is what makes the pair non-vacuous.
  - THREE DELIBERATE NEGATIVE CHECKS, each run once and reverted, to prove the load-bearing tests can actually fail: flip the bronze dedup ordering to ascending (assert_latest_capture_wins must go red); drop one player row from a fixture (assert_player_points_reconcile_to_team must go red for exactly that team-game); collapse the stint builder to one row per player (assert_stints_did_not_degenerate must go red).

REGRESSION SAFETY. Nothing in the pipeline can regress — this slice creates it. What CAN regress is the existing four-module guard suite: tests/test_doc_links.py (every new Markdown link, ADR and reviews/ file), tests/test_repo_structure.py (transform/models/ must keep agreeing with dbt_project.yml at :63-77; `transform/seeds/` appearing does not break it because seeds is not a models/ subdirectory), tests/test_agent_contract.py (the 120-line memory cap and 200-line CLAUDE.md cap at :40-41), and tests/test_handoff_contract.py. Both doc guards run in every phase's acceptance from Phase 3 onward. After Phase 4, `uv run sqlfluff lint transform/models` is a permanent standing gate that did not exist before; after Phase 5, bronze is frozen and any later red in bronze is a regression.

PER-PHASE CADENCE, PRESCRIBED AND IDENTICAL. Implement → green locally (`uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing`, plus `uv run dbt build --project-dir transform --profiles-dir transform --target ci` AND `uv run sqlfluff lint transform/models` whenever models/fixtures/seeds changed, plus `uv run ruff check && uv run ruff format --check && uv run mypy` on any Python phase) → `/commit`, which stages per-path, refuses secrets and bulk data, runs the doc checks proportionally, shows the staged list and writes only on an explicit yes. Never `git commit` ad hoc; never merge, push or amend.

## 5. Decisions

The scope's eleven decisions are **settled upstream** and are not re-opened here. What follows is
this stage's additions: the seven gated decisions the planning panel raised, disposed by the user
on 2026-08-15, and the four blocker corrections applied to the phase text.

### Gated decisions, disposed 2026-08-15

**P1 — The agent's `tests/` deny token covers repo-root `tests/` only, not `transform/tests/`.**
The deny list's own gloss is *"the guards that catch you"* — that is the pytest suite an agent
must not be able to edit and then report green. dbt singular tests are model work, inside the
agent's declared target paths. **Write this into the spec explicitly**, because the definition
instructs the agent to *stop and report* rather than guess, and an ambiguous boundary costs a
whole dispatch round-trip. (A follow-up should tighten the definition's wording; not this slice.)

**P2 — `dim_player_team_stint` intervals are SEASON-BOUNDED.** Contiguous and gapless *within* a
season, with real gaps between the non-adjacent pilot seasons. Decision 3 said "contiguous and
gapless" and is silent here only because it reads as though the pilot seasons were adjacent —
they are not. LeBron James appears in all three, and a global run-collapse would emit one stint
spanning 2004 to 2020, which is not a defensible answer to *"what team was this player on"*. This
merges naturally once the widening makes seasons contiguous. The macro setting stays
`gaps: 'allowed'` — not because intra-season gaps exist, but because the between-season gaps are
real and expected.

**P3 — The rate-limit paragraph keeps its `unconfirmed` label.** Record the measured observation
inside the paragraph — what was run, when, how many calls — without promoting. Ten calls across
both probes say nothing about sustained-backfill behaviour, and AC 23 itself names a blanket
promotion as a *failure* of the criterion. Promoting here would destroy the one property that
file has.

**P4 — Verify the raw-JSON accessor before writing SQL. Done early, at the user's direction.**
Rather than branch in Phase 2, this was measured during planning: `get_dict()` returns the NBA
envelope intact (`resource` / `parameters` / `resultSets`, with `resultSets[0]` carrying `name` /
`headers` / `rowSet`), and `get_json()` round-trips to it. Decision 8's raw-JSON path is
**satisfiable without a DataFrame round-trip**, and the bronze decode can be written against a
known envelope rather than a guess. Honest limit recorded in the probe artifact: `get_json()` is
a re-serialization of the parsed body, not the literal wire bytes.

**P5 — The 2019-20 unequal-game-count assertion is deferred to the user-run `--target local`
build.** Keep only the outside-Oct–Apr half in CI, where it survives fixture trimming and carries
a row-count floor. Do **not** write a fixture-backed version of the game-count assertion: whole-
game trimming makes it pass vacuously forever, which is exactly the failure the row-count-floor
discipline exists to prevent. Measured for the record and now citable rather than hypothetical:
2019-20 team game counts run **64–75**, with **176 games outside an Oct–Apr window**; 2024-25 is
the 82/82 control.

**P6 — `dim_team` is one row per `team_id`, name resolved as-of the latest observation.** Settle
it against the cross-season distinct-pair count before writing the model, and write the as-of
hazard into the persisted description: *a 2003-04 Seattle game renders under today's franchise
name.* Measured so far: **within** a season the pairing is 1:1 (30 pairs, 30 ids, both probed
seasons), so the drift is strictly cross-season. The alternative — one row per `(team_id, season)`
— forces every fact join to carry season for a display concern with no consumer in this slice.

**P7 — The `data-engineer` subagent builds it, with the split written into the spec BEFORE
dispatch.** This is what Decision 9 asks for, and it is a **hard gate**: if the spec cannot assign
every one of the 30 acceptance criteria to *agent* / *main-thread* / *user-run* without ambiguity,
build main-thread with the same phase gates rather than discovering the boundary at the first
handoff. Roughly a third of the criteria land on denied paths, and fixture capture is a live
network call — so the split is real work, not a formality.

### Blocker corrections applied to the phase text

Each is objective — a dangling reference, a backward dependency, or a reversal of a disposed
decision — so each was applied rather than put to a vote. They appear inline as
**`[CORRECTED — binding]`**.

**F1 · Phase 8 reversed disposed Decision 3.** The drafted construction step closed `valid_to` at
the last observed game *within* a stint, which is observation-bounded — leaving the trade gap
uncovered so an as-of join inside it returns zero rows. That is precisely the outcome Decision 3
rejected, and the plan documented the contiguous rule while building the other one. Corrected:
each stint's `valid_to` is the day before the **next** stint's `valid_from`; only a season's final
stint closes at that season's last observed game.

**SEQ-01 · Phase 3's verification gate had a backward dependency.** Its live contract test read
`transform/models/bronze/schema.yml`, which Phase 4 creates. A cold agent gets a
`FileNotFoundError`, or writes a test that silently skips — in the phase whose entire purpose is
to gate the model phases. Corrected: Phase 3 asserts against the column lists recorded in the
probe artifact; Phase 4 re-points the test at the YAML as an explicit step.

**EXEC-02 · The error fixture would have reddened a required check.** AC 20 wants an empty/error
fixture, and the draft landed it inside the same partitioned tree the bronze source globs. DuckDB
unifies schema across a glob, so a payload with no `resultSets[0].headers` either fails
unification or injects a null-headers row — turning `dbt build`, a required context, red.
Corrected: error captures live outside the landing-shaped tree under `_error_cases/`, exercised
only by offline pytest against the client and landing writer, never by dbt.

**EXEC-03 · The one seam the PR hangs on was left to a guess.** The draft said "a `vars:` block
defaulted per target", but dbt's `vars:` is a flat mapping with no target-scoping syntax, and
whether `{{ target.name }}` even renders inside `dbt_project.yml` depends on
`DbtProjectYamlRenderer` constructing a `TargetContext` — an implementation detail, not a
contract. Verified independently at `.venv/Lib/site-packages/dbt/config/renderer.py:123`.
Corrected: put the conditional in `transform/models/bronze/sources.yml`, where the full Jinja
context is guaranteed, keep `vars:` out of it, and prove it by compiling against **both** targets
and diffing the compiled output.

### Decisions carried from the panel

- @{decision=Phase 3 is a VERIFICATION phase and precedes every model phase, closing the four AC-22 questions Gate 0 left open plus the two unprobed pilot seasons.; rationale=gate-0-endpoint-probe.md:104-116 says plainly that 2019-20 was never called; its Results (:52-66) and Columns (:93-102) sections nowhere report MIN's format, DNP rows, GAME_ID width, or the distinct (team_id, team_name) pair count that AC 22 requires. Four downstream pieces depend on those answers: the team-minutes reconciliation, fact_player_game's expected row count, AC 14's fixed-width pattern, and dim_team's grain. The repo's own epistemic rule — an unconfirmed claim about an endpoint's shape is a task, not a fact — applies to the gaps in its own evidence.}

- @{decision=Capture provenance rides in the PATH (`capture=<stamp>/` as a Hive-style segment), recovered by DuckDB, never by a bronze join to the manifest sidecar.; rationale=transform/models/bronze/README.md:10 says 'No joins. A bronze model reads exactly one source.' Latest-capture-wins dedup needs a per-row capture stamp, so joining the manifest would violate the layer contract on the repo's very first bronze model. Path-carried provenance keeps bronze single-source and 1:1 while making the dedup deterministic.}

- @{decision=The capture stamp in the path is colon-free compact UTC (`YYYYMMDDTHHMMSSZ`); the true tz-aware ISO timestamp lives inside manifest.json.; rationale=`:` is illegal in a Windows path and CLAUDE.md states Windows dev / Linux CI. A colon-bearing directory segment fails on the developer's machine and passes in CI, or vice versa. ruff DTZ (pyproject.toml:58) still enforces tz-awareness on the manifest timestamp.}

- @{decision=Bronze projects columns BY NAME via `list_position(headers, 'PLAYER_ID')`, never by ordinal index into rowSet.; rationale=Decision 8 requires landing the raw envelope, which is headers-plus-positional-rows. Indexing `rowSet[i][3]` bakes column ORDER into SQL against an explicitly unversioned upstream (docs/data-sources.md:18-21): a reordered column shifts every value one field over while every uniqueness test still passes. This is CLAUDE.md's resolve-by-name rule applied to columns, and it makes AC 19's ordered drift guard the alarm rather than a nicety.}

- @{decision=One bronze model lands in Phase 4, the second in Phase 5, and the source seam is spiked in DuckDB before any model is written.; rationale=ci.yml:78-85's sqlfluff guard flips from skipped to live on the first .sql, and .sqlfluff:12-16 templates through dbt at `target = ci` — so an unresolved source reddens both required checks from one root cause (R3), and the style rules at .sqlfluff:26-39 have never been applied to anything in this repo (R4). Absorbing both shocks on one file makes a red build attributable; landing five models first turns a 20-minute style pass into an afternoon.}

- @{decision=Fixtures adopt the partitioned landing layout, and tests/fixtures/README.md:27-34's flat layout section is edited in the same change.; rationale=AC 15 requires two captures of the same (season, grain) partition with different captured_at values. A flat `<descriptive-case>.json` name cannot express that. The descriptive-case requirement survives by moving into the capture manifest's provenance field. /update-docs audits exactly this kind of documented-convention divergence, so the README edit is part of the change, not a follow-up.}

- @{decision=Fixtures are trimmed by WHOLE GAMES, rows only — pick GAME_IDs and keep every row for those games at both grains.; rationale=R12 puts fixture fidelity and fixture size in tension. Trimming by arbitrary rows silently breaks assert_every_game_has_exactly_two_teams, assert_team_minutes_reconcile and assert_player_points_reconcile_to_team — they fail spuriously or pass on empty sets. Trimming structure produces a fixture that tests a shape the API does not return, which is the assumption most likely to be wrong.}

- @{decision=Stints are SEASON-BOUNDED: the run-collapse partitions by (player_id, season_id), and mutually_exclusive_ranges is configured `gaps: 'allowed'`, `zero_length_range_allowed: true`.; rationale=The pilot's three seasons are non-adjacent (2003-04, 2019-20, 2024-25) and LeBron James appears in all three, so a global run-collapse produces a stint spanning 2004 to 2020. Decision 3's 'contiguous and gapless' can only mean within-season here, and it merges naturally when widening makes the seasons contiguous. The macro arguments are not stylistic: mutually_exclusive_ranges.sql:20-22 shows `zero_length_range_allowed=False` selects a strict `<`, so a one-game stint (a ten-day contract with one appearance) FAILS on correct data, and :15-18 shows an invalid `gaps` value raises a compiler error.}

- @{decision=dim_team is one row per team_id with the name resolved as-of the latest observation, and the as-of hazard is written into its persisted description.; rationale=Settles R5 from a counted number (the Phase-3 distinct (team_id, team_name) pair count) rather than a naive distinct that either fails its own test or gets silently 'fixed'. The alternative — one row per (team_id, season) — forces every fact join to carry season. The cost, stated out loud: a 2003-04 Seattle game renders under today's franchise name. That is the same as-of-today-versus-as-of-game-date bug docs/data-sources.md:120-123 names for players, in the dimension nobody flags it for; +persist_docs (dbt_project.yml:22-24) carries the caveat onto the relation.}

- @{decision=dim_game's home/away is derived from MATCHUP's ' vs. ' / ' @ ' token, verified against the captured payload, and proved by AC 12 rather than asserted.; rationale=The scope says collapsing the two team rows avoids MATCHUP-string parsing (PROJECT_SCOPE.md:234). That is half true — it avoids parsing the OPPONENT out, but the token remains the only home/away signal in the payload. This is the one inferred structure in the slice, so it gets a Phase-3 verification and a zero-rows singular test rather than a comment.}

- @{decision=ADR 0008 is written in Phase 2 and ADR 0009 in Phase 8 — each alongside the decision it records, not batched at the end.; rationale=docs/decisions/README.md:34-35 requires the cost section be uncomfortable to write; an ADR written six phases later is reconstructed from memory rather than recorded from the decision. Both are main-thread steps because docs/decisions/ is denied to the data-engineer at .claude/agents/data-engineer.md:132.}

- @{decision=The 2019-20 unequal-team-game-count assertion is deferred to the `--target local` run in Phase 9 rather than written as a fixture-backed test.; rationale=Whole-games trimming destroys the property, so a fixture-backed version would pass vacuously forever — the exact failure the row-count-floor discipline exists to prevent. The out-of-Oct-Apr-window half DOES survive trimming and stays in CI.}

- @{decision=The plan document's own forward references to files later phases create sit inside fenced blocks.; rationale=tests/test_doc_links.py is a blocking CI check that scans live artifact bodies; it strips fenced blocks (:55, :69) and exempts `var/` targets (:86). A plan that links a not-yet-created path outside a fence reddens the required 'Lint, types, tests' check on the plan commit itself.}

## 6. Risks & gotchas

- THE MEMORY-PRUNE PREREQUISITE IS REAL AND ONE PLANNER MEASURED IT WRONG. MEASURED at planning time with `len(text.splitlines())`: `.claude/agents/data-engineer-memory.md` is 115 physical lines against the 120 cap at tests/test_agent_contract.py:40 — matching Decision 9's number. A count of 90 obtained from PowerShell's `Measure-Object -Line` is WRONG because that cmdlet skips blank lines; tests/test_agent_contract.py:35 and :133 say explicitly that the budget is physical lines. Roughly five lines of headroom, and a memory entry is four to five lines. Pruning is forbidden to the agent (memory file :56-63), so without Phase 0 everything the build learns after the first entry is lost.

- THE DISPATCH SPLIT IS NOT WHAT DECISION 9 ASSUMES. .claude/agents/data-engineer.md:123-133 makes `tests/`, `.github/`, `ops/`, `.claude/`, `CLAUDE.md`, `docs/data-sources.md` and `docs/decisions/` a repo-level deny, and :140-141 tells the agent to STOP rather than build a spec targeting them. Acceptance criteria 10 and 16-20 all land under `tests/` (including tests/fixtures/), 23-26 land under docs/, CLAUDE.md and README.md, :157-158 forbids hitting stats.nba.com live (so Phase 3's capture cannot be agent work), and :158-159 forbids `dbt deps`. Left unaddressed, the first handoff returns `could-not-do` for a third of the acceptance criteria.

- THE FIRST BRONZE MODEL REDDENS TWO REQUIRED CHECKS FROM ONE ROOT CAUSE. ci.yml:76 builds `--target ci` on `:memory:` (profiles.yml:24-27) from a checkout where var/ is gitignored (.gitignore:16), and .sqlfluff:12-16 templates through dbt at `target = ci` — so an unresolved bronze source fails BOTH `dbt build` and `sqlfluff`, both on the required-context list at ops/branch-protection.json:4. The failure presents as a file-not-found naming a path CI was never going to have, and reads as a model bug rather than missing fixture plumbing.

- SQLFLUFF FLIPS FROM SKIPPED TO BLOCKING ON THIS PR, against rules nothing in this repo has ever been linted under: duckdb dialect and 100-char lines (.sqlfluff:5-6), lowercase keywords/functions/identifiers (:26-33), explicit table AND column aliasing (:35-39), trailing commas (:23-24). Expect the first red build to be style, not logic. The guard at ci.yml:78-85 exists because sqlfluff errors rather than no-ops on an empty selection.

- external_location INTERPOLATES WITH str.format_map. dbt-duckdb's `create_from_source` runs `ext_location_template.format_map(source_config.as_dict())` under the default `newstyle` formatter (relation.py:60-62), so `{nba_landing_root}` is the placeholder and ANY LITERAL `{` or `}` in a DuckDB glob or struct literal raises a confusing KeyError at parse time that reads as a dbt bug. Set `formatter: template` deliberately if brace-globbing is needed.

- THE mutually_exclusive_ranges DEFAULTS RED-BUILD ON CORRECT DATA. `zero_length_range_allowed` defaults to False, which selects a strict `<` (mutually_exclusive_ranges.sql:20-22) — a single-game stint (valid_from == valid_to), exactly what a ten-day contract with one appearance produces, FAILS. And with season-bounded stints, gaps between non-adjacent pilot seasons are real, so `gaps` must be 'allowed'; anything outside {'not_allowed','allowed','required'} raises a compiler error (:15-18). Defaulting either argument makes the first green data look like a bug.

- THE PILOT'S SEASONS ARE NON-CONTIGUOUS AND THE SCD2 BUILDER WILL SILENTLY SPAN THE GAP. 2003-04, 2019-20 and 2024-25 have sixteen- and five-year holes between them. A naive global run-collapse produces a stint spanning 2004 to 2020, and this is not hypothetical: LeBron James appears in all three pilot seasons and the repo is anchored to his rookie year. The scope never names this.

- THE AFFILIATION CONTAINMENT TEST IS WEAKER THAN IT LOOKS AND EVERYTHING LEANS ON IT (R6). dim_player_team_stint is derived from the same (game_date, team_id) observations assert_player_team_matches_open_stint then checks, so a zero-row result proves the run-collapsing lost and reordered nothing — it CANNOT detect a wrong interpolation inside a trade gap, where there are no observations. It is vacuous everywhere between game dates. The seed-pinned known-trade test is the non-vacuous companion, which is why the player must come from the captured payload and never from memory.

- SCD2 GAP SEMANTICS ARE SILENTLY WRONG EITHER WAY AND DECISION 3 CHOSE WHICH WRONG. Contiguous gapless intervals mean a date inside a trade gap deliberately resolves to the OLD team; observation-bounded intervals would resolve to nothing, which the request names as the answer most likely to be silently wrong downstream. Partial mitigation is baked into core: fact_player_game's team_id comes from the observed box-score row, so the stint table is a lookup surface and never on the fact-correctness join path. Residual risk accepted — any future as-of join must handle the chosen failure mode and nothing in this slice forces it to.

- dim_team IS A SECOND SCD PROBLEM HIDING BEHIND THE FIRST, AND ITS as-of HAZARD IS THE ONE NOBODY FLAGS. 2003-04 and 2024-25 in one dataset puts Seattle/Oklahoma City, New Jersey/Brooklyn and Bobcats/Hornets under shared team_ids. R5 flags this as inferred from domain knowledge and UNVERIFIED in this repo — Gate 0 did not count the distinct (team_id, team_name) pairs. And the recommended grain means a fact-to-dim_team join renders a 2003-04 Sonics game as 'Oklahoma City Thunder', the exact bug docs/data-sources.md:120-123 names for players.

- THE FIRST RUNTIME DEPENDENCY BREAKS THE TOOLCHAIN THREE DISTINCT WAYS (R10). `uv sync --locked` (ci.yml:39) fails unless uv.lock is regenerated in the SAME commit — verified: pyproject.toml:9 is `[]` and uv.lock contains no nba_api, pandas or httpx entry, only a transitive `requests` at :1550. mypy is `strict = true` over src AND tests (pyproject.toml:70-74) with no override block, so an untyped nba_api surface or pandas Any-leakage errors unless isolated at one declared boundary. ruff DTZ (:58) makes a naive capture timestamp a lint error and PTH (:59) makes os.path one.

- LANDED-PAYLOAD SHAPE IS ASSUMED, NOT MEASURED. Decision 8 requires landing nba_api's RAW JSON response, but Gate 0 only exercised `get_data_frames()[0]` (gate-0-endpoint-probe.md:83-86) and nba_api is NOT currently installed in this venv (verified). The raw accessor's name and the exact envelope determine both the bronze SQL and the fixture shape. Phase 2 must verify it against the installed package before Phase 4 writes SQL against it, with an honest fallback recorded in ADR 0008.

- GAME_ID LEADING-ZERO CORRUPTION IS THE CLASSIC SILENT FAILURE. stats.nba.com game ids are zero-padded strings; numeric inference in read_json_auto destroys the padding while every join still 'works' and every uniqueness test still passes. AC 14's fixed-width pattern test is the only thing that catches it, and the width must be MEASURED in Phase 3, not guessed.

- THE SCOPE'S docs/data-sources.md CITATIONS ARE STALE AND A COLD IMPLEMENTER WILL TRUST THEM LITERALLY. That file was edited in the scoping commit. The dangling `docs/data-dictionary.md` reference is at line 85, not :69 (which the scope repeats in three places); the traditional-box-score era row is line 76, not :59; the rate-limit paragraph is :23-28; the bulk section is :38-68 and is ALREADY promoted to `verified`. Phase 10 must edit by content match, never by line offset.

- AC 23 NAMES A PROMOTION GATE 0 EXPLICITLY DID NOT EARN. It asks for the rate-limit paragraph to be promoted, but gate-0-endpoint-probe.md:113-114 says four calls tell you nothing about how the host behaves over a sustained backfill, and a six-call pilot barely improves on that. Promoting it anyway would destroy the one property that file has — and AC 23 itself calls a blanket promotion a FAILURE of the criterion.

- CI GREEN IS NOT PROOF OF THE GRAIN (R11). Fixtures are trimmed samples; a (game_id, player_id) duplicate existing only at full-season volume passes every automated check in Phases 4-8. AC 29's `--target local` run is user-run for exactly this reason, and treating CI green as proof of the grain is the most dangerous mistake available in this slice.

- THE docs/data-sources.md RELABEL SILENTLY DOES NOT HAPPEN IF THE BUILD AGENT OWNS IT (R16). The path is denied at .claude/agents/data-engineer.md:131 and facts route through `## docs-delta` (:216-235), while the request counts the relabel as an observable success signal. Phase 10 is marked MAIN-THREAD for this reason.

- SCOPE MASS (R17). First extraction code, first landing zone, first bronze models, six silver models, first fixtures, first seed, first singular tests, first runtime dependency, doc changes across four files and two new ADRs. ADR 0001 names exactly this failure mode. Defensible ONLY under the strict ordering probe → land → bronze → one fact end-to-end → widen, each green before the next. Phase 6 is the designated 'if it ships nothing else, it ships this' milestone; a horizontal build that writes all six silver models before any has run is how this stalls.

- SCOPE CREEP BACK INTO THE CUT ITEMS (R18). dim_date, the 23-season widening, playoffs, roster supplementation from commonteamroster, contract-type modeling, the checkpoint store, a shared bronze casing macro, and dbt docs lineage as a CI artifact are each individually cheap-looking and collectively double this slice. Every one is an explicit Non-Goal. The success condition is a green build and a correct traded-player lookup, not breadth.

- NO NBA DATA MAY REACH GIT BEYOND TRIMMED FIXTURES. A full 2019-20 player log is tens of thousands of rows; .gitignore:16 (var/) and the blanket ban at :18-29 are the only guards, and :30-32 are narrow whitelists, not a licence. Also `*.jsonl` and `*.ndjson` are ignored at :28-29 with NO counter-whitelist — a fixture written as NDJSON is silently uncommitted and CI fails on a missing file. Phase 9's commit is the highest-risk one: inspect /commit's staged list by eye.

## 7. Files to touch (checklist)

- @{path=pyproject.toml; change=MODIFY :9 — replace `dependencies = []` with `["nba_api"]` and rewrite the now-false comment at :11-13. ADD a scoped `[[tool.mypy.overrides]]` block for `nba_api.*` (and `pandas.*` if it leaks) with `ignore_missing_imports = true`; :70-74 is `strict = true` over src AND tests with no override block today.}
- @{path=uv.lock; change=REGENERATE in the same commit as the pyproject change. Verified: no nba_api, pandas or httpx entry today — only a transitive `requests` at :1550. ci.yml:39 runs `uv sync --locked` and goes red otherwise (AC 5).}
- @{path=src/nba_platform/config.py; change=NEW. Resolves NBA_ENV (.env.example:8), NBA_REQUEST_DELAY_SECONDS (:14) and NBA_MAX_RETRIES (:15) BY NAME; exposes landing_root, warehouse_path, pilot_seasons, and `landing_key(...)` producing the S3-key-shaped, colon-free prefix. The only module allowed to spell `var`; no `parents[N]`, pathlib only.}
- @{path=src/nba_platform/client.py; change=NEW. The single untyped boundary over nba_api. Minimum inter-request spacing and exponential backoff, both from config, injectable clock/sleep. Returns the RAW response body (Decision 8), never a get_data_frames() round-trip.}
- @{path=src/nba_platform/landing.py; change=NEW. `write_capture(...)`: write-once, skip-if-present (which IS the checkpoint), `--recapture` writes a NEW capture directory beside the first. Emits manifest.json — endpoint, parameters, tz-aware captured_at, HTTP status, row count, sha256, nba_api version, elapsed seconds.}
- @{path=src/nba_platform/backfill.py; change=NEW. The command a human runs: --seasons / --grains / --season-type / --dry-run / --recapture. --dry-run prints planned call count, pacing and estimated wall clock with zero requests; a real run emits the measured-cost run manifest.}
- @{path=src/nba_platform/fixtures.py; change=NEW. The recorder tests/fixtures/README.md:11-13 already tells the reader to use and which does not exist. Trims by WHOLE GAMES, rows only, preserving the resultSets/headers/rowSet envelope, and writes trim provenance into each capture manifest.}
- @{path=src/nba_platform/__init__.py; change=OPTIONAL MODIFY. The :1-10 docstring already reserves this surface; its checkpointing clause stays a forward-looking promise (Decision 7). Do NOT touch `__version__` at :12 — tests/test_repo_structure.py:52-60 pins it to pyproject.toml:3.}
- @{path=tests/test_config.py; change=NEW (MAIN THREAD — tests/ is denied to the agent). AC 18: landing root resolves through the config layer from NBA_ENV; landing_key contains no `:`; and the purity guard — no `parents[` and no literal 'var/' anywhere under src/nba_platform/.}
- @{path=tests/test_landing_immutability.py; change=NEW (MAIN THREAD). AC 16: double-run hash-set comparison over a tmp_path landing tree, plus a --recapture run proving the originals are byte-identical while a new capture appears.}
- @{path=tests/test_client_pacing.py; change=NEW (MAIN THREAD). AC 17: stubbed-clock pacing floor at NBA_REQUEST_DELAY_SECONDS and exponential backoff to NBA_MAX_RETRIES, both driven from env so a literal would fail.}
- @{path=tests/test_backfill_plan.py; change=NEW (MAIN THREAD). AC 28 offline half: --dry-run makes zero client calls and its printed count equals the stubbed real run's.}
- @{path=tests/test_fixture_schema_drift.py; change=NEW (MAIN THREAD). AC 19: each fixture's `resultSets[0].headers` equals the bronze schema.yml column list IN ORDER and in both directions, parsed from YAML, with a row-count floor.}
- @{path=tests/test_live_contract.py; change=NEW (MAIN THREAD), `@pytest.mark.network`. Re-calls the endpoint and asserts the ordered column set still matches bronze's declaration. Claims the unused marker at pyproject.toml:80-82 that ci.yml:53 already excludes.}
- @{path=tests/fixtures/nba_stats/league_game_log/; change=NEW directory of captured payloads in the partitioned `season=/grain=/season_type=/capture=` layout: 2024-25 modern, 2003-04 pre-tracking, 2019-20 bubble (with July-October dates), the pinned mid-season-trade case, an empty/error response, and a SECOND capture of one partition (the AC-15 enabler). Both grains over the same GAME_ID set, `.json` only (.gitignore:28-30).}
- @{path=tests/fixtures/README.md; change=EDIT the Layout section :27-34 — from the flat `<descriptive-case>.json` shape to the partitioned capture layout, stating that a flat name cannot express two captures of one partition. Relocate the descriptive-case requirement into the manifest's provenance field.}
- @{path=transform/dbt_project.yml; change=ADD a `vars:` block declaring `nba_landing_root`, defaulted per target — `../tests/fixtures` under ci, the config-layer landing root under local. Do NOT touch the layer configs at :20-47 or `+severity: error` at :49-53.}
- @{path=transform/models/bronze/sources.yml; change=NEW. THE seam — source `nba_stats_landing` with tables league_game_log_player and league_game_log_team, `meta.external_location` built from `{{ var('nba_landing_root') }}` and rendering as `read_json_auto(...)`. Verified mechanism: dbt/adapters/duckdb/relation.py:58-74. No literal path in any model.}
- @{path=transform/models/bronze/bronze__nba_stats__league_game_log_player.sql; change=NEW. Decode headers+rowSet, project the 32 ordered player-grain columns BY NAME (gate-0-endpoint-probe.md:99), lowercase, cast explicitly, game_id as VARCHAR, captured_at from the path, latest-capture-wins dedup on (game_id, player_id) via a row_number CTE.}
- @{path=transform/models/bronze/bronze__nba_stats__league_game_log_team.sql; change=NEW. Same shape over the 29 ordered team-grain columns (gate-0-endpoint-probe.md:95-97), dedup on (game_id, team_id). Core because it is the source of dim_game's home/away and of dim_team.}
- @{path=transform/models/bronze/schema.yml; change=NEW. The source contract per transform/models/bronze/README.md:30-33: endpoint, parameters, every column described, not_null on game_id/player_id/team_id/game_date/plus_minus, and the game_id fixed-width pattern test. `data_tests:` with `arguments:`-nested args.}
- @{path=transform/models/silver/dim_game.sql; change=NEW. One row per game_id from the team-grain model; game_date, season, season_type, home/away team ids derived from MATCHUP's ' vs. ' / ' @ ' token.}
- @{path=transform/models/silver/dim_team.sql; change=NEW. Grain settled from the Phase-3 distinct (team_id, team_name) pair count; recommended one row per team_id with name as-of the latest observation, with the as-of hazard in the persisted description.}
- @{path=transform/models/silver/dim_player.sql; change=NEW. One row per player_id — identity only (id, observed name, first/last observed game date). Description states in words that coverage is players who APPEARED.}
- @{path=transform/models/silver/fact_player_game.sql; change=NEW. One row per (game_id, player_id); team_id from the OBSERVED bronze row, never from a stint join. Materialized table with `unique_key` declared and the MERGE deferral trigger in the description.}
- @{path=transform/models/silver/fact_team_game.sql; change=NEW (Decision 1, reversing FEATURE_REQUEST.md:78). One row per (game_id, team_id) — the other half of the only cross-grain proof available.}
- @{path=transform/models/silver/dim_player_team_stint.sql; change=NEW. SCD2 affiliation, key (player_id, valid_from), season-bounded run-collapse, carrying team_id, season_id, valid_to, is_current, last_game_prior_team, first_game_new_team.}
- @{path=transform/models/silver/schema.yml; change=NEW. Every model's grain in prose AND a matching uniqueness test in the `data_tests:`/`arguments:` shape (AC 6, 7); mutually_exclusive_ranges on the stints with gaps:'allowed' and zero_length_range_allowed:true (AC 8); relationships from both facts to dim_game, dim_player and dim_team.}
- @{path=transform/models/silver/README.md; change=EDIT :52 — the Dimensions list names dim_date (cut by Decision 4) and omits dim_player_team_stint (required by Decision 2). Must land in the same change as the model.}
- @{path=transform/tests/README.md; change=EDIT :16 — 'an open interval in `dim_player`'s SCD2 history' now describes a model that no longer holds affiliation.}
- @{path=transform/tests/; change=NEW .sql files: assert_bronze_row_count_matches_landed (AC 13), assert_latest_capture_wins (AC 15), assert_game_id_keeps_leading_zeros (AC 14), assert_every_game_has_exactly_two_teams (AC 12), assert_fact_player_game_row_count_matches_bronze (the fan-IN sentry), assert_fgm_never_exceeds_fga, assert_team_minutes_reconcile (conditional on the MIN finding), assert_2019_20_has_out_of_window_games, assert_player_points_reconcile_to_team, assert_player_team_matches_open_stint (AC 9), assert_stints_did_not_degenerate (AC 11), assert_known_trade_resolves_both_sides (AC 10).}
- @{path=transform/seeds/known_trade_expectations.csv; change=NEW directory + seed (verified: transform/seeds/ does not exist; .gitignore:32 already whitelists its CSVs and dbt_project.yml:10 already declares seed-paths). The pinned player_id, both team_ids and a date on each side of the trade — taken from the captured payload, never from memory.}
- @{path=docs/decisions/0008-landing-layout-and-capture-manifest.md; change=NEW (AC 25, MAIN THREAD). Landing layout, colon-free capture stamp, capture manifest, path-carried provenance, raw-JSON-not-DataFrame, bronze latest-capture-wins, and the folded-in landing-layout convention note. Five sections per docs/decisions/README.md:19-25 with an uncomfortable cost section (:34-35).}
- @{path=docs/decisions/0009-scd2-affiliation-interval-boundaries.md; change=NEW (MAIN THREAD). The within-season contiguous-gapless rule, the season-bounded choice, the macro's gap/zero-length posture, that an in-gap date deliberately resolves to the OLD team, and the containment test's vacuity between game dates.}
- @{path=docs/decisions/README.md; change=EDIT the Index at :39-47 — add rows 0008 and 0009 (the Index currently ends with 0007 at :47).}
- @{path=docs/data-sources.md; change=MAIN-THREAD EDIT (denied to the subagent at .claude/agents/data-engineer.md:131). Extend the measured bulk table (:47-64) to all three pilot seasons; promote the traditional-box-score era row at :76; LEAVE the rate-limit paragraph at :23-28 `unconfirmed` (see gated decision 3); correct the dangling `docs/data-dictionary.md` sentence at :85 (NOT :69) without creating the file, per Decision 10. Every uncalled endpoint stays `unconfirmed`.}
- @{path=README.md; change=EDIT :11-14 (the Phase-0 status blockquote, 'No pipeline code yet') and :130 (the roadmap row '| **1** | Box-score foundation — dimensional core, local end to end | Next |') — AC 26.}
- @{path=CLAUDE.md; change=EDIT :11 ('**No pipeline code yet.**') and the Project Map now that src/nba_platform/, transform/models/, transform/tests/ and transform/seeds/ have contents. Must stay under the 200 physical-line cap at tests/test_agent_contract.py:41 (measured 132 today).}
- @{path=requests/feature-requests/box-score-foundation/reviews/endpoint-probe.md; change=NEW (AC 22). The Phase-3 completion probe with a `measured` label answering every AC-22 question by name, extended in Phase 9 with the measured backfill cost table and the 2019-20 observations.}
- @{path=requests/feature-requests/box-score-foundation/IMPLEMENTATION_PLAN.md; change=NEW — this plan. Opens `> **Status:** planned · created 2026-08-14 · decided · next: implement`. Forward references to files later phases create must sit inside fenced blocks or tests/test_doc_links.py reddens a required check.}
- @{path=requests/feature-requests/box-score-foundation/PROJECT_SCOPE.md; change=EDIT :1 — the status blockquote advances off `next: plan`.}
- @{path=requests/feature-requests/box-score-foundation/FEATURE_REQUEST.md; change=EDIT the status blockquote per AC 26.}
- @{path=requests/feature-requests/README.md; change=EDIT the Index row at :100 (currently Stage `scoped`) — advance to `planned`, then `implemented`, matching the artifacts' own status headers.}
- @{path=.claude/agents/data-engineer-memory.md; change=MODIFY (MAIN THREAD). Phase 0: prune from a MEASURED 115 physical lines to ~95-100 under the 120 cap. Phase 10: append what the build learned. The agent may never do either itself (:56-63).}

## 8. Conventions (bake these in)

- RESOLVE BY NAME, NEVER HARDCODE. In dbt: bronze reaches the landing zone only through `source()` and silver only through `ref()`; the ONE target-aware indirection lives in transform/models/bronze/sources.yml as `meta.external_location` built from a dbt var, with no literal path in any model. In Python: every path, season list, delay and retry count resolves through src/nba_platform/config.py from the keys .env.example:8,14,15 declares — no literal 'var/' and no `parents[N]` walk anywhere under src/ (AC 18's purity guard). tests/test_repo_structure.py:19 uses parents[1] but that is a test-file locator and is not precedent.

- THE LANDING ZONE IS IMMUTABLE. Raw payloads are written once and never mutated: an existing capture partition is SKIPPED, never overwritten, and a deliberate re-pull writes a NEW `capture=<stamp>/` directory beside the first. AC 16 mechanizes it as a double-run hash-set comparison rather than leaving it as prose, and every write emits a manifest (endpoint, parameters, tz-aware captured_at, status, row count, sha256) so the invariant is auditable.

- BRONZE IS 1:1 WITH THE SOURCE. Typing, lowercase casing and latest-capture-wins dedup on the natural key — nothing else. No joins (which is why capture provenance rides in the path, not in a manifest join), no business logic, no renaming beyond casing, no filtering (transform/models/bronze/README.md:10-15). If bronze and the landed JSON disagree, bronze is wrong (:17-19) — AC 13 makes that executable. Naming is `bronze__<source>__<endpoint>` (:23).

- SILVER DECLARES ITS GRAIN AND PROVES IT. Every model states its grain in prose in schema.yml AND enforces it with a uniqueness test whose columns match the prose (AC 6, 7), copied from the worked block at transform/models/silver/README.md:13-23 — `data_tests:` (not `tests:`) with generic-test arguments nested under `arguments:` (:28-32). dbt_project.yml:51-53 sets `+severity: error`, so the wrong shape is a red build, not a warning.

- FACTS ARE MERGE-ON-KEY. This slice deliberately diverges — full refresh for three finalized pilot seasons — and the divergence is DECLARED in three places (this plan, the model description, the widening follow-on) with `unique_key` already configured and the trigger written as a sentence: *the first in-progress season, or the first nightly run, requires MERGE first.* An undeclared divergence becomes debt the moment it stops being written down, and /update-docs audits exactly this.

- TRACKING COLUMNS ARE STRUCTURALLY ABSENT BEFORE 2013-14 — but Gate 0 measured that this endpoint carries no tracking-derived column and that PLUS_MINUS is present in 2003-04 with zero nulls, so the boundary does not bite this request. That measurement is recorded in the bronze schema.yml description so a future reader does not re-litigate it, and no era-nullable machinery is built speculatively.

- LABEL YOUR EPISTEMICS, AND PROMOTE PER-ENDPOINT. Use docs/data-sources.md's own three-label vocabulary (verified / documented / unconfirmed) per Decision 11. Promote only what was actually run, naming what was run and when; every row for an endpoint this request did not call stays `unconfirmed`. A blanket promotion is a FAILURE of AC 23.

- AGENTS COMMIT ONLY THROUGH /commit. Every phase ends at a /commit-gated checkpoint on a green local run. Never `git commit` ad hoc, never merge, push or amend — those stay the user's. `main` is protected and everything lands by PR with green checks (ops/branch-protection.json:4).

- SUBAGENTS GET READ-ONLY GIT. No checkout/reset/restore/clean/stash or anything that discards working-tree state. Branch creation and the PR are user actions; a destructive-git NEED bubbles back up.

- USER-RUN FOR ANYTHING BILLABLE OR LIVE. Nothing here spends cloud money (NBA_ENV=local, DuckDB, no credentials) — say so explicitly so the widening does not inherit a false precedent — but the live pilot backfill, the `--target local` build and the PR are user-run (AC 27-30), and the data-engineer subagent may never hit stats.nba.com or run `dbt deps` (.claude/agents/data-engineer.md:157-159).

- NO BULK DATA IN GIT. Only trimmed fixtures, whitelisted at .gitignore:30-32. `var/` is gitignored (:16), `*.jsonl`/`*.ndjson` are ignored with no counter-whitelist (:28-29) so fixtures must be `.json`, and /commit's staged list is inspected by eye on every fixture or backfill commit.

- MECHANICAL CHECKS LIVE IN CI; JUDGMENT LIVES IN /update-docs. Do not add lint/type/test/sqlfluff steps to the doc gate, and do not ask CI to judge whether the prose still describes the repo. Renaming a CI job silently breaks branch protection — the display names at ci.yml:27/:56/:88 must stay byte-identical to ops/branch-protection.json:4.

- VERTICAL SLICES, NOT HORIZONTAL LAYERS — with one declared divergence. This slice terminates at silver (PROJECT_SCOPE.md:118); gold keeps its README and stays empty. The mitigation that keeps it honest is no widening until a slice reaches a consumer. Within the slice, Phase 6 is the mandatory end-to-end milestone before anything widens.

## 9. Data contracts touched

This slice registers the repo's first source and its first six models. All five contracts are
settled by measurement rather than assertion — see
[`reviews/gate-0-endpoint-probe.md`](reviews/gate-0-endpoint-probe.md).

**Source.** `nba_stats.league_game_log`, the `leaguegamelog` endpoint family, at two grains
(`PlayerOrTeam=P` and `=T`), Regular Season only. Registered in
`transform/models/bronze/sources.yml` behind the target-aware seam.

**Grain.** `fact_player_game` is one row per `(game_id, player_id)` — **verified**, zero
duplicates across all three pilot seasons including the bubble and a trade-heavy season.
`fact_team_game` is one row per `(game_id, team_id)`. `dim_player_team_stint` is one row per
`(player_id, season_id, valid_from)`, season-bounded per P2. `dim_team` is one row per `team_id`
per P6. Each is declared in prose in `schema.yml` **and** proven by a uniqueness test, in the
`data_tests:` + `arguments:` shape the silver README now carries.

**Keys.** `GAME_ID` is a **zero-padded 10-character string** — measured. It must land and stay a
string; casting to integer destroys the key. `PLAYER_ID` and `TEAM_ID` are integers.

**Era coverage.** The 2013-14 tracking boundary **does not bite this request**: no
tracking-derived column appears in this endpoint at either grain, and `PLUS_MINUS` — the column
flagged as the likeliest early-availability cliff — is present in 2003-04 with **zero nulls**.
Column sets are identical across 2003-04, 2019-20 and 2024-25. Era-nullable handling is therefore
genuinely out of scope here rather than deferred. The real era hazards are calendar-shaped, not
column-shaped: 2019-20 spans to **2020-08-14** with **unequal** team game counts (64–75).

**Update semantics.** Full-refresh for the pilot, per Decision 5 — all three seasons are long
finalized, so restatement is not a live concern. `unique_key` is declared now so the switch to
`MERGE` is a config change. The trigger is named, not implied: **the first in-progress season, or
the first nightly run, requires `MERGE` first.** This is a deliberate, recorded divergence from
the repo's headline `MERGE`-on-key rule.

**Cost.** ~6 calls for the three-season pilot at both grains; ~46 for the full 23-season widening.
Measured at 0.6s pacing, ~0.3–0.6s per call. The factor-of-1000 risk that sized this request is
retired.

## 10. Code-grounding verification

The stage-3 panel ran at full strength: **3/3 planners, 2/2 code-grounded adversaries, 1/1
meta-audit, no degraded lenses** — 48 findings, 4 blockers, 15 majors, across **89 cited
references**.

The four blockers are dispositioned under §5 and applied inline in §3. Beyond those, the main
thread independently re-verified a sample of the panel's citations rather than taking the
grounding on faith:

| Cited claim | Independent result |
|---|---|
| `docs/data-dictionary.md` reference is at `:85`, not the scope's `:69` | **Confirmed** — the scoping commit shifted the file; the scope's citation is stale |
| `transform/dbt_project.yml` has no `vars:` block | **Confirmed** |
| `DbtProjectYamlRenderer` builds a `TargetContext` at `renderer.py:123` | **Confirmed** — the adversary read dbt's own source |
| `pyproject.toml:9` is `dependencies = []` | **Confirmed** |
| Pilot seasons ≠ the seasons Gate 0 probed | **Confirmed, and it was the main thread's error** — 2023-24 is not a pilot season and 2019-20 was never called. Corrected by the completion probe before this plan was written. |

**5 of 89 re-verified independently; 5 confirmed; 0 refuted.** The panel's grounding held
everywhere it was checked, including where it corrected upstream work.

## References

- [`PROJECT_SCOPE.md`](PROJECT_SCOPE.md) — the decided contract: 30 acceptance criteria, the
  tiered scope, and eleven disposed decisions. Consume it; do not re-open it.
- [`FEATURE_REQUEST.md`](FEATURE_REQUEST.md) — context, and the observable signals.
- [`reviews/gate-0-endpoint-probe.md`](reviews/gate-0-endpoint-probe.md) — the only measured
  endpoint evidence, both probes, and what remains unsettled.
- `reviews/plan-proposals.md` · `reviews/plan-adversarial.md` — the panel trail. **Gitignored and
  machine-local**, so referenced as inline code rather than as links.
- [`transform/models/bronze/README.md`](../../../transform/models/bronze/README.md) ·
  [`transform/models/silver/README.md`](../../../transform/models/silver/README.md) — the layer
  contracts, including the `data_tests:` + `arguments:` shape every silver model copies.
- [`transform/tests/README.md`](../../../transform/tests/README.md) — the singular-test invariant
  menu; its SCD2 line needs editing alongside the stint model.
- [`docs/data-sources.md`](../../../docs/data-sources.md) — the belief catalog. Read the current
  line numbers, not the scope's.
- [`.claude/agents/data-engineer.md`](../../../.claude/agents/data-engineer.md) — the builder's
  rulebook: write allowlist, deny set, tool allowlist, and the docs-delta routing.
- [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) ·
  [`ops/branch-protection.json`](../../../ops/branch-protection.json) ·
  [`pyproject.toml`](../../../pyproject.toml) — the real gates.
