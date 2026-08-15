# Endpoint probe — completion run

> **Status:** evidence · created 2026-08-15 · Phase 3 output · satisfies AC 22

**Label: `measured`.** Every number below came from a call made on **2026-08-15** against
`stats.nba.com` from this repo's dev environment, through `src/nba_platform/client.py` at 0.6s
pacing, landed under `var/` by `src/nba_platform/backfill.py`, and then counted from the landed
payloads. Nothing here is inferred, and nothing is carried over from a document.

This completes [`gate-0-endpoint-probe.md`](gate-0-endpoint-probe.md), which settled the bulk-call
belief and most of the envelope but explicitly left four AC-22 questions open. Read that file for
the bulk verdict; read this one for what it did not settle.

## The run

Six calls — three pilot seasons × two grains, regular season — issued by the real backfill rather
than a probe script, so the transport, the pacing, the landing writer and the manifest were all
exercised end to end for the first time.

| Season | Grain | Rows | Gate 0 said | Agree |
|---|---|---|---|---|
| 2003-04 | player | 23,894 | 23,894 | ✅ |
| 2003-04 | team | 2,378 | 2,378 | ✅ |
| 2019-20 | player | 22,393 | 22,393 | ✅ |
| 2019-20 | team | 2,118 | 2,118 | ✅ |
| 2024-25 | player | 26,306 | 26,306 | ✅ |
| 2024-25 | team | 2,460 | 2,460 | ✅ |

**Six of six reproduce Gate 0 exactly**, on a different day through a different code path. The
bulk-endpoint belief is independently confirmed, not merely re-asserted.

Measured cost: **6 calls, 6.06s wall clock**, first call 3.48s (cold) and the rest 0.05–0.30s. The
observed call count equals the `--dry-run` planned count of 6 — the offline half of AC 28 held live.

## The AC-22 checklist, answered by name

| Question | Answer | Where measured |
|---|---|---|
| Full season per call at `P`? | **Yes**, all three pilot seasons | table above |
| Full season per call at `T`? | **Yes**, all three | table above |
| Response envelope shape | `{resource, parameters, resultSets}`, `resultSets[0]` = `{name, headers, rowSet}` | Gate 0, re-confirmed here |
| Row count per pilot season | as tabled | above |
| Complete column list per season | **29 team / 32 player, identical across all three seasons, and identical in ORDER** | §Columns |
| `PLUS_MINUS` present in 2003-04? | **Yes, zero nulls** — the 2013-14 boundary does not bite this endpoint | Gate 0 |
| `MIN` — `MM:SS` or decimal? | **Neither: `int64`.** 240 at team grain, 21–26 at player grain. No parsing needed or wanted | Gate 0 |
| `GAME_ID` zero-padded? | **Yes — `str`, exactly 10 characters, every value, all six payloads** | §Keys |
| DNP-but-active players get a row? | **Yes**, carrying `MIN == 0` — 81 rows in 2019-20, 100 in 2024-25. Bronze must not filter them | Gate 0 |
| `(GAME_ID, PLAYER_ID)` unique in a trade-heavy season? | **Yes — zero duplicates in all three**, including 2003-04 (68 traded players) and 2024-25 (81) | Gate 0 + here |
| Distinct `(team_id, team_name)` pairs across the span | **34 pairs across 30 team_ids** | §dim_team |

## Columns — ordered, and stable

Team grain, 29, in this exact order:

```
SEASON_ID TEAM_ID TEAM_ABBREVIATION TEAM_NAME GAME_ID GAME_DATE MATCHUP WL MIN FGM FGA FG_PCT
FG3M FG3A FG3_PCT FTM FTA FT_PCT OREB DREB REB AST STL BLK TOV PF PTS PLUS_MINUS VIDEO_AVAILABLE
```

Player grain, 32, in this exact order:

```
SEASON_ID PLAYER_ID PLAYER_NAME TEAM_ID TEAM_ABBREVIATION TEAM_NAME GAME_ID GAME_DATE MATCHUP WL
MIN FGM FGA FG_PCT FG3M FG3A FG3_PCT FTM FTA FT_PCT OREB DREB REB AST STL BLK TOV PF PTS
PLUS_MINUS FANTASY_PTS VIDEO_AVAILABLE
```

**The three extra player columns are interleaved, not appended** — Gate 0 recorded them as a set
difference ("the same, plus `PLAYER_ID`, `PLAYER_NAME`, `FANTASY_PTS`"), which is true of the set
and misleading about the order. `PLAYER_ID` and `PLAYER_NAME` sit at positions 1 and 2, directly
after `SEASON_ID`; `FANTASY_PTS` sits between `PLUS_MINUS` and `VIDEO_AVAILABLE`. A bronze model
that assumed the team list with three columns appended would misalign **every** field from
`TEAM_ID` onward while every uniqueness test still passed.

This is precisely why bronze projects columns **by name** via `list_position(headers, ...)` rather
than by ordinal, and why AC 19's drift guard compares the ordered list in both directions.

The ordered list is byte-identical across 2003-04, 2019-20 and 2024-25 at both grains, and matches
Gate 0's list exactly. **No column drift inside the pilot range** — so the ordered drift guard
(AC 19) starts from a real baseline rather than a hopeful one.

## Keys — `GAME_ID` is a 10-character zero-padded string

Across all six payloads the set of distinct `GAME_ID` character widths is exactly `{10}` and the
set of Python types is exactly `{str}`. Sample: `'0021900002'`.

**AC 14's fixed-width pattern is therefore `^\d{10}$`, measured and not guessed.** Casting this to
an integer destroys the padding while every join still "works" and every uniqueness test still
passes — which is why the test exists.

## dim_team — franchise drift is real, and now counted

R5 flagged cross-season franchise-identity drift as inferred from domain knowledge and unverified in
this repo. It is now measured.

| Scope | Distinct `(team_id, team_name)` pairs | Distinct `team_id` |
|---|---|---|
| Within 2003-04 | 29 | 29 |
| Within 2019-20 | 30 | 30 |
| Within 2024-25 | 30 | 30 |
| **Across all three** | **34** | **30** |

Four `team_id`s carry more than one name across the span:

| `team_id` | Names | Abbreviations |
|---|---|---|
| 1610612740 | New Orleans Hornets · New Orleans Pelicans | NOH, NOP |
| 1610612746 | LA Clippers · Los Angeles Clippers | **LAC only** |
| 1610612751 | New Jersey Nets · Brooklyn Nets | NJN, BKN |
| 1610612760 | Seattle SuperSonics · Oklahoma City Thunder | SEA, OKC |

**This settles P6 from a number.** A naive `select distinct team_id, team_name` produces 34 rows for
30 franchises and fails its own `unique(team_id)` test — exactly the failure the scope predicted.
One row per `team_id` with the name resolved as-of the latest observation is the decided grain, and
the as-of hazard it buys (a 2003-04 Sonics game rendering as "Oklahoma City Thunder") goes into the
model's persisted description.

Note 1610612746: the Clippers changed only their *display name* under one unchanged abbreviation. A
grain keyed on abbreviation instead of `team_id` would have silently collapsed it and looked fine.

## MATCHUP, home/away, and five games with no home team

`MATCHUP` carries both tokens in every pilot season, with **zero unparseable values**:

| Season | ` vs. ` | ` @ ` | Neither | Games | Every game 1 home + 1 away? |
|---|---|---|---|---|---|
| 2003-04 | 1,189 | 1,189 | 0 | 1,189 | ✅ |
| 2019-20 | 1,059 | 1,059 | 0 | 1,059 | ✅ |
| 2024-25 | 1,225 | 1,235 | 0 | 1,230 | ❌ **five exceptions** |

**Five 2024-25 games carry ` @ ` on both rows — neither team is designated home:**

```
0022400147  2024-11-02  WAS @ MIA | MIA @ WAS
0022400621  2025-01-23  SAS @ IND | IND @ SAS
0022400633  2025-01-25  SAS @ IND | IND @ SAS
0022401229  2024-12-14  ATL @ MIL | MIL @ ATL
0022401230  2024-12-14  OKC @ HOU | HOU @ OKC
```

5 games × 2 rows accounts for the imbalance exactly: 1230 − 5 = 1,225 home, 1230 + 5 = 1,235 away.

**The sharpest finding here is what 2019-20 does.** Every bubble game — all of them physically played
at one neutral site in Orlando — still carries a designated home team. So `MATCHUP`'s "home" is a
**scheduling designation, not a venue fact**, and only these five games decline to make one. Any
future model that reads home/away as "played in their own arena" is wrong for 1,059 games.

**Disposition:** `dim_game` gains an `is_neutral_site` flag with `home_team_id` / `away_team_id`
null for those games, and AC 12 is amended from *"exactly one of each game's two rows is flagged
home and one away"* to *"…for every game not flagged neutral-site"*. Decided by the user on
2026-08-15 against this measurement.

## NBA Cup — what this endpoint can and cannot say

Probed because the neutral-site games raised it. Measured:

- **No column identifies a tournament game.** All 29 are box-score fields; there is no round, venue,
  or competition marker.
- **The Cup Final is not in the regular-season log.** 2024-12-17 returns no games at all (the
  calendar jumps 2024-12-16 → 2024-12-19), and **every one of the 30 teams shows exactly 82 games**.
  Had the final been included, its two participants would show 83.
- **The semifinals are in it**, at sequence numbers **1229 and 1230** — the last two of a contiguous
  1..1230 numbering, allocated out of chronological order.
- **Neutral-site is not a proxy for Cup.** Only two of the five neutral games are Cup semifinals.

So the structure is: group stage, quarterfinals and semifinals *are* regular-season games and count
toward a team's record; the Championship game does not, and the source already excludes it. **There
is no correctness problem** in this slice from treating all 82 as regular-season games.

What is genuinely unavailable is **labelling**: which of the 82 were Cup group-stage games cannot be
determined from this endpoint, so "how did we do in group play" is unanswerable here. That needs
another source and is follow-on scope, not this slice. `dim_game` already carries `season_type` from
day one so a new game population arrives as rows rather than a migration — the same seam.

## The empty response — and an honest correction to EXEC-02

Measured via `NBAStatsHTTP.send_api_request` (not `LeagueGameLog`, whose `get_request()` also parses
and so raises on a non-conforming body rather than returning it). Two structurally valid requests
for seasons that do not exist — `2099-00` and `1900-01`:

```
http status : 200
body bytes  : 512
top keys    : parameters, resource, resultSets
resultSets[0]: {headers, name, rowSet}
headers len : 29          <-- fully populated
rowSet  len : 0
```

**An empty response is HTTP 200 with a complete, well-formed envelope.** The 29 headers are all
present; only `rowSet` is empty.

This **falsifies the stated premise of binding correction EXEC-02**, which reasoned that the error
fixture must live outside the globbed tree because *"a payload with no `resultSets[0].headers`
either fails unification or injects a null-headers row."* An empty payload has headers and would
unify across a DuckDB glob without complaint.

**EXEC-02's conclusion is kept anyway, for a different and now-measured reason:** a capture of a
non-existent season inside the partitioned tree creates a meaningless `season=2099-00` partition
that the bronze-vs-landed row-count fidelity test (AC 13) would have to special-case. The error
case therefore still lands at `_error_cases/`, outside the glob, and is exercised only by offline
pytest.

**Still unmeasured, stated rather than glossed:** a *genuine* error body — a 5xx, a rate-limit
response, or an HTML block page. The endpoint answers 200 to nonsense seasons, and forcing a real
error would mean abusing a host this project is explicitly polite to. So the "error" half of AC 20's
"empty-or-error" is satisfied by the **empty** case, and the true-error shape remains `unconfirmed`.

## The pinned trade — from the payload, never from memory

AC 10 requires a specific known mid-season trade drawn from a captured payload. Selected by scanning
the landed player-grain payloads for a player with exactly two distinct `TEAM_ID`s in one season
whose games split cleanly — every game with the old team preceding every game with the new one.

**2024-25 — the pin used by the seed:**

| Field | Value |
|---|---|
| `player_id` | **1631108** (Max Christie) |
| Old team | **1610612747** — Los Angeles Lakers, 46 games |
| Last game with old team | **2025-02-01** |
| New team | **1610612742** — Dallas Mavericks, 32 games |
| First game with new team | **2025-02-04** |
| Total games | 78 |

**2003-04 — a second pin, on the far side of the hand-checking discontinuity:**

| Field | Value |
|---|---|
| `player_id` | **2032** (Darius Miles) |
| Old team | **1610612739** — Cleveland Cavaliers, 37 games |
| Last game with old team | **2004-01-20** |
| New team | **1610612757** — Portland Trail Blazers, 42 games |
| First game with new team | **2004-01-24** |
| Total games | 79 |

The two-day gap in each case is the interval `dim_player_team_stint` must interpolate, and where a
date deliberately resolves to the **old** team per Decision 3.

Population context: **81 players appear for more than one team in 2024-25** and **68 in 2003-04**, so
`assert_stints_did_not_degenerate` (AC 11) has a large non-vacuous population to assert against.

## Irregular-season properties, re-measured

| Property | 2019-20 | 2024-25 (control) |
|---|---|---|
| Team game counts | **64–75**, nine distinct values | 82 for all 30 |
| `GAME_DATE` range | 2019-10-22 .. **2020-08-14** | 2024-10-22 .. 2025-04-13 |
| Games outside an Oct–Apr window | **176** | 0 |

Confirms P5. The unequal-game-count half cannot survive whole-games fixture trimming and stays
deferred to the `--target local` run; the outside-the-window half does survive and is asserted in CI
with a row-count floor.

## Still unsettled after this probe

- **A genuine error/5xx body.** See above — unforced on purpose.
- **Playoffs.** `season_type_all_star='Playoffs'` has still never been called at any grain. Out of
  scope for the pilot; the parameter shape stays `unconfirmed`.
- **Rate limiting.** Sixteen calls total across all three probes. That still says nothing about
  sustained-backfill behaviour, which is why the rate-limit paragraph in `docs/data-sources.md`
  keeps its `unconfirmed` label per gated decision 3.
- **The other twenty seasons.** Three probed, twenty-three in range.
- **Which regular-season games are NBA Cup group-stage games.** Not determinable from this endpoint.
