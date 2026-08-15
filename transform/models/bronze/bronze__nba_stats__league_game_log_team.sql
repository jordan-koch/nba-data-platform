-- Bronze: `leaguegamelog` at TEAM grain, 1:1 with the landed payload.
--
-- Same column-store envelope as the player model, and the same four load-bearing details:
-- DuckDB lists are ONE-indexed (`resultsets[1]`); values are unwrapped with `->> '$'` and
-- never `cast(... as varchar)`, which would return the JSON *representation* and make
-- `game_id` 12 characters of quoted text that passes every test while being wrong; columns
-- are projected BY NAME through `list_position(headers, ...)` so a header reorder cannot
-- silently swap two same-typed columns; and `game_id` stays VARCHAR because the ids are
-- zero-padded.
--
-- 29 columns, measured identical across all three pilot seasons. This is the player list
-- minus `PLAYER_ID`, `PLAYER_NAME` and `FANTASY_PTS` -- it is NOT a prefix of it, so the
-- projection is written out rather than shared.
--
-- WHY THIS MODEL EXISTS BEFORE ITS FACT DOES. The team-grain fact arrives in Phase 7, but
-- this is the source of `dim_game`'s home/away and of `dim_team`, and it costs three extra
-- API calls for the pilot seasons. Landing it now keeps the dimensional work unblocked.
--
-- DEDUPLICATION: latest capture wins, on the natural key `(game_id, team_id)`. This is the
-- one transformation `models/bronze/README.md` permits beyond typing and casing, and it is
-- deliberately the only one -- no filtering, no joins, no semantic renaming. It runs BEFORE
-- the projection, on the raw cells, so the natural key is read out of the envelope exactly
-- once and the 29 columns are written out exactly once.

with landed as (

    select
        resultsets[1].headers as headers,
        resultsets[1].rowset as row_set,
        capture as capture_stamp
    from {{ source('nba_stats_landing', 'league_game_log_team') }}

),

exploded as (

    -- One row per rowSet element, across every capture of every partition. `headers` rides
    -- along because each row is projected against the header list of its own capture.
    select
        headers,
        capture_stamp,
        unnest(row_set) as cells
    from landed

),

ranked as (

    -- A CTE rather than `qualify`: unambiguously lintable under the duckdb dialect.
    --
    -- The `capture_stamp` tiebreak is currently a no-op and is kept deliberately. The stamp
    -- is the landing path's `capture=` segment, `captured_at` is `strptime()` of that same
    -- stamp, and the landing writer advances a colliding stamp by a second rather than
    -- overwriting -- so within one partition the stamps are already distinct and already
    -- sort chronologically as fixed-width text. Determinism rests on that uniqueness; the
    -- second ordering term states the intent and costs nothing if `captured_at` ever stops
    -- being derived from the stamp.
    select
        headers,
        capture_stamp,
        cells,
        row_number() over (
            partition by
                cells[list_position(headers, 'GAME_ID')] ->> '$',
                cells[list_position(headers, 'TEAM_ID')] ->> '$'
            order by
                strptime(capture_stamp, '%Y%m%dT%H%M%SZ') desc,
                capture_stamp desc
        ) as capture_rank
    from exploded

),

deduplicated as (

    select
        headers,
        capture_stamp,
        cells
    from ranked
    where capture_rank = 1

)

select
    cells[list_position(headers, 'SEASON_ID')] ->> '$' as season_id,
    cast(cells[list_position(headers, 'TEAM_ID')] ->> '$' as bigint) as team_id,
    cells[list_position(headers, 'TEAM_ABBREVIATION')] ->> '$' as team_abbreviation,
    cells[list_position(headers, 'TEAM_NAME')] ->> '$' as team_name,
    cells[list_position(headers, 'GAME_ID')] ->> '$' as game_id,
    cast(cells[list_position(headers, 'GAME_DATE')] ->> '$' as date) as game_date,
    cells[list_position(headers, 'MATCHUP')] ->> '$' as matchup,
    cells[list_position(headers, 'WL')] ->> '$' as wl,
    cast(cells[list_position(headers, 'MIN')] ->> '$' as bigint) as min,
    cast(cells[list_position(headers, 'FGM')] ->> '$' as bigint) as fgm,
    cast(cells[list_position(headers, 'FGA')] ->> '$' as bigint) as fga,
    cast(cells[list_position(headers, 'FG_PCT')] ->> '$' as double) as fg_pct,
    cast(cells[list_position(headers, 'FG3M')] ->> '$' as bigint) as fg3m,
    cast(cells[list_position(headers, 'FG3A')] ->> '$' as bigint) as fg3a,
    cast(cells[list_position(headers, 'FG3_PCT')] ->> '$' as double) as fg3_pct,
    cast(cells[list_position(headers, 'FTM')] ->> '$' as bigint) as ftm,
    cast(cells[list_position(headers, 'FTA')] ->> '$' as bigint) as fta,
    cast(cells[list_position(headers, 'FT_PCT')] ->> '$' as double) as ft_pct,
    cast(cells[list_position(headers, 'OREB')] ->> '$' as bigint) as oreb,
    cast(cells[list_position(headers, 'DREB')] ->> '$' as bigint) as dreb,
    cast(cells[list_position(headers, 'REB')] ->> '$' as bigint) as reb,
    cast(cells[list_position(headers, 'AST')] ->> '$' as bigint) as ast,
    cast(cells[list_position(headers, 'STL')] ->> '$' as bigint) as stl,
    cast(cells[list_position(headers, 'BLK')] ->> '$' as bigint) as blk,
    cast(cells[list_position(headers, 'TOV')] ->> '$' as bigint) as tov,
    cast(cells[list_position(headers, 'PF')] ->> '$' as bigint) as pf,
    cast(cells[list_position(headers, 'PTS')] ->> '$' as bigint) as pts,
    cast(cells[list_position(headers, 'PLUS_MINUS')] ->> '$' as bigint) as plus_minus,
    cast(cells[list_position(headers, 'VIDEO_AVAILABLE')] ->> '$' as bigint) as video_available,
    -- Recovered from the landing path, not from the payload: the capture segment is
    -- colon-free compact UTC because a colon is illegal in a Windows path.
    strptime(capture_stamp, '%Y%m%dT%H%M%SZ') as captured_at
from deduplicated
