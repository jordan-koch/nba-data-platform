# Scoping Panel - Raw Proposals

Verbatim output of the three divergent scopers, before merge and before any human
triage. Recorded as provenance: this is what the panel said, not what was kept.

Panel content is fenced because it contains Markdown link syntax that does not
resolve from this directory; fencing keeps it verbatim and keeps CI green.

Panel health: 3/3 scopers, 2/2 adversaries, no degraded lenses.

---

## Scoper: fit  (ok: True)

### fit

~~~
verdict: clean
rationale: It belongs here, and it integrates through seams that already exist — but it arrives with three conditions that must be built, not assumed. WHY IT FITS: (1) `.claude/` is already first-class tracked tooling — 16 files under `.claude/skills/`, and `.gitignore` (verified, 88 lines) has no `.claude/` entry, so `.claude/agents/` needs no new mechanism to be committed and reviewed. (2) `requests/README.md:9` names "a skill" among valid feature-request subjects; tooling-not-pipeline is an in-contract request shape, not an exception. (3) ADR 0001 (`docs/decisions/0001-deliberate-over-engineering.md:27-29`) puts "testing, CI/CD, ... incident process, documentation" in the turned-all-the-way-up column precisely because practice investment is free of scale — a dedicated implementer agent is practice investment, so the standing overkill objection is pre-answered rather than needing a defense. (4) NO ACCEPTED ADR IS CONTRADICTED. The one convention that looks like a conflict is not one: `CLAUDE.md:73-75` says subagents get read-only *git* — never `checkout`/`reset`/`restore`/`clean`/`stash` — which constrains history-destroying commands, not file edits. `implement-plan/SKILL.md:155` ("modify no file") is scoped to the acceptance panel's reviewers, and the FR explicitly leaves stage 4 alone (FR:86-88). So a write-capable builder sits inside the rules as written; what it does expose is that CLAUDE.md:73 is *read* as "subagents don't touch the tree", which is a wording fix, not a supersede. ADR 0006 (public repo) constrains the memory file's contents rather than forbidding it. (5) The mechanical acceptance surface this repo needs for a prose artifact already exists: `tests/test_repo_structure.py` is the established home for "config and its filesystem agree" guards (its docstring, lines 1-9, justifies exactly this class of check), and `tests/test_doc_links.py` scans ALL Markdown outside EXCLUDED_PARTS (lines 31-48, which do not exclude `.claude/`), so both new files get link-checked in CI for free. THE THREE CONDITIONS — integration work that fits inside the scope, not reshaping of it: (a) DUPLICATION IS REAL AND ALREADY THREE DEEP. CLAUDE.md's invariant set (`CLAUDE.md:86-103`) is already restated verbatim-in-spirit at `scope_panel.js:124`, `plan_panel.js:146`, and `implement-plan/SKILL.md:100-112`. The agent definition would be the fourth copy, and none of the existing three has a drift check. In a repo whose premise is that docs are authoritative for agents, a fourth silent copy is the highest-cost thing in this request — so a drift guard ships with it. (b) VERIFICATION INVERTS. Every check the repo owns (`acceptance_panel.js` reviewers, `/update-docs`, `/commit`) was designed for code the main thread watched itself write; an arm's-length builder gives the reviewer less context than the author. CI's mechanical gates (`ci.yml` jobs `Lint, types, tests` / `dbt build` / `Secret scan`) are author-agnostic and hold, and `/commit`'s staged-list-then-yes (commit/SKILL.md Step 2 and Step 4) remains the nothing-lands-unseen checkpoint — so the safety net survives; what degrades is judgment coverage, which the return contract has to carry as evidence rather than claims. (c) `.claude/agents/` FALLS IN NO PANEL BUCKET. `AREA_TO_SPEC` (`acceptance_panel.js:200-204`) maps `skills: ['skill-quality']`, and that specialist's mandate (line 199) is written "(.claude/skills touched)"; the bucket list in `implement-plan/SKILL.md:130-132` and `update-docs/SKILL.md:47-48` says the same. Every clause of the skill-quality mandate — frontmatter validity, description drift, registration in CLAUDE.md, read-only-git conventions, link resolution — applies verbatim to an agent definition, so this is a one-word gap, not a design mismatch. NOT A DATASET: this touches no source, no landed payload, no model, so the five dataset contracts (grain / keys / era coverage / update semantics / extraction cost) do not apply and should not be manufactured. The medallion layers are not where this lives; they are what it will be asked to write, which is why the invariant set it carries must mirror `transform/models/bronze/README.md` and `transform/models/silver/README.md` rather than paraphrase them. One honest tension worth recording rather than hiding: with `/implement-plan` fenced off (FR:86-88), the headline benefit — a feature built without the main thread reading every edit — is only realized when a human invokes the agent by hand. That is coherent with "the agent stands alone first", but this scope buys the capability, not yet the context savings.
~~~

### goals

~~~
- Create `.claude/agents/` as a tracked, first-class directory alongside `.claude/skills/`, holding one implementation agent definition and one memory file it may append to — the repo's first write-capable subagent, with its permission to write files distinguished explicitly from the read-only-git rule at `CLAUDE.md:73-75`.
- Give the agent an invariant set that survives a spec that forgets to restate it — the Data Layer rules at `CLAUDE.md:86-103` (resolve-by-name, immutable landing zone, bronze 1:1, silver declares AND proves its grain, facts MERGE on key, layer promotion gated on tests, no bulk data in git) plus the Project Conventions at `CLAUDE.md:65-75` — carried in a form a machine can check against CLAUDE.md rather than a fourth silent copy.
- Establish a bounded, committed memory file for implementation ergonomics — the class of fact that is worthless to an analyst and expensive to rediscover — with an explicit routing rule sending domain and data facts to `docs/data-sources.md` through the normal doc gate instead.
- Define a return contract the main thread can act on strategically: what was built, what was VERIFIED versus ASSUMED (per this repo's epistemic-labeling rule, `CLAUDE.md:76-79`), what surprised the agent (memory candidates), what it could not do, and what stays open — carrying evidence, not diffs and not file-by-file narration.
- Settle the guard posture for a write-capable subagent against the recorded scar at `implement-plan/SKILL.md:120-124` (a write-capable review agent once ran `git checkout` and wiped uncommitted work while a vacuous selftest passed green): pre-spawn snapshot, git read-only, post-run tree-integrity re-check, `/commit` unchanged as the only committer.
- Answer, with recorded evidence and a promoted epistemic label, whether a subagent inherits project `CLAUDE.md` and whether it sees project skills — the contamination question at FR:150-155 that determines whether the definition must actively override or must carry more.
- Prove the design once on a real, small task, and record the run (return contract + pre/post tree state) as the artifact that says whether arm's-length building actually held.
- Land the doc integration the change earns: `.claude/agents/` in the CLAUDE.md project map, the subagent convention sharpened, and an ADR recording why the first write-capable subagent exists and what guards it.
~~~

### non_goals

~~~
- Rewiring `/implement-plan` to use the agent as its build step. Stage 4 keeps building the way `implement-plan/SKILL.md` Step 3 describes; its acceptance panel is untouched. (FR:86-88)
- Editing `acceptance_panel.js`, `plan_panel.js`, or `scope_panel.js`. Keeping the panel scripts out of the diff is what makes this change reviewable; the `AREA_TO_SPEC` gap at `acceptance_panel.js:200-204` is recorded, not fixed here.
- The curation protocol — pruning rules, memory-to-docs promotion mechanics, and a memory-coherence check inside `/update-docs`. Deferred deliberately until real entries exist to design against. (FR:88-90, 100-103)
- The agent invoking pipeline skills. `/scope-feature`, `/create-implementation-plan`, and `/implement-plan` each spawn their own panels; calling one from inside a subagent nests panels within panels. (FR:91-92)
- Any git write by the agent: no commit, no merge, no push, no amend, and none of `checkout`/`reset`/`restore`/`clean`/`stash`. `/commit` stays the only sanctioned committer. (`CLAUDE.md:65-69`, `commit/SKILL.md`)
- Domain or data facts in the memory file. Anything that would change an analyst's answer belongs in `docs/data-sources.md` with an epistemic label, promoted through `/update-docs`. (FR:95-96, `update-docs/SKILL.md:103-112`)
- Additional specialist agents. One agent; a reviewer or analyst agent is a separate request. (FR:97)
- Any dataset, extraction code, landed payload, or dbt model. This request touches no data — `src/nba_platform/` still contains only `__init__.py` when it lands, and `transform/models/` still holds three layer READMEs and nothing else.
- A machine-local or gitignored memory file. Committed is the posture; a gitignored memory would be invisible to `/commit`'s staged-diff review and unshared across clones.
- Solving the context-savings problem end to end. This scope buys the capability and proves it once; realizing the benefit routinely requires a later request that wires the agent into a stage.
~~~

### acceptance_criteria

~~~
- `uv run pytest tests/test_repo_structure.py -q` is green and includes a new guard that fails when `.claude/agents/<agent>.md` is absent or its YAML frontmatter lacks `name` or `description` — the same structural-agreement class as `test_every_layer_documents_itself` (lines 77-84).
- A memory-budget guard is green: the memory file exists at its declared path and its line count is at or under the agreed cap, with the assertion message naming the cap. This makes mechanical what `update-docs/SKILL.md:76-79` enforces only by judgment for CLAUDE.md's 200 lines.
- An invariant-drift guard is green: for each invariant the agent definition declares it carries, the test asserts a corresponding rule is present in `CLAUDE.md`, and fails if either side is edited alone. The test must be proven non-vacuous (a mutated in-test copy makes it fail), mirroring `test_the_guard_actually_covers_the_repo` at `tests/test_doc_links.py:95-104`.
- `uv run pytest tests/test_doc_links.py -q` is green with both new files in the scanned set — no dead relative links in the agent definition or the memory file, and `MIN_EXPECTED_FILES` still satisfied (30 tracked `.md` files today, ≥32 after).
- `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` returns under 200 after the edit (122 today), and the project-map block at `CLAUDE.md:16-33` contains a `.claude/agents/` entry alongside the existing `.claude/skills/` line.
- `CLAUDE.md`'s subagent convention (line 73) reads so that read-only *git* and file-write permission are distinguishable — a reader can tell that an agent editing a tracked file is not violating it.
- `requests/feature-requests/data-engineer-agent/reviews/contamination-probe.md` exists, states the exact probe used, and answers both halves — does a subagent inherit project `CLAUDE.md`, does it see project skills — with an epistemic label of `verified` or `measured`, never `unconfirmed`; and the agent definition's design visibly matches that answer.
- The proving run is recorded in `requests/feature-requests/data-engineer-agent/reviews/proving-run.md` with all five return-contract sections present and non-empty: what was built · verified-vs-assumed (each item individually labeled) · surprises / memory candidates · could-not-do · still-open. It contains no file-by-file diff narration.
- That same record carries tree-integrity evidence: the pre-spawn `git status --porcelain` + `git diff HEAD --stat` and the post-run pair, and the file-set delta equals the return contract's claimed file list — no tracked file reverted, nothing lost. This is the check the scar at `implement-plan/SKILL.md:120-124` demands.
- The agent definition contains an explicit routing rule naming `docs/data-sources.md` as the destination for any data, era, endpoint, or availability fact, and the memory file contains zero such claims at PR time (grep-checkable against the memory file).
- `docs/decisions/0007-*.md` exists carrying Status · Context · Decision · Consequences · Alternatives per `docs/decisions/README.md:19-25`, and its row appears in that file's Index table (lines 39-46).
- CI is green on the PR for all three checks named in `ops/branch-protection.json:4` — `Lint, types, tests`, `dbt build`, `Secret scan` — with the secret scan covering the committed memory file per ADR 0006. Marked user-run: the push and the PR stay the user's.
- `requests/feature-requests/README.md`'s Index row for `data-engineer-agent` (line 92) matches the artifacts' Status blockquotes, per the reconciliation `/update-docs` performs (`update-docs/SKILL.md:131-135`).
~~~

### core_scope

~~~
- `.claude/agents/<agent>.md` — the definition. Frontmatter in the house style already used by all eight `SKILL.md` files (`name` + a trigger-rich `description`), and a body carrying: the manager/developer role framing; the invariant set drawn from `CLAUDE.md:65-75` and `CLAUDE.md:86-103`; pointers to the layer contracts it must obey when writing models (`transform/models/bronze/README.md`, `transform/models/silver/README.md`); the memory pointer; the return contract; the spec-is-wrong protocol; and explicit prohibitions on invoking pipeline skills and on any git write.
- `.claude/agents/<agent>-memory.md` — committed, bounded, seeded with a header that states what belongs (implementation ergonomics: client shapes, casing surprises, tooling traps) and what routes elsewhere (`docs/data-sources.md` for data facts, `CLAUDE.md`'s Constraints & Gotchas for repo-wide scar tissue, `docs/decisions/` for decisions). Seeded with at most one or two real entries; an empty schema nobody fills is the failure the FR names at lines 100-103.
- The invariant-carrying mechanism, decided and built: restate in the definition AND ship the drift guard the existing three restatements (`scope_panel.js:124`, `plan_panel.js:146`, `implement-plan/SKILL.md:100-112`) lack. Restating goes with the grain of what the repo already does; the guard is what makes the fourth copy safe.
- The contamination probe (FR open question 1) executed and recorded with a promoted epistemic label, since its answer decides whether the definition overrides inherited manager context or carries more of it.
- The write-guard posture, stated in the definition and mirrored in a short spawn protocol the main thread follows: work on a feature branch; snapshot uncommitted work to gitignored `var/` before spawning, exactly as `implement-plan/SKILL.md:120-124` does; git read-only for the agent; re-check tree integrity after; `/commit` unchanged.
- Mechanical guards added to `tests/test_repo_structure.py` — definition exists with valid frontmatter, memory exists and is within budget, invariants agree with CLAUDE.md. New test code must satisfy the repo's strict gates: `mypy` runs `strict = true` over `tests` (`pyproject.toml:70-74`) and ruff selects `PTH`, `DTZ`, `N`, `B` at line-length 100 (lines 43-64).
- Doc integration: `.claude/agents/` added to the CLAUDE.md project map (line 27 area, 122/200 lines used); the subagent convention at line 73 sharpened to distinguish git-write from file-write; the `requests/feature-requests/README.md` Index row advanced.
- ADR 0007 — the first write-capable subagent, why a builder is a different role from a reviewer, and what replaces "it can't write" as the guard. Required by `update-docs/SKILL.md:100-101`: a decision someone would reasonably ask "why did you do it that way" about, recorded nowhere else.
- One proving run on a real, small, non-dataset task, with the return contract and pre/post tree state recorded under `reviews/` — the evidence that the design held, and the input the deferred curation protocol will eventually be designed against.
~~~

### enhancements

~~~
title: Extract one canonical invariant file that CLAUDE.md, the agent definition, and both panel scripts cite
rationale: The Data Layer rules exist in four places once this ships — `CLAUDE.md:86-103`, `scope_panel.js:124`, `plan_panel.js:146`, `implement-plan/SKILL.md:100-112` — with no check that they agree. A single source all four point at kills the drift surface permanently rather than guarding one edge of it. Rejected from core only because the FR fences off the panel files and because touching three tooling surfaces in a change whose point is a fourth is how a reviewable diff stops being reviewable.
cost: grows-build

title: Make CLAUDE.md's 200-line budget mechanical
rationale: `update-docs/SKILL.md:76-79` enforces the budget by asking an agent to run a PowerShell line count and exercise judgment. The memory-budget guard this request builds is the same assertion; pointing it at CLAUDE.md too costs about three lines and converts a judgment rule into a CI failure. Currently 122/200, so it lands green and stays honest.
cost: cheap

title: Teach the panels that `.claude/agents/` exists
rationale: `AREA_TO_SPEC` (`acceptance_panel.js:200-204`) has no `agents` key, and the bucket lists at `implement-plan/SKILL.md:130-132` and `update-docs/SKILL.md:47-48` name only `.claude/skills/`. Every clause of the `skill-quality` mandate (`acceptance_panel.js:199`) applies verbatim to an agent definition, so without this a future edit to these files draws no specialist reviewer at all. The doc half is a two-word edit; the JS half touches a fenced-off file.
cost: cheap

title: Seeded-omission proving run
rationale: Hand the agent a mini-spec that deliberately omits "declare the grain and prove it" and see whether the invariant set catches what the spec dropped. This is the only way to test FR:46-47 and FR:191-195 directly — every other criterion tests that the artifacts exist, not that the invariants bite. Costs one extra run against a spec that is cheap to write.
cost: cheap

title: Return contract as a machine-checkable schema rather than prose sections
rationale: FR:187-189 asks whether the contract is enforced or merely requested. Agents default to narrating file-by-file; an advisory contract spends the isolation for nothing. Declaring the five sections as required keys turns acceptance criterion 8 from a human read into a script, and matches how the existing panels already constrain their agents with StructuredOutput schemas.
cost: cheap

title: Grep guard enforcing the memory-versus-docs line
rationale: A test that fails when the memory file mentions seasons, endpoints, rate limits, or the 2013-14 boundary would mechanize the routing rule that otherwise depends on the agent's discipline plus a human's eye at `/commit`. Worth flagging as brittle — it will produce false positives on a legitimate ergonomics entry that happens to name an endpoint — so it belongs as a warning-shaped check or a curated denylist, not a hard gate.
cost: cheap

title: Split into extraction and dbt-modeling agents
rationale: FR:197-199 raises it: one definition may end up carrying two rulebooks, since immutable-landing/pacing/checkpointing and grain/merge-semantics/layer-discipline are genuinely different bodies of knowledge — the acceptance panel already models them as two separate specialists (`extraction` and `data-contract` in `SPEC_DEFS`). Splitting later is cheap; splitting before a single proving run means designing two rulebooks against zero evidence.
cost: grows-build
~~~

### risks

~~~
- The fourth restatement of the invariants is the highest-cost thing in this request. `CLAUDE.md:86-103` is already mirrored at `scope_panel.js:124`, `plan_panel.js:146`, and `implement-plan/SKILL.md:100-112`, none of them drift-checked. In a repo whose stated premise is that most of it is written by agents against docs treated as authoritative (`update-docs/SKILL.md:28-31`), a rule that quietly disagrees with itself in one of four places is a correctness failure that produces no error.
- Verification inverts at arm's length. The acceptance panel, `/update-docs`, and `/commit` were all designed for code the main thread watched itself write; here the reviewer has less context than the author. The mechanical gates in `ci.yml` are author-agnostic and hold, but the judgment layer thins exactly where the FR (lines 166-172) says it matters most.
- Instructions are not enforcement. The scar at `implement-plan/SKILL.md:120-124` is specifically a write-capable agent that ran a destructive git command while a vacuous selftest passed green. The available guards — feature branch, pre-spawn snapshot to gitignored `var/`, post-run integrity check, `/commit`'s staged-list-then-yes — are mitigations, not prevention.
- The proving run has no target yet. `box-score-foundation` is at `intake` (`requests/feature-requests/README.md:91`) with no PROJECT_SCOPE and no IMPLEMENTATION_PLAN, so FR:124's "first real use" cannot happen until stage 3 of that feature lands. Either this feature's acceptance blocks on another feature, or the proving run needs a different, self-contained target.
- Memory is a route around the doc gate. `/update-docs` checks `docs/data-sources.md`'s epistemic labels (SKILL.md:103-112) and knows nothing about `.claude/agents/`. The very first task of the first feature is verifying the `leaguegamelog` shape — a data fact the agent will discover while implementing. If it lands in memory, the repo holds two answers and the gate audits one.
- The memory file is world-readable. ADR 0006 makes the repo public from the first commit and git history permanent; `gitleaks` (ci.yml:96-99) catches credentials by content but not a carelessly pasted path, machine detail, or response fragment. A memory file the agent appends to freely is a new publication surface.
- The headline benefit is deferred by the scope's own non-goals. With `/implement-plan` untouched, nothing routinely calls the agent, so "a feature gets built without the main thread reading every edit" (FR:41-42) depends on a human remembering to invoke it. The capability is real; the context savings are not yet.
- The whole feature rests on harness behavior this repo cannot test. Whether `.claude/agents/*.md` frontmatter supports a tool allowlist, whether a subagent inherits project `CLAUDE.md`, and whether it sees project skills are properties of the Claude Code harness, `unconfirmed` here. They can change under a version bump with nothing in CI to notice.
- A committed memory nobody prunes grows monotonically. The curation protocol is deliberately deferred (FR:100-103), so between now and then the only bounds are the line cap and a human's read at `/commit` — and a cap reached with no pruning rule turns into either an arbitrary truncation or a quietly raised cap.
- `.claude/agents/` draws no specialist reviewer. `AREA_TO_SPEC` (`acceptance_panel.js:200-204`) has no key for it, so the first future change to the definition or the memory goes through the panel with only the four core reviewers — the exact blind spot the `skill-quality` specialist exists to close for `.claude/skills/`.
~~~

### open_questions

~~~
- Where does the memory file live, and what is the exact cap? Recommendation: `.claude/agents/<agent>-memory.md`, committed, with a hard line cap enforced in `tests/test_repo_structure.py`. The cap number is the user's call — `update-docs/SKILL.md:76-79` sets the 200-line precedent for CLAUDE.md, and something tighter (100-150) is defensible for a file that is appended to far more often than it is read whole.
- Restate the invariants, point at CLAUDE.md, or extract a shared file? Recommendation: restate plus a drift guard now (it matches what `scope_panel.js` and `plan_panel.js` already do, and avoids handing the developer the manager's context), with canonical extraction as a deferred enhancement once a fourth copy has proven the guard works.
- What is the proving run's target? Three options, all real: carve a non-dataset slice out of box-score-foundation (the config / path-resolution module at that request's line 101) and accept that it pre-empts scope belonging to another feature; use a seeded-omission mini-spec against a throwaway task and discard the output; or block acceptance until box-score-foundation reaches `planned`. The first two decouple the features; the third couples them.
- Does the agent get Bash, and with what allowlist? The FR raises it at lines 162-165 and it is unresolved. Related and unnoticed: the repo has no `.claude/settings.json` at all, so if tool posture is declared there rather than in the agent's frontmatter, this request introduces a config surface the CLAUDE.md project map does not mention.
- What does the agent do with a wrong or incomplete spec — push back, build-and-flag, or build silently? The invariant set is the intended guard (FR:191-195), but the guard's behavior has to be specified or it defaults to whatever the model does, which is build silently.
- Is amending the bucket lists in `implement-plan/SKILL.md:130-132` and `update-docs/SKILL.md:47-48` to say `.claude/skills/ + .claude/agents/` part of the fenced-off "rewiring `/implement-plan`", or a cheap fold? It changes no build step — only which reviewer gets spawned — but it does edit a file the FR put out of scope.
- Does ADR 0007 land with this change or after the proving run? Writing it now records the decision at the time it was made, which is the ADR set's whole stated value (`docs/decisions/README.md:29-32`); writing it after means it can record what the proving run actually showed about the guards.
~~~

---

## Scoper: ambitious  (ok: True)

### fit

~~~
verdict: clean
rationale: Tooling, not pipeline: this touches no dataset, so the five dataset contracts (grain / keys / era coverage / update semantics / extraction cost) do not bind — stated explicitly rather than fabricated. Fit is clean on four grounded checks. (1) ADR 0001 (docs/decisions/0001-deliberate-over-engineering.md:27-31) turns testing, CI/CD, incident process and documentation 'all the way up' as free-of-scale practices and declines only infrastructure over-reach; an implementation agent + memory + mechanical guards is precisely the category that ADR endorses. No accepted ADR is contradicted — all six index rows read (docs/decisions/README.md:41-46); none covers subagents. (2) The repo already carries this artifact family: eight skills under .claude/skills/ (verified via git ls-files), each a SKILL.md with name + trigger-rich description frontmatter, several with a sibling script plus an executable self-verification guard (.claude/skills/implement-plan/SKILL.md:271-273). An agent definition is the same shape, one directory over. (3) CLAUDE.md's 'Subagents get read-only git' constrains git, not file writes — a builder that edits tracked files and never runs checkout/reset/restore/clean/stash is compliant as written (the request reaches the same reading at FEATURE_REQUEST.md:137-140); one clarifying half-sentence in CLAUDE.md keeps a future reader from inferring a prohibition that is not there. (4) The premise is live now: box-score-foundation lands extraction client, config layer, landing writer, bronze and five silver models in one slice (box-score-foundation/FEATURE_REQUEST.md:71-76) — the first build large enough to exhaust a context mid-flight. Two caveats that shape rather than block the scope. First, `.claude/agents/` does not exist — verified: git ls-files returns only .claude/skills/**, and a full-tree listing confirms it — so this is greenfield with no in-repo precedent for agent frontmatter. Second, the request's stated goal of a 'deliberately narrow' developer is partly unachievable by omission: measured in this very run, a Task-spawned subagent in this repo receives the full project CLAUDE.md as a system-reminder ('Codebase and user instructions are shown below'), so the definition must actively override inherited manager context rather than merely decline to restate it. That answers Open Question 1 in the affirmative and makes the invariant-drift problem (Open Question 2) real rather than hypothetical — which is why the scope below buys a mechanical drift guard instead of a convention.
~~~

### goals

~~~
- Stand up a write-capable `data-engineer` implementation subagent under `.claude/agents/` that builds from a decided IMPLEMENTATION_PLAN at arm's length, so the main thread spends context on strategy rather than on file-by-file narration.
- Carry a bounded invariant set the agent honors even when the spec forgets to restate it — resolve-by-name, immutable landing zone, bronze 1:1, silver declares AND proves its grain, facts MERGE on key, era boundaries explicit, no commits/merges/pushes, git read-only.
- Make the two-copies-of-one-rule problem mechanical rather than cultural: a CI-enforced guard proving the agent's invariant set and CLAUDE.md still agree, red the moment either drifts.
- Give implementation-earned knowledge a durable, bounded, reviewable home: a committed memory file the agent appends to, with a per-entry schema carrying the repo's epistemic labels, evidence pointers, and an explicit memory-vs-docs routing tag.
- Make the return contract an enforced artifact, not a request: a handoff report with fixed sections — built / verified (with the command and its output) / assumed / surprised-me (memory candidates) / could-not-do / docs-delta — that is schema-linted and carries no diff hunks.
- Replace 'it can't write' with a deliberate substitute guard: a declared write allowlist, a pre-spawn snapshot, and a post-run tree-integrity check that detects reversion, deletion, or out-of-allowlist writes — mirroring the scar recorded at .claude/skills/implement-plan/SKILL.md:120-127 without pretending instructions are enforcement.
- Prove the design with a real proving run rather than an assertion — including a deliberately under-specified spec (the omission drill) that tests whether the invariant set actually holds when the plan forgets it.
- Leave the repo's existing verification posture intact: /implement-plan and its acceptance panel keep working exactly as they do today; this agent stands alone first.
- Record the write-capable-subagent decision and its cost as an ADR, so the reversal of the read-only-subagent posture is visible rather than inferred from a diff.
~~~

### non_goals

~~~
- Rewiring /implement-plan to use the agent as its build step — stage 4 keeps building the way it does today (FEATURE_REQUEST.md:86-88). The agent stands alone first.
- The curation protocol: pruning rules, memory-to-docs promotion judgment, and the memory-coherence check inside /update-docs. Deliberately deferred until real entries exist (FEATURE_REQUEST.md:100-103). The mechanical half — a budget guard, a schema guard, a routing guard — is in scope; the judgment half is not.
- Replacing or weakening the stage-4 acceptance panel. The handoff report is additional evidence, never a substitute for execution-based verification.
- The agent invoking pipeline skills (/scope-feature, /create-implementation-plan, /implement-plan) — nesting panels inside a subagent.
- Any git write by the agent: no commit, merge, push, amend, checkout, reset, restore, clean, stash. /commit stays the only sanctioned committer (CLAUDE.md, .claude/skills/commit/SKILL.md).
- Domain or data facts in memory. Anything that would change an analyst's answer belongs in docs/data-sources.md via the doc gate; the agent may not edit docs/data-sources.md directly — it emits a docs-delta section for the main thread to route.
- Additional specialist agents (reviewer, analyst, extraction-vs-dbt split). One agent; the definition is structured so a later split is cheap.
- Any pipeline code, dbt model, or extraction work landing in the repo as a by-product. The proving runs build into a gitignored scratch project under var/ — no toy silver model enters transform/models/, which the silver README (transform/models/silver/README.md:5-7) reserves for fully-scoped work.
- Anything that spends cloud money, hits stats.nba.com live, or touches prod. Proving runs are offline against committed fixtures/seeds and DuckDB.
- Making the agent a required path. The main thread must retain the ability to build directly; this is a tool, not a gate.
~~~

### acceptance_criteria

~~~
- `.claude/agents/data-engineer.md` exists and parses: valid YAML frontmatter with `name` and a trigger-rich `description`; a new pytest (e.g. tests/test_agent_contract.py) asserts this and `uv run pytest -m "not network" -q` is green.
- Invariant-drift guard is red-able: a pytest asserts every invariant clause the agent definition carries appears verbatim in CLAUDE.md, and a committed negative-control proves the guard fails when either side is mutated alone — mirroring the vacuous-pass guard pattern at tests/test_doc_links.py:95-104.
- Memory file `.claude/agents/data-engineer-memory.md` exists, is committed, and is under its declared line budget; the budget is enforced by pytest (not by convention), with a negative control proving an over-budget file fails. The CLAUDE.md 200-line precedent is either reused or consciously rejected in writing.
- Memory schema guard: every entry parses into the required fields (id, date, epistemic label from {measured, verified, inferred, assumed, unconfirmed}, evidence pointer, routing tag). An entry tagged as a domain/data fact fails the test red with a message naming docs/data-sources.md as its correct home.
- The full mechanical gate is green on the branch: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` (strict, files = ["src", "tests"] per pyproject.toml:70-74), and `uv run pytest -m "not network"`. New guards live in pytest specifically because ci.yml runs no Node step — the existing .mjs skill guards are not CI-enforced (verified: .github/workflows/ci.yml has jobs python/dbt/secrets only).
- `uv run pytest tests/test_doc_links.py -q` is green with the new Markdown included — the checker globs all *.md outside EXCLUDED_PARTS (tests/test_doc_links.py:60-65), so `.claude/agents/*.md` is covered automatically and every relative link in the new files must resolve.
- Proving run A (faithful spec) completes and leaves `requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md` containing every required handoff section, with each row in the `verified` table citing a concrete command and its actual output; a schema-lint test passes over the artifact.
- Proving run B (the omission drill): the agent is handed a spec that deliberately omits 'silver declares its grain and proves it'. PASS iff the produced model carries a uniqueness test OR the handoff report explicitly flags the omission as a spec gap — determined by grep over the drill artifacts and recorded verbatim in `reviews/proving-run-b.md`. A silent, untested grain is a FAIL and blocks the feature.
- Tree integrity: for both proving runs, the recorded pre/post snapshot shows no tracked file outside the declared write allowlist was modified or deleted, HEAD is unchanged, and `git stash list` is unchanged. The snapshot and its comparison are saved into the reviews/ trail rather than asserted in prose.
- Context economy is objectively checked: the handoff report is under its declared line cap and contains no diff hunks — grep for `^@@`, `^+++`, `^---` returns nothing.
- CLAUDE.md's project map lists `.claude/agents/` and the file stays under 200 lines (measured today: 122 lines via `(Get-Content CLAUDE.md | Measure-Object -Line).Lines`, so ~78 lines of headroom).
- ADR `docs/decisions/0007-*.md` exists recording the write-capable-subagent decision, its cost, and the guard that replaces read-only, and is listed in the docs/decisions/README.md Index — the link test proves the index link resolves.
- Request bookkeeping is consistent: PROJECT_SCOPE.md opens at `scoped · decided · next: plan`, FEATURE_REQUEST.md's Status blockquote is advanced, and the Index row in requests/feature-requests/README.md (line 92) matches — the mismatch class /update-docs exists to catch.
- If the acceptance-panel coverage enhancement is taken: `agents` appears in AREA_TO_SPEC (.claude/skills/implement-plan/acceptance_panel.js:202-206) and in the bucketing list in .claude/skills/implement-plan/SKILL.md Step 4, and both bundled guards still exit 0 — `node .claude/skills/implement-plan/tests/merge_fallback_guard.mjs` and `node .claude/skills/implement-plan/tests/verify_batching_guard.mjs`.
~~~

### core_scope

~~~
- `.claude/agents/data-engineer.md` — the agent definition: frontmatter (name, description, tool allowlist, model), the role framing (developer to the main thread's director), the bounded invariant set, the escalation policy for wrong or silent specs, the write allowlist, the git-read-only rule stated as an absolute with its recorded reason, and a pointer to its memory file. Written in house voice — the SKILL.md register: a 'What this produces and why' opener and a 'What good looks like' close.
- An explicit override preamble, because a subagent DOES inherit project CLAUDE.md (measured this run). The definition must say which inherited sections the agent ignores (intake conventions, pipeline stages, ADR index) and which it obeys absolutely (Data Layer, Constraints & Gotchas) — narrowness achieved by instruction, since it cannot be achieved by omission.
- `.claude/agents/data-engineer-memory.md` — a committed, agent-appendable memory file with a per-entry schema: id, date, epistemic label, the claim, the evidence pointer, and a routing tag (build-ergonomics vs docs-candidate). Seeded with real entries already earned by this repo so it is not a hollow schema on day one.
- The invariant-drift guard: invariants stated once as canonical text and mechanically proven identical across CLAUDE.md and the agent definition, with a negative control. This is the scope's answer to Open Question 2 — restate AND prove, rather than restate and hope or point and leak.
- The return contract as an enforced artifact: a fixed-section handoff report (built / verified-with-evidence / assumed / surprised-me / could-not-do / docs-delta / open questions), written to `requests/<track>-requests/<slug>/reviews/`, schema-linted by pytest, capped in length, and forbidden to carry diff hunks.
- The write-capable guard package: a declared write allowlist in the definition; a documented main-thread spawn protocol (pre-spawn snapshot of `git diff HEAD` to gitignored scratch plus the untracked list, mirroring .claude/skills/implement-plan/SKILL.md:120-127); and a post-run tree-integrity comparison whose output goes into the reviews/ trail.
- `.claude/agents/README.md` — what the directory is, what belongs in it, and the spawn protocol, so the directory documents itself the way each medallion layer does (a convention tests/test_repo_structure.py:77-84 already enforces for dbt layers).
- The proving run, two drills: A) a faithful spec, B) the omission drill with the grain invariant deliberately removed. Both build into a gitignored scratch dbt project under `var/` against committed fixtures — no pipeline artifact enters transform/ or src/. Both produce a scored artifact under reviews/.
- The pytest guard suite covering the above (frontmatter, invariant drift, memory budget, memory schema and routing, handoff schema), each with a negative control so no guard can pass vacuously.
- Doc updates: CLAUDE.md project map plus a clarifying half-sentence on the subagent rule (git stays read-only; a designated builder may edit tracked files); ADR 0007; the Index row and Status blockquotes.
~~~

### enhancements

~~~
title: Negative controls for every new guard
rationale: tests/test_doc_links.py:95-104 already encodes the lesson that a checker scanning nothing passes every time — MUST_COVER plus MIN_EXPECTED_FILES exist for exactly that reason. Every guard this feature adds should carry the same anti-vacuity proof, or the feature ships a green suite that proves nothing about the agent.
cost: cheap

title: Guards in pytest, not in a .mjs sibling
rationale: Measured: .github/workflows/ci.yml runs three jobs (python, dbt, secrets) and no Node step, so the existing .claude/skills/**/tests/*.mjs guards are only ever run when an agent remembers to. Putting the agent's guards under tests/ makes them a required check via ops/branch-protection.json's 'Lint, types, tests' context — enforcement instead of etiquette. Cost: new test code must pass mypy strict (pyproject.toml:70-74).
cost: cheap

title: Memory entries carry the repo's epistemic vocabulary
rationale: CLAUDE.md already demands measured/verified/inferred/assumed/unconfirmed be treated as different claims, and docs/data-sources.md:5-10 models the pattern. A memory entry labeled 'assumed' with no evidence pointer is a task, not a fact — and labeling it makes the deferred curation protocol designable against evidence rather than against speculation.
cost: cheap

title: Mechanical memory-vs-docs routing guard
rationale: Answers Open Question 5 without building the curation protocol: an entry tagged as a domain/data fact fails the test red and names docs/data-sources.md. This closes the drift route the request itself identifies — the repo holding two answers while /update-docs only checks one.
cost: cheap

title: Memory line budget mirroring CLAUDE.md's 200-line precedent
rationale: The precedent is explicit at .claude/skills/update-docs/SKILL.md:76-79 ('over budget means cutting, not reformatting'). Reusing it — with a smaller number, since memory is read alongside the definition — bounds the file before it needs curation, which is the deferred piece.
cost: cheap

title: Seed memory with 4-6 entries the repo has already earned
rationale: A memory file that ships empty is a schema nobody fills in — the exact failure the request names when deferring curation. Real seeds available today, each traceable: PowerShell 5.1 Set-Content/Out-File mangle UTF-8, use the file tools (implement-plan/SKILL.md:111-112); a subagent DOES inherit project CLAUDE.md (measured this run); the bundled .mjs skill guards are not run by CI (ci.yml); sqlfluff errors on an empty model selection, hence the guard at ci.yml:78-85.
cost: cheap

title: Handoff report as a durable reviews/ artifact, not just a final message
rationale: A message in a transcript dies with the session; a file under reviews/ joins the provenance trail the pipeline already keeps (requests/feature-requests/README.md:72). It also makes the return contract greppable — which is what turns 'is the contract enforced?' (Open Question 7) into a test rather than a hope.
cost: cheap

title: Ban diff hunks in the handoff and cap its length
rationale: The request's core complaint is that a file-by-file narration reconstitutes the detail isolation was meant to avoid. A grep for ^@@ / ^+++ plus a line cap makes 'the main thread did not have to read every edit' objectively checkable rather than a feeling.
cost: cheap

title: The omission drill as a designed experiment
rationale: Directly tests the request's fourth observable signal (FEATURE_REQUEST.md:46-47) and Open Question 8. Handing the agent a spec that deliberately omits 'declare the grain and prove it' is the only way to learn whether the invariant set is load-bearing or decorative — and a failure here is cheap now and expensive after box-score-foundation. Grows the build: it needs a scratch dbt project, a fixture, and a scoring rubric.
cost: grows-build

title: Run each drill more than once
rationale: Agent behavior is nondeterministic; a single green run is one observation, not a property. Two or three runs per drill, with the outcomes recorded honestly (including a split result), is the difference between 'the design holds' and 'it held once'. If the user declines, the scope should label the evidence as a single observation rather than a proof.
cost: grows-build

title: A reusable snapshot + tree-integrity script under ops/
rationale: Today the snapshot protocol exists only as prose inside .claude/skills/implement-plan/SKILL.md:120-127, re-typed by whoever remembers. Making it an executable that any future write-capable agent's spawner can call — record status/untracked/HEAD/stash before, diff after, report out-of-allowlist writes and deletions — turns the scar tissue into a tool. ops/ is already 'repo governance as code'.
cost: grows-build

title: Spec-triage (dry-run) mode
rationale: One paragraph in the definition plus a documented invocation phrase buys a pre-flight: the agent reads the plan, reports gaps against its invariant set, and builds nothing. It makes a bad plan cheap to discover and gives the main thread a use for the agent before it trusts it with writes.
cost: cheap

title: Three-way escalation policy for bad specs
rationale: Answers Open Question 8 precisely instead of generally: a spec that CONTRADICTS an invariant stops the agent with a spec-gap report; a spec SILENT on an invariant is built to the invariant and flagged; an AMBIGUOUS requirement is built at the smaller interpretation and flagged. All three are observable in the handoff, so the policy is testable.
cost: cheap

title: Track-agnostic by construction
rationale: /implement-plan already serves both the feature and bugfix tracks, auto-detecting from the artifact path (implement-plan/SKILL.md:49-53). An agent whose return contract assumes 'feature' will need reworking the first time a bug is handed to it; a track field costs a line now.
cost: cheap

title: Separable extraction vs dbt rulebook sections
rationale: Open Question 9 asks whether one agent is the right granularity. Rather than deciding it prematurely, structure the invariant set so the extraction rules and the modeling rules are self-contained sections — then a later split is a copy, not a rewrite.
cost: cheap

title: Teach the acceptance panel about .claude/agents/
rationale: Grounded gap: AREA_TO_SPEC at .claude/skills/implement-plan/acceptance_panel.js:202-206 maps skills to the skill-quality specialist, but has no key for agents, and the bucketing list in SKILL.md Step 4 names .claude/skills/ only. So a future change to an agent definition would be reviewed by the core four with no specialist lens. Adding an `agents` bucket (reusing skill-quality, or a new agent-quality mandate covering frontmatter, invariant drift, memory budget, and the write allowlist) closes it — but it edits panel JS covered by two guards, so both must stay green.
cost: grows-build

title: Promotion queue surfaced in the handoff
rationale: The mechanical half of the deferred curation protocol: memory entries tagged docs-candidate are listed in the handoff's docs-delta section, so /update-docs sees them through the normal gate without the agent ever editing docs/data-sources.md. Keeps the deferral intact while preventing the drift the deferral risks.
cost: cheap

title: A purpose-built CLAUDE.md-inheritance probe, recorded
rationale: Open Question 1 is answered measured-in-passing by this scoping run, which is weaker than a deliberate test. A one-minute probe agent that reports whether it received CLAUDE.md, with the result written into memory with its date and label, converts an incidental observation into a citable one — and it is the cheapest possible first exercise of the memory file.
cost: cheap

title: CLAUDE.md convention clarification on subagent writes
rationale: The current bullet reads 'Subagents get read-only git', which is true and, after this feature, easy to misread as 'subagents may not write'. A clarifying half-sentence (git read-only for all; a designated builder agent may edit tracked files, and /commit remains the only committer) prevents a future agent from refusing a legitimate instruction — and keeps the invariant-drift guard's two copies genuinely identical.
cost: cheap

title: DEFERRED / needs the user's call: the /update-docs memory-coherence check
rationale: Adding a memory-vs-docs coherence check to /update-docs is the natural home for the judgment half of curation — but the request explicitly puts it out of scope (FEATURE_REQUEST.md:88-90), so folding it in silently would be exactly the laundered greed the pipeline forbids. Surfaced as a gated decision, recommended deferred until real entries exist.
cost: grows-build

title: DEFERRED / needs the user's call: feed the handoff into stage 4, then wire the agent as its build step
rationale: Open Question 4 notes that arm's-length building inverts the usual asymmetry — the reviewer now has less context than the author. Passing the handoff report into the acceptance panel's context restores some of it, and is a much smaller step than making the agent stage 4's builder. Both are explicitly out of scope for this request; naming the sequencing now keeps it from being rediscovered.
cost: grows-build
~~~

### risks

~~~
- Narrowness is not achievable by omission. Measured this run: a Task-spawned subagent receives the full project CLAUDE.md as a system-reminder. So the manager/developer seam has to be enforced by explicit override text, and the inherited context still costs tokens on every spawn. If the definition's override is weak, the agent is a normal agent with extra steps.
- Instructions are not enforcement, and the substitute guard is detection, not prevention. The scar at .claude/skills/implement-plan/SKILL.md:120-127 (a write-capable agent ran git checkout and silently wiped uncommitted work while a vacuous selftest passed green) is exactly the failure mode being re-admitted. Snapshot + integrity check catches it after the fact; nothing stops it. This is the single most consequential risk and the ADR should say so plainly.
- The invariant-drift guard adds friction to ordinary CLAUDE.md editing: any wording change to an invariant clause turns CI red until the agent definition is updated in the same commit. That is the point, but it is a real cost and the failure message must say what to do — the same trap ops/branch-protection.json documents for renamed CI jobs.
- Memory is a knowledge store outside the doc gate. Until the curation protocol lands, it can accumulate stale, wrong, or duplicative entries, and a wrong entry read as authoritative is worse than no entry — the correctness framing update-docs/SKILL.md:28-31 uses for doc drift applies here.
- The repo is public (ADR 0006). A committed memory file is published, and an agent appending freely could paste an account ID, a bucket name, or a path with a username. gitleaks (ci.yml:87-99) and /commit's refusal list are the backstops, but the memory file is a new surface for the one careless paste ADR 0006:48-49 names.
- Proving-run evidence is inherently weak: agent behavior varies run to run, so a single passing drill proves less than it appears to. Honest labeling (single observation) or repeated runs is the only fix; a scope that claims 'the design holds' off one green run is overclaiming.
- Scope leakage into pipeline work. The proving runs need something to build. If the drills are wired to box-score-foundation (which is at intake, unscoped — Index row 91), this feature inherits an unscoped dependency and may quietly start settling dataset contracts that belong to that request. Building into a gitignored scratch project under var/ against committed fixtures is the containment.
- Two-guard blast radius on the panel enhancement: .claude/skills/implement-plan/acceptance_panel.js is covered by merge_fallback_guard.mjs and verify_batching_guard.mjs, neither of which CI runs. Editing AREA_TO_SPEC without running both by hand is an easy silent regression.
- Tool-allowlist calibration is a genuine unknown. Denying Bash makes the agent unable to verify its own work by execution — the standard this repo holds every reviewer to (acceptance_panel.js:161-163). Allowing Bash re-admits arbitrary git. The allowlist has to permit uv run pytest / ruff / mypy / dbt against the ci and local targets while excluding every tree-mutating git subcommand, and no mechanism in the harness enforces that beyond instruction.
- Adjacent drift found while grounding, not this feature's job: tests/fixtures/README.md:12-13 tells the reader to 'capture them with the recorder', and no recorder exists (src/nba_platform/ contains only __init__.py). Worth its own request; noted here so it is not silently absorbed into the proving run.
~~~

### open_questions

~~~
- Restate-and-prove, or extract the invariants to a third file both CLAUDE.md and the agent read? This scope recommends restate-and-prove (a verbatim drift guard) because it leaves CLAUDE.md's readability intact and costs one test; extraction is cleaner in principle but fragments the rules a human onboards from. The user should dispose it — it is the scope's most structural call.
- Does the agent get Bash, and with what allowlist? Recommendation: yes, restricted to uv run pytest / ruff / mypy / dbt (--target ci or local only) and read-only git, mirroring the READONLY constant's structure at acceptance_panel.js:163 but inverted for a builder. Denying Bash outright would make it the only actor in this repo that cannot verify its own work.
- What is the memory line budget, and is 200 (CLAUDE.md's number, enforced at update-docs/SKILL.md:76-79) the right reuse or a lazy one? Memory is read alongside the definition, so the pair's combined size is the number that matters.
- How many proving-run repetitions before the design is called proven — one, two, or three per drill? This directly sets how strongly the acceptance ledger may be worded.
- What does the agent do when it discovers a data fact (e.g. the actual leaguegamelog response shape)? This scope says: never edit docs/data-sources.md; emit it in the handoff's docs-delta and let the main thread route it through /update-docs. Confirm that is the intended division, since it means a verified endpoint fact sits in a handoff artifact until a human moves it.
- Should the proving-run target be a synthetic scratch build (containment, recommended) or a genuinely useful small artifact such as the missing fixture recorder (real value, but network-touching and it starts settling extraction decisions that belong to box-score-foundation)?
- Does the write allowlist include `.claude/agents/data-engineer-memory.md` only, or the definition too? Letting the agent edit its own definition is a self-modification path the request does not ask for; recommendation is memory-only, definition human-maintained, as the request frames it (FEATURE_REQUEST.md:53-58).
- Is the handoff report committed as part of the feature's reviews/ trail, or is it scratch? Committed matches the pipeline's provenance habit; scratch keeps the repo smaller. Recommendation: committed, since it is the evidence the acceptance criteria are scored against.
~~~

---

## Scoper: minimalist  (ok: True)

### fit

~~~
verdict: reshape
rationale: The FORM fits and the TIMING does not. Form: process tooling sits squarely in ADR 0001's turned-all-the-way-up category (`docs/decisions/0001-deliberate-over-engineering.md:27-31` — testing, CI/CD, governance, documentation, incident process are free of scale and are what gets evaluated), and this repo already invests heavily there: eight committed `SKILL.md` files, three deterministic panel scripts, five guard tests under `.claude/skills/*/tests/`. An agent definition is more of the same and is not overkill by this repo's standard. Timing: the problem being solved has not happened yet, and the request says so — `FEATURE_REQUEST.md:16` reads 'This is not yet acute, because there is no pipeline code.' Measured against the repo: `src/nba_platform/` contains only `__init__.py`, `transform/models/` holds three layer READMEs and no models, and the whole history is three Phase-0 commits. No feature has EVER been implemented through `/implement-plan` here. The claim that one context ends up holding the scoping rationale, the plan, every edit, the test output and the panel findings is INFERRED from reading the skill, not MEASURED from a run — and ADR 0001 names precisely this hazard: 'The failure mode is picking the wrong thing to inflate' (`:18`), and lists 'the temptation to over-process is a standing risk' as an accepted cost (`:47-49`). The reshape is narrow and does not fight the request. Build the definition and the memory file — both cheap, both durable, both useful the moment the first real build happens. Add ONE thing the request omits: a mechanical guard test, so the invariants and the budget are checked rather than trusted, which is what makes the acceptance criteria testable in this repo's sense. CUT the coupling of the proving run to `box-score-foundation`. That coupling is the single riskiest line in the request (`FEATURE_REQUEST.md:124-126`): it points the repo's first, unproven, write-capable subagent at the dimensional core, which `transform/models/silver/README.md:5-7` states plainly is 'the most expensive mistake available in this project' and the reason silver goes through the full scoping panel. Proving an unproven tool on the least reversible work in the repo is exactly backwards, and it is free to fix — prove it on something small first. One further note for the merge: this feature touches NO dataset (`FEATURE_REQUEST.md:107` says so, and it is accurate — nothing here reads an endpoint, lands a payload, or defines a model). The five dataset contracts — grain, keys, era coverage, update semantics, extraction cost — do not bind and must not be invented for it. The only data-adjacent surface is the memory-versus-`docs/data-sources.md` boundary, handled in Core by a single rule rather than a protocol.
~~~

### goals

~~~
- Ship one agent definition under `.claude/agents/` that carries the developer-role framing, the return contract, and the guardrails — and that a fresh main thread can spawn without the author present.
- Ship one committed, bounded memory file the agent may append to, with a stated entry format and an explicit cap, seeded with the format rather than with invented entries.
- Make the guardrails and the budget MECHANICALLY checked, not merely written down, via one small structural test — because every other guard in this feature is instruction, and this repo has a recorded scar proving instructions are not enforcement (`.claude/skills/implement-plan/SKILL.md:120-126`).
- Close the memory-versus-docs drift hole with one rule rather than a promotion protocol, so `docs/data-sources.md` remains the single home for anything an analyst's answer depends on.
- Prove the design once, on a small reversible task, and record honestly whether the return contract survived contact — including the possibility that it did not.
~~~

### non_goals

~~~
- NOT rewiring `/implement-plan`. Stage 4 keeps building exactly as it does today (`.claude/skills/implement-plan/SKILL.md:85-116`). The agent stands alone.
- NOT using `box-score-foundation` as the proving run. Explicitly reversing the request's suggestion at `FEATURE_REQUEST.md:124-126`, for the reason in the fit verdict.
- NOT building a curation protocol, pruning rules, promotion machinery, or a `/update-docs` coherence check over memory. Deferred until real entries exist.
- NOT enforcing the return contract with a schema, a wrapper, or anti-stub retry machinery. Prose sections for v1.
- NOT a second specialist agent, and NOT splitting extraction from dbt modeling. One definition, one memory file.
- NOT granting the agent any working-tree-mutating git, and NOT letting it commit, merge, push, or amend. `/commit` stays the only sanctioned committer (`CLAUDE.md:66-72`).
- NOT letting the agent invoke `/scope-feature`, `/create-implementation-plan`, or `/implement-plan`. Those spawn their own panels and nesting them is a cost multiplier with no return.
- NOT restating `CLAUDE.md`'s data-layer rules as a second authoritative copy inside the definition. A one-line reminder plus a pointer, following the shape `scope_panel.js:124` already uses.
- NOT writing any pipeline code, dbt model, extraction client, or fixture. This request touches no data.
- NOT changing `.claude/skills/scope-feature/scope_panel.js`, `.claude/skills/implement-plan/acceptance_panel.js`, or their guard tests. They do not consume `.claude/agents/` and do not need to.
~~~

### acceptance_criteria

~~~
- MECHANICAL — `uv run pytest tests/test_repo_structure.py -q` is green with a new structural test asserting: `.claude/agents/` exists, contains exactly one `*.md` agent definition, and that file opens with YAML frontmatter carrying a non-empty `name` and `description` (mirroring the shape all eight committed `SKILL.md` files use).
- MECHANICAL — the same test file asserts the agent definition contains the literal guardrail strings for read-only git and for never commit/merge/push/amend. A substring assertion is enough; its job is to fail loudly if a future edit silently deletes the guardrail, not to interpret it.
- MECHANICAL — the same test file asserts the memory file exists, is referenced by path from the agent definition, and is at or under its declared line cap. Enforced as a test, not as prose: `CLAUDE.md`'s own 200-line budget is enforced only by a human-run one-liner (`.claude/skills/update-docs/SKILL.md:76-79`), and a budget nobody runs is not a budget.
- MECHANICAL — `uv run pytest tests/test_doc_links.py -q` is green. This is not a formality: `tests/test_doc_links.py:31-48` excludes by directory name and `.claude` is not in `EXCLUDED_PARTS`, so both new files are link-checked automatically, and `test_the_guard_actually_covers_the_repo` (`tests/test_doc_links.py:95-104`) proves they were actually scanned rather than silently skipped.
- MECHANICAL — `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy` are green, since the new test module runs under the same CI gates as everything else (`.github/workflows/ci.yml:41-48`).
- MECHANICAL — `CLAUDE.md` stays under 200 lines after the project-map row for `.claude/agents/` is added. Measured today: 122 lines, so there are 78 lines of headroom and this criterion is expected to pass trivially — it is stated so the budget claim is checked rather than assumed.
- USER-RUN (marked per `requests/feature-requests/README.md:56-59`) — the proving run: the user spawns the agent on the designated low-stakes task with a clean working tree, and the return it produces contains all four contract sections (what it built / verified vs assumed / surprises worth remembering / what it could not do) with no file-by-file diff narration. A human reads and judges this; no command proves it.
- USER-RUN — after the proving run, `git status --porcelain` shows only files the agent was asked to touch, and nothing that existed before the spawn was reverted. This is the tree-integrity re-check that `.claude/skills/implement-plan/SKILL.md:187-190` already specifies for read-only reviewers, applied unchanged to a write-capable builder.
- USER-RUN — a `/commit` run over the proving-run diff stages the memory delta as a visible per-path entry. This is the actual review gate the request relies on (`FEATURE_REQUEST.md:140`), and confirming it behaves as assumed is worth one observation.
~~~

### core_scope

~~~
- One agent definition file under `.claude/agents/` — role framing (developer to the main thread's manager), the return contract as named prose sections, the guardrails (git read-only; never commit/merge/push/amend; no invoking pipeline skills), and a POINTER to `CLAUDE.md` for the data-layer rules rather than a second authoritative copy of them.
- One memory file, committed, pointed at from the definition, with a declared line cap and a stated entry format. It ships with the format and zero or one real entries — seeding it with invented gotchas is the failure the request itself diagnoses one paragraph before proposing the file.
- A one-line rule in the definition closing the memory-versus-docs hole without building a promotion protocol: domain and data facts never enter memory; they are reported in the return contract's verified-vs-assumed section and left for the main thread, which owns `/update-docs`. This is the cheapest possible closure of open question 5 and adds no machinery.
- A memory-entry convention that paths are cited as inline code, never as `[text](path)` markdown links. Grounded, not stylistic: `tests/test_doc_links.py:72-91` checks only markdown-link syntax, so backticked paths are invisible to it while a link to a file that later moves turns CI red on an unrelated PR.
- One new structural test module (or additions to `tests/test_repo_structure.py`, which already exists to assert config-and-filesystem agreement) carrying the mechanical acceptance criteria. Roughly ten assertions; this is the only new code in the build.
- One `CLAUDE.md` project-map row for `.claude/agents/`, plus one sentence distinguishing read-only-GIT (universal, `CLAUDE.md:73`) from write-to-FILES (this agent only). Measured: `CLAUDE.md` is 122 lines against a 200-line budget, so the request's worry that this will not fit is unfounded.
- One proving run against a small, reversible, already-decided task — explicitly NOT `box-score-foundation`.
~~~

### enhancements

~~~
title: Verify the spawn mechanism and the `.claude/agents/` frontmatter schema BEFORE writing either file
rationale: This is a de-risking step, not an enhancement, and it is the cheapest thing in the whole scope. The repo's existing multi-agent machinery does not consume `.claude/agents/` at all: `scope_panel.js:95-115` and `:174` spawn agents as `agent(prompt, {label, phase, schema, effort})` — a prompt-and-schema call with no agent-type parameter. So the definition is only reachable from whatever the main thread's own spawn path is, and that path is `unconfirmed` here. Frontmatter is likewise `unconfirmed`: the eight committed files use `name` + `description`, but that is the SKILL format, and an agent definition may take a tools or model field instead. There is also no `.claude/settings.json` in this repo (confirmed against `git ls-files`), so there is currently no committed place to declare per-agent tool permissions. Writing a definition that nothing loads is the most likely way this feature ships broken.
cost: cheap

title: Give the agent Bash but no working-tree-mutating git, and require the main thread to snapshot before spawning
rationale: Near-decided rather than optional. Without Bash the agent cannot run `uv run pytest` or `uv run dbt build`, cannot self-verify, and hands every verification back to the main thread — which reconstitutes exactly the detail the isolation exists to avoid. Granting Bash means the recorded scar applies in full (`.claude/skills/implement-plan/SKILL.md:120-126`: a write-capable agent once ran `git checkout` and wiped uncommitted work while a vacuous selftest passed green). The mitigation already exists and costs nothing new — reuse stage 4's exact procedure verbatim: snapshot the diff to gitignored scratch, work on a branch, re-check tree integrity after. Do not invent a second mechanism.
cost: cheap

title: Require a clean tree, or a tree containing only the agent's own prior work, before spawning
rationale: The one genuinely NEW guard worth adding, and it is a sentence. Every existing guard here is instruction rather than enforcement; the real net is `/commit`'s per-path staging (`.claude/skills/commit/SKILL.md:47-67`). That net only works if a human can tell the agent's writes from their own in the staged diff. Spawning a write-capable builder onto a dirty tree destroys that distinction, and it is the specific way this feature could lose work without any subagent doing anything forbidden.
cost: cheap

title: Commit the memory file rather than gitignoring it
rationale: Recommended as decided, not gated, on a concrete asymmetry. `tests/test_doc_links.py:60-65` walks by directory name and is not gitignore-aware, so a gitignored `.claude/agents/` memory file is still scanned locally while being invisible to CI. A bad link in it would fail `uv run pytest tests/test_doc_links.py -q` — the exact command `/update-docs` Step 1 runs (`.claude/skills/update-docs/SKILL.md:53-58`) — while CI stays green. Local-red plus CI-green is the worst of both. Committing also delivers the reviewability the request is counting on.
cost: cheap

title: A schema-enforced or wrapper-validated return contract
rationale: Argue AGAINST for v1. Enforcement here means either a StructuredOutput schema or a validating wrapper, and this repo already knows what that costs: `scope_panel.js:27` records that structured agents intermittently degenerate into placeholders, and the entire `ANTISTUB_RETRY` / `runChecked` / `safeAgent` apparatus (`:95-115`) exists to survive it. Building anti-stub machinery for one agent that has never returned once is premature. Prose sections plus a main thread that re-asks on a non-conforming return is the v1. Revisit only after a real return has actually degenerated.
cost: grows-build

title: Wiring the agent into `/implement-plan` as its build step
rationale: Already out per the request, and it should stay out — but the deferral has an unnamed consequence that belongs in the scope. Stage 4's acceptance panel is what currently catches the narrow-developer failure mode: `.claude/skills/implement-plan/SKILL.md:104-105` treats a silver model whose declared grain has no test as a blocker. A v1 agent spawned OUTSIDE stage 4 is therefore outside the only mechanism that catches exactly the mistake open question 8 worries about. That is not a reason to rewire stage 4 now; it is a reason the proving run must be low-stakes.
cost: grows-build

title: Splitting into separate extraction and dbt-modeling agents
rationale: Defer outright, and say so in one line rather than designing for it. The request's own reasoning is correct — splitting later is cheap. One definition, one memory file. A second agent before the first has run once is speculation compounding speculation.
cost: grows-build

title: A `/update-docs` coherence check over the memory file
rationale: Correctly deferred by the request; keep it deferred. Pruning rules and promotion criteria designed against zero entries produce a schema nobody fills in — the request makes this argument itself and it applies with equal force to any gate written now. The domain-facts-never-enter-memory rule in Core is the minimum needed to stop drift in the meantime.
cost: grows-build
~~~

### risks

~~~
- PREMISE RISK, the largest one: the problem is inferred, not observed. Measured — `src/nba_platform/` holds only `__init__.py`, `transform/models/` holds three READMEs and no models, and the repo's entire history is three Phase-0 commits. `/implement-plan` has never run here. If the first real stage-4 run turns out to fit comfortably in one context, this agent is pure maintenance burden. Mitigation is to keep the build genuinely small, which is what this scope argues for.
- DRIFT RISK: two statements of one rule. Directly relevant evidence — I am myself a subagent spawned by `scope_panel.js`, and I received the full project `CLAUDE.md` in my context as a system-reminder at spawn, unrequested. That is MEASURED for this spawn path. Whether a `.claude/agents/`-defined subagent inherits identically is `unconfirmed` (different spawn path), but the evidence points at inheritance, which makes restating the data-layer rules in the definition a guaranteed second copy. Note the existing precedent cuts the same way: `scope_panel.js:124` restates a compressed rule set inline DESPITE inheritance, but as a one-line pointer-shaped reminder, never as authoritative text. Copy that shape.
- CI RISK, concrete: `tests/test_doc_links.py` scans every Markdown file outside `EXCLUDED_PARTS` (`:31-48`, `:60-65`), and `.claude` is not excluded — so a committed memory file is link-checked in CI (`.github/workflows/ci.yml:50-53`). An agent appending an entry with a `[text](path)` pointer to a file that later moves turns CI red on an unrelated PR, with a confusing failure. Fully avoided by the inline-code convention in Core; unavoidable without it.
- LOCAL/CI ASYMMETRY RISK: if the memory file is gitignored instead, `test_doc_links.py`'s directory-name exclusion is not gitignore-aware, so it is still walked locally. A bad link then fails `uv run pytest tests/test_doc_links.py -q` — the exact command `/update-docs` Step 1 runs — while CI stays green. Argues for committing.
- PUBLIC-REPO RISK: ADR 0006 makes the repo public from the first commit and names 'one careless paste of a connection string is a real incident, not a hypothetical one' as an accepted ongoing cost (`docs/decisions/0006-public-repository.md:48-49`). A free-text file an agent appends to is exactly the surface `/commit`'s per-path refusal list (`.claude/skills/commit/SKILL.md:55-67`) and gitleaks are weakest against, because the content is prose rather than a recognizable credential file.
- VERIFICATION-GAP RISK the request does not name: `/implement-plan`'s acceptance panel is what currently catches a silver model whose declared grain has no uniqueness test — it treats that as a blocker (`.claude/skills/implement-plan/SKILL.md:104-105`). Because this request deliberately does NOT rewire stage 4, a v1 agent spawned outside stage 4 is outside the only mechanism that catches exactly the failure open question 8 fears. The narrow-developer risk is therefore real AND currently unguarded except by prose in the definition.
- WORK-LOSS RISK: the recorded scar (`.claude/skills/implement-plan/SKILL.md:120-126`) is a write-capable agent running `git checkout` and silently wiping uncommitted work while a vacuous selftest passed green. A builder with Bash reopens it. Every mitigation available — snapshot to gitignored scratch, feature branch, post-hoc integrity check — is instruction, not enforcement. The genuinely new exposure is spawning onto a dirty tree, where a human can no longer separate the agent's writes from their own in the staged diff.
- DEAD-ARTIFACT RISK: the definition may be written in a format nothing loads. `scope_panel.js:95-115` and `:174` show the repo's own machinery spawns by prompt with no agent-type hook, and no `.claude/settings.json` exists. If the frontmatter or the spawn path is wrong, the feature ships two Markdown files, a passing test suite, and zero working capability — and the mechanical acceptance criteria would all still be green, because they check shape rather than behavior. This is why the proving run is core and cannot be dropped to save time.
- BLAST-RADIUS RISK if the proving run stays coupled to `box-score-foundation`: that request lands an extraction client, a landing-zone writer, a config layer, bronze models, and five silver models including SCD2 affiliation. `transform/models/silver/README.md:5-7` states getting silver wrong is the most expensive mistake available in this project. An unproven builder is the wrong instrument for it.
- HONEST LIMIT on acceptance: the request's actual claim — that arm's-length implementation preserves the main thread's strategic capacity — is not machine-checkable by anything in this repo. Six criteria here are mechanical and check SHAPE; three are user-run and check BEHAVIOR. A green `pytest` run proves the files exist and are well-formed, and proves nothing about whether the design holds. Stating this plainly is better than manufacturing a criterion that pretends otherwise.
~~~

### open_questions

~~~
- BLOCKING, and answerable in minutes: what actually loads a `.claude/agents/*.md` definition on this harness, and what frontmatter schema does it take? The repo's own panels spawn via `agent(prompt, {label, phase, schema, effort})` (`scope_panel.js:174`) with no agent-type parameter, so the existing machinery is not the consumer. The eight committed files use `name` + `description` frontmatter, but that is the SKILL format. `unconfirmed`. Verify before writing either file.
- Where are the agent's tool permissions declared — frontmatter, or `.claude/settings.json`? There is no `.claude/settings.json` in this repo (checked against `git ls-files`), so if the guardrail 'Bash yes, git-write no' is meant to be anything stronger than a sentence in the prompt, the mechanism for expressing it is currently unknown. `unconfirmed`.
- Does the first write-capable subagent warrant an ADR? `.claude/skills/update-docs/SKILL.md:100-101` says a new decision someone would reasonably ask 'why did you do it that way' about is a missing ADR, and this qualifies. Against: it is a clarification of `CLAUDE.md:73` (which governs GIT, not file writes), not a reversal of an accepted decision, so nothing needs superseding. ADRs are cheap here and the repo likes them. User's call.
- What is the proving-run task, concretely? It needs to be small, reversible, already decided, and to exercise at least one real convention so the run is not vacuous. Naming it is part of disposing this scope — 'a small task' is not a target.
- What line cap for the memory file? The 200-line `CLAUDE.md` precedent (`.claude/skills/update-docs/SKILL.md:76-79`) is available to reuse or consciously reject. Recommendation is to go smaller — memory is read on every implementation task and its value density is lower than the project map's — but the number is the user's.
- Does the agent push back on a wrong spec, build-and-flag, or build silently (the request's open question 8)? Recommendation: build-and-flag, reported in the return contract's 'what I could not do' section, because a narrow developer that argues with its spec is no longer narrow. Worth an explicit decision rather than a default, since it is the behavior most likely to matter on the first real build.
~~~

