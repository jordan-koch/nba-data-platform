<!-- handoff: v1 -->

# Phase 1 handoff — the resolve-by-name config layer

## track

`feature` — box-score-foundation, Phase 1 (config layer only).

## built

`src/nba_platform/config.py`, the whole and only deliverable. Nothing else was written;
`src/nba_platform/__init__.py`, `pyproject.toml` and `uv.lock` are untouched (the last two were
already modified in the working tree when I started — that is the main thread's Phase 1 half).

It exposes a frozen `Settings` dataclass (`env`, `repo_root`, `landing_root`, `warehouse_path`,
`pilot_seasons`, `request_delay_seconds`, `max_retries`) built by `Settings.from_env()` /
`get_settings()`, plus `landing_key(...)` and a `ConfigError`. Resolution is eager, uncached and
re-reads the environment on every call, so a monkeypatched key takes effect immediately and no
test inherits a neighbour's resolution. `from_env()` also accepts an explicit mapping, so it can
be tested without touching global state if you prefer that to `monkeypatch.setenv`.

Repo root is found by **walking up from `__file__` to the directory holding `pyproject.toml`**,
stopping at the filesystem root rather than spinning — that choice is named in the module
docstring as step 5 requires. No `parents` subscript anywhere. `NBA_REPO_ROOT` overrides the walk.

Seven keys, every one read by name: the three from `.env.example` (`NBA_ENV`,
`NBA_REQUEST_DELAY_SECONDS`, `NBA_MAX_RETRIES`) plus `NBA_LANDING_ROOT`, `NBA_WAREHOUSE_PATH`,
`NBA_PILOT_SEASONS`, `NBA_REPO_ROOT`. Relative overrides anchor at the repo root, not the process
working directory, so a run from `transform/` lands where one from the top does.

`landing_key` renders exactly the shape the plan specifies, lowercases every component, rejects
`/ \ = :` and empties inside one, and refuses a naive `captured_at`. The capture stamp is compact
UTC via `%Y%m%dT%H%M%SZ` — colon-free by construction, not by convention.

## verified

| Claim | Command | Actual output |
|---|---|---|
| Lint clean | `uv run ruff check` | `All checks passed!` · exit 0 |
| Format clean | `uv run ruff format --check` | `53 files already formatted` · exit 0 |
| Types clean under `strict` | `uv run mypy` | `Success: no issues found in 6 source files` · exit 0 |
| CI pytest line (AC 1, byte-identical to `ci.yml:53`); AC 21 guards inside it | `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing` | `40 passed in 0.63s` · exit 0 · `config.py 135 stmts, 0%` (expected — `tests/test_config.py` does not exist yet) |
| Purity guard (AC 18) would pass | `uv run python -c` walking `src/nba_platform/**/*.py` and counting substrings | `__init__.py parents[ = 0 \| var/ = 0`; `config.py parents[ = 0 \| var/ = 1 \| os.path = 0`; `PURITY OK` · exit 0 |
| (a) landing root resolves from `NBA_ENV` through the config layer | scratchpad script, `os.environ["NBA_ENV"]="local"`, then `get_settings()` | `landing_root = D:\Projects\nba-analysis\var\landing` · PASS |
| `warehouse_path` agrees with `transform/profiles.yml:17` | same script | `D:\Projects\nba-analysis\var\warehouse\nba_local.duckdb` · PASS |
| (b) an overriding env var wins | same script, `NBA_LANDING_ROOT`/delay/retries/seasons set | all four overrides PASS; relative override anchored at repo root; absolute override kept verbatim |
| (c) `landing_key` colon-free, `key=value/` shape, trailing `/` | same script | `nba_stats/league_game_log/season=2003-04/grain=player/season_type=regular/capture=20260815T143005Z/` · no `:` · 6 segments, 4 hive pairs · PASS |
| Naive `captured_at`, and `: / \ =` or empty inside a component, all raise | same script | 4 of 4 raise `ConfigError` · PASS |
| Bad env values fail loudly by name | same script | unknown `NBA_ENV`, non-numeric delay, zero delay, negative retries, `2003-2004` season, and cloud env with no landing override each raise `ConfigError` · 6 of 6 PASS |
| Settings is genuinely frozen | same script | `FrozenInstanceError` on attribute assignment · PASS |
| Nothing outside the target path was written | `git status --short` | ` M pyproject.toml`, ` M uv.lock` (both pre-existing, not mine), `?? src/nba_platform/config.py` |

The script ran 32 checks, all PASS, exit 0. It lives in the session scratchpad, outside the repo,
because `tests/` is denied to me — it is evidence, not a deliverable.

## assumed

- **Three of the seven env-var names are mine.** `NBA_LANDING_ROOT` is evidenced — Phase 4's
  `[CORRECTED — binding]` clause already spells it, so bronze and config now agree.
  `NBA_PILOT_SEASONS` comes from `plan-adversarial.md`'s GAP-04. `NBA_WAREHOUSE_PATH` and
  `NBA_REPO_ROOT` I named. If `tests/test_config.py` wants other spellings, say so — they are
  constants at the top of the module.
- Blank-but-exported (`NBA_ENV=""`) is treated as unset, not as an empty path. `grain` is not
  constrained to `{player, team}` — that belongs to the landing writer, not the key renderer.
- Rulebook invariants the spec did not restate but that bind (escalation case 2): resolve by
  name throughout, `pathlib` only, tz-aware timestamps only, no `parents` subscript.

## surprised-me

Memory candidates, all implementation ergonomics rather than data facts:

- **`Path.resolve()` returns the filesystem's casing on Windows.** The repo lives at
  `D:\projects\nba-analysis` but `resolve()` reports `D:\Projects\nba-analysis`. A test comparing
  `str(settings.landing_root)` to a hand-built string fails on Windows and passes on Linux CI.
  Compare `Path` objects, or compare against `settings.repo_root / ...`.
- **`ruff format` enforces `line-length` even though `E501` is in the lint `ignore` list.** A long
  `raise ConfigError(f"...")` was reformatted; ignoring E501 buys nothing from the formatter.
- **The purity guard is a raw substring check, so prose burns the carve-out too.** A comment I
  wrote citing `transform/profiles.yml`'s literal local-target path spent the single permitted
  `var/` before any code did. Cite that path by file and line, never by quoting it.

## could-not-do

- **`.env.example` is not in my target paths**, so the four override keys I added are undocumented
  there. That file is a one-line-each edit and is main-thread this dispatch. Listed in
  `still-open` with the exact lines.
- **`tests/test_config.py`** is repo-root `tests/` — denied. I built to the guard as specified and
  proved it with the scan above, but I did not author it.
- Did not run `uv lock`, `uv sync`, `dbt deps`, or anything touching `stats.nba.com` (per R-C and
  the tool allowlist). No destructive git needed; none run. No `.sql` exists yet, so
  `sqlfluff lint` (authorized by R-B) had nothing to lint.

## docs-delta

**none.** No endpoint-shape, era-boundary, rate-limit or column fact came out of this dispatch —
nothing here changes an analyst's answer, so nothing routes to `docs/data-sources.md`. The 0.6s
default is already recorded there; I only made it resolvable by name.

## still-open

1. **Ambiguity I resolved by under-building (escalation case 3).** The spec's grounding says
   "every segment is a Hive-style `key=value` pair", but the verbatim plan literal leads with two
   bare segments (`nba_stats/league_game_log/`). **I built the literal**, because
   `hive_partitioning` ignores leading non-`key=value` segments and "do not invent extra segments"
   is the stronger instruction. The reading I did *not* take:
   `source=nba_stats/endpoint=league_game_log/`. If Phase 4's glob wants it, it is two lines here.
2. **Non-`local` environments raise rather than guess.** With `NBA_ENV=dev|prod` and no
   `NBA_LANDING_ROOT` / `NBA_WAREHOUSE_PATH`, `from_env()` raises `ConfigError` naming the key to
   set. That is the smaller interpretation — S3/Snowflake plumbing is a declared Phase 2 non-goal.
   `tests/test_config.py` should assert the raise, not a path, if it exercises `dev`.
3. **I did not clamp `request_delay_seconds` to the 0.6s floor**, only rejected `<= 0`. A clamp
   would redden Phase 2's `tests/test_client_pacing.py` if it sets a small delay against a stubbed
   clock. The floor is stated in a comment beside `DEFAULT_REQUEST_DELAY_SECONDS`. If you would
   rather enforce it, decide it now — Phase 2's client is where it becomes load-bearing.
4. **Main-thread edit suggested for `.env.example`**, under the Extraction block: `NBA_LANDING_ROOT`,
   `NBA_WAREHOUSE_PATH`, `NBA_PILOT_SEASONS=2003-04,2019-20,2024-25`, `NBA_REPO_ROOT`. Commented
   out is fine — the point is discoverability, since all four are defaulted.
5. **Line-number drift in the spec's citations.** `DTZ`/`PTH` are at `pyproject.toml:60-61` now,
   not `:58-59`; mypy `strict` is at `:72-76`, not `:70-74`. The main thread's own dependency edit
   shifted them. Harmless here, but later phases quote these numbers.
