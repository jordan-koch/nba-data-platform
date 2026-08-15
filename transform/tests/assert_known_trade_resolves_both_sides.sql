-- THE NON-VACUOUS COMPANION. One real trade, pinned to a committed seed, asserted on BOTH sides of
-- the trade date AND on the days in between where no game was played.
--
-- `assert_player_team_matches_open_stint.sql` is derived from the same observations it checks, so
-- it proves the run-collapse lost and reordered nothing and is VACUOUS EVERYWHERE BETWEEN GAME
-- DATES. The interpolated span -- the whole reason `valid_to` runs to the day before the next
-- stint rather than to the last game played -- is invisible to it. This test is the one that reads
-- the interpolation, because `transform/seeds/known_trade_expectations.csv` carries dates on which
-- NO OBSERVATION EXISTS and states what the model must answer for them anyway.
--
-- THE PINNED TRADE, taken from the captured payload and not from memory: Max Christie
-- (`player_id` 1631108) appears for the Los Angeles Lakers (1610612747) from 2024-10-22 through
-- 2025-02-01, and for the Dallas Mavericks (1610612742) from 2025-02-04 onward. 2025-02-02 and
-- 2025-02-03 fall in the gap between those two observations, and per this model's boundary rule
-- they RESOLVE TO THE OLD TEAM -- the Lakers. That is a deliberate disposition, not an artefact:
-- the rejected alternative leaves those two days answering with zero rows.
--
-- EVERY PINNED DATE IS PRESENT UNDER BOTH TARGETS. The committed CI fixture retains 2024-10-22,
-- 2025-01-30, 2025-02-01, 2025-02-04 and 2025-02-06 for this player -- both trade-boundary games
-- plus one more each side -- so the seed deliberately pins NO date after 2025-02-06. His real
-- season runs to 2025-04-13 under `--target local`; pinning that date would redden CI on a
-- correctly built model, which is a fixture-shaped failure rather than a data one.
--
-- THE JOIN IS `between valid_from and valid_to`, WHICH IS THE POINT. Any future as-of join must
-- resolve affiliation as-of the GAME DATE this way and must NEVER filter on `is_current` --
-- resolving as-of today instead of as-of the game is this project's likeliest silent join bug, and
-- this test is written in the shape downstream code should copy.
--
-- TWO ROW-COUNT FLOORS: an empty seed, and a seed that still has rows but no longer pins any
-- INTERPOLATED date. The second one matters more than it looks -- delete the two gap rows and this
-- file keeps passing while testing nothing the containment test did not already cover.

with expectations as (

    -- `as_of_date` is cast rather than trusted: seed column types are inferred by the adapter, and
    -- a date that lands as VARCHAR would make the comparison below silently lexical.
    select
        player_id,
        player_name,
        expected_team_id,
        expectation_kind,
        cast(as_of_date as date) as as_of_date
    from {{ ref('known_trade_expectations') }}

),

resolved as (

    select
        expectations.player_id,
        expectations.player_name,
        expectations.as_of_date,
        expectations.expected_team_id,
        expectations.expectation_kind,
        count(stint.player_id) as containing_stints,
        min(stint.team_id) as resolved_team_id
    from expectations
    left join {{ ref('dim_player_team_stint') }} as stint
        on
            expectations.player_id = stint.player_id
            and expectations.as_of_date between stint.valid_from and stint.valid_to
    group by
        expectations.player_id,
        expectations.player_name,
        expectations.as_of_date,
        expectations.expected_team_id,
        expectations.expectation_kind

),

violations as (

    select
        'pinned as-of date does not resolve to the expected team' as failure,
        player_id,
        player_name,
        as_of_date,
        expectation_kind,
        expected_team_id,
        resolved_team_id,
        containing_stints
    from resolved
    where containing_stints <> 1 or resolved_team_id is distinct from expected_team_id

),

seed_coverage as (

    select
        count(*) as pinned_dates,
        count(*) filter (where expectation_kind = 'interpolated') as pinned_gap_dates
    from expectations

),

empty_seed as (

    select
        'the pinned-trade seed is empty -- this test proves nothing' as failure,
        cast(null as bigint) as player_id,
        cast(null as varchar) as player_name,
        cast(null as date) as as_of_date,
        cast(null as varchar) as expectation_kind,
        cast(null as bigint) as expected_team_id,
        cast(null as bigint) as resolved_team_id,
        cast(null as bigint) as containing_stints
    from seed_coverage
    where pinned_dates = 0

),

no_gap_pinned as (

    select
        'the seed pins no interpolated date -- only observed dates are checked' as failure,
        cast(null as bigint) as player_id,
        cast(null as varchar) as player_name,
        cast(null as date) as as_of_date,
        cast(null as varchar) as expectation_kind,
        cast(null as bigint) as expected_team_id,
        cast(null as bigint) as resolved_team_id,
        cast(null as bigint) as containing_stints
    from seed_coverage
    where pinned_gap_dates = 0

)

select
    failure,
    player_id,
    player_name,
    as_of_date,
    expectation_kind,
    expected_team_id,
    resolved_team_id,
    containing_stints
from violations

union all

select
    failure,
    player_id,
    player_name,
    as_of_date,
    expectation_kind,
    expected_team_id,
    resolved_team_id,
    containing_stints
from empty_seed

union all

select
    failure,
    player_id,
    player_name,
    as_of_date,
    expectation_kind,
    expected_team_id,
    resolved_team_id,
    containing_stints
from no_gap_pinned
