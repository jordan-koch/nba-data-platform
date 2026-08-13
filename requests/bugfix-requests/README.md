# Bugfix Requests

Defects in existing code, config, or tooling — an extractor that crashes, a broken path
resolution, a CI workflow that passes when it shouldn't, a skill that misfires.

> **Not for wrong numbers.** If the code ran clean and the *data* is wrong, that's
> [`../data-incidents/`](../data-incidents/) — different triage, different artifacts, and it
> owes a restatement plan this track doesn't. Tie-break: **did anything fail?** If the pipeline
> went green and the output is still wrong, it's an incident.

## The pipeline

| # | Stage | Skill | Produces |
|---|---|---|---|
| 1 | **Intake** | `/make-bugfix-request` | `BUGFIX_REQUEST.md` — symptom, reproduction, blast radius |
| 2 | **Diagnose** | `/diagnose-bug` | `ROOT_CAUSE_ANALYSIS.md` — a refute-the-diagnosis panel, not a confirm-it one |
| 3–4 | **Plan + Implement** | `/create-implementation-plan` → `/implement-plan` | Shared with the feature track |

Stages 3–4 are the feature track's back half, reused. They auto-detect the track from the
artifact's path.

## Definition of done

**A red reproduction goes green, and a regression test is left behind.**

Both halves are required. A fix without a test is an invitation to fix it again — and in a repo
where agents do most of the writing, the test is the only thing that remembers.

The reproduction is written *first*, at diagnosis time, and it must **fail** before the fix
lands. A repro that passes against the broken code is not a repro; it means the diagnosis is
wrong. That red-to-green transition is the evidence, and `/implement-plan` will ask for it.

Where the test lives depends on what broke:

| Broke | Test goes |
|---|---|
| Python — extraction, landing, lib | `tests/` (pytest, against committed fixtures) |
| A dbt model's logic | `transform/tests/` (singular test) or a schema test on the model |
| A source contract assumption | A schema test on the source, so the *next* upstream change fails loudly |
| CI or workflow config | A workflow assertion, or a fixture that would have caught it |

## Layout

```
bugfix-requests/
  <slug>/
    BUGFIX_REQUEST.md          # stage 1
    ROOT_CAUSE_ANALYSIS.md     # stage 2
    IMPLEMENTATION_PLAN.md     # stage 3 (skipped when the fix is obvious)
    IMPLEMENTATION_REPORT.md   # stage 4
    reviews/                   # panel working files
  _done/<slug>/                # archived at terminal stage
```

**Status grammar:** `intake` → `diagnosed` → `planned` → `fixed`

Same active-vs-done convention as the feature track: one move into `_done/` at the terminal
stage, Index row stays with its link updated.

## Index

| Bug | Stage | Notes |
|---|---|---|
| _(none yet)_ | | |
