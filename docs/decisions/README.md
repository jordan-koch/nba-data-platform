# Architecture Decision Records

Why each choice was made, written down at the time it was made.

These exist because **this project is deliberately built past what its current data volume
requires**, and that only reads as competence if the reasoning is visible. An unexplained
lakehouse over a million rows looks like poor judgment. The same lakehouse with a document
saying *"at this volume a single Parquet directory would do; here is what the extra complexity
buys and what it costs"* reads as an architect making a call.

## Format

One file per decision, numbered and immutable once accepted:

```
NNNN-short-slug.md
```

Each carries:

- **Status** — proposed / accepted / superseded by NNNN
- **Context** — what forced a decision; the constraints in play at the time
- **Decision** — what was chosen, stated plainly
- **Consequences** — what this buys, what it costs, and what it forecloses
- **Alternatives considered** — and why they lost

## Rules

**Don't edit an accepted ADR to reflect a change of mind.** Write a new one that supersedes it,
and update the old one's status line to point at it. The value here is the record of what was
believed *at the time* — rewriting it destroys exactly what makes it useful in an interview or a
post-mortem.

**Record the cost honestly.** An ADR that lists only benefits is marketing. The consequences
section should be uncomfortable to write.

## Index

| # | Decision | Status |
|---|---|---|
| [0001](0001-deliberate-over-engineering.md) | Build past current need, and document the delta | accepted |
| [0002](0002-season-range-2003-forward.md) | Cover 2003-04 through present | accepted |
| [0003](0003-iceberg-as-storage-substrate.md) | Apache Iceberg on S3 as the storage substrate | accepted |
| [0004](0004-snowflake-first-databricks-later.md) | Snowflake first; Databricks as a later phase | accepted |
| [0005](0005-browser-side-serving.md) | Serve gold marts to the browser via DuckDB-WASM | accepted |
| [0006](0006-public-repository.md) | Public repository from the first commit | accepted |
| [0007](0007-write-capable-implementation-subagent.md) | A write-capable implementation subagent | accepted |
| [0008](0008-landing-layout-and-capture-manifest.md) | Landing layout, capture manifest, latest-capture-wins | accepted |
