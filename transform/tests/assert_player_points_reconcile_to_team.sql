-- THE CROSS-GRAIN PROOF. For every team-game, the sum of the players' box-score lines equals the
-- team's own line -- for points and for every other measure that is a plain sum of player events.
--
-- This is the invariant `transform/tests/README.md:30` names as this directory's canonical
-- example and lists first, and the one `requests/feature-requests/README.md` uses as its example
-- of a testable acceptance criterion. It is also the cheapest fan-out detector this repo has: a
-- join that multiplies player rows shows up here as a doubled sum long before anyone notices a
-- number looks wrong on a dashboard, and a join that DROPS rows shows up as a short one.
--
-- MEASURED, at full volume over all three pilot seasons: every measure in the `on` lists below
-- reconciles EXACTLY on 6,956 of 6,956 team-games. There is no tolerance band here and there must
-- not be one -- these are integer counts of discrete events, and a tolerance wide enough to
-- absorb a real fan-out catches nothing.
--
-- `tov` IS EXCLUDED FROM THE LISTS ON PURPOSE, AND IT IS A BASKETBALL FACT RATHER THAN A DEFECT.
-- A turnover can be charged to the TEAM rather than to any player -- a shot-clock violation, a
-- five-second inbound. Measured over the same 6,956 team-games, team `tov` equals the player sum
-- in only 3,541 of them; in 3,415 the team figure is HIGHER, by 0 to 7 with a mean excess of
-- 0.70, and it is LOWER in exactly ZERO. The excess is stable across seasons (0.68 / 0.63 / 0.80),
-- so it is not an era artefact. Adding `tov` here would redden the build on 49% of correct data.
-- The direction that IS invariant is asserted separately, and deliberately, by
-- `transform/tests/assert_team_turnovers_never_below_player_sum.sql`. If you came here because you
-- noticed `tov` was missing and assumed an oversight: it is not, and that test is the reason.
--
-- WHY `minutes_played` IS ALSO ABSENT: the source rounds player minutes to whole numbers before
-- this repo ever sees them, so twelve rounded values do not re-sum to the exact team total -- it
-- holds for only 58.5% of team-games. That reconciliation was dropped on evidence and replaced by
-- `assert_team_minutes_are_regulation_plus_overtime.sql`. The percentage columns (`fg_pct` and
-- friends) are ratios, not sums, and do not belong in an additive reconciliation at all.
--
-- BOTH GRAINS ARE UNPIVOTED TO LONG FORM SO THE FAILURE NAMES THE MEASURE. A reconciliation that
-- reports "something differs on this team-game" is worth far less than one that reports "`ast`
-- differs on this team-game, 24 against 25", and a wide comparison cannot say the second without
-- fourteen near-identical branches. `measure_name` survives into the output for that reason.
--
-- THE JOIN IS A FULL OUTER JOIN, NOT AN INNER ONE. "For every team-game" has to mean every
-- team-game on EITHER side: an inner join would let a team-game with zero surviving player rows
-- pass vacuously, which is precisely the shape a bad fixture trim or a dropped partition produces.
-- `is distinct from` then makes a missing side a violation rather than an unknown.
--
-- IF THIS GOES RED, SUSPECT THE FIXTURE BEFORE THE MODEL. A fixture trimmed by ROWS rather than by
-- WHOLE GAMES breaks this test by construction, which is exactly why `tests/fixtures/README.md`
-- makes "whole games, rows only" a rule rather than a preference. Do not relax the model or the
-- test to make a mis-trimmed fixture pass.
--
-- ROW-COUNT FLOOR: `nothing_checked` fires when no measure-comparisons happened at all, so an
-- empty corpus fails instead of passing vacuously.

with player_sums as (

    select
        game_id,
        team_id,
        sum(pts) as pts,
        sum(fgm) as fgm,
        sum(fga) as fga,
        sum(ftm) as ftm,
        sum(fta) as fta,
        sum(fg3m) as fg3m,
        sum(fg3a) as fg3a,
        sum(oreb) as oreb,
        sum(dreb) as dreb,
        sum(reb) as reb,
        sum(ast) as ast,
        sum(stl) as stl,
        sum(blk) as blk,
        sum(pf) as pf
    from {{ ref('fact_player_game') }}
    group by game_id, team_id

),

team_measures as (

    select
        game_id,
        team_id,
        pts,
        fgm,
        fga,
        ftm,
        fta,
        fg3m,
        fg3a,
        oreb,
        dreb,
        reb,
        ast,
        stl,
        blk,
        pf
    from {{ ref('fact_team_game') }}

),

player_long as (

    -- One row per (team-game, measure). DuckDB's `unpivot` drops NULL measures by default, and
    -- that is fine here rather than papered over: a measure that vanishes from one side finds no
    -- partner in the full outer join below, so it surfaces as a violation with a NULL on the
    -- side that lost it instead of being quietly skipped on both.
    unpivot player_sums
    on pts, fgm, fga, ftm, fta, fg3m, fg3a, oreb, dreb, reb, ast, stl, blk, pf
    into name measure_name value player_sum

),

team_long as (

    unpivot team_measures
    on pts, fgm, fga, ftm, fta, fg3m, fg3a, oreb, dreb, reb, ast, stl, blk, pf
    into name measure_name value team_value

),

compared as (

    select
        coalesce(player_long.game_id, team_long.game_id) as game_id,
        coalesce(player_long.team_id, team_long.team_id) as team_id,
        coalesce(player_long.measure_name, team_long.measure_name) as measure_name,
        player_long.player_sum,
        team_long.team_value
    from player_long
    full join team_long
        on
            player_long.game_id = team_long.game_id
            and player_long.team_id = team_long.team_id
            and player_long.measure_name = team_long.measure_name

),

violations as (

    select
        'player sum does not reconcile to the team total' as failure,
        measure_name,
        game_id,
        team_id,
        player_sum,
        team_value
    from compared
    where player_sum is distinct from team_value

),

checked as (

    select count(*) as comparisons_checked
    from compared

),

nothing_checked as (

    select
        'no measures compared -- the test saw an empty set' as failure,
        cast(null as varchar) as measure_name,
        cast(null as varchar) as game_id,
        cast(null as bigint) as team_id,
        cast(null as bigint) as player_sum,
        cast(null as bigint) as team_value
    from checked
    where comparisons_checked = 0

)

select
    failure,
    measure_name,
    game_id,
    team_id,
    player_sum,
    team_value
from violations

union all

select
    failure,
    measure_name,
    game_id,
    team_id,
    player_sum,
    team_value
from nothing_checked
