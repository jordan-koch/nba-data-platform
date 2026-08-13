> **Status:** scoped · created 2026-08-12 · decided · next: plan

# Feature Request — Data-Engineer Agent

## Problem / Motivation

**Implementation detail and strategic judgment compete for one context window, and detail wins.**

Today the main thread does everything. [`/implement-plan`](../../../.claude/skills/implement-plan/SKILL.md)
has the main-thread agent write all the code — its subagents are the *read-only acceptance panel*,
reviewers rather than builders. So by the time a feature ships, one context holds the scoping
rationale, the plan, every file edit, the test output, and the panel's findings. The capacity to
ask "is this still the right shape?" degrades exactly when the work gets large enough for that
question to matter.

This is not yet acute, because there is no pipeline code — but
[`box-score-foundation`](../box-score-foundation/FEATURE_REQUEST.md) will land an extraction
client, a landing-zone writer, a config layer, bronze models, and five silver models in a single
slice. That is the first piece of work large enough to exhaust a context window mid-build.

**Second, knowledge earned during implementation has nowhere durable to go.** The repo has three
knowledge stores and none of them fits implementation ergonomics.
[`CLAUDE.md`](../../../CLAUDE.md)'s Constraints & Gotchas is the repo's scar tissue, but it is
budgeted under 200 lines and read on every task by every agent.
[`docs/data-sources.md`](../../../docs/data-sources.md) holds labeled beliefs about the *data*. The
ADRs hold decisions and their costs. None of them is the right home for "`nba_api` returns a
DataFrame rather than JSON, and its column casing differs from the docs" — a fact that is
worthless to an analyst, expensive to rediscover, and certain to be rediscovered every session.

The two problems are related: an implementer working at arm's length needs somewhere to put what
it learned, or the isolation costs knowledge instead of saving context.

## Desired Outcome

Implementation happens at arm's length. The main thread hands a spec to a dedicated agent, and gets
back a summary it can act on strategically — not a file-by-file narration that reconstitutes the
detail it was trying to avoid.

Observable signals:

- A feature gets built without the main thread reading every edit, and the main thread can still
  answer "what was built, what's verified, what's assumed, what's still open" afterward.
- The agent hits a repo-specific trap, records it, and a later session doesn't hit it again.
- The agent's knowledge of *how to build here* survives a session restart; the main thread's
  context does not have to.
- A convention the agent must respect — silver declares its grain and proves it — holds even when
  the spec forgets to restate it.

## Rough Ideas (non-binding)

The requester has built this pattern in a professional setting; there is no working example on this
machine to copy. The shape as described:

**Two paired files.** A static agent definition holding architecture, the ecosystem the agent works
in, and the conventions that apply to *all* implementation work — human-maintained, first-class,
evolving as the repo evolves. Alongside it a **memory file the agent edits directly**, pointed to
from the definition, carrying gotchas, design patterns, and tribal knowledge. Curated from outside
the agent so it stays current and bounded.

**The seam, as worked out in conversation** — not "how much context" but *what is always true
versus what is true for this task*:

| Store | Holds | Maintained by |
|---|---|---|
| Agent definition | Invariants true of every implementation task here | Human, deliberately |
| Spec (`IMPLEMENTATION_PLAN`) | This task's requirements | Stage 3 |
| Memory | What we learned the hard way | Agent appends, human curates |

Three stores, no overlap — and none of them is `CLAUDE.md`.

**Organizing principle:** main thread is manager/director, agent is developer. The developer does
not need what the manager knows about how the project is run; it builds to a spec settled during
intake and scoping. Deliberately narrow, not dumb.

**A proposed return contract** (the piece the original design had not specified): what it built,
what it **verified versus assumed**, what surprised it (memory candidates), and what it could not
do. Not diffs.

## Scope Signals

- **In:** the agent definition under `.claude/agents/`; a memory file it may append to; the return
  contract it reports through; the behavioral guardrails below; and enough of a proving run to know
  whether the design holds.

- **Explicitly out:**
  - **Rewiring [`/implement-plan`](../../../.claude/skills/implement-plan/SKILL.md).** The agent
    stands alone first. Stage 4 keeps building the way it does today.
  - **The curation protocol** — pruning rules, memory-to-docs promotion, the coherence check in
    [`/update-docs`](../../../.claude/skills/update-docs/SKILL.md). Deliberately deferred; see
    *Not now* for why.
  - **The agent invoking pipeline skills.** `/scope-feature` and `/implement-plan` already spawn
    their own panels; calling them from inside a subagent nests panels within panels.
  - **Any git write, and committing.** Those stay in the main thread through
    [`/commit`](../../../.claude/skills/commit/SKILL.md).
  - **Domain or data facts in memory.** Anything that would change an *analyst's* answer belongs in
    `docs/data-sources.md`, promoted through the normal doc gate.
  - **Additional specialist agents.** One agent. A reviewer or analyst agent is a separate request.
  - Replacing the acceptance panel in stage 4.

- **Not now / later:** the curation protocol, once real entries exist — the argument for deferring
  is that speculating about tribal knowledge *before having any* produces a schema nobody fills in,
  so pruning criteria should be designed against evidence; wiring the agent into `/implement-plan`
  as its build step once it has proven itself; further specialist agents.

## Affected Area & Pointers

Tooling, not pipeline. This touches no data, no model, and no extraction code.

| Area | State today | What this touches |
|---|---|---|
| `.claude/agents/` | **Does not exist** | Created by this request — the definition and its memory file |
| [`.claude/skills/`](../../../.claude/skills/) | Eight skills, `SKILL.md` + frontmatter each | Read for house style; not modified by this request |
| [`CLAUDE.md`](../../../CLAUDE.md) | Project map names `.claude/skills/` only | Map gains a directory; the subagent conventions may need revisiting |

Read first: [`.claude/skills/implement-plan/SKILL.md`](../../../.claude/skills/implement-plan/SKILL.md)
— it is both the closest prior art and the source of the central tension (see Constraints);
[`CLAUDE.md`](../../../CLAUDE.md)'s Project Conventions and Data Layer sections, which are the
candidate invariant set; [`.claude/skills/update-docs/SKILL.md`](../../../.claude/skills/update-docs/SKILL.md)
for the existing doc-coherence checks and the 200-line budget precedent — the repo already has a
worked example of bounding an agent-read document by explicit line count, which is directly
applicable to the memory file; and an existing skill such as
[`/commit`](../../../.claude/skills/commit/SKILL.md) for house voice.

**First real use** would be [`box-score-foundation`](../box-score-foundation/FEATURE_REQUEST.md),
which gives the proving run a concrete target rather than a synthetic one.

## Constraints / Non-negotiables

- **This would be the first write-capable subagent in the repo, and that cuts against a scar.**
  [`implement-plan/SKILL.md:120`](../../../.claude/skills/implement-plan/SKILL.md) records the
  reason every current subagent is read-only: *"a write-capable review agent once ran `git checkout`
  and silently wiped uncommitted work while a vacuous selftest passed green."* Stage 4 snapshots the
  diff to gitignored scratch before spawning anything, and re-checks tree integrity afterward,
  precisely because *instructions aren't enforcement*. A builder is a different role from a
  reviewer, and the requester has decided the agent writes directly — but whatever guard replaces
  "it can't write" has to be deliberate, not assumed.
- **Git is read-only for the agent.** Never `checkout`/`reset`/`restore`/`clean`/`stash`, or
  anything discarding working-tree state; destructive needs bubble up. Editing a tracked file is not
  a git operation, so the agent can write code and memory freely while `/commit` stays the
  nothing-lands-unseen checkpoint — and every memory delta surfaces in a staged diff.
- **The agent never commits, merges, pushes, or amends.**
- **The repo is public.** A committed memory file is published, and inherits the no-secrets,
  no-bulk-data discipline `/commit` already screens for.
- **The invariants the agent carries must not contradict `CLAUDE.md`.** They are the same rules;
  two statements of the same rule can drift apart.
- **`CLAUDE.md` is budgeted under 200 lines.** Whatever this adds to the project map has to fit.

## Open Questions for Scoping

1. **Does a subagent inherit project `CLAUDE.md` automatically?** `unconfirmed`, and empirically
   testable in minutes. The purpose of the test is **contamination-checking, not capability**: under
   the manager/developer framing, inheriting `CLAUDE.md` hands the developer the intake conventions,
   the ADR index, and the pipeline stages — manager context the agent is supposed to be narrow of.
   If it inherits, the definition must actively override; if it doesn't, the definition carries more
   and duplication-rot becomes the real maintenance cost.

2. **Point at the invariants, or restate them?** The data-layer rules live in `CLAUDE.md` today. If
   the agent definition restates them, there are two copies of one rule and they will drift. If it
   points at `CLAUDE.md`, the agent reads manager context to find developer rules — the exact
   leakage question 1 is about. A third option: move the invariants to a file both read.

3. **What guards a write-capable subagent?** Given the recorded incident: does the agent get Bash at
   all? Does the main thread snapshot before spawning, as stage 4 does? Is tree integrity re-checked
   after? "It's a builder, not a reviewer" explains why it may write — it does not explain what
   catches it when it writes something wrong.

4. **How do we check its work?** The requester named this directly, and it is the sharpest question
   here. Stage 4's acceptance panel verifies criteria by running them — but it was designed for code
   the main thread *watched itself write*. An arm's-length builder inverts that: the reviewer now has
   less context than the author, not more. Does the existing panel still suffice, does the return
   contract need to carry evidence rather than claims, or does arm's-length work need a different
   verification posture entirely?

5. **What is the exact memory-versus-docs line, and how does promotion work?** The proposed boundary
   is implementation ergonomics versus domain facts — an entry that would change an analyst's answer
   belongs in the docs. But the agent will *discover data facts while implementing*; verifying the
   `leaguegamelog` shape is literally task one of the first feature. What happens when it learns
   something that belongs in `docs/data-sources.md`? If it writes to memory instead, the repo holds
   two answers and `/update-docs` only checks one — the drift the doc gate exists to prevent, routed
   around via a file the gate doesn't know about.

6. **Where does the memory file live, is it committed, and what bounds it?** Committed makes it
   reviewable through `/commit` and published with a public repo; gitignored makes it machine-local
   and unshared. `/update-docs` already enforces a 200-line budget on `CLAUDE.md`, which is a
   precedent worth reusing or consciously rejecting.

7. **What is the return contract, concretely — and is it enforced or merely requested?** Prose
   sections, or a schema the agent must fill? Agents default to narrating file-by-file; if the
   contract is advisory, the isolation may be spent for nothing.

8. **What does the agent do when the spec is wrong or incomplete?** A deliberately narrow developer
   that only knows the spec will build what it was told. The consequent risk is real: miss "declare
   the grain and prove it" in one plan and the agent ships a silver model with no uniqueness test and
   no sense that it did anything wrong. The invariant set in the definition is the intended guard —
   but does the agent push back on a bad spec, build it and flag it, or build it silently?

9. **Is one agent the right granularity?** Extraction work and dbt modeling are different enough
   that one definition may end up carrying two rulebooks. Splitting later is cheap; noting the
   question now is cheaper.
