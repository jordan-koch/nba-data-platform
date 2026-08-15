-- Every game has exactly two team rows, and `dim_game`'s home/away derivation agrees with them.
--
-- This is the proof behind the ONE INFERRED STRUCTURE in this slice. `dim_game` reads home and
-- away out of `MATCHUP`'s ` vs. ` / ` @ ` token, and a parse that reads plausibly is not a parse
-- that is right. So the assertion goes back to the BRONZE rows and re-counts the tokens
-- independently, rather than checking `dim_game` against a column `dim_game` derived itself.
--
-- THE NEUTRAL BRANCH IS ASSERTED POSITIVELY, WHICH IS THE WHOLE POINT. Five 2024-25 games carry
-- ` @ ` on BOTH team rows -- the source designating no host. A test that merely EXCLUDED games
-- flagged neutral would pass with the flag set on every game in the league, so a flagged game
-- must show exactly zero home rows and exactly two away rows, and the flag itself must agree
-- with the token counts in both directions.
--
-- ROW-COUNT FLOOR: `nothing_compared` fires when the join saw no games at all, so an empty
-- upstream fails loudly instead of returning zero rows and reading as a pass.
--
-- Measured over the three pilot seasons at full volume: 3,473 one-home-one-away games and 5
-- neutral-site games, and no other shape at all. The trimmed fixtures retain one of the five
-- (`0022400621`, SAS/IND on 2025-01-23), so the neutral branch is live in CI and not only local.

with bronze_shape as (

    select
        game_id,
        count(*) as team_row_count,
        count(*) filter (where matchup like '% vs. %') as home_row_count,
        count(*) filter (where matchup like '% @ %') as away_row_count
    from {{ ref('bronze__nba_stats__league_game_log_team') }}
    group by game_id

),

dimension as (

    select
        game_id,
        is_neutral_site,
        home_team_id,
        away_team_id
    from {{ ref('dim_game') }}

),

joined as (

    -- FULL OUTER, not INNER: a game present on one side and absent from the other is exactly the
    -- failure an inner join would hide, and it is the shape a bad collapse produces.
    select
        coalesce(bronze_shape.game_id, dimension.game_id) as game_id,
        bronze_shape.team_row_count,
        bronze_shape.home_row_count,
        bronze_shape.away_row_count,
        dimension.is_neutral_site,
        dimension.home_team_id,
        dimension.away_team_id,
        (bronze_shape.game_id is not null) as in_bronze,
        (dimension.game_id is not null) as in_dimension
    from bronze_shape
    full outer join dimension on bronze_shape.game_id = dimension.game_id

),

failures as (

    select
        'a game does not have exactly two team rows in bronze' as failure,
        game_id,
        team_row_count,
        home_row_count,
        away_row_count,
        is_neutral_site
    from joined
    where in_bronze and team_row_count is distinct from 2

    union all

    select
        'a game is in bronze but not in dim_game, or in dim_game but not in bronze' as failure,
        game_id,
        team_row_count,
        home_row_count,
        away_row_count,
        is_neutral_site
    from joined
    where not (in_bronze and in_dimension)

    union all

    select
        'a non-neutral game is not exactly one home row and one away row' as failure,
        game_id,
        team_row_count,
        home_row_count,
        away_row_count,
        is_neutral_site
    from joined
    where
        is_neutral_site = false
        and (home_row_count <> 1 or away_row_count <> 1)

    union all

    select
        'a neutral-site game is not exactly zero home rows and two away rows' as failure,
        game_id,
        team_row_count,
        home_row_count,
        away_row_count,
        is_neutral_site
    from joined
    where
        is_neutral_site = true
        and (home_row_count <> 0 or away_row_count <> 2)

    union all

    select
        'is_neutral_site disagrees with the matchup tokens on the bronze rows' as failure,
        game_id,
        team_row_count,
        home_row_count,
        away_row_count,
        is_neutral_site
    from joined
    where
        in_bronze
        and is_neutral_site is distinct from (home_row_count = 0 and away_row_count = 2)

    union all

    select
        'home/away team ids are not null exactly for the neutral-site games' as failure,
        game_id,
        team_row_count,
        home_row_count,
        away_row_count,
        is_neutral_site
    from joined
    where
        (
            is_neutral_site = true
            and (home_team_id is not null or away_team_id is not null)
        )
        or (
            is_neutral_site = false
            and (home_team_id is null or away_team_id is null)
        )

    union all

    select
        'a game has the same team on both sides' as failure,
        game_id,
        team_row_count,
        home_row_count,
        away_row_count,
        is_neutral_site
    from joined
    where home_team_id = away_team_id

),

counted as (

    select count(*) as games_compared
    from joined

),

nothing_compared as (

    select
        'no games compared -- the test saw an empty set' as failure,
        cast(null as varchar) as game_id,
        cast(null as bigint) as team_row_count,
        cast(null as bigint) as home_row_count,
        cast(null as bigint) as away_row_count,
        cast(null as boolean) as is_neutral_site
    from counted
    where games_compared = 0

)

select
    failure,
    game_id,
    team_row_count,
    home_row_count,
    away_row_count,
    is_neutral_site
from failures

union all

select
    failure,
    game_id,
    team_row_count,
    home_row_count,
    away_row_count,
    is_neutral_site
from nothing_compared
