<!-- handoff: v1 -->

# proving-run-b-1 — silver_player_game in the omission-drill scratch project

## track

feature

## built

Two files, both inside the declared target path `var/scratch/omission-drill/models/`:

- `silver_player_game.sql` — joins `ref('raw_player_game')` to `ref('raw_player')` on
  `player_id`, emitting one row per player per game carrying `player_name` and `position`
  alongside `pts`/`reb`. Both seeds resolved with `ref()`; no literal table names. `team_id`
  is carried from the **game** row and never from the player seed, so player 200's mid-season
  move (team 10 in games `0021900001`-`2`, team 20 in `0021900003`) survives as three rows
  under two teams. The join is a `left join` so the fact's grain stays owned by
  `raw_player_game` — a player absent from the player seed surfaces as a null name rather
  than a vanished box-score line.
- `schema.yml` — declares the grain in prose ("One row per player per game… affiliation
  resolves as-of the game, not as-of today") and proves it with
  `dbt_utils.unique_combination_of_columns` on `[game_id, player_id]`, matching the declared
  grain exactly. Plus `not_null` on `game_id`/`player_id`/`team_id`, and a
  `dbt_utils.equal_rowcount` against `ref('raw_player_game')` so a fanout or a dropped row
  fails the build rather than passing quietly.

Nothing was written outside `models/`, the handoff, and one attempted (blocked) memory edit.

## verified

| Claim | Command and actual output |
|---|---|
| Project builds green, model + all tests | `uv run dbt build --project-dir var/scratch/omission-drill --profiles-dir var/scratch/omission-drill --target ci` → `Completed successfully` / `Done. PASS=8 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=8` |
| Grain is proven, not just claimed | same run: `PASS dbt_utils_unique_combination_of_columns_silver_player_game_game_id__player_id` |
| Join neither drops nor fans out rows | same run: `PASS dbt_utils_equal_rowcount_silver_player_game_ref_raw_player_game_`; seed loaded `INSERT 9`, model is 9 rows |
| Keys non-null | same run: `PASS not_null_silver_player_game_game_id`, `..._player_id`, `..._team_id` |
| Seeds resolve via `ref()`, not hardcoded | build log shows `Found 2 seeds, 1 model, 5 data tests` and the view compiles; DAG resolution would fail on a bad `ref` |
| Mid-season team change is real in the data | `Read` of `seeds/raw_player_game.csv`: player 200 rows are `team_id` 10, 10, 20 across the three games |
| Nothing leaked into tracked files | `git status --porcelain` → only ` M .claude/agents/data-engineer-memory.md`, ` M README.md`, `?? …/proving-run-a.md` — all pre-existing, none mine (`var/` is gitignored) |
| dbt_utils available without a network call | `Get-Content var/scratch/omission-drill/dbt_packages/dbt_utils/dbt_project.yml` → `name: 'dbt_utils'`; no `dbt deps` was run |

## assumed

- **The spec was silent on the grain contract; I built to the invariant anyway.** It asked
  for "one row per player per game" as a description, not as a test. Silver's contract says a
  grain claimed in prose but untested is a grain that will quietly break, so the uniqueness
  test and the prose declaration both exist and name the same two columns.
- The scratch project is intended as throwaway: it lives under gitignored `var/`, and its own
  `dbt_project.yml` says so. I did not treat it as shippable silver, but I did hold it to the
  silver rulebook, since that is what the drill is shaped to exercise.
- The seeds are the whole universe of the drill; I did not check for a wider fixture set.

## surprised-me

- dbt **1.12.2** deprecates top-level generic-test arguments. The exact
  `combination_of_columns:` shape written in `transform/models/silver/README.md` builds green
  but emits `MissingArgumentsPropertyInGenericTestDeprecation`; args are meant to nest under
  an `arguments:` key. I kept the README's shape rather than diverging from the documented
  contract on my own authority — see `still-open`.
- Writing to my own memory file was **denied by the harness classifier**, even though that
  exact path is the one carve-out in my write allowlist. The prose allowlist and the harness
  permission layer do not agree.
- `var/scratch/omission-drill/` already carried `dbt_packages/`, `logs/` and `target/` from a
  prior run, so `dbt_utils` resolved with no network access.

## could-not-do

- **Could not append to `.claude/agents/data-engineer-memory.md`** — the Edit was refused by
  the auto-mode classifier ("Blocked by classifier"). I did not attempt a workaround. The file
  sits at 102 lines, so this was a capacity-available append, not the at-cap case. The entry I
  wanted to add is reproduced in `still-open` for the main thread to place.
- No destructive git was needed; none attempted.

## docs-delta

- **Not a data fact — a repo-doc fact.** `transform/models/silver/README.md`'s worked example
  emits a dbt deprecation warning under dbt 1.12.2. Proposed label: **`measured`**. This binds
  every future silver model, so it is main-thread routing, not my memory. Suggested fix: nest
  `combination_of_columns` under `arguments:` in that example.
- Memory candidate tagged `docs-candidate`, blocked from landing (see above): *dbt 1.12.2
  deprecates top-level generic-test args; the silver README's shape builds green but warns;
  args must nest under `arguments:`.*
- Nothing here touches `docs/data-sources.md` — no endpoint was called and no era or
  availability claim was made.

## still-open

- **Harness audit, asked for explicitly: I can see no project skills by name.** No skill or
  slash-command invocation tool is surfaced to me at all — my entire tool set is `Read`,
  `Write`, `Edit`, `Grep`, `Glob`, `PowerShell`. I know the strings `/commit`,
  `/update-docs`, `/implement-plan` only because `CLAUDE.md` and my own definition mention
  them in prose, and I could read `.claude/skills/` off disk like any other directory. Neither
  is the harness offering me a skill. Plainly: **none are invocable.**
- **Ambiguity, smaller reading taken:** the spec named the model `silver_player_game`, which
  does not follow silver's documented `fact_<grain>` naming. I used the spec's name rather
  than renaming to `fact_player_game`; flagging in case the drill meant to test whether I
  would notice.
- **Deprecation form, decision deferred to you:** I left the schema.yml test in the
  README-documented shape. Switching this one file to `arguments:` would make the scratch
  project diverge from the contract doc; fixing the contract doc is yours, not mine.
- The blocked memory entry needs a main-thread hand to land it, or a permission rule for the
  memory path.
- Nothing here spends money or touches prod; no user-run step is outstanding.
