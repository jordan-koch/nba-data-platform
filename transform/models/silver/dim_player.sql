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

)

select
    player_id,
    player_name
from ranked
where observation_rank = 1
