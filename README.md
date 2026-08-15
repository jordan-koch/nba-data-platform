# NBA Data Platform

A lakehouse for NBA data — extraction, medallion transformation, and analytics serving, built
the way a professional data team would build it.

**The framing:** this project is structured as if I were the data architect for an NBA
franchise. The job is to build the systems that let analysts keep the team competitive. I don't
have the data access a team would — no optical tracking, no wearables, no medical — but the
backend can be modeled faithfully, and the public data is richer than most people assume.

> **Status: Phase 0 — scaffolding.** The repo, process, and CI harness are in place. No
> pipeline code yet. The first data lands via
> [`requests/feature-requests/`](requests/feature-requests/), which is the only route by which
> any dataset enters this project.

---

## Architecture

```
nba_api  ─▶  landing zone  ─▶  Iceberg on S3  ─▶  Snowflake  ─▶  Parquet on CDN  ─▶  browser
 extract      immutable raw      bronze/silver/gold    dbt          gold marts       DuckDB-WASM
              JSON, partitioned                                                       React
                        └──────────── Airflow orchestrates ────────────┘
```

| Stage | Choice | Why |
|---|---|---|
| **Extract** | Python + `nba_api` | Rate-limited, undocumented upstream. Polite pacing, checkpointing, and resumability are the real engineering here. |
| **Land** | Immutable raw JSON, partitioned | Never mutated. Lets any incident be diagnosed by diffing against a fresh pull, and lets history be replayed without re-hitting the API. |
| **Store** | Apache Iceberg on S3 | Open table format decouples storage from compute — Snowflake, Spark, DuckDB, and Trino all read the same files. Engine choice stays reversible. |
| **Transform** | dbt, medallion (bronze → silver → gold) | Version-controlled models, tested contracts, lineage. Layer promotion is gated on tests passing. |
| **Orchestrate** | Airflow | Partitioned DAG runs keyed to game date, with real backfill semantics. |
| **Serve** | Parquet on CDN + DuckDB-WASM | Gold marts are small enough to query *in the browser*. No API, no warehouse cost on reads, sub-100ms interactions. |

Every one of these decisions is written up in [`docs/decisions/`](docs/decisions/), including
the ones where the honest answer is "this is more than the data currently requires, and here's
why that's deliberate."

## Scope

**Seasons 2003-04 through 2025-26** — anchored to LeBron James's rookie year so his full career
sits inside the dataset.

That range contains exactly one data-availability boundary (tracking-derived stats begin
2013-14), one major rule change (hand-checking banned in 2004-05, so the first season sits alone
on the far side of a real discontinuity), and three structurally irregular seasons:

| Season | Irregularity |
|---|---|
| 2011-12 | Lockout — 66 games |
| 2019-20 | Suspended in March, resumed in a bubble, unequal game counts |
| 2020-21 | Compressed calendar — 72 games |

Anything that assumes "82 games" or "October through April" breaks on all three. They make
excellent test cases.

## Data provenance

All data comes from public NBA sources via [`nba_api`](https://github.com/swar/nba_api), an
unofficial Python client for `stats.nba.com`.

**This repository redistributes no NBA data.** It contains code, configuration, documentation,
and a small set of API-response fixtures used for offline testing. The landing zone and
warehouse are not tracked in git — see [`.gitignore`](.gitignore).

Not affiliated with or endorsed by the NBA.

## Repo layout

```
├── docs/               Architecture, data-source catalog, and ADRs
│   └── decisions/        Why each choice was made — read these first
├── requests/           Work intake — features, bugfixes, data incidents
├── .claude/            Agent definitions and request-pipeline skills
│   ├── agents/           Write-capable implementation subagents (see below)
│   └── skills/           The request stages, plus /update-docs and /commit
├── src/nba_platform/   Extraction and landing (transformation lives in transform/)
├── transform/          dbt project — bronze / silver / gold
├── ops/                Repo governance as code — branch protection, applied via gh
├── tests/              pytest + committed API fixtures for offline testing
└── var/                Gitignored — local landing zone, DuckDB files, caches
```

## Implementation agents

[`.claude/agents/`](.claude/agents/) holds write-capable implementation subagents. One
Markdown file defines one agent, and the harness registers each frontmatter-bearing `.md`
there as a spawnable type. There is one today — `data-engineer` — alongside the memory file
it appends to and humans curate.

The split is manager and developer. The main thread keeps the strategy: scoping rationale,
the roadmap, whether a piece of work is still the right shape. The agent keeps a build
rulebook, implements one spec against it, and returns a fixed-format handoff into that
request's `reviews/` directory — so the main thread reviews a summary instead of every edit.

Spawning one has preconditions: a feature branch, a clean working tree, a fresh session, and
a snapshot of the tree taken before and compared afterward. That last part is load-bearing.
This harness has no path-level permission system, so an agent's write allowlist is prose
rather than a sandbox, and the checks around it detect a bad write rather than prevent one.
The full protocol is in [`.claude/agents/README.md`](.claude/agents/README.md).

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/jordan-koch/nba-data-platform.git
cd nba-data-platform
uv sync                      # creates .venv and installs dev + transform groups
cp .env.example .env         # defaults to NBA_ENV=local — no cloud, no cost
```

Verify:

```bash
uv run pytest
uv run ruff check
cd transform && uv run dbt build --target local
```

`NBA_ENV=local` runs the whole stack on disk — landing zone in `var/`, warehouse in DuckDB. No
AWS or Snowflake credentials needed to develop or to run CI.

## Roadmap

| Phase | Scope | Status |
|---|---|---|
| **0** | Repo, process, CI harness | ✅ |
| **1** | Box-score foundation — dimensional core, local end to end | Next |
| **2** | S3 + Iceberg; Snowflake | |
| **3** | Airflow, with 2025-26 replayed as synthetic nightly increments | |
| **4** | Gold marts published; React + DuckDB-WASM front end | |
| **5** | Play-by-play and shot detail — the diagnostic layer | |

## License

MIT — see [LICENSE](LICENSE).
