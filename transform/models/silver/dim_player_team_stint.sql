-- Silver: one row per player per team-stint. THE MODEL THIS REQUEST EXISTS FOR.
--
-- NO ENDPOINT RETURNS PLAYER-TEAM HISTORY AS A TIME SERIES. `leaguegamelog` answers with
-- observations -- this player appeared for this team in this game -- so affiliation history has to
-- be DERIVED from the box-score rows themselves. That is why the facts landed first, and why this
-- model reads `fact_player_game` (the OBSERVED `team_id`) joined to `dim_game` for the date, and
-- never bronze: bronze is one row per capture-decoded source row, and the dedup that makes an
-- observation unique already happened in the fact.
--
-- GAPS AND ISLANDS, PARTITIONED BY (player_id, season_id) -- NOT GROUPED BY TEAM. Grouping by
-- `(player_id, season_id, team_id)` is the obvious implementation and it is WRONG on this corpus:
-- two `(player, season, team)` combinations are observed in TWO SEPARATE RUNS (A -> B -> A), and
-- 2024-25 has a player with three team switches in one season. A team-grouped aggregate merges the
-- two A-spells into one stint spanning the B-spell, and then B OVERLAPS it -- so
-- `mutually_exclusive_ranges` goes red on data that is perfectly correct. Returning to a former
-- team is A NEW STINT here, and the run-collapse below is what makes that true.
--
-- THE PARTITION INCLUDES season_id ON PURPOSE, AND LEBRON IS WHY. Exactly one player appears in
-- all three pilot seasons: 2544, from 2003-10-29 to 2025-04-11. A globally partitioned
-- run-collapse emits ONE stint spanning twenty-two years for him, because his observed team never
-- changes between the collapsed runs -- which is not a defensible answer to "what team was this
-- player on", in a repo anchored to his rookie year. Season-bounding also means the ranges are
-- non-contiguous by construction, which is exactly why the range test runs `gaps: 'allowed'`.
--
-- THE BOUNDARY RULE: valid_to IS THE DAY BEFORE THE NEXT STINT STARTS, NOT THE LAST GAME PLAYED.
-- Closing a stint at its own last observed game leaves the trade gap UNCOVERED -- an as-of join
-- for 2025-02-02 would return zero rows, which is the observation-bounded behaviour this model
-- deliberately rejects. Within a `(player_id, season_id)` partition each stint therefore runs
-- through to the day before the next stint's first game, and only the season's FINAL stint closes
-- at its own last observed game. A DATE INSIDE A TRADE GAP RESOLVES TO THE OLD TEAM.
--
-- THE INTERPOLATION STAYS VISIBLE RATHER THAN BEING FABRICATED SILENTLY. `last_game_prior_team`
-- and `first_game_new_team` are carried alongside so any reader can see which part of a stint is
-- observed and which part is interpolated, and falsify it against the fact.
--
-- valid_to IS NEVER NULL AND NEVER A 9999 SENTINEL. `mutually_exclusive_ranges` compares the
-- bounds directly and a null upper bound is a meaningless comparison; a sentinel year is a fake
-- fact that sorts. "Exactly one open interval per player" is expressed instead as a uniqueness
-- test on `is_current`, in this model's `schema.yml`.
--
-- MEASURED, over all three pilot seasons: 1,764 stints, 209 player-seasons carrying more than one
-- stint (68 / 60 / 81 by season) and 2 A -> B -> A revisits.
--
-- THREE DIFFERENT ONE-DAY COUNTS EXIST AND THEY ARE NOT INTERCHANGEABLE. 24 `(player, season,
-- team)` COMBINATIONS span exactly one date; 25 STINTS do, because one of those combinations is
-- split in two by a revisit; and only 20 survive as ZERO-LENGTH RANGES, because the boundary rule
-- extends every non-final one to the day before the next stint. The last number is the only one
-- `zero_length_range_allowed` ever sees -- and it is 216 on the trimmed CI fixture, where most
-- players retain a single game. Set it to the macro's default of `false` and the strict `<` it
-- selects fails on all of them, which is correct data reddening a build.
--
-- ONE GAME PER PLAYER PER DATE IS MEASURED, NOT ASSUMED: zero `(player_id, game_date)` pairs carry
-- two rows, and zero carry two different teams. That is what makes `valid_to >= valid_from` hold
-- by construction -- the next stint's first game is always a strictly later date -- and
-- `transform/tests/assert_stints_did_not_degenerate.sql` asserts it rather than trusting it.

with observed_affiliation as (

    -- The evidence, and the whole of it: one row per player per game, carrying the team the player
    -- was OBSERVED to appear for, dated by the game rather than by anything as-of today.
    select
        player_game.player_id,
        player_game.team_id,
        game.season_id,
        game.game_date
    from {{ ref('fact_player_game') }} as player_game
    inner join {{ ref('dim_game') }} as game
        on player_game.game_id = game.game_id

),

stint_boundaries as (

    -- The previous observation's team, within the season. Split into its own step rather than
    -- being nested inside the `case` below: sqlfluff's duckdb dialect cannot parse a window
    -- function on the right of `is distinct from` inside a `case when`, and reports it as an
    -- unparsable section plus a phantom unused-CTE error that names the wrong CTE entirely.
    select
        player_id,
        team_id,
        season_id,
        game_date,
        lag(team_id) over (
            partition by player_id, season_id
            order by game_date
        ) as prior_observed_team_id
    from observed_affiliation

),

stint_runs as (

    -- A stint STARTS wherever the observed team differs from the previous observation's, and the
    -- running sum of those starts numbers each island. `is distinct from` rather than `<>` so the
    -- partition's FIRST row -- whose `lag` is null -- opens a stint instead of evaluating to null
    -- and never incrementing. A return to a former team gets a NEW number here, which is the whole
    -- point of collapsing runs rather than grouping by team.
    select
        player_id,
        team_id,
        season_id,
        game_date,
        sum(case when team_id is distinct from prior_observed_team_id then 1 else 0 end) over (
            partition by player_id, season_id
            order by game_date
            rows between unbounded preceding and current row
        ) as stint_number
    from stint_boundaries

),

collapsed_runs as (

    -- One row per island. `team_id` is constant within an island by construction -- the island is
    -- defined by the team not changing -- so the aggregate picks the only value there is.
    select
        player_id,
        season_id,
        stint_number,
        min(team_id) as team_id,
        min(game_date) as valid_from,
        max(game_date) as last_game_prior_team
    from stint_runs
    group by player_id, season_id, stint_number

),

interpolated as (

    -- `first_game_new_team` is the next stint's first observed game, null for a season's final
    -- stint. It is both the evidence for the interpolated span and the source of `valid_to`.
    select
        player_id,
        season_id,
        team_id,
        valid_from,
        last_game_prior_team,
        lead(valid_from) over (
            partition by player_id, season_id
            order by valid_from
        ) as first_game_new_team
    from collapsed_runs

),

with_currency as (

    -- `is_current` marks the stint holding the player's GLOBALLY latest observation -- latest
    -- across seasons, not within one -- so a player last seen in 2003-04 still has exactly one.
    select
        player_id,
        season_id,
        team_id,
        valid_from,
        last_game_prior_team,
        first_game_new_team,
        coalesce(first_game_new_team - 1, last_game_prior_team) as valid_to,
        row_number() over (
            partition by player_id
            order by valid_from desc
        ) = 1 as is_current
    from interpolated

)

select
    player_id,
    team_id,
    season_id,
    valid_from,
    valid_to,
    is_current,
    last_game_prior_team,
    first_game_new_team
from with_currency
