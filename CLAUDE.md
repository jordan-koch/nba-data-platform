# NBA Data Platform

An NBA lakehouse — extraction, medallion transformation, and analytics serving. Structured as if
building the backend for an NBA franchise's analytics department: the job is to build the
systems that let analysts answer questions, not to answer them ad hoc.

**Deliberately built past what the data volume requires.** Read
[`docs/decisions/0001-deliberate-over-engineering.md`](docs/decisions/0001-deliberate-over-engineering.md)
before concluding something here is overkill — it probably is, and the ADR says why.

> **Phase 0.** Repo, process, and CI harness exist. **No pipeline code yet.** The first data
> arrives via a feature request.

## Project Map

```
nba-data-platform/
├── README.md          Public-facing overview, architecture, setup — the prose introduction
├── CLAUDE.md          This file — onboarding map + the rules to work by
├── docs/
│   ├── data-sources.md    Endpoint catalog, era availability, rate limits, known gotchas
│   └── decisions/         ADRs — why each choice was made, and what it cost
├── requests/          Work intake — one dir per item; three tracks (see each README)
│   ├── feature-requests/  New capability. EVERY dataset enters here.
│   ├── bugfix-requests/   Something failed
│   └── data-incidents/    Nothing failed and the data is wrong
├── .claude/skills/    The four request stages, plus /update-docs (doc gate) and /commit (the committer)
├── src/nba_platform/  Extraction + landing (transformation lives in transform/)
├── transform/         dbt project — bronze / silver / gold
├── tests/             pytest + committed API fixtures for offline testing
└── var/               GITIGNORED — local landing zone, DuckDB files, caches, checkpoints
```

Directories appear when their phase does. `orchestration/`, `infra/`, and `app/` don't exist
yet — see the roadmap in [`README.md`](README.md).

## Important Locations

- **[docs/decisions/](docs/decisions/)** — start here. Six ADRs cover the scope range, the
  storage substrate, the engine choice, the serving layer, and why the repo is public.
- **[docs/data-sources.md](docs/data-sources.md)** — what's available, from when, and what
  breaks. **Everything in it is currently `unconfirmed`** — no endpoint has been called from
  this repo. Confirming it is the first task of the first feature request.
- **[requests/README.md](requests/README.md)** — the intake contract and the three-track split.
  Each track's README is authoritative for its own layout and status grammar.
- **[transform/models/](transform/models/)** — each medallion layer carries a README stating
  what belongs in it and what doesn't. Read the layer's README before adding a model to it.

## Key Context

- **Scope:** seasons 2003-04 through 2025-26 — anchored to LeBron's rookie year.
- **One availability boundary:** tracking-derived stats begin 2013-14. Before that they are
  *structurally absent*, not missing. Averaging across the boundary produces wrong numbers.
- **One rule change:** hand-checking banned starting 2004-05, so 2003-04 sits alone on the far
  side of a real discontinuity.
- **Three irregular seasons:** 2011-12 (lockout, 66g), 2019-20 (bubble, unequal game counts),
  2020-21 (compressed, 72g). Anything assuming 82 games or an Oct–Apr calendar breaks on all
  three. They are the best test fixtures available.
- **Current environment:** `NBA_ENV=local` — landing zone in `var/`, warehouse in DuckDB. No
  cloud, no cost, no credentials. CI runs the same way.

## Project Conventions

- **Agents commit only through `/commit`.** Never run `git commit` ad hoc — not for a one-line
  change, not for an "obviously safe" one. `/commit` stages per-path (never a blind `git add -A`),
  refuses secrets and bulk data, runs the doc checks proportionally, shows you the staged list, and
  commits only on an explicit yes. **Never merge, push, or amend** — those stay the user's. `main`
  is protected; everything lands by PR with green checks.
- **Every dataset comes from a feature request.** No source gets extracted, no table landed, no
  model written without one. A dataset carries contracts — grain, keys, era coverage, update
  semantics, cost — and those are decisions, not implementation details.
- **Subagents get read-only git.** When spawning any subagent, tell it git is read-only —
  never `checkout`/`reset`/`restore`/`clean`/`stash` or anything that discards working-tree
  state. Bubble a destructive-git *need* back up.
- **Label your epistemics.** *Measured*, *verified*, *inferred*, *assumed*, *unconfirmed* mean
  different things. An unconfirmed claim about an endpoint's shape is a task, not a fact. This
  matters more than usual here because most of this repo is written by agents against docs
  treated as authoritative.
- **Mechanical checks live in CI; judgment lives in `/update-docs`.** Lint, types, tests,
  sqlfluff, `dbt build`, and secret scanning run on every PR. `/update-docs` handles what CI
  can't: whether the prose still describes the repo that now exists.

## Data Layer

- **Resolve by name, never hardcode.** dbt's `ref()` and `source()` are compiler-enforced —
  use them. In Python, resolve paths through the config layer, never by literal string or
  `parents[N]` walks.
- **The landing zone is immutable.** Raw API responses are written once and never mutated.
  This is what makes data-incident triage tractable: if bronze and the landed JSON disagree,
  bronze is wrong, and you can always diff against a fresh pull. It also means history replays
  without re-hitting a rate-limited API.
- **Bronze is 1:1 with the source.** Typing, casing, deduplication. No joins, no business logic,
  no filtering, no semantic renaming. Those happen in silver where they can be documented.
- **Silver declares its grain and proves it.** Every model states its grain in prose in
  `schema.yml` *and* enforces it with a uniqueness test. A grain claimed but not tested is a
  grain that will quietly break.
- **Facts are `MERGE`-on-key, not append-only.** Box scores get restated after the fact,
  sometimes days later. Nightly runs re-pull a trailing window rather than only yesterday.
- **Layer promotion is gated on tests.** A layer that fails its tests must not feed the next one.
- **No bulk data in git.** Code, config, docs, and small fixtures only. The repo is public and
  `.gitignore` blocks the common data formats — if you find yourself wanting to commit a
  `.parquet`, something has gone wrong.

## Constraints & Gotchas

- **`stats.nba.com` blocks impolite clients** — it does not throttle them, and a block is hard
  to distinguish from a transient failure. Default pacing is 0.6s between requests with
  exponential backoff. Read [`docs/data-sources.md`](docs/data-sources.md) before lowering it.
- **Prefer bulk endpoints.** The `leaguegamelog` family is believed to return a full season per
  call; the per-game `boxscore*` family needs one call per game. For a 23-season backfill that's
  the difference between ~50 calls and ~60,000. `unconfirmed` — verify before building on it.
- **Player *affiliation* is date-dependent, not player identity.** `PERSON_ID` is stable. But
  trades, ten-day contracts, two-way players, and buyouts mean a player's team is a function of
  the game date. Resolving as-of *today* instead of as-of the *game* is the most likely source of
  silently wrong joins in this project.
- **Cost is a guardrail.** A cluster left running over a weekend is this repo's version of
  silently destroyed work. Auto-suspend everything; keep billing alarms on. Anything that spends
  cloud money or touches prod is a user-run action, not an agent one.
- **`pre-commit` means the Python hook framework here**, not a skill. The doc-coherence skill is
  **`/update-docs`**, deliberately named to avoid the collision.
- **Windows dev, Linux CI.** `.gitattributes` normalizes to LF. Don't defeat it.

## How to Help

- **Reach for the pipeline, sized to the work.** A new capability starts at
  `/make-feature-request`. Something that failed starts at `/make-bugfix-request`. Wrong data
  from a green run is a data incident. Skip stages when the work is small; run the full panel
  when the decision is expensive to reverse.
- **The dimensional model is the expensive decision.** SCD2 player affiliation, grain for traded
  players, era-nullable columns. That one earns the full scoping panel. Most things don't.
- **Vertical slices, not horizontal layers.** Every phase goes source → landing → lakehouse →
  model → published before the next one widens. A platform with impressive infrastructure and no
  basketball insight in it has failed at both of this project's goals.
- **Check `docs/data-sources.md` before assuming anything about an endpoint.** It is a catalog of
  beliefs, not facts, and it says so.
