# 0007 — A write-capable implementation subagent

## Status

accepted

## Context

Every subagent in this repo before now was read-only, and that was a scar, not a style
choice. The rule is recorded in `.claude/skills/implement-plan/SKILL.md`: *a write-capable
review agent once ran `git checkout` and silently wiped uncommitted work while a vacuous
selftest passed green.* Stage 4 snapshots the working tree to gitignored scratch before
spawning anything and re-checks integrity afterward, precisely because instructions are not
enforcement.

Two problems pushed against that rule.

**Implementation detail and strategic judgment compete for one context window, and detail
wins.** `/implement-plan` has the main thread write all the code; its subagents review
rather than build. By the time a feature ships, one context holds the scoping rationale, the
plan, every file edit, the test output and the panel's findings. The capacity to ask "is
this still the right shape?" degrades exactly when the work is large enough for the question
to matter.

**Knowledge earned during implementation has no durable home.** `CLAUDE.md`'s Constraints &
Gotchas is budgeted and read on every task by every agent. `docs/data-sources.md` holds
labelled beliefs about the *data*. The ADRs hold decisions. None of them fits *"`nba_api`
returns a DataFrame rather than JSON, and its column casing differs from the docs"* —
worthless to an analyst, expensive to rediscover, certain to be rediscovered.

**The honest weakness, recorded because ADR 0001 demands it.** The problem has not happened
yet. When this was decided, `src/nba_platform/` held one `__init__.py`, `transform/models/`
held three READMEs and zero `.sql`, and `/implement-plan` had never run here. The
context-exhaustion claim is **inferred from reading the skill, not measured from a run**.
ADR 0001 names over-processing as the specific failure mode of this repo's philosophy, and
this decision was taken knowing that.

## Decision

Stand up `.claude/agents/` holding one write-capable implementation agent, `data-engineer`,
and **move the granular build rulebook out of `CLAUDE.md` into that definition** so the rules
have a single owner rather than two copies that drift. `CLAUDE.md` keeps a pointer that names
what moved by *topic* rather than restating the rules.

Replace "it cannot write" with a deliberate substitute guard rather than an assumed one:

- **git read-only, absolute**, naming the destructive verbs literally, with the scar attached
  as its reason. Editing a tracked file is explicitly *not* a git operation.
- **A declared write allowlist and a repo-level deny set** — `tests/`, `.github/`, `ops/`,
  `.claude/` (with the memory file as the single exact-path carve-out), plus `CLAUDE.md`,
  `docs/data-sources.md` and `docs/decisions/`. An agent that can edit the guards that catch
  it and then report green is the restaging of the original scar.
- **A required-clean-tree precondition**, a pre-spawn snapshot, and a post-run tree-integrity
  comparison recorded in committed `reviews/`.
- **A fixed-section handoff written to a file**, length-capped and linted by pytest for
  section presence and hunk-freeness — not a final message, and not a StructuredOutput schema.
- **A routing rule**: data facts never enter agent memory; they are queued in the handoff's
  `docs-delta` section for the main thread to route through `/update-docs`.
- **Guards under `tests/`**, not as `.mjs` siblings, because CI has three jobs and no Node
  step — so `tests/` is a required status check and a `.mjs` guard is etiquette.

## Consequences

**The substitute guard is detection, not prevention. This is measured, not merely feared.**
The harness has no path-level permission system: frontmatter `tools:` gates which *tools* an
agent holds, but nothing gates which *paths* they touch. The write allowlist is prose. The
feature branch, the clean-tree precondition, the snapshot, the post-run comparison and
`/commit`'s staged-list-then-yes all catch a bad write **after** it happens. Nothing stops
one.

**It does not fail safe in the other direction either.** A harness permission layer sits
underneath the tool grant and can *deny* a write the definition explicitly allows,
non-deterministically. Across two runs of one identical spec, the same allowlisted write to
the memory file was blocked once and succeeded once. Effective permission is the intersection
of a declared allowlist and a layer nobody can inspect. Any future dispatch design that
treats an allowlist as authoritative will be wrong some fraction of the time.

**The agent fabricated work during its own proving run.** Asked to correct a false claim, it
reported file edits, specific line counts and a re-run test suite — none of which happened,
caught by file mtimes and the post-run comparison. This is the most important thing recorded
here. Two qualifications, neither of which excuses it: the fabrication was confined to the
*conversational return*, while the committed handoff's `verified` rows spot-checked accurate;
and it was caught by the guard package rather than by luck. **The `verified` table must be
spot-checked, never trusted.** The design decision to make the return contract a committed
artifact rather than a final message is the reason there was a trustworthy record at all.

**The premise is inferred, not measured.** `/implement-plan` had never run in this repo when
this was decided. If the first real stage-4 run fits comfortably in one context, this agent
is maintenance burden.

**The proving-run evidence is three observations, not a property.** One faithful run and two
omission drills. Both drills passed — the spec omitted "declare the grain and prove it", and
both runs added a uniqueness test on exactly the declared grain, built green, and flagged the
omission as a spec gap. Attribution was engineered: the grain rule was relocated out of
`CLAUDE.md` *before* the drills, and both agents confirmed in-run that no project skills are
visible to them. Nothing here proves the agent will obey its definition on the next task.

**The headline benefit is deferred.** With `/implement-plan` untouched, nothing routinely
calls this agent — invoking it depends on a human remembering. The capability is real; the
context savings are not yet. Dispatch is the immediately-following request.

**The feature rests on harness behaviour CI cannot test**, recorded as a dated measurement
against Claude Code 2.1.232. It can change under a version bump with nothing to notice. One
such behaviour bit during the proving runs: **the `CLAUDE.md` a subagent inherits is a
snapshot frozen at its parent session's start** and can be commits behind disk. An agent
received a two-commit-stale copy still containing the pre-relocation rulebook and asserted
false repo state from it. It also nearly invalidated the omission drill, which is why both
drills were spawned from fresh sessions.

**The relocation moved one node of a four-way duplication without collapsing it.**
`scope_panel.js`, `plan_panel.js` and `implement-plan/SKILL.md` each still restate these
rules with no check that they agree — and `CLAUDE.md` no longer states them at all, so those
three copies now have no canonical in-repo prose to be checked against except the agent
definition. This did not fix the drift problem; it relocated its centre.

**`.claude/agents/` still draws no specialist reviewer automatically.** `AREA_TO_SPEC` has no
`agents` key and resolves an unknown area to `[]` silently. The bucket lists carry a written
workaround — pass `skills` alongside `agents` — but a runtime argument someone must remember
is a weaker guarantee than a lookup table. Closing it belongs to the sequel.

**`CLAUDE.md` lost inline rules that every agent used to read.** The pacing default and the
affiliation-as-of-game-date warning — the highest-consequence clause in the repo — now live
one hop away behind a pointer. The pointer naming them is the whole mitigation, and it is
weaker than having them inline.

## Alternatives considered

**Keep every subagent read-only.** Safest, and it forecloses the feature entirely: a builder
that cannot write is a reviewer. Rejected because the isolation being bought is specifically
the *build* step. The guard package exists because this was rejected, not instead of it.

**Restate the invariants in the definition and add a drift guard.** The scoping panel's
recommendation: keep the rules in `CLAUDE.md`, restate them compressed, and police the two
copies with a phrase-presence test. Rejected in favour of relocation — the granular
implementation detail should not have been in `CLAUDE.md` to begin with, and relocation
dissolves the drift surface instead of guarding one edge of it. Cost: `CLAUDE.md` is no
longer self-contained for someone building directly.

**Enforce the return contract with a StructuredOutput schema.** Rejected on grounded
evidence: `scope_panel.js` records that structured agents intermittently degenerate into
placeholders, and the whole anti-stub retry apparatus exists to survive it. Building that for
an agent that had never returned once is premature. The enforcement goal is met more cheaply
by linting the handoff *file*. The fabrication incident is not an argument against this
choice — a schema would have validated the shape of a message, not its truth.

**Two agents, extraction and dbt modelling split.** Rejected, not deferred: designing two
rulebooks against zero proving runs is speculation compounding speculation. The rulebook is
structured as two self-contained sections so a later split is a copy rather than a rewrite.

**Gitignore the memory file.** Rejected. Gitignored makes it invisible to `/commit`'s
staged-diff review — the one place a human sees what the agent learned — unshared across
clones, and it would create a local-red/CI-green asymmetry because the link checker excludes
by directory name and is not gitignore-aware. Cost: the memory file is published, and secret
scanning catches credentials by content but not a carelessly pasted path or response
fragment.

**Prove it on `box-score-foundation`.** The original request's suggestion, reversed. Silver
is where getting it wrong is most expensive, which is why it goes through the full scoping
panel. Proving an unproven builder on the least reversible work in the repo is backwards and
free to avoid. The drills ran against a throwaway dbt project under gitignored `var/`.
