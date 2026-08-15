# Gate 0 — Endpoint Probe

**Verdict: the bulk-endpoint belief is `verified`.** One `leaguegamelog` call returns one full
season, at both player and team grain. The pilot is ~6 calls; the 23-season backfill is ~46.
The factor-of-1000 risk that sized this entire request is retired.

Measured **2026-08-14** from the project's dev environment via `nba_api`, invoked through
`uv run --with nba_api` — a throwaway install, nothing added to `pyproject.toml`. Read-only:
the probe hits the API, prints findings, and writes nothing. Pacing 0.6s between calls per
`CLAUDE.md`.

## Correction to the scoping panel

**The panel recorded, as `MEASURED` and "independently reproduced this session", that
`stats.nba.com` does not respond from this environment** — and marked Gate 0, the backfill,
and the fixture capture all **USER-RUN** on that basis, affecting 4 of 30 acceptance criteria.

That finding is **false**, and the cause is instructive.

It reproduces exactly as the panel described when the request is made with raw
`Invoke-WebRequest`, even with browser-like headers:

~~~
Invoke-WebRequest https://stats.nba.com/stats/leaguegamelog?... -Headers <browser-like> -TimeoutSec 25
  -> FAILED: The operation has timed out.
~~~

But a control the panel did not run separates the two candidate causes:

~~~
Invoke-WebRequest https://pypi.org/simple/ -TimeoutSec 15   -> HTTP 200      (egress works)
Resolve-DnsName stats.nba.com                               -> 23.62.65.90   (DNS resolves)
~~~

So it is not a sandboxed environment and not a DNS failure. And the client the request
actually proposes to use works fine:

~~~
LeagueGameLog(season='2023-24', player_or_team_abbreviation='T', timeout=45)
  -> OK rows=2460 cols=29 elapsed=0.6s
~~~

**The panel measured the wrong client and drew a scope-shaping conclusion from it.** All four
USER-RUN markings derived from it are void. This is also direct evidence for gated decision 8:
the "undocumented header knowledge a client needs to avoid being blocked" is real and
`nba_api` carries it — both halves of that were measured here by accident.

## Results

Four calls, 0.6s spacing, ~1.3s of API time total.

| Season | Grain | Rows | Cols | Distinct `GAME_ID` | Distinct `PLAYER_ID` | Dupe `(GAME_ID, PLAYER_ID)` |
|---|---|---|---|---|---|---|
| 2023-24 | team | 2,460 | 29 | 1,230 | — | — |
| 2023-24 | player | 26,401 | 32 | 1,230 | 572 | **0** |
| 2003-04 | team | 2,378 | 29 | 1,189 | — | — |
| 2003-04 | player | 23,894 | 32 | 1,189 | 442 | **0** |

**The counts are internally consistent, not coincidental.** 2,460 = 1,230 games × 2 teams.
2003-04 returns 1,189 games because the league had 29 teams that season — Charlotte joined in
2004-05 — and 29 × 82 / 2 = 1,189. A truncated or paginated response would not land on the
right number by accident.

Both seasons' `GAME_DATE` ranges are complete: 2023-10-24 .. 2024-04-14 and
2003-10-28 .. 2004-04-14.

## What this settles

**Open question 1 — does `leaguegamelog` return a full season per call, at both grains?**
`verified`. Yes, both. This was the request's first task and everything was sized against it.

**Grain (data contract).** The presumed `(GAME_ID, PLAYER_ID)` grain **holds** — zero
duplicates in either season, including 2003-04 which contains mid-season trades. This is the
key `dbt_utils.unique_combination_of_columns` will assert. Note the honest limit: verified on
two seasons, not twenty-three.

**Era coverage (data contract).** `PLUS_MINUS` — the column the request flagged as the most
likely to have its own early-availability cliff — is **present in 2003-04 with zero nulls**.
No tracking-derived columns appear in this endpoint at all. **The 2013-14 tracking boundary
does not bite this request**, which is a real simplification rather than a deferral: era-nullable
column handling is genuinely out of scope here.

**Return shape.** `get_data_frames()[0]` returns a pandas `DataFrame`, not JSON, with
`UPPER_SNAKE` column names. This confirms the repo's own canonical memory entry — *"`nba_api`
returns a DataFrame rather than JSON, and its column casing differs from the docs"* — which
had been carried as the archetypal example and never actually checked.

**Gated decision 10 is resolved by evidence, not judgment.** The panel asked whether to create
`docs/data-dictionary.md` or correct the dangling reference to it, and said to decide at Gate 0:
create it if any column has its own availability cliff, correct the sentence if none does.
None does. **Correct the sentence.**

## Columns returned

Team grain (29): `SEASON_ID, TEAM_ID, TEAM_ABBREVIATION, TEAM_NAME, GAME_ID, GAME_DATE,
MATCHUP, WL, MIN, FGM, FGA, FG_PCT, FG3M, FG3A, FG3_PCT, FTM, FTA, FT_PCT, OREB, DREB, REB,
AST, STL, BLK, TOV, PF, PTS, PLUS_MINUS, VIDEO_AVAILABLE`

Player grain (32): the same, plus `PLAYER_ID`, `PLAYER_NAME`, `FANTASY_PTS`.

Identical column sets across 2003-04 and 2023-24 at both grains — no column drift inside the
pilot range.

## What this probe did NOT settle

- **Only two of the three pilot seasons were probed.** 2019-20 (the bubble) was not called.
  It is the season most likely to break a calendar assumption, and its unequal team game counts
  are an assertion this slice should make against landed data.
- **Regular season only.** `season_type_all_star='Playoffs'` was not exercised; playoffs are
  out of scope for the pilot but the parameter shape is unverified.
- **Two seasons, not twenty-three.** The grain result is strong evidence, not proof, for the
  other twenty-one.
- **Nothing about rate limiting.** Four calls at 0.6s tells you nothing about how the host
  behaves over a sustained backfill. The 0.6s default stands unchallenged and untested.
- **No landing-zone or fixture work was done.** This probe wrote no files. Fixture capture is
  the plan's job.
