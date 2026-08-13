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

```
fixtures/
  <source>/<endpoint>/<descriptive-case>.json
```

e.g. `nba_stats/league_game_log/2019-20-bubble-restart.json`

The case name should say what makes the fixture interesting, not just its parameters. A future
reader needs to know *why* it was captured.

## Size

Keep them small — trim to the rows that matter. These are committed to a public repo, and a
fixture directory that grows into a dataset defeats the point of not tracking data here. If a
case needs thousands of rows to be meaningful, it probably belongs in a dbt test against real
data instead.
