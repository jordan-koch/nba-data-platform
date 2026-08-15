-- Bronze: `leaguegamelog` at PLAYER grain, 1:1 with the landed payload.
--
-- The endpoint answers with a column-store envelope: `resultSets[0].headers` holds the
-- column names and `resultSets[0].rowSet` holds one parallel array of values per row. A
-- tabular row only exists after that envelope is decoded, so the decode below is decoding
-- -- not business logic. No join, no filter, no rename beyond casing, no derived stat.
--
-- Four things here are load-bearing and quiet when wrong:
--
--   * DuckDB lists are ONE-indexed. It is `resultsets[1]`, never `[0]`.
--   * `rowSet` elements arrive typed JSON, not VARCHAR. `cast(v as varchar)` returns the
--     JSON *representation* -- '"0020300001"', quotes included, width 12 -- which passes
--     every uniqueness and not-null test while being silently wrong. `v ->> '$'` unwraps
--     to '0020300001', width 10, and preserves a real null as a real null.
--   * Columns are projected BY NAME through `list_position(headers, ...)`, never by
--     ordinal. A positional projection would survive the endpoint reordering its headers
--     and would swap two same-typed columns without failing anything.
--   * `game_id` stays VARCHAR. stats.nba.com ids are zero-padded; any numeric inference
--     eats the leading zero while every downstream join still appears to work.
--
-- No deduplication here. Latest-capture-wins arrives in the next phase alongside the
-- two-capture fixture that proves it, so this model is currently one row per landed
-- rowSet row across every capture -- which is what 1:1-with-the-source means.

with landed as (

    select
        resultsets[1].headers as headers,
        resultsets[1].rowset as row_set,
        capture as capture_stamp
    from {{ source('nba_stats_landing', 'league_game_log_player') }}

),

exploded as (

    -- One row per rowSet element. `headers` rides along because the projection below
    -- resolves every column against the header list of the capture it came from.
    select
        headers,
        capture_stamp,
        unnest(row_set) as cells
    from landed

)

select
    cells[list_position(headers, 'SEASON_ID')] ->> '$' as season_id,
    cast(cells[list_position(headers, 'PLAYER_ID')] ->> '$' as bigint) as player_id,
    cells[list_position(headers, 'PLAYER_NAME')] ->> '$' as player_name,
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
    cast(cells[list_position(headers, 'FANTASY_PTS')] ->> '$' as double) as fantasy_pts,
    cast(cells[list_position(headers, 'VIDEO_AVAILABLE')] ->> '$' as bigint) as video_available,
    -- Recovered from the landing path, not from the payload: the capture segment is
    -- colon-free compact UTC because a colon is illegal in a Windows path.
    strptime(capture_stamp, '%Y%m%dT%H%M%SZ') as captured_at
from exploded
