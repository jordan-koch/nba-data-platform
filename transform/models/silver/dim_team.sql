-- Silver: one row per franchise, keyed on `team_id`. The conformed team dimension every fact in
-- this layer joins through.
--
-- `select distinct team_id, team_name` IS THE WRONG MODEL AND IT FAILS ITS OWN GRAIN TEST.
-- Measured over the three pilot seasons at full volume: 30 distinct `team_id`s but 34 distinct
-- `(team_id, team_name)` pairs. Four franchises are observed under two names across the span:
--
--     1610612740  New Orleans Hornets   -> New Orleans Pelicans
--     1610612746  Los Angeles Clippers  -> LA Clippers
--     1610612751  New Jersey Nets       -> Brooklyn Nets
--     1610612760  Seattle SuperSonics   -> Oklahoma City Thunder
--
-- `team_id` IS THE STABLE THING; the name and the abbreviation are not. A relocation or a rename
-- changes what the payload calls the franchise and leaves the id alone, which is exactly why the
-- grain is keyed on the id and the uniqueness test in `schema.yml` is on `team_id` ALONE.
--
-- A GRAIN KEYED ON ABBREVIATION WOULD LOOK CORRECT AND BE WRONG. 1610612746 changed only its
-- display name -- `Los Angeles Clippers` to `LA Clippers` -- under one unchanged `LAC`. Measured,
-- there are 33 distinct `(team_id, team_abbreviation)` pairs against 34 name pairs, so an
-- abbreviation key silently collapses that franchise's two display names into one row and reports
-- a clean 33 that hides the collapse.
--
-- NAME AND ABBREVIATION ARE RESOLVED AS-OF THE LATEST OBSERVATION, AND THEY COME FROM THE SAME
-- ROW. Picking each column's latest value independently could assemble a pair that never existed
-- in any game. `row_number()` over one ordering picks one real observed row and both attributes
-- are read off it. A CTE rather than `qualify`, matching the bronze models: unambiguously
-- lintable under the duckdb dialect.
--
-- THE TIEBREAK IS `game_id`, NOT NOTHING. A franchise plays at most one game on a date in this
-- corpus, but leaving the ordering non-total would make the model's output depend on scan order,
-- and a dimension that changes between two builds of identical data is the worst kind of flake.

with team_rows as (

    select
        team_id,
        team_name,
        team_abbreviation,
        game_date,
        game_id
    from {{ ref('bronze__nba_stats__league_game_log_team') }}

),

ranked as (

    select
        team_id,
        team_name,
        team_abbreviation,
        row_number() over (
            partition by team_id
            order by game_date desc, game_id desc
        ) as observation_rank
    from team_rows

)

select
    team_id,
    team_name,
    team_abbreviation
from ranked
where observation_rank = 1
