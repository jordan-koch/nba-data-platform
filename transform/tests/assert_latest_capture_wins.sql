-- Bronze keeps exactly one row per natural key, and it keeps the LATEST capture's version.
--
-- Four clauses, because no one of them implies the others:
--
--   * `duplicated_keys` -- one row per `(game_id, player_id)` and per `(game_id, team_id)`.
--     A dedup that never ran fails here.
--   * `wrong_capture_won` -- for a recaptured key, the surviving row's `captured_at` is the
--     MAXIMUM capture stamp in the source. Catches a dedup ordered the wrong way round; a
--     uniqueness check cannot, because keeping the earlier row also keeps exactly one row.
--   * `value_mismatches` -- for a recaptured key, EVERY column of the surviving bronze row
--     equals the same column of the source row from that maximum capture. Provenance and
--     payload are asserted separately on purpose: a rewrite that took `max(captured_at)`
--     independently of the cells would satisfy the clause above while serving superseded
--     numbers, and this clause is what notices.
--   * `empty_population` -- the floor.
--
-- GENERIC, NOT A SENTINEL. An earlier version hardcoded the corpus's restated row
-- (`0020300003`, `1610612742`, `video_available = 99`). That can never pass against a real
-- landing zone, where no partition has been recaptured -- and a fidelity test that only
-- works on fixtures is not a fidelity test. The recaptured key set is derived from the
-- source instead, so this is non-vacuous on the committed corpus (which holds one restated
-- game, two keys), correctly vacuous on a landing zone that has never been re-pulled, and
-- automatically covers every restatement the backfill ever lands.
--
-- Deliberately NO floor requiring a restatement to exist: on real data none does, and that
-- is legitimate. The corpus-completeness half is asserted offline and main-thread in
-- `tests/test_fixture_recorder.py`, which fails if the fixtures ever stop containing a
-- recaptured partition.
--
-- COST. Everything past `recaptured_keys` is gated on that key set, which is EMPTY against a
-- never-recaptured landing zone, so the expensive half of this test does no work there. The
-- full-volume half is one unnest and one group-by, and the header list is never broadcast
-- across unnested rows -- see `assert_bronze_row_count_matches_landed` for what that costs.
--
-- Values are compared through `coalesce(cast(try_cast(v as double) as varchar), v)`, applied
-- identically to both sides, so that a landed `0.500` and a bronze DOUBLE `0.5` agree while
-- `DAL` and `2003-10-28` still compare as text.

with player_key_counts as (

    select
        game_id,
        player_id,
        count(*) as rows_per_key
    from {{ ref('bronze__nba_stats__league_game_log_player') }}
    group by game_id, player_id

),

team_key_counts as (

    select
        game_id,
        team_id,
        count(*) as rows_per_key
    from {{ ref('bronze__nba_stats__league_game_log_team') }}
    group by game_id, team_id

),

duplicated_keys as (

    select
        'more than one row survives dedup for this natural key' as failure,
        'player' as grain,
        game_id,
        cast(player_id as varchar) as entity_id,
        rows_per_key as observed
    from player_key_counts
    where rows_per_key > 1

    union all

    select
        'more than one row survives dedup for this natural key' as failure,
        'team' as grain,
        game_id,
        cast(team_id as varchar) as entity_id,
        rows_per_key as observed
    from team_key_counts
    where rows_per_key > 1

),

player_src as (

    -- Column positions resolved ONCE PER FILE, before the unnest. `headers` stays in this
    -- six-row relation and is joined back to only where it is needed.
    select
        season,
        capture,
        resultsets[1].headers as headers,
        resultsets[1].rowset as row_set,
        list_position(resultsets[1].headers, 'GAME_ID') as i_game,
        list_position(resultsets[1].headers, 'PLAYER_ID') as i_entity
    from {{ source('nba_stats_landing', 'league_game_log_player') }}

),

team_src as (

    select
        season,
        capture,
        resultsets[1].headers as headers,
        resultsets[1].rowset as row_set,
        list_position(resultsets[1].headers, 'GAME_ID') as i_game,
        list_position(resultsets[1].headers, 'TEAM_ID') as i_entity
    from {{ source('nba_stats_landing', 'league_game_log_team') }}

),

file_headers as (

    select
        'player' as grain,
        season,
        capture,
        headers
    from player_src

    union all

    select
        'team' as grain,
        season,
        capture,
        headers
    from team_src

),

player_cells as (

    select
        season,
        capture,
        i_game,
        i_entity,
        unnest(row_set) as cells
    from player_src

),

team_cells as (

    select
        season,
        capture,
        i_game,
        i_entity,
        unnest(row_set) as cells
    from team_src

),

landed_keyed as (

    select
        'player' as grain,
        season,
        capture,
        cells,
        cells[i_game] ->> '$' as game_id,
        cells[i_entity] ->> '$' as entity_id
    from player_cells

    union all

    select
        'team' as grain,
        season,
        capture,
        cells,
        cells[i_game] ->> '$' as game_id,
        cells[i_entity] ->> '$' as entity_id
    from team_cells

),

recaptured_keys as (

    -- Empty whenever no partition has been re-pulled, which is the normal state of a real
    -- landing zone. Everything below is gated on it.
    select
        grain,
        game_id,
        entity_id,
        max(capture) as winning_capture
    from landed_keyed
    group by grain, game_id, entity_id
    having count(distinct capture) > 1

),

bronze_restated as (

    -- `exists` keeps the FROM single-table, so the semi-join filters BEFORE `to_json` is
    -- evaluated: on a never-recaptured landing zone this projects zero rows, not 79k.
    select
        'player' as grain,
        p.game_id,
        cast(p.player_id as varchar) as entity_id,
        p.captured_at,
        to_json(p) as row_json
    from {{ ref('bronze__nba_stats__league_game_log_player') }} as p
    where
        exists (
            select 1
            from recaptured_keys as r
            where
                r.grain = 'player'
                and r.game_id = p.game_id
                and r.entity_id = cast(p.player_id as varchar)
        )

    union all

    select
        'team' as grain,
        t.game_id,
        cast(t.team_id as varchar) as entity_id,
        t.captured_at,
        to_json(t) as row_json
    from {{ ref('bronze__nba_stats__league_game_log_team') }} as t
    where
        exists (
            select 1
            from recaptured_keys as r
            where
                r.grain = 'team'
                and r.game_id = t.game_id
                and r.entity_id = cast(t.team_id as varchar)
        )

),

wrong_capture_won as (

    select
        'a recaptured key did not keep the maximum capture stamp' as failure,
        bronze_restated.grain,
        bronze_restated.game_id,
        bronze_restated.entity_id,
        cast(null as bigint) as observed
    from bronze_restated
    inner join recaptured_keys
        on
            bronze_restated.grain = recaptured_keys.grain
            and bronze_restated.game_id = recaptured_keys.game_id
            and bronze_restated.entity_id = recaptured_keys.entity_id
    where
        bronze_restated.captured_at
        is distinct from strptime(recaptured_keys.winning_capture, '%Y%m%dT%H%M%SZ')

),

winning_cells as (

    select
        landed_keyed.grain,
        landed_keyed.season,
        landed_keyed.capture,
        landed_keyed.game_id,
        landed_keyed.entity_id,
        landed_keyed.cells
    from landed_keyed
    inner join recaptured_keys
        on
            landed_keyed.grain = recaptured_keys.grain
            and landed_keyed.game_id = recaptured_keys.game_id
            and landed_keyed.entity_id = recaptured_keys.entity_id
            and landed_keyed.capture = recaptured_keys.winning_capture

),

winning_columns as (

    -- Two parallel unnests zip elementwise, so header i lines up with cell i. Column names
    -- still come from the envelope's own header list, never from an ordinal literal.
    select
        winning_cells.grain,
        winning_cells.game_id,
        winning_cells.entity_id,
        winning_cells.capture,
        unnest(file_headers.headers) as column_name,
        unnest(winning_cells.cells) as cell
    from winning_cells
    inner join file_headers
        on
            winning_cells.grain = file_headers.grain
            and winning_cells.season = file_headers.season
            and winning_cells.capture = file_headers.capture

),

compared_values as (

    select
        winning_columns.grain,
        winning_columns.game_id,
        winning_columns.entity_id,
        winning_columns.capture,
        winning_columns.column_name,
        winning_columns.cell ->> '$' as landed_value,
        json_extract_string(
            bronze_restated.row_json, lower(winning_columns.column_name)
        ) as bronze_value
    from winning_columns
    inner join bronze_restated
        on
            winning_columns.grain = bronze_restated.grain
            and winning_columns.game_id = bronze_restated.game_id
            and winning_columns.entity_id = bronze_restated.entity_id

),

value_mismatches as (

    select
        'a recaptured key kept the wrong capture value for ' || column_name
        || ' -- bronze has ' || coalesce(bronze_value, '<null>')
        || ', capture ' || capture || ' landed ' || coalesce(landed_value, '<null>') as failure,
        grain,
        game_id,
        entity_id,
        cast(null as bigint) as observed
    from compared_values
    where
        coalesce(cast(try_cast(landed_value as double) as varchar), landed_value)
        is distinct from coalesce(cast(try_cast(bronze_value as double) as varchar), bronze_value)

),

populated as (

    select
        (select count(*) from player_key_counts) as player_keys,
        (select count(*) from team_key_counts) as team_keys

),

empty_population as (

    select
        'no natural keys at this grain -- the test saw an empty set' as failure,
        'player' as grain,
        cast(null as varchar) as game_id,
        cast(null as varchar) as entity_id,
        cast(null as bigint) as observed
    from populated
    where player_keys = 0

    union all

    select
        'no natural keys at this grain -- the test saw an empty set' as failure,
        'team' as grain,
        cast(null as varchar) as game_id,
        cast(null as varchar) as entity_id,
        cast(null as bigint) as observed
    from populated
    where team_keys = 0

)

select
    failure,
    grain,
    game_id,
    entity_id,
    observed
from duplicated_keys

union all

select
    failure,
    grain,
    game_id,
    entity_id,
    observed
from wrong_capture_won

union all

select
    failure,
    grain,
    game_id,
    entity_id,
    observed
from value_mismatches

union all

select
    failure,
    grain,
    game_id,
    entity_id,
    observed
from empty_population
