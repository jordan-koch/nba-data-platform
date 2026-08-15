# Data-engineer memory

Implementation ergonomics, learned the hard way. Read this before you build; append to it
when something costs you time that it should not cost the next session.

## What belongs here

Things that make *building* here go wrong: client and library shapes, column-casing
surprises, tooling traps, commands that behave differently than documented, harness
behaviour. Facts an analyst would never care about but an implementer rediscovers every
session.

## What routes elsewhere — do not put these here

- **Data facts** — endpoint shapes and parameters, era and availability boundaries,
  rate-limit behaviour, what a column actually contains. These go to `docs/data-sources.md`
  via your handoff's `docs-delta` section. Never here: that file is audited by the doc gate
  and this one is not, so a data fact recorded here means the repo holds two answers and
  the gate checks one.
- **Repo-wide scar tissue** — a trap that binds every agent, not just you: `CLAUDE.md`
  Constraints & Gotchas, via `docs-delta`.
- **Decisions and their costs** — `docs/decisions/`, via `docs-delta`.

## Entry format

One bullet per entry, opening line a fixed shape so it can be checked mechanically:

```
- **YYYY-MM-DD** · `label` · <the claim> · evidence: <pointer> · tag: <routing tag>
```

Continuation lines are indented under the bullet. Keep an entry to about four lines.
`label` is one of this repo's five — `measured`, `verified`, `inferred`, `assumed`,
`unconfirmed`. An `assumed` claim written as `verified` is worse than no entry.

**Paths are inline code, never markdown links** — the link checker scans only markdown-link
syntax, so a backticked path is invisible to it. **Cite a repo artifact, never raw environment
output**: this file is committed and the repo is public.

## The budget — two numbers, two jobs

**~120 physical lines is the curation target**, enforced by judgment at the `/update-docs`
sweep before merge. **250 is the runaway ceiling**, enforced mechanically in CI.

**Append freely while you work.** Do not ration yourself toward 120 — that is how a build
loses what it learned in its last three phases. **At the ceiling, append nothing**: report
the entry plus *"memory at cap, pruning needed"* under `still-open`.

**Pruning is a main-thread decision, never yours**, made once at the end. Prune what is now
enforced by code, by a failing test, or by a comment at its point of use; keep what would
cost the next session real time.

## Entries

- **2026-08-14** · `assumed` · PowerShell 5.1's `Set-Content` and `Out-File` mangle UTF-8;
  write files with the Write/Edit tools instead. · evidence:
  `.claude/skills/implement-plan/SKILL.md` · tag: `tooling-trap`

- **2026-08-15** · `measured` · Three PowerShell counting/quoting traps. `Get-Content` decodes
  UTF-8 as ANSI (box-drawing chars measure 3x). `Measure-Object -Line` skips blank lines, so it
  under-reports against a physical-line budget — use `(Get-Content f).Count`. And `->> '$'` inside
  a **double-quoted** string loses the `$`, so every DuckDB key returns NULL and a probe gives a
  coherent but FALSE answer — use a single-quoted here-string. · evidence: Phase 5 probes · tag:
  `tooling-trap`

- **2026-08-14** · `measured` · The `CLAUDE.md` and git status injected into your context are a
  snapshot from the **parent session's start** and can be commits behind disk. Inherited context
  is indistinguishable from something you verified — **read from disk before asserting repo
  state.** · evidence:
  `requests/feature-requests/data-engineer-agent/reviews/proving-run-a-verification.md` · tag:
  `harness-behaviour`

- **2026-08-14** · `measured` · In agent frontmatter the shell tool is **`PowerShell`**, not
  `Bash` — declaring `Bash` silently yields an agent with no shell at all. A new agent definition
  is also not spawnable immediately after being written ("Agent type not found" means *not yet*). ·
  evidence: `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md` · tag:
  `harness-behaviour`

- **2026-08-14** · `verified` · The bundled `.claude/skills/**/tests/*.mjs` guards are **not**
  run by CI — no Node step exists — so they execute only when someone remembers. Guards that must
  actually enforce belong under `tests/`. Relatedly, CI lints **`transform/models` only**, so
  singular tests under `transform/tests` are never linted; run them by hand. · evidence:
  `.github/workflows/ci.yml` · tag: `ci-behaviour`

- **2026-08-14** · `measured` · dbt 1.12 warns on top-level generic-test args: nest them under
  `arguments:`. `tests:` is not deprecated, but `data_tests:` replaced it in dbt 1.8. With
  `+severity: error` a warn is a RED build. · evidence:
  `transform/models/silver/README.md` · tag: `tooling-trap`

- **2026-08-15** · `measured` · DuckDB identifiers are case-insensitive **including struct
  fields**, so `resultsets[1].rowset` resolves against `read_json_auto`'s camelCase columns.
  Writing the envelope decode all-lowercase satisfies `.sqlfluff` with no quoting. Lists are
  **1-indexed**. · evidence:
  `transform/models/bronze/bronze__nba_stats__league_game_log_player.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · **Never select `headers` alongside `unnest(rowset)`** — it
  broadcasts a 32-element array onto every row (~2.3M strings over three seasons) and dies with
  `Out of Memory` at 91s, after passing in 0.06s on trimmed fixtures. Resolve `list_position`
  once per file, before the unnest, and carry the integers: 0.19s at full volume. · evidence:
  `transform/tests/assert_bronze_row_count_matches_landed.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · **A JSON element cast to VARCHAR keeps its quotes.**
  `cast(v as varchar)` on a `JSON` value gives `'"0020300001"'` — width 12, not 10 — and passes
  every uniqueness test while being wrong in every row. Use `->> '$'`. · evidence:
  `transform/models/bronze/bronze__nba_stats__league_game_log_player.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · Three sqlfluff traps, all with green `dbt build` throughout — only
  lint sees them. AL09 forbids a self-alias while `aliasing.column = explicit` demands `as` on a
  genuine one. LT02 rejects a `{% for %}` loop generating select-list lines even when the compiled
  output is perfect. And the duckdb dialect cannot parse a window function on the right of
  `is distinct from` inside a `case when` — it reports an unparsable section plus a *phantom*
  `ST03` naming the wrong CTE; hoist the `lag()` into its own CTE. · evidence:
  `transform/models/silver/dim_player_team_stint.sql` · tag: `tooling-trap`

- **2026-08-15** · `verified` · DuckDB `unpivot <cte> on a, b, c into name x value y` parses
  cleanly under sqlfluff's duckdb dialect and works as a CTE body — the lintable way to compare
  many measures without N union branches, and it keeps the measure name in the failure row. ·
  evidence: `transform/tests/assert_player_points_reconcile_to_team.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · `dbt show` appends its own `limit`, so inline SQL carrying one is
  a parser error — filter with `where` instead. It also elides trailing COLUMNS with `...`, so a
  wide select silently hides the numbers you ran it for. And a column named `min` cannot be
  selected bare: `select t.min` works. · evidence:
  `transform/models/silver/dim_player_team_stint.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · **Make a fixture-backed test go red WITHOUT editing a fixture**:
  copy `tests/fixtures/nba_stats` to a scratch dir, mutate the copy, then run `--target local`
  with `NBA_LANDING_ROOT` pointed at it and `NBA_WAREHOUSE_PATH` at a scratch `.duckdb`. Same
  evidence as an in-repo edit, and `tests/` stays in your deny set with no revert to get wrong. ·
  evidence: `transform/models/bronze/sources.yml` · tag: `harness-behaviour`

- **2026-08-15** · `measured` · **Uniqueness and `mutually_exclusive_ranges` are both blind to a
  degenerate gaps-and-islands collapse.** Rebuilding the stint model as one row per player-season
  left both schema tests PASSING; only a singular population floor went red. A range test proves
  ranges do not overlap, never that the right NUMBER of ranges exists — always pair it with a
  `> 0` floor on the population it models. · evidence:
  `transform/tests/assert_stints_did_not_degenerate.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · `LeagueGameLog.get_request()` sends **and then** parses, indexing
  `resultSets['LeagueGameLog']` — a non-conforming body raises inside the call instead of being
  returned, so this transport can never LAND an error response. Use
  `NBAStatsHTTP().send_api_request`. · evidence: `src/nba_platform/client.py` · tag:
  `tooling-trap`

- **2026-08-15** · `measured` · Serialise **every** document before opening **any** handle. The
  landing writer used to render its manifest inline at its own `open("xb")`, so an unserialisable
  optional field landed a payload with no manifest — an aborted capture — instead of failing
  clean. Any writer taking caller-supplied JSON wants this ordering. · evidence:
  `src/nba_platform/landing.py` (`write_capture`) · tag: `tooling-trap`
