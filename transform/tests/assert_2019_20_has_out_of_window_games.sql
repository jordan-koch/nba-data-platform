-- The 2019-20 season contains games OUTSIDE an October-April calendar, and the corpus keeps them.
--
-- This one is inverted on purpose: it fails when the property is ABSENT. The bubble season
-- restarted in Florida in late July 2020 and ran into August, so anything in this repo that
-- assumes an Oct-Apr season -- a date filter, a season-inferring `case`, a calendar join -- is
-- wrong for those games. The guard against that is a corpus that still HAS them, and a trimmed
-- fixture is exactly the thing that quietly loses them.
--
-- MEASURED at full volume: 88 DISTINCT 2019-20 games fall outside the window (8 in July, 80 in
-- August). Note 88 is distinct GAMES; the 176 in the plan and in the Gate 0 notes counted team
-- ROWS and is corrected in `requests/feature-requests/box-score-foundation/reviews/`
-- `endpoint-probe.md`. The trimmed fixtures retain 3 of the 88, so the floor below is 3 and the
-- assertion is non-vacuous on BOTH targets rather than only against the real landing zone.
--
-- WHAT THIS DELIBERATELY DOES NOT TEST: the other half of the 2019-20 irregularity, that teams
-- played UNEQUAL game counts. Fixture trimming removes whole games, so a fixture-backed version
-- would report unequal counts forever and pass for the wrong reason. It belongs to a
-- `--target local` check against the full landing zone, and it is deferred there rather than
-- faked here.
--
-- The season is selected by `season_id`'s four-digit start year rather than by its full value,
-- so a playoff or play-in row for the same season -- a different leading digit -- counts too
-- once one is ever landed.

with season_games as (

    select
        game_id,
        game_date
    from {{ ref('dim_game') }}
    where substr(season_id, 2, 4) = '2019'

),

counted as (

    select
        count(*) as season_game_count,
        count(*) filter (
            where month(game_date) not in (10, 11, 12, 1, 2, 3, 4)
        ) as out_of_window_game_count
    from season_games

)

select
    'the 2019-20 season is absent -- the assertion evaluated an empty set' as failure,
    season_game_count,
    out_of_window_game_count
from counted
where season_game_count = 0

union all

select
    'fewer 2019-20 games outside Oct-Apr than the corpus is known to retain' as failure,
    season_game_count,
    out_of_window_game_count
from counted
where out_of_window_game_count < 3
