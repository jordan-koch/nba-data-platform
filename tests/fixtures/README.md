# Fixtures

Committed API responses, captured once and replayed forever.

## Why these exist

Testing extraction against the live `stats.nba.com` endpoints would be slow, flaky, and
rate-limited — and CI would be hammering an endpoint that blocks impolite clients. So the
extraction layer is tested offline against real captured payloads.

**Fixtures are real responses, never hand-written.** A hand-authored fixture tests your idea of
what the API returns, which is exactly the assumption most likely to be wrong. Capture them
with the recorder, inspect them, then commit.

## What to capture

When a feature request adds a source, its fixtures should span the range that breaks things:

| Case | Why |
|---|---|
| A modern season (2023-24 or later) | The common path, all columns present |
| A pre-tracking season (before 2013-14) | Tracking columns structurally absent |
| 2011-12, 2019-20, or 2020-21 | Lockout / bubble / compressed — irregular calendars |
| A game with a mid-season traded player | Exercises SCD2 affiliation resolution |
| An empty or error response | The failure path, which is otherwise never tested |

## Layout

Fixtures mirror the landing zone's own partitioned layout, capture segment and all:

```
fixtures/
  <source>/<endpoint>/season=<s>/grain=<g>/season_type=<t>/capture=<YYYYMMDDTHHMMSSZ>/
      payload.json
      manifest.json
```

e.g. `nba_stats/league_game_log/season=2019-20/grain=player/season_type=regular/capture=.../`

**This replaced a flat `<source>/<endpoint>/<descriptive-case>.json` shape, and the reason is a
requirement rather than a preference.** Bronze resolves two captures of one partition by
latest-capture-wins, and proving that needs *two captures of the same (season, grain) with
different capture stamps* in the fixture set. A flat filename cannot express that — there is
nowhere to put the second one. Mirroring the landing layout also means the bronze source glob is
the same expression against fixtures under `--target ci` as against `var/` under `--target local`,
so CI exercises the real path rather than a parallel one.

**The descriptive case name moved into the manifest**, since the path no longer has room for it.
Every capture's `manifest.json` carries its provenance: the request parameters, the capture
timestamp, the original and retained row counts, the `GAME_ID`s kept, and a `case` naming what
makes this fixture interesting. That last requirement did not go away — a future reader still
needs to know *why* it was captured, and now the answer is a field instead of a filename.

### Error cases live outside the partitioned tree

```
fixtures/nba_stats/league_game_log/_error_cases/<case>.json
```

The leading underscore means **"not a landing partition, never globbed by a source."** This is
load-bearing, not tidiness: the bronze source globs `season=*/grain=*/season_type=*/capture=*/
payload.json`, and anything matching it is unioned into the model. A capture of an impossible
season landed inside the tree would create a meaningless partition that the bronze-vs-landed
row-count test then has to special-case. Error and empty responses are exercised by offline
pytest against the client and the landing writer — never by dbt.

## Capturing

Use the recorder at `src/nba_platform/fixtures.py`. It is the only supported way to add a
fixture, and it enforces the two rules below so they cannot be got wrong by hand.

**Trim by whole games, rows only — never by structure.** Choose a set of `GAME_ID`s and keep
*every* row carrying one of them, at *both* grains, over the *same* `GAME_ID` set. Trimming to
"the first N rows" instead silently breaks every reconciliation the suite depends on: a team-game
with one team fails the two-teams assertion, and a game whose player rows are half missing fails
the points reconciliation — or worse, passes on an empty set. The envelope itself
(`resource` / `parameters` / `resultSets[0].headers`) is never touched; only `rowSet` shrinks.

**Fixtures must be `.json`.** `.gitignore` ignores `*.jsonl` and `*.ndjson` with **no**
counter-whitelist, and whitelists only `tests/fixtures/**/*.json`. A fixture written as NDJSON is
silently not committed, and CI then fails on a file that exists perfectly well on your machine.

## Size

Keep them small — trim to whole games, and to as few of those as still make the case. These are
committed to a public repo which redistributes no NBA data; the `.gitignore` whitelist is a narrow
carve-out for test fixtures, not a licence. If a case needs thousands of rows to be meaningful, it
belongs in a dbt test against real data under `--target local` instead.

Every fixture-backed test also carries a **row-count floor**, so an over-trimmed fixture makes the
suite go red rather than pass vacuously on an empty set.
