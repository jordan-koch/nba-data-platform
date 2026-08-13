# Silver

**The conformed dimensional core.** Grain is decided here, and enforced.

Everything downstream joins through these models. Getting them wrong is the most expensive
mistake available in this project, which is why silver models go through the full scoping panel
rather than straight to implementation.

## Every model declares its grain

In its `schema.yml` description, in plain language, and then proves it:

```yaml
models:
  - name: fact_player_game
    description: >-
      One row per player per game. A player traded mid-season appears under the team he
      played that game for — team affiliation resolves as-of the game date, not as-of today.
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns: [game_id, player_id]
```

A grain claimed in prose but not proven by a test is a grain that will quietly break. The
`/update-docs` skill checks these against each other.

## The hard parts, named

These are known and deliberate, not discovered later:

- **Player–team affiliation is SCD Type 2.** Trades, ten-day contracts, two-way players, and
  February buyouts all mean "what team was this player on" has no answer without a date. Facts
  resolve affiliation as-of the game date.
- **Traded players have multiple team-stints per season.** A season-grain model must decide
  whether a row is per-player-season or per-player-team-season, and both are legitimate for
  different questions. Say which, in the description.
- **Stat availability varies by era.** Tracking-derived columns do not exist before 2013-14.
  That is *structurally absent*, not missing — averaging over it silently produces a wrong
  number. See [`docs/data-sources.md`](../../../docs/data-sources.md).
- **History gets restated.** Box scores are corrected after the fact. Facts here are
  `MERGE`-on-key, not append-only.

## Naming

- Dimensions: `dim_<entity>` — `dim_player`, `dim_team`, `dim_game`, `dim_date`
- Facts: `fact_<grain>` — `fact_player_game`, `fact_team_game`
