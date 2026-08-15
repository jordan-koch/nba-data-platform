# Dispatch split — box-score-foundation

> **Status:** evidence · created 2026-08-15 · Phase 0 output · satisfies gated decision P7's hard gate

The `data-engineer` subagent builds this slice (Decision 9, gated decision P7). P7 makes the split a
**hard gate**: if every one of the 30 acceptance criteria cannot be assigned to *agent* /
*main-thread* / *user-run* without ambiguity, the build goes main-thread instead. This document is
that assignment. It is written **before** the first dispatch so the agent never has to guess at
`.claude/agents/data-engineer.md:140-141` ("stop and report" rather than build into a denied path).

## 1. Boundary rulings

Three boundaries were ambiguous. Each is settled here in words, and each ruling is quoted into the
per-phase spec the agent receives.

**R-A · The bare `tests/` deny token covers repo-root `tests/` ONLY — not `transform/tests/`.**
This is gated decision P1. The deny list's own gloss at `.claude/agents/data-engineer.md:126` is
*"the guards that catch you"* — that is the pytest suite an agent must not be able to edit and then
report green. dbt singular tests are model work, inside the agent's declared target paths, and they
are executed by `dbt build`, which the agent already runs. So `transform/tests/*.sql` is
**agent-buildable**; everything under repo-root `tests/` — including `tests/fixtures/` — is denied.

**R-B · `uv run sqlfluff lint transform/models` is authorized; `sqlfluff fix` is not.**
The tool allowlist at `.claude/agents/data-engineer.md:148-155` names pytest, ruff, ruff format,
mypy, dbt build and read-only git, and the governing sentence at `:145` is *"You may run read and
verify commands."* `sqlfluff lint` spends nothing, hits no network and mutates nothing, so it is
inside that sentence and merely absent from an illustrative list. It becomes a **required** check on
this branch (`.github/workflows/ci.yml:78-85` flips from skipped to live on the first `.sql` file),
so an agent that cannot run it cannot verify its own model work. `sqlfluff fix` **rewrites files**
and is therefore excluded — style fixes are hand edits like any other.

**R-C · `uv lock` / `uv sync` are network calls and stay MAIN-THREAD.**
`.claude/agents/data-engineer.md:157-159` forbids the agent anything that hits the network and names
`dbt deps` as the worked example — *"if a package is missing, report it under `could-not-do` rather
than fetching it."* Dependency resolution against PyPI is the same class of call. So `pyproject.toml`
and `uv.lock` are **main-thread** despite `pyproject.toml` being nominally writable: they must land
in one commit (`ci.yml:39` runs `uv sync --locked`), and the half that needs network cannot be the
agent's. This narrows the agent's surface from what `IMPLEMENTATION_PLAN.md` §2.7 sketched, and is
the one deviation from it recorded at Phase 0.

## 2. The agent's buildable surface

```
src/nba_platform/                             config, client, landing, backfill, fixtures
transform/models/bronze/                      sources.yml, schema.yml, 2 models
transform/models/silver/                      schema.yml, 6 models, README.md edit
transform/tests/                              12 singular tests, README.md edit   (per R-A)
transform/seeds/                              known_trade_expectations.csv
requests/feature-requests/box-score-foundation/reviews/   its own handoff only
.claude/agents/data-engineer-memory.md        its own memory (append; never prune)
```

Denied to it, and therefore main-thread for the whole build: all of repo-root `tests/` (including
`tests/fixtures/`), `.github/`, `ops/`, the rest of `.claude/`, `CLAUDE.md`, `README.md`,
`docs/data-sources.md`, `docs/decisions/`, `pyproject.toml`, `uv.lock`, and all `requests/`
bookkeeping outside its own handoff.

Forbidden **actions** regardless of path: any live call to `stats.nba.com` (so the Phase 3 completion
probe and the whole fixture capture are main-thread), `dbt deps`, `uv lock`/`uv sync`, `sqlfluff fix`,
any working-tree-mutating or history-rewriting git, and `/commit`.

## 3. Criterion assignment — all 30, none unassigned

`A` = data-engineer subagent · `M` = main thread · `U` = user-run. A split row names who owns which
half; no row is unassigned, and no row is owned by two parties without the seam being stated.

| # | Criterion (abbreviated) | Owner | Why / seam |
|---|---|---|---|
| 1 | `pytest -m "not network" --cov` exits 0 | **M** | Every module it runs lives under repo-root `tests/`. Agent *runs* it as verification; it cannot author it. |
| 2 | `dbt build --target ci` exits 0 | **A** | Models, sources, singular tests are all its surface; the command is in its allowlist. |
| 3 | `sqlfluff lint transform/models` exits 0 | **A** | Its own `.sql`. Authorized by R-B, lint only. |
| 4 | `ruff check` / `ruff format --check` / `mypy` exit 0 | **A** | `src/nba_platform/` is its surface; all three commands are in its allowlist. |
| 5 | `uv sync --locked` exits 0 | **M** | R-C — lock regeneration is a network resolve. |
| 6 | `fact_player_game` unique on `[game_id, player_id]` | **A** | `transform/models/silver/schema.yml`. |
| 7 | Every silver model: prose grain + matching uniqueness test | **A** | Same file. |
| 8 | `mutually_exclusive_ranges` on the stints | **A** | Same file; both macro arguments set explicitly. |
| 9 | `assert_player_team_matches_open_stint.sql` returns zero rows | **A** | `transform/tests/` per R-A. |
| 10 | Known mid-season trade resolves on both sides | **split — M pins, A builds** | The player, both team_ids and both boundary dates come from the **captured payload** (Phase 3, network → M). Given those values, the seed CSV and `assert_known_trade_resolves_both_sides.sql` are A's. M hands the pinned row to A in the Phase 8 spec. |
| 11 | `assert_stints_did_not_degenerate.sql` | **A** | `transform/tests/`. |
| 12 | `assert_every_game_has_exactly_two_teams.sql` | **A** | `transform/tests/`. |
| 13 | Bronze row count matches landed | **A** | `transform/tests/`. |
| 14 | `game_id` keeps leading zeros | **split — M measures, A builds** | The fixed-width pattern uses the width **measured** in Phase 3 (M); the test is A's. Never guessed. |
| 15 | Latest-capture-wins on two captures of one partition | **split — M captures, A builds** | The second-capture fixture is M's (denied path + live capture); the dedup CTE and the test are A's. |
| 16 | Offline landing-immutability pytest | **M** | `tests/test_landing_immutability.py`. A builds the `landing.py` behaviour it proves. |
| 17 | Offline pacing/backoff pytest | **M** | `tests/test_client_pacing.py`. A builds `client.py`. |
| 18 | Offline resolve-by-name pytest + src purity guard | **split — M builds the guard, A must satisfy it** | The guard greps A's own output for `parents[` and a literal `var/`. Stated in A's spec as a build constraint so it is not discovered as a red. |
| 19 | Fixture/schema ordered drift guard | **M** | `tests/test_fixture_schema_drift.py`. Reads A's `schema.yml` — A is told the guard exists and is order-sensitive in both directions. |
| 20 | The fixture corpus | **M** | `tests/fixtures/` is denied **and** capture is a live call. Wholly M. |
| 21 | `test_doc_links` + `test_repo_structure` green after doc edits | **split** | A owns the two edits inside its surface — `transform/models/silver/README.md:52` and `transform/tests/README.md:16`. Every other doc edit is M's. M verifies. |
| 22 | `reviews/endpoint-probe.md` with a `measured` label | **M** | Live network. |
| 23 | `docs/data-sources.md` label promotion, no blanket promote | **M** | Denied path (`:131`); facts route to M through A's `## docs-delta`. |
| 24 | Dangling `docs/data-dictionary.md` reference resolved | **M** | Denied path. |
| 25 | ADR 0008 (landing layout + manifest) | **M** | `docs/decisions/` denied (`:132`). |
| 26 | Bookkeeping: README, CLAUDE.md, status blockquotes, Index | **M** | `CLAUDE.md` and `README.md` denied; `requests/` bookkeeping is M's. |
| 27 | `pytest -m network` live probe prints measured figures | **M** | Live `stats.nba.com` call — forbidden to A at `:157-158`. Runnable from this environment (probe measured 0.6s), so M, not U. |
| 28 | `--dry-run` count equals the real run's count | **split — A builds, M tests offline, U proves live** | `backfill.py` is A's; `tests/test_backfill_plan.py` is M's; the live equality is U's in Phase 9. |
| 29 | Live pilot backfill + `dbt build --target local` green | **U** | Full-season live extraction. |
| 30 | CI green on the PR for all three required contexts | **U** | Push, PR and merge stay the user's. |

**Totals:** A owns 9 outright and half of 6 more; M owns 13 outright and the other half of 6; U owns
2 outright and half of 1. **Zero unassigned.** The P7 gate is satisfied — dispatch proceeds.

## 4. Dispatch cadence

One dispatch per phase, not one for the build. Each phase's spec carries: the phase's steps verbatim
from `IMPLEMENTATION_PLAN.md` §3 including any `[CORRECTED — binding]` clause, the three boundary
rulings above, the phase's acceptance commands, and any value M measured that A needs (the game_id
width, the pinned trade row, the distinct team-pair count). A returns a v1 handoff to
`requests/feature-requests/box-score-foundation/reviews/`; M reads it, does its own half, runs the
phase acceptance, and gates on `/commit` before the next dispatch.

Phases with no agent surface are not dispatched at all: **Phase 0** (this document), **Phase 3**
(network capture, except `src/nba_platform/fixtures.py` which A writes in advance), **Phase 9**
(user-run) and **Phase 10** (denied paths end to end).
