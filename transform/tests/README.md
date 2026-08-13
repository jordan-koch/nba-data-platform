# Singular tests

Assertions that don't fit the schema-test shape — basketball invariants, mostly.

A singular test is a SQL file that returns rows **only when something is wrong**. Zero rows
means pass.

## What belongs here

The domain invariants that no generic test can express:

- A team's points in a box score equal the sum of its players' points
- Every game has exactly two teams
- Team minutes sum to 240 per regulation game, plus 25 per overtime period
- No player appears twice in one game for the same team
- A player's team on a game date matches an open interval in `dim_player`'s SCD2 history
- Field goals made never exceed field goals attempted, for any grain

These catch real bugs. A fan-out from a bad join shows up as points not reconciling long before
anyone notices the number looks off on a dashboard.

## What doesn't

Uniqueness, not-null, accepted values, and referential integrity belong in `schema.yml` next to
the model they constrain — they're cheaper to read there, and they document the model while
testing it.

## Naming

`assert_<what_must_be_true>.sql` — e.g. `assert_player_points_reconcile_to_team.sql`.

Name the invariant, not the failure. The test's name is what shows up in a red build, and
"assert_player_points_reconcile_to_team" tells you more than "test_points_check".

## Every incident leaves one behind

Per [`requests/data-incidents/README.md`](../../requests/data-incidents/README.md), a resolved
data incident must ship a test that would have caught it. Over time this directory becomes a
ledger of everything that has ever gone wrong — which is exactly what you want a test suite to be.
