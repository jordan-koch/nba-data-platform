# Data Incidents

For when **the pipeline ran green and the data is wrong.**

Nothing crashed. No test failed, or a test failed that only exists because someone already
suspected this. The extractor returned 200s, dbt built every model, the dashboard refreshed —
and the numbers are not right.

> **Status: convention established, tooling deferred.** The track and its contract exist so the
> shape is settled before the first incident rather than designed under pressure. The
> `/report-data-incident` and `/diagnose-data-incident` skills arrive once there is data to have
> incidents about — building them now would be building on spec. Until then, run the stages by
> hand against the artifact templates below.

## Why this isn't the bugfix track

A code defect announces itself. A data defect is **silent, retroactive, and already
downstream.** Three consequences shape the whole process:

**Impact assessment outranks root cause.** Before you know *why*, you need to know *how bad* —
which models consumed the bad rows, how long it has been wrong, whether it reached anything
published. A code bug affects whoever runs the code next. A data bug has already affected
everyone who read the table.

**Root cause has a taxonomy, and the layers look identical from the symptom.** The same wrong
number can come from any of four places, and you cannot tell which from the output alone:

| Layer | What went wrong | Tell |
|---|---|---|
| **Source** | Upstream changed shape, semantics, or history | The raw landed payload differs from the same call last week |
| **Extraction** | Dropped, duplicated, or mis-paginated rows | Raw row count ≠ what the API reports as available |
| **Model** | Wrong join, wrong grain, fanned-out rows | Bronze is right; silver or gold is not |
| **Infrastructure** | Partial load, out-of-order run, stale cache | The data is right, just not all of it, or not the right vintage |

Because the raw landing zone is **immutable**, you can always answer the first question by
diffing what you have against a fresh pull. That's the whole reason it's immutable.

**Fixing forward is half the work.** Bad rows are already in the warehouse and may already be
published. Every incident owes a **restatement plan** — which partitions to rebuild, in what
order, and how to verify the corrected numbers — alongside the code fix. This obligation has no
equivalent in the bugfix track.

## The pipeline

| # | Stage | Produces | The question |
|---|---|---|---|
| 1 | **Report** | `INCIDENT.md` | What looks wrong, how it was noticed, when it started |
| 2 | **Assess** | Impact section of `INCIDENT.md` | Blast radius. Which models, how far downstream, was it published, how long |
| 3 | **Diagnose** | `ROOT_CAUSE_ANALYSIS.md` | Which of the four layers, proven by evidence — not inferred from plausibility |
| 4 | **Resolve** | `RESOLUTION.md` | Forward fix + restatement + the test that makes recurrence loud |

Stage 4 hands to `/create-implementation-plan` → `/implement-plan` when the fix is nontrivial.

## Definition of done

Three things, all required:

1. **The defect is fixed forward** — new runs produce correct data.
2. **Existing bad data is restated** — or explicitly, deliberately accepted as-is, with the
   reasoning written down and the affected range documented.
3. **A data-quality test exists that would have caught it**, and it is wired into the layer
   promotion gate — so a recurrence fails the build instead of reaching gold.

Point 3 is the one that compounds. Every incident should permanently retire its own failure
mode, and the test suite becomes a ledger of everything that has ever gone wrong.

## Layout

```
data-incidents/
  <YYYY-MM-DD>-<slug>/         # date-prefixed — incidents are events, order matters
    INCIDENT.md                # report + impact assessment
    ROOT_CAUSE_ANALYSIS.md     # which layer, with evidence
    RESOLUTION.md              # forward fix + restatement + the new test
    evidence/                  # queries, row counts, raw-payload diffs
  _done/<YYYY-MM-DD>-<slug>/
```

**Status grammar:** `reported` → `assessed` → `root-caused` → `resolved`

Incidents are date-prefixed rather than plain slugs because they are events on a timeline, and
the same failure mode recurring twice is itself a finding.

## Index

| Incident | Status | Layer | Notes |
|---|---|---|---|
| _(none yet)_ | | | |
