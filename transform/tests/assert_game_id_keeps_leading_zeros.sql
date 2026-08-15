-- `game_id` stays a zero-padded 10-character string at every bronze grain.
--
-- This is the quietest way this project could break. `0020300001` inferred as a number
-- becomes 20300001, every join still matches because both sides lost the same digits, every
-- uniqueness and not-null test still passes, and nothing looks wrong until a value is
-- compared against a source that kept the padding. So the assertion is made on both the
-- declared TYPE and the literal SHAPE, not on one of them:
--
--   * `typeof(game_id) = 'VARCHAR'` catches a numeric inference at the read.
--   * `^\d{10}$` catches a value that is textual but mangled -- ` 0020300001`, `2.03e7`, or
--     the 12-character `"0020300001"` that `cast(v as varchar)` returns instead of `->> '$'`
--     when someone unwraps the JSON envelope the wrong way.
--
-- Width 10 is MEASURED, not assumed: all 335 rows across the six committed payloads, both
-- grains, all three pilot seasons.
--
-- FLOOR: `nothing_checked` fires when either model produced no values at all, so an empty
-- input fails rather than passing vacuously.

with game_ids as (

    select
        'player' as grain,
        game_id,
        typeof(game_id) as game_id_type
    from {{ ref('bronze__nba_stats__league_game_log_player') }}

    union all

    select
        'team' as grain,
        game_id,
        typeof(game_id) as game_id_type
    from {{ ref('bronze__nba_stats__league_game_log_team') }}

),

malformed as (

    select
        'game_id is not a 10-character string of digits' as failure,
        grain,
        game_id,
        game_id_type
    from game_ids
    where
        game_id_type <> 'VARCHAR'
        or game_id is null
        or not regexp_matches(game_id, '^\d{10}$')

),

checked as (

    select
        count(*) filter (where grain = 'player') as player_values,
        count(*) filter (where grain = 'team') as team_values
    from game_ids

),

nothing_checked as (

    select
        'no game_id values at this grain -- the test saw an empty set' as failure,
        'player' as grain,
        cast(null as varchar) as game_id,
        cast(null as varchar) as game_id_type
    from checked
    where player_values = 0

    union all

    select
        'no game_id values at this grain -- the test saw an empty set' as failure,
        'team' as grain,
        cast(null as varchar) as game_id,
        cast(null as varchar) as game_id_type
    from checked
    where team_values = 0

)

select
    failure,
    grain,
    game_id,
    game_id_type
from malformed

union all

select
    failure,
    grain,
    game_id,
    game_id_type
from nothing_checked
