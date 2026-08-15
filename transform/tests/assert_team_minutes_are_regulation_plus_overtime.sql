-- Every team-game's minutes are 240 plus 25 per overtime period: 240, 265, 290, 315, ...
--
-- FIVE PLAYERS x 48 MINUTES = 240 for regulation; each overtime adds five players x 5 minutes.
-- So the assertion is `min >= 240 and (min - 240) % 25 = 0`, and it is a real check on the `MIN`
-- parse: a `MM:SS` misread, a seconds-versus-minutes unit mix-up, or a decode reading the wrong
-- column all break the residue immediately, over 6,956 team-games of population.
--
-- THIS REPLACES THE CROSS-GRAIN RECONCILIATION, WHICH WAS DROPPED ON EVIDENCE. The scope made
-- "sum of player minutes equals team minutes" conditional on the `MIN` format
-- (`PROJECT_SCOPE.md:280`). Measured over all three real pilot seasons, that identity holds for
-- only 4,069 of 6,956 team-games -- 58.5%. The cause is not a bug and no parser recovers it:
-- `MIN` is an INTEGER at BOTH grains, so each player's minutes are already rounded to a whole
-- number before this repo ever sees them, and twelve rounded values do not re-sum to the exact
-- team total. Shipping the cross-grain version would have meant a permanently red test or a
-- tolerance band wide enough to catch nothing. Team-grain minutes, by contrast, are exact:
-- 6,956 of 6,956 land on a clean 240 + 25n.
--
-- IT READS BRONZE, NOT A SILVER FACT, because `fact_team_game` arrives next phase. Repoint it
-- then; the invariant does not change.
--
-- ROW-COUNT FLOOR: `nothing_checked` fires when no team-games were evaluated at all.

with team_games as (

    select
        team_box.game_id,
        team_box.team_id,
        team_box.min as team_minutes
    from {{ ref('bronze__nba_stats__league_game_log_team') }} as team_box

),

violations as (

    select
        'team minutes are not 240 plus 25 per overtime period' as failure,
        game_id,
        team_id,
        team_minutes
    from team_games
    where
        team_minutes is null
        or team_minutes < 240
        or (team_minutes - 240) % 25 <> 0

),

checked as (

    select count(*) as team_games_checked
    from team_games

),

nothing_checked as (

    select
        'no team-games checked -- the test saw an empty set' as failure,
        cast(null as varchar) as game_id,
        cast(null as bigint) as team_id,
        cast(null as bigint) as team_minutes
    from checked
    where team_games_checked = 0

)

select
    failure,
    game_id,
    team_id,
    team_minutes
from violations

union all

select
    failure,
    game_id,
    team_id,
    team_minutes
from nothing_checked
