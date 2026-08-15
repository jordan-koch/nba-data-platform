-- Silver: one row per player, keyed on `player_id` (the endpoint's `PERSON_ID`). The conformed
-- player dimension -- identity only.
--
-- THIS DIMENSION CARRIES NO TEAM, DELIBERATELY. `PERSON_ID` is stable; affiliation is a function
-- of the game date (`docs/data-sources.md`, "Player identity"). A `team_id` column here would be
-- an as-of-today answer to a question that only has as-of-game-date answers, and it would be the
-- first thing a downstream join reached for. Affiliation lives on `fact_player_game.team_id`,
-- read off the observed box-score row, and gets its interval form in the SCD2 stint model.
--
-- THE NAME HAS THE SAME MULTIPLE-OBSERVATION PROBLEM `dim_team` HAS, and it is easy to miss
-- because it is three rows in thirteen hundred. Measured over the three pilot seasons at full
-- volume: 1,306 distinct `player_id`s but 1,309 distinct `(player_id, player_name)` pairs. Three
-- players are spelled two ways across the span. The arrow is CHRONOLOGICAL -- earlier spelling on
-- the left, later on the right, verified against `min(game_date)` per spelling in bronze:
--
--     1626171   Bobby Portis Jr.  -> Bobby Portis         (suffix REMOVED, not added)
--     202685    Jonas Valanciunas -> Jonas Valanciunas    (diacritics added)
--     1628427   Vlatko Cancar     -> Vlatko Cancar        (diacritics added)
--
-- (The two diacritic pairs are written here without their accents on purpose -- this comment is
-- ASCII so it cannot be the thing that breaks on an encoding round-trip. The accented spellings
-- are the LATER ones, and they are what this model returns.)
--
-- THE PORTIS DIRECTION IS THE ONE WORTH NOTING, because it is the opposite of the obvious guess.
-- Measured: `Bobby Portis Jr.` spans 2019-10-23 to 2020-03-11 and `Bobby Portis` spans 2024-10-23
-- to 2025-04-11, so the source DROPPED the suffix and as-of-latest returns the bare name. Anyone
-- who assumes suffixes only ever get added -- and writes a "prefer the longer spelling" rule on
-- that assumption -- gets this player wrong. There is no lexical rule here; there is only a date.
--
-- So "the name as observed" has no single answer, and `select distinct player_id, player_name`
-- yields 1,309 rows for 1,306 players and fails `unique(player_id)` exactly as the naive
-- `dim_team` would. The rule is the same one `dim_team` uses: AS-OF THE LATEST OBSERVATION. A
-- 2003-04 row therefore renders under a spelling that may postdate the game by twenty years; the
-- spelling as it was observed on any given game stays recoverable from bronze.
--
-- ONE ORDERING, ONE ROW: `row_number()` picks a single real observed row rather than assembling
-- attributes from different games. A CTE rather than `qualify`, matching the bronze models. The
-- `game_id` tiebreak makes the ordering total, so two builds of identical data cannot disagree --
-- and unlike a team, a player CAN appear on two rows of one date (traded mid-season, playing for
-- the new club the same evening is not possible, but nothing in the data structurally forbids two
-- rows sharing a date), so the tiebreak is doing real work here rather than only stating intent.
--
-- COVERAGE IS PLAYERS WHO APPEARED IN A BOX SCORE, WHICH IS NARROWER THAN "PLAYERS". A player
-- under contract for a whole season who never got off the bench is ABSENT ENTIRELY -- not a row
-- with nulls, no row at all -- and so is anyone whose only appearances fall in a season this repo
-- has not landed. The model is named `dim_player` and that name overclaims; the description in
-- `schema.yml` says so in words and `+persist_docs` writes it onto the relation.
--
-- THE SPAN COLUMNS ARE OBSERVATION BOUNDS, NOT CAREER BOUNDS, and the pilot makes the difference
-- extreme rather than subtle. `first_observed_game_date` is the earliest game this corpus has the
-- player playing in, which is a DEBUT only by coincidence; `last_observed_game_date` is likewise
-- not a retirement. The three pilot seasons are 2003-04, 2019-20 and 2024-25, so player 2544 spans
-- 2003-10-29 to 2025-04-11 with two decades of unlanded seasons inside it, and a player who
-- appeared only in 2010-11 is not in this dimension at all. Any "career length" derived from
-- subtracting these two columns is wrong, and wrong by years.
--
-- THE SPAN IS READ FROM `fact_player_game` JOINED TO `dim_game`, NOT FROM BRONZE'S OWN
-- `game_date`. `fact_player_game` is the model that decides what "appeared" means, so the span has
-- to be the span of ITS rows or the coverage sentence above stops being true of these columns; and
-- `dim_game` is silver's single answer for a game's date. THE JOIN IS `left`, DELIBERATELY: the
-- name side is derived from bronze and the span side from the fact, and an `inner` join would
-- silently DROP any player the two disagree about. Left-joining instead turns that disagreement
-- into NULL dates, which the `not_null` tests in `schema.yml` turn into a red build. Measured, the
-- two sides agree on every player in the corpus -- but they agree because it is asserted, not
-- because it is assumed.

with player_rows as (

    select
        player_id,
        player_name,
        game_date,
        game_id
    from {{ ref('bronze__nba_stats__league_game_log_player') }}

),

ranked as (

    select
        player_id,
        player_name,
        row_number() over (
            partition by player_id
            order by game_date desc, game_id desc
        ) as observation_rank
    from player_rows

),

latest_name as (

    select
        player_id,
        player_name
    from ranked
    where observation_rank = 1

),

observed_span as (

    -- The first and last game the player is observed IN A BOX SCORE, dated through `dim_game`.
    -- One row per player by construction, so the join below cannot fan out.
    select
        player_game.player_id,
        min(game.game_date) as first_observed_game_date,
        max(game.game_date) as last_observed_game_date
    from {{ ref('fact_player_game') }} as player_game
    inner join {{ ref('dim_game') }} as game
        on player_game.game_id = game.game_id
    group by player_game.player_id

)

select
    latest_name.player_id,
    latest_name.player_name,
    observed_span.first_observed_game_date,
    observed_span.last_observed_game_date
from latest_name
left join observed_span
    on latest_name.player_id = observed_span.player_id
