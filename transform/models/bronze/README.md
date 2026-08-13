# Bronze

**One model per source endpoint, 1:1 with the landed record.**

Bronze exists to make raw payloads queryable without deciding anything. Typing, column casing,
and deduplication on the natural key — nothing else.

## Rules

- **No joins.** A bronze model reads exactly one source.
- **No business logic.** No derived stats, no rate calculations, no era adjustments.
- **No renaming beyond casing.** If the API calls it `PLAYER_ID`, bronze calls it `player_id`.
  Semantic renaming happens in silver, where it can be documented and tested.
- **No filtering.** Including rows that look wrong — they are evidence, and silver decides what
  to do about them.

If bronze and the landed JSON disagree, **bronze is wrong.** That invariant is what makes the
data-incident triage in [`requests/data-incidents/`](../../../requests/data-incidents/) tractable:
the layer that diverged is the layer at fault, and you can always diff against the immutable raw.

## Naming

`bronze__<source>__<endpoint>` — e.g. `bronze__nba_stats__league_game_log`.

The doubled underscore separates the parts so a source or endpoint containing an underscore
stays unambiguous.

## What goes in schema.yml

Every bronze model declares its **source contract**: the upstream endpoint, its parameters, and
the columns this project depends on. A `not_null` test on a column here is a statement that the
upstream promised it — so when the promise breaks, the build fails loudly at the boundary
instead of producing a silently wrong number four layers downstream.
