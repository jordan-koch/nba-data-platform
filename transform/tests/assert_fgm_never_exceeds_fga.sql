-- Field goals made never exceed field goals attempted, at either grain.
--
-- The cheapest possible arithmetic sanity check, and it is here because it fails LOUDLY on the
-- two mistakes that are otherwise invisible: a projection that swaps two same-typed columns, and
-- a join that fans a fact out and lands the wrong row's values beside each other. `fgm` and
-- `fga` sit adjacent in the endpoint's header list, which is exactly where a positional decode
-- goes wrong.
--
-- BOTH GRAINS, VIA DIFFERENT RELATIONS FOR NOW. Player grain reads the silver fact. Team grain
-- reads the BRONZE team model, because `fact_team_game` does not exist yet -- it arrives in the
-- next phase, and this test should be repointed at it then. Reading bronze in the meantime is
-- what keeps the team-grain half of the assertion from being silently absent for a phase.
--
-- A null `fga` beside a non-null `fgm` is also a failure: it means attempts went missing while
-- makes survived, which no real box score does.
--
-- ROW-COUNT FLOOR: `nothing_checked` fires per grain, so an empty relation on either side fails
-- rather than contributing zero rows and reading as a pass.
--
-- Measured at full volume over the three pilot seasons: zero violations at either grain.

with graded as (

    select
        'player' as grain,
        game_id,
        cast(player_id as varchar) as entity_id,
        fgm,
        fga
    from {{ ref('fact_player_game') }}

    union all

    select
        'team' as grain,
        game_id,
        cast(team_id as varchar) as entity_id,
        fgm,
        fga
    from {{ ref('bronze__nba_stats__league_game_log_team') }}

),

violations as (

    select
        'field goals made exceed field goals attempted' as failure,
        grain,
        game_id,
        entity_id,
        fgm,
        fga
    from graded
    where
        fgm > fga
        or (fgm is not null and fga is null)

),

checked as (

    select
        count(*) filter (where grain = 'player') as player_rows,
        count(*) filter (where grain = 'team') as team_rows
    from graded

),

nothing_checked as (

    select
        'no rows checked at this grain -- the test saw an empty set' as failure,
        'player' as grain,
        cast(null as varchar) as game_id,
        cast(null as varchar) as entity_id,
        cast(null as bigint) as fgm,
        cast(null as bigint) as fga
    from checked
    where player_rows = 0

    union all

    select
        'no rows checked at this grain -- the test saw an empty set' as failure,
        'team' as grain,
        cast(null as varchar) as game_id,
        cast(null as varchar) as entity_id,
        cast(null as bigint) as fgm,
        cast(null as bigint) as fga
    from checked
    where team_rows = 0

)

select
    failure,
    grain,
    game_id,
    entity_id,
    fgm,
    fga
from violations

union all

select
    failure,
    grain,
    game_id,
    entity_id,
    fgm,
    fga
from nothing_checked
