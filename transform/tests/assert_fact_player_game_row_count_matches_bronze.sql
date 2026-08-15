-- THE GRAIN SENTRY: `fact_player_game` neither loses nor invents a player-game.
--
-- Its row count must equal bronze's DISTINCT `(game_id, player_id)` count, and the two key sets
-- must be identical.
--
-- WHY THIS EXISTS ALONGSIDE THE UNIQUENESS TEST, WHICH IS THE PART WORTH READING. Uniqueness
-- catches fan-OUT: a join that multiplies rows. Nothing in `schema.yml` catches silent row
-- LOSS -- an inner join to a dimension that is missing a key drops the fact rows for that key
-- and leaves a table that is still perfectly unique, still not-null, still passing every generic
-- test, and quietly short. That failure mode is one refactor away for as long as this model
-- exists, because the obvious next edit to a fact is to join it to something.
--
-- The comparison is against BRONZE rather than against the landing zone: bronze's own fidelity
-- to the landed JSON is already asserted by `assert_bronze_row_count_matches_landed.sql`, so
-- chaining the two covers landing -> bronze -> silver without decoding the envelope a third time.
--
-- ROW-COUNT FLOOR: `empty_population` fires when either side contributed no rows, so a build
-- against an empty corpus fails instead of passing vacuously with 0 = 0.

with bronze_keys as (

    select distinct
        game_id,
        player_id
    from {{ ref('bronze__nba_stats__league_game_log_player') }}

),

fact_keys as (

    select
        game_id,
        player_id
    from {{ ref('fact_player_game') }}

),

labelled as (

    select
        'bronze' as source_name,
        game_id,
        player_id
    from bronze_keys

    union all

    select
        'fact' as source_name,
        game_id,
        player_id
    from fact_keys

),

counted as (

    select
        count(*) filter (where source_name = 'bronze') as bronze_key_count,
        count(*) filter (where source_name = 'fact') as fact_row_count
    from labelled

),

count_mismatch as (

    select
        'fact_player_game row count differs from bronze distinct (game_id, player_id)' as failure,
        cast(null as varchar) as game_id,
        cast(null as bigint) as player_id,
        bronze_key_count,
        fact_row_count
    from counted
    where bronze_key_count is distinct from fact_row_count

),

empty_population as (

    select
        'no player-games compared -- the test saw an empty set on at least one side' as failure,
        cast(null as varchar) as game_id,
        cast(null as bigint) as player_id,
        bronze_key_count,
        fact_row_count
    from counted
    where bronze_key_count = 0 or fact_row_count = 0

),

key_differences as (

    -- Equal counts are not equal SETS. A drop of one key paired with a spurious one nets to zero
    -- on the count and shows up here.
    select
        'a (game_id, player_id) is in bronze but missing from fact_player_game' as failure,
        bronze_keys.game_id,
        bronze_keys.player_id,
        cast(null as bigint) as bronze_key_count,
        cast(null as bigint) as fact_row_count
    from bronze_keys
    left join fact_keys
        on
            bronze_keys.game_id = fact_keys.game_id
            and bronze_keys.player_id = fact_keys.player_id
    where fact_keys.game_id is null

    union all

    select
        'a (game_id, player_id) is in fact_player_game but not in bronze' as failure,
        fact_keys.game_id,
        fact_keys.player_id,
        cast(null as bigint) as bronze_key_count,
        cast(null as bigint) as fact_row_count
    from fact_keys
    left join bronze_keys
        on
            fact_keys.game_id = bronze_keys.game_id
            and fact_keys.player_id = bronze_keys.player_id
    where bronze_keys.game_id is null

)

select
    failure,
    game_id,
    player_id,
    bronze_key_count,
    fact_row_count
from count_mismatch

union all

select
    failure,
    game_id,
    player_id,
    bronze_key_count,
    fact_row_count
from empty_population

union all

select
    failure,
    game_id,
    player_id,
    bronze_key_count,
    fact_row_count
from key_differences
