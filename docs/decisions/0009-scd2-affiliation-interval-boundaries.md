# 0009 — SCD2 affiliation intervals: season-bounded, gap-covering, old-team-wins

**Status:** accepted · 2026-08-15

## Context

"What team was this player on?" has no answer without a date. Trades, ten-day contracts, two-way
assignments and February buyouts all mean player–team affiliation is Slowly Changing Dimension
Type 2, and `transform/models/silver/README.md` names it as the hardest part of this layer.

**No endpoint returns it.** `leaguegamelog` returns box scores; nothing in this project's sources
returns player-team history as a time series. So `dim_player_team_stint` is **derived** from
observed box-score rows — which is why facts had to land before the dimensional core, and why the
model is an inference rather than a record.

Deriving it forces three decisions that a naive implementation makes silently and wrongly.

**First, what bounds a stint.** Observations are game dates. A player traded on 2 February has a
last game with the old team and a first game with the new one, and **the days between them are not
observed at all**. Something must decide what an interval covers.

**Second, whether stints span seasons.** The pilot is 2003-04, 2019-20 and 2024-25 — deliberately
*non-adjacent*, with sixteen- and five-year holes. A run-collapse that ignores season boundaries
merges observations across those holes.

**Third, what the tests actually prove.** The obvious test — every observed
`(player, date, team)` falls inside a matching interval — is derived from the very observations it
checks.

Measured against all three pilot seasons before deciding (`reviews/endpoint-probe.md` and the
Phase 8 probe): **68 / 60 / 81** players change team within a single season; **24**
`(player, season, team)` runs span exactly one date; **two** combinations show a player returning
to a former team in the same season; and **exactly one player appears in all three pilot seasons**
— `player_id` 2544, LeBron James, 2003-10-29 to 2025-04-11.

## Decision

**1. Intervals are SEASON-BOUNDED.** The run-collapse partitions by `(player_id, season_id)`.
Contiguous and gapless *within* a season; real gaps between seasons.

The alternative is not hypothetical. A global collapse emits, for LeBron James, **one stint
spanning 2003 to 2025** — the player this repository is anchored to, and not a defensible answer to
the question the model exists to answer. This merges naturally when widening makes the seasons
contiguous, so it costs nothing later.

**2. A stint's `valid_to` is the day BEFORE the next stint's `valid_from`.** Only a season's final
stint closes at that season's last observed game. Intervals therefore **cover the trade gap**, and
a date inside it resolves to the **OLD** team.

**3. `valid_to` is never null and never a sentinel.** `dbt_utils.mutually_exclusive_ranges`
compares bounds directly, so a null upper bound is a meaningless comparison. "Exactly one open
interval per player" is expressed as an `is_current` uniqueness test instead.

**4. The macro's arguments are set explicitly, and both matter.** `gaps: 'allowed'` — because the
non-adjacent pilot seasons create real between-season gaps. `zero_length_range_allowed: true` —
because the default `False` selects a strict `<`, and **20 real zero-length stints would fail on
correct data** (216 of them on the trimmed CI corpus, where most players appear in a single game).

That count is worth stating precisely, because three plausible numbers differ: **24**
`(player, season, team)` combinations span a single date, **25** stints do once a return to a former
team splits one of them, and **20** survive as zero-length *ranges* after the boundary rule above
extends every non-final stint to the day before the next one. The macro governs the third number.

**5. Returning to a former team is a NEW stint.** The collapse is gaps-and-islands over
consecutive observations, not a grouping by team. Two players do exactly this within one season;
grouping by `(player, season, team)` would merge two spells into one interval spanning the other
team's stint, which would then overlap it.

**6. The observed boundaries are carried as columns.** `last_game_prior_team` and
`first_game_new_team` sit beside the interpolated bounds, so the inference is visible and
falsifiable rather than fabricated.

## Consequences

**Buys:**

- **An as-of join always resolves.** `game_date between valid_from and valid_to` returns exactly
  one row for any date within a season the player played in — including the trade gap.
- **The interpolation is auditable.** Anyone can compare `valid_to` against
  `last_game_prior_team` and see precisely how many days were inferred.
- **Fact correctness does not depend on it.** `fact_player_game.team_id` comes from the observed
  box-score row, never from this model, so a wrong interval cannot corrupt a fact. This model is a
  lookup surface, not a join dependency.

**Costs:**

- **A date inside a trade gap resolves to the OLD team, and that is sometimes just wrong.** A
  player traded on 2 February whose last old-team game was 1 February and first new-team game was
  4 February is, on 3 February, already on the new team in reality. This model says otherwise. The
  alternative — leaving the gap uncovered — returns *zero rows*, which the feature request names as
  the answer most likely to be silently wrong downstream. **Both choices are wrong; this one is
  wrong in a direction a reader can predict and detect.**
- **The containment test is weaker than it looks, and everything leans on it.**
  `assert_player_team_matches_open_stint` is derived from the same `(game_date, team_id)`
  observations it then checks, so a zero-row result proves the run-collapse lost and reordered
  nothing. It **cannot** detect a wrong interpolation inside a trade gap, because there are no
  observations there. It is **vacuous everywhere between game dates** — which is exactly where the
  model does its only real work. The seed-pinned known-trade test is the non-vacuous companion, and
  it is the reason that player had to come from a captured payload rather than from memory.
- **Season-bounded intervals mean an off-season date resolves to nothing.** Ask "what team was this
  player on in August 2024" and you get zero rows, not "the team he finished 2023-24 with." That is
  defensible for a box-score-derived model and will annoy someone.
- **A player who appears in no box score has no stint at all.** Coverage is players who APPEARED —
  an injured player under contract all season is invisible here. `dim_player` carries the same
  limit and says so.
- **This is an inference presented in a dimension table.** Dimension tables read as records of
  fact. Nothing about the shape of `dim_player_team_stint` tells a casual consumer that its
  boundaries were computed rather than observed; only the description and the two observed-boundary
  columns do.

**Forecloses:** nothing permanently. Widening to contiguous seasons merges the between-season gaps
away without a model change. A future roster or transactions source would replace the interpolation
with observation, at which point the observed-boundary columns become the migration's test.

## Alternatives considered

**Observation-bounded intervals** — close each stint at its own last observed game and leave the
gap uncovered. Rejected by disposed Decision 3: an as-of join inside the gap returns zero rows, and
a consumer who does not check for that silently drops the row. Wrong data that looks like missing
data is worse than wrong data that looks like an answer.

**Split the difference at the midpoint of the gap.** Rejected as the worst of both: it fabricates a
boundary with no evidence behind it *and* is harder to explain than either extreme. A reader can
reason about "the old team holds until the new one is observed"; nobody can reason about
"whichever side of 2 February the arithmetic landed on."

**Fold the stints into `dim_player`** rather than splitting them out. Rejected by disposed
Decision 2: it makes `dim_player` multi-grain, so every join to it must know whether it wants
identity or affiliation, and `unique(player_id)` stops being true.

**A global (season-agnostic) run-collapse.** Simpler, and correct once the season range is
contiguous. Rejected on the measured LeBron case — a 22-year stint is not a defensible row.

**Nulls or a 9999 sentinel for the open interval.** Rejected because `mutually_exclusive_ranges`
compares bounds directly: a null makes the comparison meaningless and a sentinel makes every open
interval overlap every other one at the far end.
