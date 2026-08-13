# Gold

**Business-facing marts, shaped for how the question gets asked.**

Gold models answer a question rather than describing an entity. They are allowed to be
denormalized, pre-aggregated, and opinionated — that is the point.

## League context is the job

A descriptive stat without context is not actionable. "We shoot 36.1% from three" tells a coach
nothing; "36.1%, 18th in the league, league average 36.5%" tells them something. Gold models
carry rank and percentile alongside the raw value, because computing it downstream means every
consumer recomputes it slightly differently.

For the same reason, cross-era comparisons are normalized here — per-100-possessions and
within-season z-scores — not left to whoever writes the query. League pace has swung far enough
across this dataset's range that raw counting stats are not comparable end to end.

## Sized to ship to a browser

Gold is the layer that gets published as Parquet to a CDN and queried client-side with
DuckDB-WASM. That imposes a real constraint: **a gold model should be small enough that a
browser can hold or range-scan it.**

Aggregated marts — player-season summaries, team splits, game logs — are comfortably in range.
Anything approaching play-by-play volume belongs in silver with a pre-aggregated gold model on
top, not published whole.

## Naming

`<subject>_<grain>` — `team_season_summary`, `player_game_detail`, `league_season_context`.

No `gold_` prefix. These are the names analysts and the front end actually type, and the schema
already says which layer they're in.
