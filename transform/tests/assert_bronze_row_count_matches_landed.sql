-- Bronze must not lose or invent a row relative to the landing zone.
--
-- `models/bronze/README.md` states the invariant in prose: if bronze and the landed JSON
-- disagree, bronze is wrong. This is that sentence made executable. The comparison decodes
-- the payloads a SECOND time, straight from the source relation, rather than reading the
-- model -- so it catches a glob that matched no partition, a decode that dropped rows, a
-- union that double-counted, and a dedup that deleted too much.
--
-- THE RESTATED PARTITION IS WHY THIS IS NOT `count(*) = count(*)`. `season=2003-04` at team
-- grain holds two captures, eight landed rows between them, and six surviving rows. The
-- right expectation is the WINNING row per natural key -- neither the sum of all captures
-- (eight, which would fail) nor the newest capture's row count on its own (two, which would
-- also fail, because a restatement of one game does not restate the season around it).
--
-- Partitions are keyed on the payload's own `SEASON_ID` rather than the landing path's
-- `season=` segment, because the bronze models carry the former and not the latter. Both
-- sides of the comparison read it from the same place, so a path/payload disagreement
-- cannot masquerade as a row-count bug here.
--
-- FLOOR: a singular test that returns zero rows because it evaluated an empty set is worse
-- than no test. `nothing_compared` fires when EITHER grain contributed no partitions, which
-- is portable across corpora in a way that a hardcoded partition count is not.
--
-- RESOLVE THE COLUMN POSITIONS ONCE PER FILE, BEFORE THE UNNEST. This is not a micro-
-- optimisation. Selecting `resultsets[1].headers` alongside `unnest(resultsets[1].rowset)`
-- broadcasts the 32-element header list onto every unnested row: at three real pilot seasons
-- that is ~2.3M strings materialised to look up three positions that are CONSTANT per file,
-- and it died with `Out of Memory Error: Allocation failure` after 91 seconds. Three integers
-- carried through the unnest cost nothing and resolve by name just as `list_position` on the
-- header list does -- the positions still come from the envelope's own headers, never from an
-- ordinal literal. Fixtures are trimmed samples; shape bugs like this are invisible on them.

with player_src as (

    select
        capture as capture_stamp,
        resultsets[1].rowset as row_set,
        list_position(resultsets[1].headers, 'SEASON_ID') as i_season,
        list_position(resultsets[1].headers, 'GAME_ID') as i_game,
        list_position(resultsets[1].headers, 'PLAYER_ID') as i_entity
    from {{ source('nba_stats_landing', 'league_game_log_player') }}

),

team_src as (

    select
        capture as capture_stamp,
        resultsets[1].rowset as row_set,
        list_position(resultsets[1].headers, 'SEASON_ID') as i_season,
        list_position(resultsets[1].headers, 'GAME_ID') as i_game,
        list_position(resultsets[1].headers, 'TEAM_ID') as i_entity
    from {{ source('nba_stats_landing', 'league_game_log_team') }}

),

player_cells as (

    select
        capture_stamp,
        i_season,
        i_game,
        i_entity,
        unnest(row_set) as cells
    from player_src

),

team_cells as (

    select
        capture_stamp,
        i_season,
        i_game,
        i_entity,
        unnest(row_set) as cells
    from team_src

),

landed_keys as (

    select
        'player' as grain,
        capture_stamp,
        cells[i_season] ->> '$' as season_id,
        cells[i_game] ->> '$' as game_id,
        cells[i_entity] ->> '$' as entity_id
    from player_cells

    union all

    select
        'team' as grain,
        capture_stamp,
        cells[i_season] ->> '$' as season_id,
        cells[i_game] ->> '$' as game_id,
        cells[i_entity] ->> '$' as entity_id
    from team_cells

),

landed_ranked as (

    select
        grain,
        season_id,
        row_number() over (
            partition by grain, game_id, entity_id
            order by capture_stamp desc
        ) as capture_rank
    from landed_keys

),

landed_counts as (

    select
        grain,
        season_id,
        count(*) as landed_rows
    from landed_ranked
    where capture_rank = 1
    group by grain, season_id

),

bronze_counts as (

    select
        'player' as grain,
        season_id,
        count(*) as bronze_rows
    from {{ ref('bronze__nba_stats__league_game_log_player') }}
    group by season_id

    union all

    select
        'team' as grain,
        season_id,
        count(*) as bronze_rows
    from {{ ref('bronze__nba_stats__league_game_log_team') }}
    group by season_id

),

compared as (

    -- FULL OUTER, not INNER: a partition present on one side and absent from the other is
    -- the exact failure an inner join would hide.
    select
        coalesce(landed_counts.grain, bronze_counts.grain) as grain,
        coalesce(landed_counts.season_id, bronze_counts.season_id) as season_id,
        landed_counts.landed_rows,
        bronze_counts.bronze_rows
    from landed_counts
    full outer join bronze_counts
        on
            landed_counts.grain = bronze_counts.grain
            and landed_counts.season_id = bronze_counts.season_id

),

mismatched as (

    select
        'bronze row count disagrees with the winning capture in the landing zone' as failure,
        grain,
        season_id,
        landed_rows,
        bronze_rows
    from compared
    where landed_rows is distinct from bronze_rows

),

covered as (

    select
        count(*) filter (where grain = 'player') as player_partitions,
        count(*) filter (where grain = 'team') as team_partitions
    from compared

),

nothing_compared as (

    select
        'no partitions compared at this grain -- the test saw an empty set' as failure,
        'player' as grain,
        cast(null as varchar) as season_id,
        cast(null as bigint) as landed_rows,
        cast(null as bigint) as bronze_rows
    from covered
    where player_partitions = 0

    union all

    select
        'no partitions compared at this grain -- the test saw an empty set' as failure,
        'team' as grain,
        cast(null as varchar) as season_id,
        cast(null as bigint) as landed_rows,
        cast(null as bigint) as bronze_rows
    from covered
    where team_partitions = 0

)

select
    failure,
    grain,
    season_id,
    landed_rows,
    bronze_rows
from mismatched

union all

select
    failure,
    grain,
    season_id,
    landed_rows,
    bronze_rows
from nothing_compared
