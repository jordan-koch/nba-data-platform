-- A team's turnovers are NEVER fewer than the sum of its players' turnovers.
--
-- WHY THIS IS AN INEQUALITY AND NOT AN EQUALITY -- the whole point of the file. Every other
-- summable measure in a box score reconciles exactly across the two grains, and
-- `transform/tests/assert_player_points_reconcile_to_team.sql` asserts that for fourteen of them.
-- `tov` does not, and the reason is basketball rather than plumbing: SOME TURNOVERS ARE CHARGED
-- TO THE TEAM AND TO NO PLAYER. A shot-clock violation, a five-second inbound, a defensive
-- three-second call in some scorings -- nobody committed them individually, so they land on the
-- team line and never appear in any player's row.
--
-- MEASURED at full volume over all three pilot seasons, 6,956 team-games:
--
--     team.tov EQUAL to sum(player.tov):  3,541 games
--     team.tov HIGHER  than the sum:      3,415 games   excess 0..7, mean 0.70
--     team.tov LOWER   than the sum:          0 games   <- never, and that is the invariant
--
-- Mean excess by season is 0.68 / 0.63 / 0.80 -- flat across a pre-tracking season, the bubble
-- season and a modern one -- so this is not an era boundary and not a scoring-convention change
-- that a date filter could carve around. An equality test on `tov` would be red on 49% of
-- perfectly correct data, which is why `tov` is excluded from the reconciliation and why this
-- file exists instead of a comment saying "tov is weird".
--
-- WHAT IT STILL CATCHES, which is the reason it is worth having rather than skipping `tov`
-- entirely. The inequality is one-directional and tight in the direction that matters: a fan-out
-- in `fact_player_game` doubles the player sum and pushes it above the team figure immediately; a
-- turnover misattributed from the team line onto a player does the same; a grain mix-up that puts
-- both teams' players under one team_id does it by roughly a factor of two. Every one of those
-- shows up here even though the equality version is unusable.
--
-- INNER JOIN IS DELIBERATE HERE. Presence on both grains is already asserted by the reconciliation
-- test's full outer join; this file makes exactly one claim, about the team-games that exist on
-- both sides, and duplicating the presence check would put two tests on one failure.
--
-- ROW-COUNT FLOOR: `nothing_checked` fires when no team-games were compared at all.

with player_turnovers as (

    select
        game_id,
        team_id,
        sum(tov) as player_tov
    from {{ ref('fact_player_game') }}
    group by game_id, team_id

),

team_turnovers as (

    select
        game_id,
        team_id,
        tov as team_tov
    from {{ ref('fact_team_game') }}

),

joined as (

    select
        player_turnovers.game_id,
        player_turnovers.team_id,
        player_turnovers.player_tov,
        team_turnovers.team_tov
    from player_turnovers
    inner join team_turnovers
        on
            player_turnovers.game_id = team_turnovers.game_id
            and player_turnovers.team_id = team_turnovers.team_id

),

violations as (

    select
        'team turnovers are BELOW the sum of player turnovers' as failure,
        game_id,
        team_id,
        player_tov,
        team_tov
    from joined
    where team_tov < player_tov

),

checked as (

    select count(*) as team_games_checked
    from joined

),

nothing_checked as (

    select
        'no team-games compared -- the test saw an empty set' as failure,
        cast(null as varchar) as game_id,
        cast(null as bigint) as team_id,
        cast(null as bigint) as player_tov,
        cast(null as bigint) as team_tov
    from checked
    where team_games_checked = 0

)

select
    failure,
    game_id,
    team_id,
    player_tov,
    team_tov
from violations

union all

select
    failure,
    game_id,
    team_id,
    player_tov,
    team_tov
from nothing_checked
