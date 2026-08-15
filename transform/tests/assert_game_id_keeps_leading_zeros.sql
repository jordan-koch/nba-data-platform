-- `game_id` stays a zero-padded 10-character string IN BRONZE AND IN SILVER.
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
-- BOTH LAYERS, BECAUSE THE PROPERTY IS NOT INHERITED. Bronze reading the padding correctly says
-- nothing about what silver does with it afterwards: a `cast`, a `coalesce` against an integer, a
-- `join ... using` that widens a type, or a projection through a numeric intermediate all lose the
-- padding one layer down while every bronze assertion here stays green. Asserting only in bronze
-- would have left a future silver change free to strip the zeros and pass the whole suite -- so
-- every model in this project that CARRIES a `game_id` is listed below, and adding a model that
-- carries one without adding it here is the omission this test is meant to make hard.
-- `dim_player_team_stint` is deliberately absent: it carries dates and ids, no `game_id` column.
--
-- Width 10 is MEASURED, not assumed: all 335 rows across the six committed payloads, both
-- bronze grains, all three pilot seasons, and every silver row derived from them.
--
-- FLOOR: `nothing_checked` fires for any listed model that produced no values at all, so an empty
-- input fails rather than passing vacuously. The list is written out a SECOND time in
-- `expected_models` on purpose -- the floor is a left join FROM that list, so a model whose label
-- above is misspelled or whose branch is deleted reports zero values and turns the build red
-- instead of quietly dropping out of the assertion.

with game_ids as (

    select
        'bronze__nba_stats__league_game_log_player' as model_name,
        game_id,
        typeof(game_id) as game_id_type
    from {{ ref('bronze__nba_stats__league_game_log_player') }}

    union all

    select
        'bronze__nba_stats__league_game_log_team' as model_name,
        game_id,
        typeof(game_id) as game_id_type
    from {{ ref('bronze__nba_stats__league_game_log_team') }}

    union all

    select
        'dim_game' as model_name,
        game_id,
        typeof(game_id) as game_id_type
    from {{ ref('dim_game') }}

    union all

    select
        'fact_player_game' as model_name,
        game_id,
        typeof(game_id) as game_id_type
    from {{ ref('fact_player_game') }}

    union all

    select
        'fact_team_game' as model_name,
        game_id,
        typeof(game_id) as game_id_type
    from {{ ref('fact_team_game') }}

),

malformed as (

    select
        'game_id is not a 10-character string of digits' as failure,
        model_name,
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
        model_name,
        count(*) as game_id_values
    from game_ids
    group by model_name

),

expected_models as (

    select 'bronze__nba_stats__league_game_log_player' as model_name

    union all

    select 'bronze__nba_stats__league_game_log_team' as model_name

    union all

    select 'dim_game' as model_name

    union all

    select 'fact_player_game' as model_name

    union all

    select 'fact_team_game' as model_name

),

nothing_checked as (

    select
        'no game_id values in this model -- the test saw an empty set' as failure,
        expected.model_name,
        cast(null as varchar) as game_id,
        cast(null as varchar) as game_id_type
    from expected_models as expected
    left join checked as counted
        on expected.model_name = counted.model_name
    where coalesce(counted.game_id_values, 0) = 0

)

select
    failure,
    model_name,
    game_id,
    game_id_type
from malformed

union all

select
    failure,
    model_name,
    game_id,
    game_id_type
from nothing_checked
