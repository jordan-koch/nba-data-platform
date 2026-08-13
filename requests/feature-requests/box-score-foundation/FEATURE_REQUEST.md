> **Status:** intake · created 2026-08-12 · open · next: scope

# Feature Request — Box-Score Foundation

## Problem / Motivation

The platform cannot answer a single basketball question. There is no extraction code, no landed
data, and no dbt model — `src/nba_platform/` contains only `__init__.py`, and
[`transform/models/`](../../../transform/models/) has three layer READMEs and nothing else. Every
architectural claim in [`README.md`](../../../README.md) and the six ADRs is currently untested
against a real payload.

Two concrete consequences:

**Nothing in [`docs/data-sources.md`](../../../docs/data-sources.md) has been checked.** That file
labels itself `unconfirmed` throughout and says so in its own epistemic-status blockquote. The
most load-bearing belief in it is that the `leaguegamelog` family returns an entire season per
call. If true, a 23-season backfill is ~50 calls and finishes in under a minute. If false, the
per-game `boxscore*` family needs ~60,000 calls at 0.6s pacing — roughly ten hours, against a
source that blocks impolite clients rather than throttling them. That is a factor-of-1000
difference in the cost of every extraction decision downstream, and it is currently a guess.

**Player–team affiliation has no source at all.** This is the non-obvious part, and it drives the
ordering of the work. `PERSON_ID` is stable, so player *identity* is not the problem. *Affiliation*
is: trades, ten-day contracts, two-way contracts, and February buyouts all mean "what team was this
player on" has no answer without a date, and
[`docs/data-sources.md`](../../../docs/data-sources.md) names resolving it as-of *today* instead of
as-of the *game date* as the single most likely source of silently wrong joins in this project.
No endpoint returns player-team history as a time series. It has to be **derived**, and box scores
are the only raw material: a player's `TEAM_ID` on a given game date is an *observed* affiliation,
and the SCD2 intervals get reconstructed from the sequence of those observations.

That is the real reason bronze box scores must precede `dim_player` — not the textbook
"dimensions before facts" rule. Facts would load perfectly well without dimensions, since
`PERSON_ID` and `TEAM_ID` ride along on every box-score row. The dependency runs the other way:
the dimension cannot exist until the facts have been landed, because the facts *are* its source.

## Desired Outcome

A local end-to-end slice: `nba_api` → immutable landing zone → bronze → silver, running from a
clean checkout with `NBA_ENV=local`, no credentials, and no cloud spend.

Observable signals that it worked:

- A backfill command runs for the pilot seasons and writes raw JSON into `var/` that is never
  subsequently mutated.
- `dbt build --target local` is green through silver, including the grain uniqueness tests each
  silver model is required to declare and prove.
- A traded player can be looked up by game date and resolves to the team he actually played for
  that night, not the team he finished the season on.
- [`docs/data-sources.md`](../../../docs/data-sources.md) has its `unconfirmed` labels replaced
  with `verified` or corrected — for the endpoints this request actually calls. Labels for
  endpoints it doesn't touch stay `unconfirmed`.

## Rough Ideas (non-binding)

Requester's hunches, recorded so scoping can take them or leave them:

- Extract via the `leaguegamelog` family at both player and team grain, one call per season per
  grain, rather than the per-game `boxscore*` family.
- Land raw JSON partitioned by season and grain; bronze reads it 1:1 per
  [`transform/models/bronze/README.md`](../../../transform/models/bronze/README.md).
- Derive SCD2 affiliation intervals in silver by ordering each player's observed
  `(game_date, team_id)` pairs and collapsing runs of the same team into stints.
- Commit a small set of API-response fixtures under
  [`tests/fixtures/`](../../../tests/fixtures/README.md) so the transformation logic tests offline
  without hitting the API.

## Scope Signals

- **In:** extraction + landing for the box-score endpoints; bronze models 1:1 with those
  endpoints; silver `dim_player` (carrying SCD2 team affiliation), `dim_team`, `dim_game`,
  `dim_date`, and `fact_player_game`; the config layer needed to resolve paths by name rather
  than by literal string or `parents[N]` walks; grain tests; offline fixtures; the
  `docs/data-sources.md` corrections this work earns.

- **Explicitly out:**
  - `fact_team_game` — the team-grain fact. Deferred deliberately; see below.
  - **Gold marts and anything published.** This slice terminates at a tested silver layer.
  - **Descriptive player attributes** — height, weight, position, draft year, college. Those live
    on `commonplayerinfo`, a per-player endpoint (~5,000 calls), not on box scores. `dim_player`
    here carries identity and affiliation only.
  - Play-by-play and shot detail (Phase 5). Advanced and tracking-derived box scores.
  - S3, Iceberg, Snowflake (Phase 2) — the warehouse stays DuckDB, local.
  - Airflow and any orchestration (Phase 3). The backfill is a command a human runs.
  - Any season before 2003-04, per
    [ADR 0002](../../../docs/decisions/0002-season-range-2003-forward.md).

- **Not now / later:** widening the backfill to all 23 seasons once the pilot proves the pipeline;
  `fact_team_game` and the player-points-reconcile-to-team-total check that becomes possible once
  both fact grains exist; incremental `MERGE` semantics and the trailing-window nightly re-pull
  (the pilot can afford full refresh); roster supplementation for players who never appeared in a
  box score.

## Affected Area & Pointers

This request creates the first code in three subsystems that are currently empty or scaffold-only.

| Area | State today | What this touches |
|---|---|---|
| [`src/nba_platform/`](../../../src/nba_platform/) | `__init__.py` only | Extraction client, pacing/backoff, checkpointing, landing-zone writer, config/path resolution |
| [`transform/models/bronze/`](../../../transform/models/bronze/) | README only | First bronze models, named `bronze__<source>__<endpoint>` per that README |
| [`transform/models/silver/`](../../../transform/models/silver/) | README only | The dimensional core |
| [`tests/`](../../../tests/) | `test_doc_links.py`, `test_repo_structure.py` | Extraction tests + committed response fixtures |
| [`docs/data-sources.md`](../../../docs/data-sources.md) | `unconfirmed` throughout | Gets its first `verified` labels |

Read first, in this order: [`docs/data-sources.md`](../../../docs/data-sources.md) (the catalog of
beliefs this request is here to test), the silver layer contract in
[`transform/models/silver/README.md`](../../../transform/models/silver/README.md) (which already
names SCD2 affiliation and the traded-player grain problem as known hard parts, and shows
`fact_player_game` as its worked example), the bronze rules in
[`transform/models/bronze/README.md`](../../../transform/models/bronze/README.md), and the data-layer
conventions in [`CLAUDE.md`](../../../CLAUDE.md).

**Pilot seasons** — proposed, three seasons chosen to hit the boundaries rather than to be
representative:

- **2003-04** — the far side of the hand-checking discontinuity, and the oldest season in scope.
- **2019-20** — the bubble. Suspended in March, resumed in July, ended in October, and teams
  played **unequal** game counts. Breaks any code assuming an Oct–Apr calendar.
- **2024-25** — a recent complete season, well inside the tracking era.

2011-12 (lockout, 66g) and 2020-21 (compressed, 72g) come in with the widening. Scoping should
confirm this set — the intent is that anything surviving these three survives the other twenty.

## Data Contracts

Stated as open questions. Intake's job is to put them on the table; scoping decides them.

- **Grain.** `fact_player_game` is presumed one row per player per game — but that presumption
  needs proving against a season containing mid-season trades, not asserting. Does
  `leaguegamelog` at player grain ever emit two rows for one `(game_id, player_id)`? And does
  `dim_player` hold one row per player with affiliation as SCD2 versions, or one row per player
  with affiliation living in a separate structure? Both are defensible; they are different tables.
- **Keys.** Is `(game_id, player_id)` genuinely unique across all pilot seasons, and enforceable
  as a `dbt_utils.unique_combination_of_columns` test? What is the natural key for an SCD2
  affiliation row — `(player_id, valid_from)`, and what closes the last interval?
- **Era coverage.** Traditional box scores are believed available from 1946-47, which would mean
  the 2013-14 tracking boundary **does not bite this request at all**. Worth confirming early: if
  it holds, era-nullable column handling is genuinely out of scope here rather than deferred, and
  that is a meaningful simplification. `PLUS_MINUS` is the column most likely to have its own
  earlier availability cliff — check it specifically.
- **Update semantics.** Box scores get restated after the fact, so the eventual answer is
  `MERGE`-on-key. Does the pilot need that now, or can it full-refresh and defer incrementality
  to the widening?
- **Cost.** ~6 calls for the pilot if the bulk endpoint works as believed (3 seasons × 2 grains);
  ~50 for the full 23-season widening. If it does not, both numbers rise by ~1000×, and the
  request's shape changes with them.

## Constraints / Non-negotiables

- **The landing zone is immutable.** Raw responses written once, never mutated. This is what makes
  data-incident triage tractable and what lets history replay without re-hitting the API.
- **Bronze is 1:1 with the source.** Typing, casing, dedup. No joins, no filtering, no semantic
  renaming — those belong in silver where they can be documented and tested.
- **Every silver model declares its grain in prose *and* proves it with a uniqueness test.** A
  grain claimed but not tested is a grain that will quietly break.
- **Resolve by name, never hardcode.** `ref()` and `source()` in dbt; the config layer in Python.
  No literal paths, no `parents[N]` walks.
- **Pacing starts at 0.6s with exponential backoff.** `stats.nba.com` blocks impolite clients
  rather than throttling them, and a block is hard to distinguish from a transient failure. Do not
  lower this without reading [`docs/data-sources.md`](../../../docs/data-sources.md) first.
- **No bulk data in git.** The repo is public. Code, config, docs, and small fixtures only.
- **Label epistemics.** Most of this repo is written by agents against docs treated as
  authoritative. An unconfirmed claim about an endpoint's shape is a task, not a fact.
- **Windows dev, Linux CI.** `.gitattributes` normalizes to LF.
- Agents commit only through `/commit`; never merge, push, or amend.

## Open Questions for Scoping

1. **Does `leaguegamelog` actually return a full season per call, at both player and team grain?**
   The first task of this request, and the one everything else is sized against. `unconfirmed`.
   Everything below assumes it holds.

2. **The roster hole.** Affiliation derived from observed box-score appearances cannot see a
   player who was rostered but never played — injured all season, deep bench, or a two-way player
   spending the year in the G League. Three postures, and this is a genuine decision:
   *(a)* accept it and document `dim_player` as covering *appeared* players only; *(b)* supplement
   from `commonteamroster`, which is per-team-per-season (~30 × 23 ≈ 690 calls — cheap in absolute
   terms but it changes the extraction shape and adds a second source of truth to reconcile);
   *(c)* leave the gap and revisit when something downstream actually needs it. Note that (a)
   makes `dim_player`'s coverage claim *narrower than its name suggests*, which is a documentation
   hazard as much as a modeling one.

3. **Where does an SCD2 interval boundary actually fall?** Observations are game dates, so a trade
   is only known to have happened *somewhere between* a player's last game with team A and his
   first with team B — a gap that can be a week or more, and longer across an All-Star break. Does
   `valid_from` snap to the first game with the new team, the day after the last game with the old
   one, the midpoint, or does the model carry the ambiguity explicitly? This determines whether a
   join on a date inside the gap returns the old team, the new team, or nothing — and "nothing" is
   the answer most likely to be silently wrong downstream.

4. **Is `dim_date` worth building in this slice?** `dim_game` will carry `game_date`. A separate
   date dimension earns its keep for season-calendar attributes (is this a bubble game? a
   pre-All-Star-break game?), which matter for the irregular seasons — but it may be premature.

5. **Does the pilot need `MERGE` semantics, or can it full-refresh?** Related: the pilot seasons
   are all historical and long since finalized, so stat corrections are not a live concern for
   them. That may make full-refresh correct *for the pilot* and wrong the moment 2025-26 is added
   — a trap worth naming now rather than discovering during the widening.

6. **Are the three pilot seasons the right three?** See the reasoning under *Affected Area*.

7. **Does a two-way contract show up distinguishably in a box score?** Probably not — likely just
   a `TEAM_ID` like any other. If so, `dim_player` cannot represent contract type, and should not
   pretend to. `unconfirmed`.
