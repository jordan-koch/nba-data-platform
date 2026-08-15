-- THE ANTI-DEGENERACY FLOOR. Multi-team seasons must SURVIVE the run-collapse, and no stint may
-- close before it opens.
--
-- WHY THIS TEST EXISTS AT ALL, given that containment already passes: a stint model that collapses
-- to ONE ROW PER PLAYER PER SEASON -- or one row per player, full stop -- can still contain every
-- observation it is asked about, as long as the player never changed teams. For the players who
-- DID change teams it would answer with the wrong team, but only for dates where the two stints
-- disagree, and `assert_player_team_matches_open_stint` would catch that. What it would NOT catch
-- is the same collapse applied to a corpus that has been trimmed, filtered or refactored down to
-- single-team players: containment stays green and the model quietly stops modelling trades. A
-- floor on the POPULATION is the only thing that turns that into a red build.
--
-- MEASURED, over all three pilot seasons: 209 player-seasons carry more than one stint -- 68 in
-- 2003-04, 60 in 2019-20, 81 in 2024-25, across 205 distinct players. This test asserts only that
-- the count is GREATER THAN ZERO rather than pinning 209, because the number legitimately moves
-- with the corpus: the CI target builds from trimmed fixtures and must satisfy the same floor.
--
-- THE SECOND ASSERTION IS THE ORDERING ONE. `valid_to` is the day before the NEXT stint's first
-- game, so it can only precede `valid_from` if two stints for one player-season started on the
-- same date -- which is measured impossible here (no player has two box-score rows on one date,
-- and none has two teams on one date) but is exactly what a same-day double-header or a bad
-- ordering key would introduce. A ZERO-LENGTH stint is NOT a violation: 20 season-final stints
-- span a single date, which is the ten-day-contract case and is why the range test in `schema.yml`
-- sets `zero_length_range_allowed: true`.
--
-- ROW-COUNT FLOOR: an empty model reports zero multi-stint player-seasons, so the first branch
-- fires and an empty corpus fails rather than passing vacuously.

with stints_per_player_season as (

    select
        player_id,
        season_id,
        count(*) as stint_count
    from {{ ref('dim_player_team_stint') }}
    group by player_id, season_id

),

multi_stint_population as (

    select count(*) as multi_stint_player_seasons
    from stints_per_player_season
    where stint_count > 1

),

degenerated as (

    select
        'the run-collapse degenerated -- no player-season has more than one stint' as failure,
        cast(null as bigint) as player_id,
        cast(null as varchar) as season_id,
        cast(null as date) as valid_from,
        cast(null as date) as valid_to
    from multi_stint_population
    where multi_stint_player_seasons = 0

),

inverted_ranges as (

    select
        'stint closes before it opens -- valid_to precedes valid_from' as failure,
        player_id,
        season_id,
        valid_from,
        valid_to
    from {{ ref('dim_player_team_stint') }}
    where valid_to < valid_from

)

select
    failure,
    player_id,
    season_id,
    valid_from,
    valid_to
from degenerated

union all

select
    failure,
    player_id,
    season_id,
    valid_from,
    valid_to
from inverted_ranges
