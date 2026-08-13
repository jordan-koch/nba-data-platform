# 0005 — Serve gold marts to the browser via DuckDB-WASM

**Status:** accepted · 2026-08-12

## Context

Reports need a home that can be pointed at — a URL, not a desktop BI file. Power BI and Tableau
would work and are already familiar, but the goal includes practicing an unfamiliar serving
layer, and there's a real observation behind it: business users respond well to purpose-built
web pages, and the cost of producing one has collapsed.

The conventional design is React → API → warehouse. That puts a backend, a warehouse, and
network latency between the user and a gold layer that is, in aggregated form, a few tens of
megabytes.

## Decision

**Publish gold marts as Parquet to a CDN and query them client-side with DuckDB-WASM.**

DuckDB compiled to WebAssembly runs in the browser tab. Pointed at a Parquet file over HTTP, it
uses range requests to fetch only the columns and row groups a query touches.

## Consequences

**Buys:**

- **No backend.** Nothing to write, deploy, secure, or pay for on the read path.
- **No warehouse cost on reads.** Snowflake spins up for the nightly build only.
- **Genuinely interactive.** Cross-filtering and drill-downs run locally in milliseconds — the
  thing enterprise BI tools are usually worst at.
- Static hosting, so the serving layer is nearly free and trivially scalable.
- Reporting becomes version-controlled software: reviewed, CI/CD'd, diffable. That's the durable
  industry trend (Evidence, Rill, Lightdash), and it predates the AI tooling that accelerated it.

**Costs:**

- **A hand-built front end is exactly as flexible as it was built to be.** Ad-hoc exploration
  along an unanticipated dimension is not possible — that's where Power BI genuinely wins.
- **No governed semantic layer for free.** Metric definitions live in dbt and must stay
  disciplined, or the front end will quietly redefine them.
- **No row-level security.** Everything published is public. Fine here; disqualifying in an
  enterprise setting.
- **Play-by-play doesn't fit.** At ~18M rows it's 500MB+, past comfortable browser range. That
  layer stays server-side or gets pre-aggregated — which is what a gold layer is for, but it is a
  real constraint on what can be published.
- Front-end work is a genuinely new skill and will be slower than the familiar path.

## Alternatives considered

**Power BI against Snowflake.** Already known, fully featured, governed. Rejected because it
practices nothing new and cannot be pointed at publicly without licensing friction.

**React → FastAPI → Snowflake.** The conventional shape. Rejected as strictly worse here: it adds
a service to run and a warehouse to keep warm, in exchange for flexibility this dataset's size
makes unnecessary.

**Evidence.dev.** SQL-in-markdown compiling to a static BI site — much faster to a working
dashboard and shares the BI-as-code philosophy. Genuinely close. Kept as a fallback and worth a
weekend trial; rejected as primary because the front-end reps are part of the point.
