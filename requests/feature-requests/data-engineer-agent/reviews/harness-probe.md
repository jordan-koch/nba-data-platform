# Harness Probe — Phase 0

## Verdict: **PROCEED**

A project `.claude/agents/*.md` is loaded by this harness, registers as a spawnable
`subagent_type`, and its **body reaches the agent** (sentinel round-trip confirmed five
times). Per-agent **tool** permissions are declarable and honoured. Per-agent **path**
permissions are not — that half of the guard is prose, and the plan's fallback applies.

**Harness version:** `2.1.232 (Claude Code)`. Measured **2026-08-14** on Windows 11,
PowerShell 5.1. Every finding below is a **dated measurement of harness behaviour**, not a
standing fact — it can change under a version bump with nothing in CI to notice.

## The two probe attempts

The plan's two-stage STOP rule (blocker fix A2-02) required this, and it earned its keep:
**attempt 1 came back negative and the negative was false.**

**Attempt 1 — mid-session, file created after session start. NEGATIVE (false).**

Created `.claude/agents/probe-canary.md`, then spawned it from the running session:

~~~
Agent(subagent_type="probe-canary", ...)
→ Error: Agent type 'probe-canary' not found. Available agents: claude,
  claude-code-guide, Explore, general-purpose, Plan, statusline-setup
~~~

The returned roster is byte-identical to the one this session was given at start-up. That
is the signature of plan case **(b)**: the registry is resolved at session start and does
not re-scan. Treated as provisional, not as a STOP.

**Attempt 2 — fresh session, file already on disk. POSITIVE.**

~~~
claude -p "List every subagent_type available to you ... then spawn probe-canary ..."
     --allowedTools "Agent Task Read Grep Glob" --model sonnet
~~~

Resolved and spawned. The finding stands on attempt 2.

## Answers

### 1. What loads a `.claude/agents/*.md`? — `measured`

The harness registers every **frontmatter-bearing** `.md` under `.claude/agents/` as a
`subagent_type`, resolvable by the subagent-spawn tool. That is the same surface Phases 4–5
will use. Enumerated from a fresh session:

~~~
claude -p "Print the exact list of subagent_type values available to you, one per line,
          and nothing else." --allowedTools "Read" --model sonnet
→
claude
Explore
general-purpose
Plan
probe-canary
probe-scoped
probe-shell
probe-writer
statusline-setup
~~~

**The registry is resolved at session start.** A definition created mid-session does not
register in that session. This is load-bearing for Phases 4–5 — see *Consequences* below.
**Partly superseded the same day — see *Corrections* at the end of this file.** The second
sentence is too strong: the registry does re-scan mid-session.

Corroborating surface evidence from `claude --help`: `--agents <json>` documents the agent
shape as `{name: {description, prompt}}`, and `--safe-mode` lists "custom commands and
**agents**" among the customizations it disables. The `claude agents` subcommand is
*"Manage background agents"* — a different surface, and correctly excluded as evidence.

### 2. Does the body reach the agent? — `verified`

Yes. Every canary quoted its unique sentinel back verbatim — `ZEPHYR-QUOKKA-7731-BASELINE`,
`CINNABAR-PELICAN-9184-WRITER`, `TOURMALINE-HERON-5520-SCOPED`,
`AMARANTH-IBEX-3067-SHELL`, `VERMILION-AXOLOTL-8815-SCOPE2`. A name resolving is not
evidence the body loaded; a sentinel round-trip is, and this is the finding the
dead-artifact risk turns on.

### 3. Frontmatter schema accepted — `measured`

`name`, `description`, `tools` and `model` are accepted and **honoured**. No key produced a
rejection message; unknown/unsupported keys are absorbed silently.

**The schema AC1's guard should assert: `name` and `description`, both non-empty.** That is
the confirmed minimum, and the SKILL-format shape does transfer. `tools` and `model` are
honoured but are not universal, so the guard should not require them.

### 4. Are per-agent TOOL permissions declarable? — `verified` — **YES**

`tools:` is honoured exactly, as a grant *and* as a restriction:

| Declared | Actually received |
|---|---|
| `Read, Grep, Glob` | `Read, Grep, Glob` — no Bash, no Edit, no Write |
| `Read, PowerShell(git status:*)` | `Read, PowerShell` |
| `Read, Grep, Glob, PowerShell, Write, Edit` | all six |

This settles Decision 3. The agent **can** be given the verify commands it needs.

### 5. The shell tool is `PowerShell`, not `Bash` — `verified`

**The single most load-bearing correction this probe produced.** `probe-writer` declared
`tools: Read, Grep, Glob, Bash, Write, Edit` and received **Read, Grep, Glob, Write, Edit**
— the shell was silently dropped, with no warning. Its own report:

> I do **not** have a `Bash` tool — it is absent from my tool set entirely, not merely
> restricted. […] a writer-only agent (this configuration) cannot self-verify by running
> tests.

Re-declared as `PowerShell`, the shell is granted and works. `probe-shell` ran, and pasted
back real output:

~~~
uv run pytest tests/test_repo_structure.py -q
→ ......                                                                   [100%]

git status --porcelain
→ ?? .claude/agents/
~~~

Had the definition shipped naming `Bash`, the agent would have had no way to run `pytest`,
`mypy` or `dbt build`; the return contract's "cite a command and its actual output" would
have been impossible; and every acceptance criterion in the feature would still have passed
green, because they check form. This is precisely the failure Phase 0 step 6 exists to
catch.

### 6. Argument-scoped tool syntax is ignored — `verified`

`PowerShell(git status:*)` grants `PowerShell` **unrestricted**. The out-of-scope call ran
with no block and no prompt:

~~~
git status --porcelain   (in scope)     → ?? .claude/agents/
git log --oneline -1     (OUT of scope) → 46c76d0 Plan data-engineer-agent: 7 phases, 9 gates disposed
~~~

`Edit(README.md)` behaved the same way — `Edit` granted, unrestricted. The tool is not
dropped; the scope simply has no enforcement effect. An earlier reading that
`Bash(git status:*)` had been "dropped by the scoping syntax" was **wrong** and is corrected
here: plain `Bash` is equally absent, so that drop is the platform (finding 5), not the
syntax. The `PowerShell` control isolates it cleanly.

### 7. Where can a WRITE ALLOWLIST be declared? — `measured` — **nowhere machine-readable**

There is no harness-enforced path allowlist. `tools:` gates *which tools*, never *which
paths*. `probe-writer` wrote `var/tmp/probe-write-check.txt` with no prompt, no gate and no
refusal, and reported:

> There is no technical, harness-enforced path allowlist visible to me. […] *which paths*
> those tools may touch appears to be governed entirely by instruction-following on my
> part — CLAUDE.md and the task prompt — not by any allowlist I can detect being enforced
> underneath the tool.

**Disposition — the plan's G8 fallback applies.** The allowlist goes in a fenced list under
a stable `## Write allowlist` heading in the definition body: parseable without harness
support, and readable by the sequel's dispatcher. **No `.claude/settings.json` is adopted** —
the probe did not show it to be the only place permissions can live, and `tools:` covers the
half that is enforceable.

**This promotes ADR 0007's "detection, not prevention" line from inferred to measured.** The
path bound is prose. The definition must say so plainly rather than implying enforcement.

### 8. Does the agent inherit project `CLAUDE.md`? — `verified` — **YES**

Unrequested, via system-reminder, before the agent reads any file. `probe-canary` quoted the
distinctive line back verbatim:

> **One availability boundary:** tracking-derived stats begin 2013-14. Before that they are
> *structurally absent*, not missing. Averaging across the boundary produces wrong numbers.

Same behaviour as the panel spawn path recorded at `PROJECT_SCOPE.md:143`. **The override
preamble (Phase 1 step 2) is load-bearing, not a cheap precaution** — narrowness cannot be
achieved by omission. The agent also received a fragment of the user's cross-conversation
memory file and the current date.

### 9. Does the agent see project skills? — `verified` — **NO**

> I see no project skills by name anywhere in my context — no `commit`, `update-docs`,
> `implement-plan`, or any other skill identifiers were surfaced to me. I have no
> skill-invocation mechanism available at all.

Useful: the scope's non-goal *"NOT letting the agent invoke `/scope-feature`,
`/create-implementation-plan`, or `/implement-plan`"* is **enforced by the harness**, not
merely requested in prose. The definition should still state the prohibition — harness
behaviour is a dated measurement — but the belt has suspenders.

### 10. Directory hygiene for frontmatter-less Markdown — `verified` — **safe**

`probe-plain.md` was placed in `.claude/agents/` with no frontmatter. It is **absent from
the registry** (see the enumeration in answer 1), produced **no warning**, and did **not**
prevent the four valid definitions from loading.

**Gate G7 holds.** `data-engineer-memory.md` and `README.md` can live in `.claude/agents/`
alongside the definition. No path in the plan shifts.

## Consequences for later phases

1. **Phases 4–5 cannot spawn `data-engineer` from this session.** The definition is created
   in Phase 1 *of this session*, and the registry is session-start-resolved. The proven
   mechanism is a fresh session via subprocess — used successfully four times here:

   ~~~
   claude -p "<spec>" --allowedTools "Agent Task Read Grep Glob Write Edit PowerShell" --model sonnet
   ~~~

   This must also be written into `.claude/agents/README.md`'s spawn protocol, because it is
   the difference between a working proving run and a "not found" error read as a STOP.

2. **Phase 1 step 6 must name `PowerShell`, never `Bash`,** in the tool allowlist.

3. **Phase 1 step 5's write allowlist is a prose bound.** State it under `## Write allowlist`
   and say explicitly that the harness does not enforce it.

4. **The override preamble is required,** not optional — `CLAUDE.md` inheritance is confirmed.

## What this probe could NOT settle

Stated plainly rather than papered over:

- **`allowed-tools` as a distinct key.** `probe-canary` declared it identically to `tools`,
  so its effect is confounded and unmeasured. Use `tools` only.
- **Whether the registry re-scans on any event short of a new session.** Only session-start
  was tested. A cheaper refresh may exist.
- **Whether `model:` accepts full model IDs.** Only the `sonnet` alias was tested; the agent
  self-reported "Sonnet 5", consistent with the alias resolving.
- **User-level vs project-level agent precedence.** `claude-code-guide` appears in this
  session's roster but not the fresh session's. Not investigated; irrelevant to this feature,
  but it means the enumeration in answer 1 is the *project* view, not a global one.
- **Whether a malformed frontmatter block is rejected loudly or silently.** Only well-formed
  frontmatter and no-frontmatter were tested.

## Canary hygiene

Six throwaway files were created and all six deleted with `Remove-Item` (a filesystem
operation — no `git clean`/`checkout`/`restore` was used): `probe-canary.md`,
`probe-plain.md`, `probe-writer.md`, `probe-scoped.md`, `probe-shell.md`, `probe-scope2.md`.

~~~
Get-ChildItem .claude/agents -Filter *.md → (empty)
git status --porcelain                    → (empty)
~~~

No canary survives, so the Phase 2 "exactly one definition" guard cannot redden against one.
`var/tmp/probe-write-check.txt` was also removed.

## Corrections — later the same day

Three findings from Phases 4–5 that revise or extend what is recorded above. Kept as
corrections rather than edited into the findings, so the record shows what was believed when.

### C1 — The registry DOES re-scan mid-session · `measured`

Answer 1 says a definition created mid-session "does not register in that session". Too
strong. `probe-canary.md` genuinely failed to resolve seconds after being written — that
observation stands — but `data-engineer.md`, also created mid-session, **became spawnable
later in the same session without a restart**, and was then spawned successfully.

So the registry re-scans on some event this probe did not isolate; it is simply not
instantaneous on file creation. **Read "Agent type not found" immediately after writing a
definition as *not yet*, never as *unsupported*.** A fresh session remains the reliable
route, and the *Consequences* guidance is unaffected.

### C2 — The inherited `CLAUDE.md` can be STALE · `measured` — the important one

Answer 8 establishes that an agent inherits project `CLAUDE.md` unrequested. What it does
**not** say, and should: **the inherited copy is a snapshot frozen at the parent session's
start, and can be arbitrarily far behind the file on disk.**

Measured: a subagent spawned from a session that began at commit `46c76d0` received
`46c76d0`'s `CLAUDE.md` while `HEAD` was `f71e50d`, two commits later. The injected
`gitStatus` block was stale identically. A **fresh** session inherits the current file —
verified.

Three consequences, all load-bearing:

- **It nearly destroyed the omission drill.** The stale copy still contained the full
  pre-relocation rulebook *including the grain rule*, so an in-session drill spawn would
  have made a PASS unattributable. The drill was spawned from a fresh session instead.
- **It caused the one false claim in proving run A**, where the agent asserted `CLAUDE.md`
  state from inherited context without reading the file.
- **Inherited context is indistinguishable from something the agent verified.** That is the
  general hazard, and it is why the definition tells the agent to read from disk before
  asserting repo state.

### C3 — `tools:` is not the only thing gating writes · `measured`

Answer 7 concludes there is no path-level allowlist and that the write bound is prose. True,
but incomplete in a way that matters: **a harness permission layer sits underneath the tool
grant and can deny a write the definition explicitly allows.**

Measured across the two omission-drill runs — identical spec, identical allowlisted path
(`.claude/agents/data-engineer-memory.md`), identical tool grant:

- run 1: the memory write was **blocked**. The agent reported the block and placed the entry
  text in its handoff instead of working around it. Verified: the file's mtime did not move.
- run 2: the same write **succeeded**. Verified: mtime moved, entry count 6 → 7.

So the effective write permission is the **intersection** of the declared allowlist and a
harness layer that is not fully deterministic. Any future dispatch design that treats a
declared allowlist as authoritative will be wrong some fraction of the time, in the
restrictive direction. Worth its own request; recorded here so it is not rediscovered.
