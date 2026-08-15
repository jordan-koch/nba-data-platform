# Data Sources

What this project can get, what it can't, and what breaks.

> **Epistemic status.** Everything below is marked `verified` (someone called it and looked at
> the response), `documented` (stated by the source's own docs or widely-used client code), or
> `unconfirmed` (believed true, never checked here). **One endpoint has now been called from
> this repo** — `leaguegamelog`, during `box-score-foundation`'s Gate 0 probe on 2026-08-14 —
> and its claims below are promoted to `verified`. **Everything else remains `unconfirmed`**
> and exists to shape a feature request rather than to be built on. Promotion is deliberate and
> per-endpoint: a claim is only `verified` for what was actually called.

## The source

[`nba_api`](https://github.com/swar/nba_api) — an unofficial Python client for
`stats.nba.com`, the endpoint that powers the league's public stats site.

It is comprehensive and free. It is also **undocumented, unversioned, and governed by no
contract.** Endpoints change shape without notice, occasionally disappear, and will block a
client that requests impolitely. Every design decision in the extraction layer follows from
that.

### Rate limiting

`unconfirmed` — the endpoint publishes no rate limit. Community practice converges on roughly
**0.6 seconds between requests**, with exponential backoff on failure. Being impolite gets the
client **blocked**, not throttled, and the block is not obviously distinguishable from a
transient failure.

Consequences baked into the architecture:

- **The landing zone is immutable.** Raw responses are written once and never mutated, so
  history can be replayed without re-hitting the API. Re-extraction is expensive; re-reading a
  file is not.
- **Long backfills checkpoint.** A backfill that dies at hour six must resume at hour six.
- **Bulk endpoints are strongly preferred.** See below — this is worth a factor of ~1000.

### Bulk vs. per-game endpoints

The single most consequential extraction decision.

| Approach | Calls for full 2003–2026 backfill | Wall clock at 0.6s |
|---|---|---|
| Per-game box scores (`boxscore*` family) | ~30,000 games × 2 endpoints ≈ **60,000** | ~10 hours |
| Season-wide bulk (`leaguegamelog` family) | ~2 grains × 23 seasons ≈ **50** | under a minute |

`verified` — **it holds.** `leaguegamelog` returns every player-game or team-game for an entire
season in one response, at both grains. Measured 2026-08-14 via `nba_api`, four calls at 0.6s
pacing:

| Season | Grain | Rows | Distinct `GAME_ID` | Duplicate `(GAME_ID, PLAYER_ID)` |
|---|---|---|---|---|
| 2023-24 | player | 26,401 | 1,230 | 0 |
| 2023-24 | team | 2,460 | 1,230 | — |
| 2003-04 | player | 23,894 | 1,189 | 0 |
| 2003-04 | team | 2,378 | 1,189 | — |

The counts are internally consistent: 2,460 = 1,230 games × 2 teams, and 2003-04 returns 1,189
games because the league had 29 teams that season. So the box-score foundation is a minutes-long
backfill — ~6 calls for the three-season pilot, ~46 for the full range — not an overnight one.

**Verified for the regular season at these two seasons only.** Playoffs were not called, and the
other twenty-one seasons are inferred from these. Evidence:
`requests/feature-requests/box-score-foundation/reviews/gate-0-endpoint-probe.md`.

Per-game endpoints only become necessary for play-by-play and shot detail, which have no bulk
equivalent. Those are Phase 5, and they are where the rate-limit engineering actually earns its
keep.

## Availability by era

This project covers **2003-04 through 2025-26**. One boundary falls inside that range:

| Data | Available from | Notes |
|---|---|---|
| Traditional box scores | 1946-47 | Full coverage of our range |
| Play-by-play | ~1996-97 | `unconfirmed` — early seasons are believed sparser |
| Shot chart detail (x/y) | ~1996-97 | `unconfirmed` |
| Advanced box scores | 1996-97 | `unconfirmed` |
| **Tracking-derived stats** | **2013-14** | Speed, distance, touches, drives, contested shots, defensive matchups, hustle |

**Tracking columns before 2013-14 are structurally absent, not missing.** The distinction
matters: averaging a column over a period where it could not have been recorded produces a
number that is wrong rather than incomplete. Models must handle the boundary explicitly, and
`docs/data-dictionary.md` records which columns are era-bounded.

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
