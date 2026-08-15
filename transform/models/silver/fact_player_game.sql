{{
    config(
        unique_key=['game_id', 'player_id']
    )
}}

-- Silver: one row per player per game. The first fact this repo has ever had.
--
-- `unique_key` IS DECLARED ABOVE THOUGH THE MATERIALIZATION IGNORES IT. The materialization is
-- `table` (full refresh), inherited from `dbt_project.yml`'s silver block rather than restated
-- here. Declaring the key now means the eventual switch to `incremental` + `merge` is a config
-- change rather than a rewrite, and it puts the fact's identity next to the SQL that produces it.
-- The MERGE deferral and its trigger are written out in this model's `schema.yml` description so
-- a future reader inherits them from the relation itself, not from a commit message.
--
-- `team_id` COMES FROM THE OBSERVED BOX-SCORE ROW AND FROM NOWHERE ELSE. Not from a join to
-- `dim_team`, and above all not from the SCD2 stint model built later: the fact is what the stint
-- model is DERIVED FROM, so joining back to it would make fact correctness depend on the
-- interpolation the fact is supposed to be the evidence for. A player traded mid-season therefore
-- appears under the team he actually played that game for, resolved as-of the game and not
-- as-of today.
--
-- WHAT IS DELIBERATELY NOT CARRIED, and why:
--   * `game_date`, `season_id`, `matchup`, `wl` -- game attributes; they live on `dim_game`, and
--     the join is the point.
--   * `player_name`, `team_abbreviation`, `team_name` -- dimension attributes, arriving with
--     `dim_player` and `dim_team`. Duplicating them here would create a second answer to
--     "what is this player called".
--   * `fantasy_pts` -- the endpoint's own scoring formula, carried in bronze because bronze is
--     1:1 with the source. Nothing in this slice consumes it and silver is where that choice
--     gets made.
--   * `video_available` -- MUST NOT be read here. `transform/models/bronze/schema.yml` documents
--     it as read by no model and no reconciliation, which is precisely what makes it safe as the
--     restated-capture sentinel in `transform/tests/assert_latest_capture_wins.sql`. Consuming
--     it downstream would quietly retire that test's edited-column probe.
--   * `captured_at` -- landing provenance, not a measure.
--
-- `min` IS AN INTEGER COUNT OF MINUTES ON THIS ENDPOINT, NOT `MM:SS` -- measured in Phase 3 and
-- again at full volume, so there is no parser here. It is renamed to `minutes_played` because
-- semantic renaming is exactly what silver is for and because a column literally named `min`
-- cannot be selected bare in DuckDB (`select min from t` is a syntax error). Player minutes are
-- rounded to whole minutes AT THE SOURCE, so twelve of them do not re-sum to the exact team
-- total -- see the header of
-- `transform/tests/assert_team_minutes_are_regulation_plus_overtime.sql`.

select
    player_box.game_id,
    player_box.player_id,
    player_box.team_id,
    player_box.min as minutes_played,
    player_box.fgm,
    player_box.fga,
    player_box.fg_pct,
    player_box.fg3m,
    player_box.fg3a,
    player_box.fg3_pct,
    player_box.ftm,
    player_box.fta,
    player_box.ft_pct,
    player_box.oreb,
    player_box.dreb,
    player_box.reb,
    player_box.ast,
    player_box.stl,
    player_box.blk,
    player_box.tov,
    player_box.pf,
    player_box.pts,
    player_box.plus_minus
from {{ ref('bronze__nba_stats__league_game_log_player') }} as player_box
