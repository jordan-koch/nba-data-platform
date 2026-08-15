# Data Sources

What this project can get, what it can't, and what breaks.

> **Epistemic status.** Everything below is marked `verified` (someone called it and looked at
> the response), `documented` (stated by the source's own docs or widely-used client code), or
> `unconfirmed` (believed true, never checked here). **Exactly one endpoint has been called from
> this repo** — `leaguegamelog`, across three probes and one real backfill between 2026-08-14 and
> 2026-08-15 — and only its claims are promoted. **Everything else remains `unconfirmed`** and
> exists to shape a feature request rather than to be built on. Promotion is deliberate and
> per-endpoint: a claim is only `verified` for what was actually called, at the grains and seasons
> it was called at. A blanket promotion would destroy the only property this file has.

## The source

[`nba_api`](https://github.com/swar/nba_api) — an unofficial Python client for
`stats.nba.com`, the endpoint that powers the league's public stats site.

It is comprehensive and free. It is also **undocumented, unversioned, and governed by no
contract.** Endpoints change shape without notice, occasionally disappear, and will block a
client that requests impolitely. Every design decision in the extraction layer follows from
that.

### Rate limiting

`unconfirmed` — **and it stays that way deliberately.** The endpoint publishes no rate limit.
Community practice converges on roughly **0.6 seconds between requests**, with exponential backoff
on failure. Being impolite gets the client **blocked**, not throttled, and the block is not
obviously distinguishable from a transient failure.

What has actually been run here, so the label can be judged rather than trusted: **22 calls total**
across three probes, a six-call pilot backfill and a six-call live contract test, all at 0.6s
pacing, between 2026-08-14 and 2026-08-15. Zero blocks, zero throttling, observed spacing
0.59–0.86s. **That says nothing about sustained-backfill behaviour** — twenty-two polite calls is
not evidence about the hundredth or the thousandth, and the failure mode being a block rather than
a 429 means the first evidence of impoliteness is losing access. The 0.6s default therefore stands
unchallenged rather than validated, and this paragraph keeps its `unconfirmed` label until
something genuinely sustained has run.

Consequences baked into the architecture:

- **The landing zone is immutable.** Raw responses are written once and never mutated, so
  history can be replayed without re-hitting the API. Re-extraction is expensive; re-reading a
  file is not. `verified` — implemented and tested; see
  [ADR 0008](decisions/0008-landing-layout-and-capture-manifest.md).
- **Long backfills checkpoint.** A backfill that dies at hour six must resume at hour six. At the
  pilot's six calls, write-once skip-if-present *is* the checkpoint and no separate store was
  built; the real thing is deferred to the play-by-play phase below.
- **Bulk endpoints are strongly preferred.** See below — this is worth a factor of ~1000.

### Bulk vs. per-game endpoints

The single most consequential extraction decision.

| Approach | Calls for full 2003–2026 backfill | Wall clock at 0.6s |
|---|---|---|
| Per-game box scores (`boxscore*` family) | ~30,000 games × 2 endpoints ≈ **60,000** | ~10 hours |
| Season-wide bulk (`leaguegamelog` family) | ~2 grains × 23 seasons ≈ **50** | under a minute |

`verified` — **it holds.** `leaguegamelog` returns every player-game or team-game for an entire
season in one response, at both grains. Measured across all three pilot seasons, and reproduced
independently on 2026-08-15 by the real backfill after the probes:

| Season | Grain | Rows | Distinct `GAME_ID` | Duplicate `(GAME_ID, PLAYER_ID)` |
|---|---|---|---|---|
| 2003-04 | player | 23,894 | 1,189 | 0 |
| 2003-04 | team | 2,378 | 1,189 | — |
| 2019-20 | player | 22,393 | 1,059 | 0 |
| 2019-20 | team | 2,118 | 1,059 | — |
| 2023-24 | player | 26,401 | 1,230 | 0 |
| 2023-24 | team | 2,460 | 1,230 | — |
| 2024-25 | player | 26,306 | 1,230 | 0 |
| 2024-25 | team | 2,460 | 1,230 | — |

The counts are internally consistent rather than coincidental: every team-grain count is exactly
twice its game count, and 2003-04 returns 1,189 games because the league had 29 teams that season
(29 × 82 / 2). A truncated or paginated response would not land on those numbers by accident. So
the box-score foundation is a minutes-long backfill — **6 calls, measured at 6.06 seconds
wall-clock** for the three-season pilot, ~46 for the full range — not an overnight one.

**`(GAME_ID, PLAYER_ID)` is confirmed unique in all four seasons**, including two trade-heavy ones
(68 and 81 players changed team mid-season in 2003-04 and 2024-25). That is the grain
`fact_player_game` enforces.

**Verified for the REGULAR SEASON at these four seasons only.** `SeasonType=Playoffs` has never
been called at any grain, and the other nineteen seasons in range are inferred from these. Evidence:
[`gate-0-endpoint-probe.md`](../requests/feature-requests/box-score-foundation/reviews/gate-0-endpoint-probe.md)
and [`endpoint-probe.md`](../requests/feature-requests/box-score-foundation/reviews/endpoint-probe.md).

Per-game endpoints only become necessary for play-by-play and shot detail, which have no bulk
equivalent. Those are Phase 5, and they are where the rate-limit engineering actually earns its
keep.

## Availability by era

This project covers **2003-04 through 2025-26**. One boundary falls inside that range:

| Data | Available from | Notes |
|---|---|---|
| Traditional box scores | 1946-47 | `verified` for 2003-04, 2019-20, 2023-24 and 2024-25 at both grains — identical 29/32 column sets, no drift. The rest of the range is `unconfirmed` |
| Play-by-play | ~1996-97 | `unconfirmed` — early seasons are believed sparser |
| Shot chart detail (x/y) | ~1996-97 | `unconfirmed` |
| Advanced box scores | 1996-97 | `unconfirmed` |
| **Tracking-derived stats** | **2013-14** | Speed, distance, touches, drives, contested shots, defensive matchups, hustle |

**Tracking columns before 2013-14 are structurally absent, not missing.** The distinction
matters: averaging a column over a period where it could not have been recorded produces a
number that is wrong rather than incomplete. Models must handle the boundary explicitly, and a
model's `schema.yml` description is where its era-bounded columns are recorded.

> **The boundary does not touch the box-score foundation at all** — `verified`, not deferred.
> `leaguegamelog` carries **no tracking-derived column** at either grain, and `PLUS_MINUS`, the
> column flagged as the likeliest to have its own early cliff, is present in 2003-04 with **zero
> nulls**. So no era-nullable machinery was built for this slice, and none should be added
> speculatively. It bites the first request that touches an endpoint which actually has such a
> column.

## Things that will break naive assumptions

### Irregular seasons

| Season | What happened |
|---|---|
| 2011-12 | Lockout — 66 games, season started in December |
| 2019-20 | Suspended March 11, resumed in a bubble in July, ended in October. Teams played **unequal** game counts |
| 2020-21 | Compressed — 72 games, started in December |

Anything assuming 82 games, an October start, or an April end breaks on all three. They are the
best test cases in the dataset and belong in the fixture set.

### The 2004-05 rule change

Hand-checking was banned starting 2004-05, measurably shifting scoring, pace, and drive
frequency. **2003-04 sits alone on the far side of that discontinuity.** Cross-era comparisons
that span it need to say so.

### Pace

League pace varies enough across this range that raw counting stats are not comparable end to
end. Per-100-possession normalization is not an enhancement; it is a correctness requirement for
any cross-season comparison.

### Stat corrections

`documented` — box scores are revised after the fact, sometimes days later. A game's numbers on
the night are not final. This is why silver facts are `MERGE`-on-key rather than append-only,
and why nightly runs re-pull a trailing window rather than only the previous day.

### Player identity

`PERSON_ID` is stable, so identity itself is not the problem. **Affiliation** is: trades,
ten-day contracts, two-way players, and buyouts all mean a player's team is a function of date.
Resolving it as-of "today" instead of as-of the game date is the single most likely source of
silently wrong joins in this project.

## What this project will never have

Not obtainable publicly, at any price a hobbyist would pay:

- **Raw optical tracking.** Hawk-Eye skeletal data (~29 keypoints per player at high frequency)
  is delivered to teams, not the public. Only league-published *aggregates* are available.
- **Wearables.** Catapult/Kinexon load and accelerometry data is team-internal.
- **Medical and availability.** Beyond public injury reports.
- **Internal video and scouting.** Synergy feeds, scouting notes, private evaluations.

One partial exception worth investigating: raw SportVU tracking for a large portion of the
**2015-16** season was publicly available before the NBA withdrew it, and has been mirrored and
used extensively in academic work. `unconfirmed` — current availability and licensing both need
checking before this repo depends on it.

Where real volume is needed to prove the architecture handles it, the plan is **synthetic
tracking data** generated at realistic frequency from play-by-play. Fake basketball, real bytes,
real partitioning pressure. See [`decisions/`](decisions/).

## Terms

`nba_api` is itself public and widely used, and this repo publishes code that calls it — not
data. **Nothing sourced from the NBA is committed here** beyond a small set of response fixtures
used for offline testing. See the provenance note in [`../README.md`](../README.md).
