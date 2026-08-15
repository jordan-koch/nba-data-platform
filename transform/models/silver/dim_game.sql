-- Silver: one row per game. The team-grain payload's two rows per game collapse to one here,
-- and this is where home/away stops being a string and becomes a pair of columns.
--
-- HOME/AWAY IS THE ONE INFERRED STRUCTURE IN THIS SLICE. `matchup` is the only home/away signal
-- the endpoint carries: the row reading `DAL vs. LAL` is the home side, the row reading
-- `DAL @ LAL` is the away side, and nothing else in the payload says which is which. That is why
-- the derivation is PROVED by a zero-rows singular test that reads the bronze rows back
-- (`transform/tests/assert_every_game_has_exactly_two_teams.sql`) rather than trusted because it
-- reads plausibly. Deriving it is business logic, so it lives here and never in bronze.
--
-- NEUTRAL-SITE GAMES ARE REAL AND CARRY NO HOME SIDE. Measured over the three pilot seasons at
-- full volume: five 2024-25 games have ` @ ` on BOTH team rows -- 0022400147, 0022400621,
-- 0022400633, 0022401229 and 0022401230 -- while 2003-04 (1189 games) and 2019-20 (1059 games)
-- have none. For those five the source is explicitly saying neither team was designated home, so
-- `is_neutral_site` is true and BOTH `home_team_id` and `away_team_id` are NULL. Picking a side
-- to keep a test green would be fabricating a fact the payload denies.
--
-- GROUPED BY (game_id, game_date, season_id), NOT BY game_id ALONE. The two rows of a game agree
-- on all three today. If they ever stop agreeing this emits two rows and `unique` on `game_id`
-- goes red, which is louder than `min(game_date)` quietly picking a winner.
--
-- HOME AND AWAY ARE ASSIGNED ONLY FOR THE ONE-AND-ONE SHAPE. Any other row shape -- a missing
-- side, a duplicated side, two home rows -- leaves both ids NULL rather than letting `max()`
-- invent an answer, and the singular test above is what turns that shape into a red build.

with team_rows as (

    select
        game_id,
        game_date,
        season_id,
        team_id,
        (matchup like '% vs. %') as is_home_row,
        (matchup like '% @ %') as is_away_row
    from {{ ref('bronze__nba_stats__league_game_log_team') }}

),

collapsed as (

    select
        game_id,
        game_date,
        season_id,
        count(*) filter (where is_home_row) as home_row_count,
        count(*) filter (where is_away_row) as away_row_count,
        max(team_id) filter (where is_home_row) as home_side_team_id,
        max(team_id) filter (where is_away_row) as away_side_team_id
    from team_rows
    group by game_id, game_date, season_id

)

select
    game_id,
    game_date,
    season_id,
    -- The leading digit of SEASON_ID encodes the season type. `2` -> Regular Season is VERIFIED
    -- for this corpus: every landed row was pulled with `SeasonType=Regular Season` and every
    -- `season_id` in it starts with `2`. `4` -> Playoffs is INFERRED from stats.nba.com
    -- convention and is unverified here because no playoff game has been landed yet -- it is
    -- carried so playoffs arrive as ROWS rather than as a schema migration. Any other leading
    -- digit resolves to NULL ON PURPOSE: the `not_null` test in schema.yml then turns a newly
    -- landed season type into a red build asking for a decision, instead of a guessed label.
    case substr(season_id, 1, 1)
        when '2' then 'Regular Season'
        when '4' then 'Playoffs'
    end as season_type,
    (home_row_count = 0 and away_row_count = 2) as is_neutral_site,
    case
        when home_row_count = 1 and away_row_count = 1 then home_side_team_id
    end as home_team_id,
    case
        when home_row_count = 1 and away_row_count = 1 then away_side_team_id
    end as away_team_id
from collapsed
