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

**Paths are inline code, never markdown links.** The link checker scans only markdown-link
syntax, so a backticked path is invisible to it — while a real link to a file that later
moves turns CI red on an unrelated PR. **Cite a repo artifact, never raw environment
output**: this file is committed and the repo is public.

## The budget — two numbers, two jobs

**~120 physical lines is the curation target**, enforced by judgment at the `/update-docs`
sweep before merge. **250 is the runaway ceiling**, enforced mechanically in CI.

**Append freely while you work.** Do not ration yourself toward 120 — that is how a build
loses what it learned in its last three phases. **At the ceiling, append nothing**: report
the entry plus *"memory at cap, pruning needed"* under `still-open`.

**Pruning is a main-thread decision, never yours**, and it is made once at the end rather
than reactively mid-build. Prune what is now enforced by code or a failing test; keep what
would cost the next session real time.

## Entries

- **2026-08-14** · `assumed` · PowerShell 5.1's `Set-Content` and `Out-File` mangle UTF-8;
  write files with the Write/Edit tools instead. · evidence:
  `.claude/skills/implement-plan/SKILL.md` · tag: `tooling-trap`

- **2026-08-14** · `measured` · PowerShell 5.1's `Get-Content` decodes UTF-8 as ANSI, so each
  box-drawing char measures as 3 and every column calculation is wrong. Use
  `[System.IO.File]::ReadAllText(path, [Text.Encoding]::UTF8)` for any length check. ·
  evidence: `README.md` layout tree · tag: `tooling-trap`

- **2026-08-15** · `measured` · PowerShell mangles two things silently. `->> '$'` inside a
  **double-quoted** string loses the `$`, so every DuckDB key returns NULL and a probe gives a
  coherent but FALSE answer — use a single-quoted here-string. And `2>$null` on a native exe
  then piped buries real output in binding errors. · evidence: Phase 5 probes · tag:
  `tooling-trap`

- **2026-08-14** · `measured` · The `CLAUDE.md` and git status injected into your context are a
  snapshot from the **parent session's start** and can be commits behind disk. Inherited
  context is indistinguishable from something you verified — **read from disk before asserting
  repo state.** · evidence:
  `requests/feature-requests/data-engineer-agent/reviews/proving-run-a-verification.md` · tag:
  `harness-behaviour`

- **2026-08-14** · `measured` · In agent frontmatter the shell tool is **`PowerShell`**, not
  `Bash`. Declaring `Bash` silently yields an agent with no shell at all. Argument-scoped
  syntax like `PowerShell(git status:*)` parses but is **not enforced**. · evidence:
  `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md` · tag:
  `harness-behaviour`

- **2026-08-14** · `verified` · The bundled `.claude/skills/**/tests/*.mjs` guards are **not**
  run by CI — no Node step exists — so they execute only when someone remembers. Guards that
  must actually enforce belong under `tests/`. · evidence: `.github/workflows/ci.yml` · tag:
  `ci-behaviour`

- **2026-08-15** · `measured` · CI lints **`transform/models` only**; singular tests under
  `transform/tests` are never linted. Run `uv run sqlfluff lint transform/tests` by hand or
  style rot accumulates where nobody looks. · evidence: `.github/workflows/ci.yml` · tag:
  `ci-behaviour`

- **2026-08-14** · `measured` · dbt 1.12 warns on top-level generic-test args: nest them under
  `arguments:`. `tests:` is not deprecated, but `data_tests:` replaced it in dbt 1.8. With
  `+severity: error` a warn is a RED build. · evidence:
  `transform/models/silver/README.md` · tag: `tooling-trap`

- **2026-08-15** · `measured` · **`dbt --project-dir X` does NOT chdir into X.** DuckDB resolves
  a relative `external_location` and a relative `profiles.yml` `path:` against the PROCESS
  working directory, so both must be written relative to the **repo root**. A `../` prefix
  fails naming a path that looks plausible. · evidence:
  `transform/models/bronze/sources.yml` · tag: `tooling-trap`

- **2026-08-15** · `measured` · DuckDB identifiers are case-insensitive **including struct
  fields**, so `resultsets[1].rowset` resolves against `read_json_auto`'s camelCase columns.
  Writing the envelope decode all-lowercase satisfies `.sqlfluff` with no quoting. · evidence:
  `transform/models/bronze/bronze__nba_stats__league_game_log_player.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · **Never select `headers` alongside `unnest(rowset)`** — it
  broadcasts a 32-element array onto every row (~2.3M strings over three seasons) and dies with
  `Out of Memory` at 91s, after passing in 0.06s on trimmed fixtures. Resolve `list_position`
  once per file, before the unnest, and carry the integers: 0.19s at full volume. · evidence:
  `transform/tests/assert_bronze_row_count_matches_landed.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · sqlfluff AL09 forbids a self-alias (`t.col as col`) while this
  repo's `aliasing.column = explicit` demands `as` on a genuine one. In a coalesce-plus-full-
  outer-join CTE, drop the alias on carried-through columns and keep it on coalesced ones. ·
  evidence: `transform/tests/assert_bronze_row_count_matches_landed.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · Two `dbt show` papercuts: it appends its own `limit`, so an
  inline query carrying one is a parser error (use `--limit N`); and a column named `min`
  cannot be selected bare — `select t.min` works, `select min from t` does not. · evidence:
  `transform/models/bronze/schema.yml` · tag: `tooling-trap`

- **2026-08-15** · `measured` · `LeagueGameLog.get_request()` sends **and then** parses,
  indexing `resultSets['LeagueGameLog']` — a non-conforming body raises inside the call instead
  of being returned, so this transport can never LAND an error response. Use
  `NBAStatsHTTP().send_api_request`. · evidence: `src/nba_platform/client.py` · tag:
  `tooling-trap`

- **2026-08-15** · `measured` · Serialise **every** document before opening **any** handle. The
  landing writer used to render its manifest inline at its own `open("xb")`, so an
  unserialisable optional field landed a payload with no manifest — an aborted capture —
  instead of failing clean. Any writer taking caller-supplied JSON wants this ordering. ·
  evidence: `src/nba_platform/landing.py` (`write_capture`) · tag: `tooling-trap`

- **2026-08-15** · `measured` · **`dbt test --select X --target ci` can never pass here** — `ci` is
  `:memory:`, so a test-only process has no relations and every test ERRORs on a missing schema.
  Nor does `dbt build --select +X --target ci` help: indirect test selection is EAGER, so singular
  tests referencing unselected models get pulled in and error. Use `--target local`, or build all. ·
  evidence: reproduces on Phase-5-only `--select bronze__..._player` · tag: `tooling-trap`

- **2026-08-15** · `measured` · dbt 1.12 accepts `unique_key` on a `table` materialization silently
  — no warning, and it lands in `manifest.json` under `config.unique_key`. So "declare the merge key
  now, switch to incremental later" is a real config-only path, not wishful. · evidence:
  `transform/models/silver/fact_player_game.sql` · tag: `tooling-trap`

- **2026-08-15** · `measured` · Two probe traps when checking `+persist_docs` output. DuckDB `like`
  is CASE-SENSITIVE, so probing a persisted description for a sentence written in caps returns False
  and reads exactly like a missing sentence — use `ilike`. And `dbt show` elides trailing COLUMNS
  with `...`, so a wide select silently hides the numbers you ran it for. · evidence:
  `transform/models/silver/schema.yml` · tag: `tooling-trap`

- **2026-08-15** · `measured` · Comparing rows without enumerating columns: `to_json(t)` renders
  a row, `json_extract_string(j, 'col')` takes a bare key, and two `unnest()`s in one select
  **zip elementwise**. Normalise with `coalesce(cast(try_cast(v as double) as varchar), v)` so
  `0.500` and `0.5` agree while `DAL` stays text. · evidence:
  `transform/tests/assert_latest_capture_wins.sql` · tag: `tooling-trap`
