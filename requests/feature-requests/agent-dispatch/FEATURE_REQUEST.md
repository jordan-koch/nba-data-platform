> **Status:** intake · created 2026-08-14 · open · next: scope

# Feature Request — Agent Dispatch

## Problem / Motivation

**The repo has a builder it never calls.**

[`data-engineer`](../../../.claude/agents/data-engineer.md) landed with a rulebook, a memory
file, a return contract and three passing proving runs. Nothing routes work to it.
[`/implement-plan`](../../../.claude/skills/implement-plan/SKILL.md) Step 3 still has the
main-thread agent write every line, exactly as it did before the agent existed, so invoking
the agent depends on a human remembering to — and the person most likely to forget is the one
already deep in a build.

[ADR 0007](../../../docs/decisions/0007-write-capable-implementation-subagent.md) says this
plainly in its Consequences: *"With `/implement-plan` untouched, nothing routinely calls this
agent … The capability is real; the context savings are not yet."* That was a deliberate
sequencing choice — stage 4 should never point at an unproven builder — and the agent has now
been proven. The reason for the deferral has expired.

The cost is the original complaint, unchanged: implementation detail and strategic judgment
compete for one context window, and detail wins. The first request large enough to exhaust a
context is [`box-score-foundation`](../box-score-foundation/FEATURE_REQUEST.md), which is next
in the queue. Arriving there without dispatch means the agent gets used under pressure, or not
at all.

Two smaller frictions come from the same root. A `.claude/agents/` change draws **zero**
specialist reviewers, because `AREA_TO_SPEC` has no `agents` key and silently resolves an
unknown area to `[]` — today's mitigation is a sentence in two bucket lists telling a human to
also pass `skills`. And a second agent cannot be added without someone hand-editing a skill.

## Desired Outcome

**Stage 4 decides who builds, from the plan's own target paths, without asking a model to
judge it.**

Concretely: `/implement-plan` reads the plan's declared target paths, compares them against
what each agent under `.claude/agents/` is permitted to touch, and either dispatches to that
agent or builds in the main thread — and says which it did and why. Adding a second agent is a
new file, not a new branch in the skill.

Observable signals:

- A feature gets built without the main thread reading every edit, **because the routing
  happened on its own**, not because someone remembered to invoke an agent.
- The routing decision for a given set of paths is predictable and explainable before the run
  starts, and the same paths always route the same way.
- A plan targeting `.claude/agents/` routes to the main thread every time — no agent can build
  an agent, including itself.
- A `.claude/agents/` change draws a specialist reviewer without anyone passing an extra
  argument by hand.

## Rough Ideas (non-binding)

**The sketch recorded in the predecessor's scope** (see *Sequel* in
[`PROJECT_SCOPE.md`](../data-engineer-agent/PROJECT_SCOPE.md)): an agent's declared write
allowlist is its routing table. Targets ⊆ one agent's allowlist → dispatch; targets touching
no allowlist → main thread; targets spanning both → main thread builds the out-of-allowlist
parts and records which and why; two agents claiming one path → hard error, never a silent
guess.

**That sketch has a hole, found while grounding this request, and it is the most useful thing
intake can hand forward.** The definition's allowlist has three entries and the third is a
*placeholder* — `<the target paths the spec declares>`. Read literally, every target is
trivially inside "whatever the spec declares", so the subset test matches everything and the
rule is **vacuous**. The standing allowlist is really only two concrete entries: the memory
file and the handoff directory.

The non-vacuous inversion, offered as a starting point rather than a decision: **route on the
deny set.** Targets intersecting any agent's deny set → main thread. Targets clear of it →
that agent. This preserves the bootstrap property the sketch wanted (`.claude/**` is denied,
so agent-building always routes to the main thread) and it tests something real, because the
deny set is a concrete enumerated list while the allowlist is not. Scoping should decide
whether to fix the allowlist, invert to the deny set, or use both.

**Mechanically**, both readings parse the same way: the definition carries stable
`## Write allowlist` and `## Tool allowlist` headings with fenced blocks under them. That is
the fallback the harness probe forced — there is no machine-readable permission surface to
read instead.

**Precedent worth copying:** `AREA_TO_SPEC` in `acceptance_panel.js` already routes areas →
specialist *reviewers*. This is the same mechanism pointed at *builders*.

## Scope Signals

- **In:** the routing rule and where it lives; rewiring `/implement-plan` Step 3 so a
  qualifying plan dispatches instead of being built in-thread; the agent becoming the
  **default builder** for work that qualifies; the blocked-write failure path; building the
  routing table by reading `.claude/agents/` rather than hardcoding names; and closing the
  `AREA_TO_SPEC` gap so `.claude/agents/` draws a specialist without a hand-passed argument.

- **Explicitly out:**
  - **A second agent.** Dispatch must *scale* to one without the skill changing, and that is
    the test — but adding a reviewer or analyst agent is its own request.
  - **Changing the agent definition's rulebook, return contract, or memory format.** Those are
    settled and proven. If the allowlist block needs a machine-readable shape, that is a
    surgical edit to one section, not a redesign.
  - **A stronger verification posture.** Decided: keep what exists — the pre/post
    tree-integrity comparison plus a human's read of the staged diff at `/commit`. That
    package caught a fabricated report during the proving runs, so it is not assumed to work;
    it is observed to.
  - **Feeding the handoff into the acceptance panel as reviewer context.** Adjacent and
    tempting; a separate request.
  - **Anything that lets an agent commit, merge, push, or amend.** Unchanged and
    non-negotiable.

- **Not now / later:** parallel dispatch of independent phases to multiple agents; a
  dispatch-decision dry-run mode; promoting the routing rule into a shared module both
  `/implement-plan` and `/update-docs` read.

## Affected Area & Pointers

Tooling, not pipeline. **This request's subject is a pipeline stage** — it modifies stage 4
itself. No dataset, no model, no extraction code.

| Area | State today | What this touches |
|---|---|---|
| `.claude/skills/implement-plan/SKILL.md` | Step 3 has the main thread build everything; Step 4 buckets touched areas | The dispatch decision and the rewired build step |
| `.claude/skills/implement-plan/acceptance_panel.js` | `AREA_TO_SPEC` has no `agents` key; unknown areas resolve to `[]` silently | The specialist-routing gap, deliberately deferred by the predecessor's Decision 7 |
| `.claude/agents/data-engineer.md` | `## Write allowlist` / `## Tool allowlist` headings, fenced blocks | Read as the routing input; possibly a shape fix to the allowlist block |
| `tests/` | `test_agent_contract.py`, `test_handoff_contract.py` | A routing guard belongs here — pure function from paths to a builder, with negative controls |

Read first, in this order:

0. [`box-score-foundation/reviews/dispatch-split.md`](../box-score-foundation/reviews/dispatch-split.md)
   — **the manual version of the thing this request automates.** 30 acceptance criteria routed by
   hand, three boundary rulings, written before the first dispatch. Read alongside
   [`IMPLEMENTATION_REPORT.md`](../box-score-foundation/IMPLEMENTATION_REPORT.md) §3, where the
   plan's own dispatch assumption is recorded as a deviation because it was wrong.
1. [`PROJECT_SCOPE.md`](../data-engineer-agent/PROJECT_SCOPE.md) — the *Sequel* section is the
   original design sketch; Decision 13 is why this is a separate request.
2. [`reviews/harness-probe.md`](../data-engineer-agent/reviews/harness-probe.md) — answer 7 and
   corrections **C1–C3**. C3 is the one that changes the design.
3. [`ADR 0007`](../../../docs/decisions/0007-write-capable-implementation-subagent.md) — the
   Consequences section states the constraints this request inherits.
4. [`reviews/proving-run-b.md`](../data-engineer-agent/reviews/proving-run-b.md) — the
   blocked-vs-succeeded write divergence, measured.

## Constraints / Non-negotiables

- **The declared allowlist is prose, not enforcement.** Measured: this harness has no
  path-level permission system. Dispatch routes on a *declaration*, and the declaration binds
  nothing. Routing is a prediction about where an agent will write, never a guarantee — the
  tree-integrity comparison remains the thing that actually catches a bad write.
- **The harness can deny an allowlisted write, non-deterministically.** Measured across two
  runs of one identical spec: the same write to the memory file was blocked once and succeeded
  once. **Decided:** when a dispatched agent reports a blocked write, the main thread completes
  that path itself and records the split, rather than aborting the run. A routing table with
  no failure path for "routed correctly, then denied" is wrong by construction.
- **The bootstrap must resolve itself.** `.claude/**` sits in the deny set, so a plan targeting
  `.claude/agents/` always routes to the main thread. No agent builds an agent, including
  itself.
- **Two agents claiming one path is a hard error**, never a silent guess.
- **Agents never commit, merge, push, or amend**; `/commit` stays the only sanctioned
  committer, and git stays read-only for every subagent.
- **Spawn from a fresh session.** Measured: the `CLAUDE.md` a subagent inherits is a snapshot
  frozen at the parent session's start and can be commits behind disk — one such agent
  asserted false repo state from it. Dispatch that reuses a long-running session will hand
  agents stale context.
- **`acceptance_panel.js` is covered by two `.mjs` guards CI does not run.** Editing it obliges
  running both by hand; CI has three jobs and no Node step.
- **Renaming a CI job silently breaks branch protection** — not expected here, but this request
  touches skill wiring near it.

## Worked example — `box-score-foundation` ran the manual version, end to end

**Added 2026-08-15, after this request was written.** The Motivation above predicted that
`box-score-foundation` would be *"the first request large enough to exhaust a context"* and warned
that *"arriving there without dispatch means the agent gets used under pressure, or not at all."*

It arrived, and it shipped — **11 phases, 96 files, +11,864 lines, merged as PR #5.** The agent was
used, deliberately and throughout, with every routing decision made **by hand**. That makes the
whole build a worked example of the process this request wants to automate, and several of the
Open Questions below move from speculation to measurement because of it.

**The dispatch record**, all committed under
[`box-score-foundation/reviews/`](../box-score-foundation/reviews/): **nine spawns plus two
resumptions**, producing **ten handoffs** (109–120 lines, every one conforming to the return
contract). Plus one hand-written routing table,
[`dispatch-split.md`](../box-score-foundation/reviews/dispatch-split.md) — 30 acceptance criteria
assigned to *agent* / *main-thread* / *user-run*, with three boundary rulings, written before the
first dispatch because gated decision P7 made an unambiguous split a hard gate.

**That document is the artifact to read first when scoping.** It is, in substance, a manual
execution of the routing table this request proposes to build — and it took real effort, which is
the cost being targeted.

### What the run measured

**Every phase split. Not one was purely agent-buildable.** All nine dispatches needed a
hand-written agent/main-thread boundary in the spec. There was never a phase where "hand the whole
thing over" was correct, and never one where "build it all in-thread" was either.

**Three carve-outs emerged that the recorded sketch does not name**, and all three are *action*
boundaries rather than path boundaries:

- **Network calls.** `uv lock` / `uv sync` resolve against PyPI, so they are the same class of call
  the rulebook already forbids via `dbt deps`. The plan's own §2.7 put `pyproject.toml`/`uv.lock` on
  the agent's surface and was **wrong**; it was corrected at Phase 0 and recorded as a deviation.
- **Live extraction.** Fixture capture and the completion probe hit `stats.nba.com`, so Phase 3 was
  main-thread even though `src/nba_platform/fixtures.py` — the recorder it uses — is agent-built.
  The *tool* routed to the agent; *pulling the trigger* did not.
- **Anything the agent must not be able to edit and then report green on.** All of `tests/`.

A path-only routing rule decides none of these three, because the deciding factor is what the work
*does*, not where it writes.

**The deny set held against a wrong spec — mine.** In Phase 7 the dispatch instructed the agent to
mutate a file under `tests/fixtures/` for a negative check. It **refused**, correctly ranking its
deny set above the instruction, and produced equivalent evidence against a scratch copy with
`NBA_LANDING_ROOT` repointed. The guard caught a main-thread error, which is the direction of
failure nobody plans for. Recorded in
[`phase-7-handoff.md`](../box-score-foundation/reviews/phase-7-handoff.md).

**The `AREA_TO_SPEC` gap was hit exactly as described.** The acceptance panel was launched with
`skills` passed alongside `agents` by hand, because `agents` alone resolves to zero specialists
silently. The mitigation sentence works — and it only works because a human read it.

**Handoff quality was not the bottleneck.** Ten handoffs, none over the 120-line cap, every
`verified` row citing a real command and its output. Two of them corrected the main thread's own
spec on measured grounds. The return contract is doing its job; the routing is what was manual.

1. **Allowlist or deny set — which is the routing input?** The recorded sketch says allowlist;
   grounding shows the allowlist contains a placeholder that makes the subset test vacuous.
   Invert to the deny set, fix the allowlist block to be genuinely enumerable, or use both?
   This is the central design question and everything else follows from it.

   > **Evidence from the worked example.** The deny set did all the work; the allowlist decided
   > nothing, exactly as the vacuity argument predicts. But **neither** would have routed the run
   > correctly on its own, because three of the boundaries that actually mattered were *actions*,
   > not paths — network calls, live extraction, and `dbt deps`. Those are already enumerated in
   > the definition, but under `## Tool allowlist`, not under either path list. Scoping should
   > consider whether the routing input is *two* sections rather than one.

2. **Where does the routing rule live?** Prose in `SKILL.md` that an agent follows, a pure
   function in `tests/` that CI can prove, or a shared module the skill reads? The repo's own
   lesson is that a rule enforced only by prose is etiquette — but stage 4 is a skill, not
   code, and there is no existing module for it to import.

3. **What exactly are "the plan's target paths"?** `IMPLEMENTATION_PLAN.md` carries a §7
   files-to-touch checklist as a Markdown table. Is that parsed, or does dispatch need a
   declared machine-readable field the planning stage must emit? If the latter, stage 3's
   template changes too, and that widens this request.

   > **Evidence from the worked example.** §7 was never parsed, and would not have been usable if
   > it had been. It is a **whole-plan** list, while every dispatch needed a **per-phase** target
   > set — so the paths handed to each agent were derived by hand from that phase's §3 steps, not
   > read off §7. §7's granularity and dispatch's granularity are different, which is the same
   > finding as Q7 approached from the other side.

4. **What are the carve-out boundaries?** *Default builder with carve-outs* is decided, and
   three are named — denied paths, trivial edits, fixing the agent's own output. "Trivial" is
   the soft one: who judges it, and against what threshold, without it becoming an escape hatch
   that quietly restores today's behaviour?

5. **Does closing the `AREA_TO_SPEC` gap belong here or in its own request?** It is a two-line
   JS change with a real blast radius: the file is guarded by two `.mjs` tests CI never runs,
   and the predecessor deliberately deferred it. In scope by adjacency, but it is the one part
   of this request that edits panel code.

6. **How is the routing decision surfaced?** Silent dispatch makes stage 4 unpredictable to
   watch; announcing every decision is noise. What does the user see, and when — before the
   spawn, or in the report after?

7. **What happens when a plan has phases that route differently?** A plan whose Phase 2 is
   agent-eligible and Phase 3 is not — does dispatch decide per phase or once per plan? The
   predecessor's own plan is a worked example: it would have split.

   > **Answered empirically, and more strongly than the question assumes.** It is not that *some*
   > plans split — **every phase of an 11-phase plan split**, and so did the routing *within*
   > several of them. Phase 3 is the sharpest case: `src/nba_platform/fixtures.py` was agent-built
   > while the capture that runs it was main-thread, because the tool is a path and pulling the
   > trigger is an action. "Once per plan" was never viable. Per-phase was the working granularity,
   > and even that needed a hand-written split inside each spec.

8. **Is a follow-up dispatch to a still-warm agent a different case?** Not in the original list,
   and it came up twice. Two of the nine dispatches were **resumptions** of an agent that had
   already finished — sent back to fix something found after its handoff, with its context intact
   ([`phase-3b-handoff.md`](../box-score-foundation/reviews/phase-3b-handoff.md) and the Phase 5
   test rewrite). Both were markedly cheaper than a fresh spawn would have been, because the agent
   already knew the code.

   That sits awkwardly against the recorded constraint **"spawn from a fresh session"**, which
   exists because a subagent's inherited `CLAUDE.md` is a snapshot frozen at its parent's start.
   A resumption inherits an even older snapshot. Neither resumption went wrong here — but both
   were judgment calls a routing rule would have to make explicitly, and the constraint as written
   does not cover them.
