{{
    config(
        unique_key=['game_id', 'team_id']
    )
}}

-- Silver: one row per team per game -- 6,956 rows over the 3,478 pilot games. The other half of
-- the cross-grain pair: this is what `fact_player_game` reconciles TO.
--
-- `minutes_played`, NOT `min`. Phase 6 renamed bronze's `min` to `minutes_played` on
-- `fact_player_game`; this model uses the same name because two facts decoded from ONE endpoint
-- disagreeing about a column name is the kind of drift nobody notices until a union or a
-- grain-to-grain comparison silently fails. The other reason is unchanged: `select min from t` is
-- a syntax error in DuckDB. Unlike the player grain, TEAM minutes are exact -- 240 plus 25 per
-- overtime period, 6,956 of 6,956, asserted by
-- `transform/tests/assert_team_minutes_are_regulation_plus_overtime.sql`.
--
-- `unique_key` IS DECLARED THOUGH THE MATERIALIZATION IGNORES IT, for the same reason it is on
-- `fact_player_game`: the materialization is `table` (full refresh) inherited from
-- `dbt_project.yml`, all three pilot seasons are long finalized, and the first in-progress season
-- or first nightly run requires the switch to `incremental` + `merge`. Declaring the key now makes
-- that a config change rather than a rewrite. Box scores get restated days later -- the fixture
-- set carries a second capture of one 2003-04 game precisely so that rule has evidence behind it.
--
-- BRONZE HAS ALREADY DEDUPLICATED ON `(game_id, team_id)` -- latest capture wins -- so this is a
-- straight projection with no aggregation. If that ever stops being true, the
-- `unique_combination_of_columns` test in `schema.yml` goes red here rather than the reconcile
-- test going red one grain away from the cause.
--
-- WHAT IS DELIBERATELY NOT CARRIED, mirroring `fact_player_game` column for column:
--   * `game_date`, `season_id`, `matchup` -- game attributes; they live on `dim_game`.
--   * `wl` -- NOT CARRIED, and this is the one place this model departs from the obvious. It is a
--     genuine team-game attribute rather than a game one, so it has a defensible home here. It is
--     left out because `fact_player_game`'s schema already assigns `wl` to the game attributes,
--     and because the winner is derivable from the two sides' `pts` plus `dim_game`. Carrying it
--     is a small, additive change if a consumer wants it; carrying it inconsistently across the
--     two facts is not.
--   * `team_abbreviation`, `team_name` -- dimension attributes, and they are `dim_team`'s answer.
--     Duplicating them here would create a second answer to "what is this team called", which is
--     the exact drift the as-of-latest rule in `dim_team` exists to make legible.
--   * `video_available` -- MUST NOT be read here. It is the restated-capture sentinel in
--     `transform/tests/assert_latest_capture_wins.sql`, and that test works only because no model
--     consumes the column. Reading it downstream quietly retires the probe.
--   * `captured_at` -- landing provenance, not a measure.
--
-- `tov` IS CARRIED AND IT IS NOT COMPARABLE TO THE PLAYER SUM BY EQUALITY. Team turnovers exist:
-- a shot-clock violation or a five-second inbound is charged to the team and to no player. See
-- `transform/tests/assert_team_turnovers_never_below_player_sum.sql`, which asserts the
-- inequality that IS true, and the header of `assert_player_points_reconcile_to_team.sql`, which
-- records why `tov` is the one measure missing from the equality list.

select
    team_box.game_id,
    team_box.team_id,
    team_box.min as minutes_played,
    team_box.fgm,
    team_box.fga,
    team_box.fg_pct,
    team_box.fg3m,
    team_box.fg3a,
    team_box.fg3_pct,
    team_box.ftm,
    team_box.fta,
    team_box.ft_pct,
    team_box.oreb,
    team_box.dreb,
    team_box.reb,
    team_box.ast,
    team_box.stl,
    team_box.blk,
    team_box.tov,
    team_box.pf,
    team_box.pts,
    team_box.plus_minus
from {{ ref('bronze__nba_stats__league_game_log_team') }} as team_box
