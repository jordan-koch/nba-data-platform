-- THE CONTAINMENT PROOF. Every observed box-score row falls inside EXACTLY ONE stint for that
-- player, and that stint names the team the player was actually observed to appear for.
--
-- This is the invariant `transform/tests/README.md` lists as "a player's team on a game date
-- matches an open interval in the SCD2 history" -- now against `dim_player_team_stint`, which is
-- where affiliation lives. `dim_player` deliberately carries no team at all.
--
-- IT CATCHES THREE FAILURES AT ONCE, which is why the counts are separated rather than being one
-- `exists` check:
--   * ZERO containing stints -- the run-collapse dropped an observation, or a boundary closed a
--     day early. This is the shape the rejected observation-bounded `valid_to` would produce for
--     every date in a trade gap.
--   * MORE THAN ONE containing stint -- the ranges overlap, which is the shape a team-GROUPED
--     collapse produces the moment a player returns to a former team (A -> B -> A).
--   * EXACTLY ONE, NAMING THE WRONG TEAM -- the runs were collapsed in the wrong order, or a
--     boundary landed on the wrong side of a trade.
--
-- READ ITS LIMIT BEFORE YOU TRUST IT: THIS TEST IS DERIVED FROM THE SAME OBSERVATIONS IT CHECKS.
-- It proves the run-collapse lost nothing, reordered nothing and invented no overlap -- and it is
-- VACUOUS EVERYWHERE BETWEEN GAME DATES, because there is no observation there to compare against.
-- The interpolated span is precisely the part this cannot see. That is what
-- `transform/tests/assert_known_trade_resolves_both_sides.sql` exists for: it pins dates INSIDE a
-- real trade gap against a committed seed. Neither test is sufficient alone; they are a pair.
--
-- ROW-COUNT FLOOR: `nothing_checked` fires when no observation was checked at all, so an empty
-- corpus -- or a fixture trim that removed every row -- fails instead of passing vacuously.

with observations as (

    select
        player_game.player_id,
        player_game.game_id,
        player_game.team_id,
        game.game_date
    from {{ ref('fact_player_game') }} as player_game
    inner join {{ ref('dim_game') }} as game
        on player_game.game_id = game.game_id

),

containment as (

    -- LEFT JOIN, not inner: an observation that matches NO stint has to survive to be counted as
    -- a violation. An inner join would silently drop exactly the rows this test exists to find.
    -- The join is `between valid_from and valid_to` -- an as-of-GAME-DATE resolution, never
    -- `is_current`, which would answer as of today for a 2003-04 game.
    select
        observations.player_id,
        observations.game_id,
        observations.game_date,
        observations.team_id as observed_team_id,
        count(stint.player_id) as containing_stints,
        count(*) filter (
            where stint.team_id = observations.team_id
        ) as agreeing_stints
    from observations
    left join {{ ref('dim_player_team_stint') }} as stint
        on
            observations.player_id = stint.player_id
            and observations.game_date between stint.valid_from and stint.valid_to
    group by
        observations.player_id,
        observations.game_id,
        observations.game_date,
        observations.team_id

),

violations as (

    select
        'observed team does not match exactly one containing stint' as failure,
        player_id,
        game_id,
        game_date,
        observed_team_id,
        containing_stints,
        agreeing_stints
    from containment
    where containing_stints <> 1 or agreeing_stints <> 1

),

checked as (

    select count(*) as observations_checked
    from containment

),

nothing_checked as (

    select
        'no observations checked -- the test saw an empty set' as failure,
        cast(null as bigint) as player_id,
        cast(null as varchar) as game_id,
        cast(null as date) as game_date,
        cast(null as bigint) as observed_team_id,
        cast(null as bigint) as containing_stints,
        cast(null as bigint) as agreeing_stints
    from checked
    where observations_checked = 0

)

select
    failure,
    player_id,
    game_id,
    game_date,
    observed_team_id,
    containing_stints,
    agreeing_stints
from violations

union all

select
    failure,
    player_id,
    game_id,
    game_date,
    observed_team_id,
    containing_stints,
    agreeing_stints
from nothing_checked
