> **Status:** plan · created 2026-08-14 · decided · next: implement

# Implementation Plan — Data-Engineer Agent

> **One-line goal:** stand up `.claude/agents/` holding the repo's first write-capable
> implementation subagent — one definition, one committed memory file, one README — move the granular
> build rulebook out of `CLAUDE.md` into that definition, enforce every clause with pytest guards, and
> prove the design twice. · **Target component:** `.claude/agents/` (new), `tests/` (new guards),
> `CLAUDE.md` (the cut), two skill bucket lists, ADR 0007.

**This is tooling, not pipeline.** No dataset is landed, no dbt model is written, no extraction client
is added. `src/nba_platform/` still holds only `__init__.py` and `transform/models/` still holds three
layer READMEs and zero `.sql` when this ships. The five dataset contracts — grain, keys, era coverage,
update semantics, extraction cost — **do not bind and must not be manufactured**, which is why this
plan carries no data-contracts section.

---

## 1. Onboarding — read these first

The upstream artifact is **decided**. Consume it; do not re-open it.

| Path | Why |
|---|---|
| [`PROJECT_SCOPE.md`](PROJECT_SCOPE.md) | The contract. 16 acceptance criteria (`:120-157`), the tiered Core scope (`:159-211`), Decisions 1–11 (`:367-427`), the two post-panel amendments (`:428-490` — the exact rulebook cut is at `:444-448`), and the six adopted blocker fixes (`:492-509`). |
| [`FEATURE_REQUEST.md`](FEATURE_REQUEST.md) | Context only. `:35-37` is the core complaint the diff-hunk ban targets; `:46-47` is the observable signal the omission drill measures. |
| `.claude/skills/implement-plan/SKILL.md` | **Read first.** Closest prior art and the source of the central tension. `:100-112` the invariant restatement; `:111-112` the PowerShell UTF-8 trap (a seeded memory entry); `:120-125` the pre-spawn snapshot **and the recorded scar**; `:127-132` the bucket list; `:155-156` the read-only-subagents rule this feature carves a guarded exception to; `:187-190` the post-run integrity re-check. |
| [`CLAUDE.md`](../../../CLAUDE.md) | The file this change edits most invasively — 140 physical lines. `:16-33` project map; `:52-59` era boundaries (Key Context); `:73-75` the subagent bullet needing clarification; `:76-79` the five epistemic labels; `:84-103` the Data Layer section that **moves**; `:105-126` Constraints & Gotchas, of which four bullets move and three stay. |
| `tests/test_repo_structure.py` | The idiom every new guard copies. Docstring `:1-9`; `REPO_ROOT = Path(__file__).resolve().parents[1]` at `:19`; `yaml` already imported at `:17`; the `isinstance` narrowing at `:25-26` that satisfies mypy strict; `test_every_layer_documents_itself` at `:77-84` is the structural analogue AC1 names. |
| `tests/test_doc_links.py` | Both a free win and a trap. `EXCLUDED_PARTS` (`:31-48`) has no `.claude` entry, so all three new files are link-checked automatically; `MIN_EXPECTED_FILES = 20` (`:53`) against 33 tracked `.md` today; `FENCED_BLOCK` (`:55`, applied at `:69`) strips fenced content — how to write a forward reference; `MARKDOWN_LINK` (`:56`) scans **only** `[text](<path>)` syntax, which is why memory paths stay inline code; targets resolve relative to each file's own parent (`:89`). |
| `.github/workflows/ci.yml` | Exactly three jobs and **no Node step** — `Lint, types, tests` (`:26-27`, steps `:41-53`), `dbt build` (`:55-56`, with `dbt deps` at `:70-71` and `dbt build` at `:76`), `Secret scan` (`:87-88`, gitleaks `:96-99`). This is why guards go under `tests/`. `:78-85` is the sqlfluff conditional — it errors on an empty model selection. |
| `pyproject.toml` | The real gates. ruff at line-length 100 selecting `E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF` (`:43-64`); `mypy strict = true` over `src` and `tests` (`:70-74`); pytest config and the `network` marker (`:77-82`); the `transform` group already provides dbt-core, dbt-duckdb, duckdb and sqlfluff (`:24-30`). |
| `.claude/skills/update-docs/SKILL.md` | The doc gate this change perturbs. `:47-48` the bucket list; `:53-57` the one mechanical check the gate owns; `:66-78` the CLAUDE.md checks and the 200-line budget one-liner this plan reconciles; `:100-101` the missing-ADR rule; `:103-112` the `docs/data-sources.md` label audit the routing rule must not route around; `:114-126` the grain-vs-test agreement rule the omission drill reuses. |
| `.claude/skills/commit/SKILL.md` | The review gate the whole design leans on, and the house voice. `:42-45` branch check; `:47-67` per-path staging and the refusal table; `:59` refuses anything under `var/`. |
| `transform/models/silver/README.md` | `:5-7` is the grounded reason the proving runs must not target the dimensional core; `:9-25` carries the worked declare-then-prove example the definition **points at** rather than paraphrasing. |

**Current state, measured 2026-08-14.** Branch `feature/data-engineer-agent`. `Test-Path .claude/agents`
is False. No `.claude/settings.json`. `git ls-files .claude` returns 16 paths, all under
`.claude/skills/**`. 33 tracked Markdown files. `CLAUDE.md` is 140 physical lines / 122 by
`Measure-Object -Line`. Root `README.md` is 117 lines and mentions neither `.claude` nor "skill".

---

## 2. Architecture map

Six seams, in the order the phases hit them.

**(a) Filesystem.** New `.claude/agents/` holding three Markdown files: the definition (frontmatter),
the memory file (no frontmatter), the README (no frontmatter).

**(b) Enforcement.** New pytest guards under `tests/`. They go there and not as `.mjs` siblings
because `ci.yml` has no Node step — the five existing `.claude/skills/**/tests/*.mjs` guards run only
when an agent remembers, while `ops/branch-protection.json:4` makes the pytest job a required context.
That is the difference between enforcement and etiquette.

**(c) Doc.** `CLAUDE.md` gains a `.claude/agents/` project-map row, a clarified subagent bullet, and a
pointer replacing the cut rulebook. The bucket lists in `implement-plan/SKILL.md` and
`update-docs/SKILL.md` gain an `agents` entry **carrying its own workaround** (see Decision 12).
`acceptance_panel.js` is **not** touched.

**(d) Decision record.** `docs/decisions/0007-*.md` with the five sections required by
`docs/decisions/README.md:19-25`, plus its Index row. Written **last**, because `:29-32` makes accepted
ADRs immutable — the Consequences section cannot be amended once the evidence arrives.

**(e) Spawn protocol.** Prose only. Reuses stage 4's procedure rather than inventing a second
mechanism. No new executable tooling.

**(f) Provenance.** `reviews/` gains `harness-probe.md`, `proving-run-a.md`, `proving-run-b.md`.
Evidence lands in **committed** `reviews/`, never only in gitignored `var/` — `/commit` refuses
anything under `var/` and CI never sees it (blocker fix F2).

### Two structural facts to settle before writing guards

**AC1's literal wording collides with the scope's own deliverables.** It says `.claude/agents/`
contains "exactly one `*.md` agent definition"; Core scope puts **three** `.md` files there. The guard
therefore discriminates by **frontmatter**: exactly one `*.md` opens with `---` and parses to a mapping
with non-empty `name` and `description`; the other two carry none, and the guard asserts that too.
**Discover by glob, never by hardcoded filename** — a rename must not turn the guard vacuous.

**The memory file lives under `.claude/`, which the sequel's dispatch rule treats as every agent's deny
prefix** (`PROJECT_SCOPE.md:478-482`). State the carve-out in the definition as an **exact path**,
never as a prefix rule, or the sequel's routing table has to special-case it.

### Resolve-by-name, applied honestly

`CLAUDE.md:86-88` forbids literal paths and `parents[N]` walks, but that rule targets the Python config
layer, which does not exist yet. Both existing test modules deliberately use
`REPO_ROOT = Path(__file__).resolve().parents[1]` (`tests/test_repo_structure.py:19`,
`tests/test_doc_links.py:27`). The new guards follow that established precedent — **say so in a
docstring** so a reviewer does not flag the repo's own idiom — and resolve everything below the root by
glob.

---

## 3. Phased implementation

Every phase ends green locally, then lands via `/commit`. **`/commit` is the only sanctioned
committer** — never `git commit` ad hoc, never merge, push, or amend.

**The standing local gate, matched to what CI actually runs** (`ci.yml:41-53`):

~~~
uv run ruff check
uv run ruff format --check
uv run mypy
uv run pytest -m "not network" -q
uv run pytest tests/test_doc_links.py -q
~~~

CI runs `ruff check --output-format=github` and
`pytest -m "not network" --cov=nba_platform --cov-report=term-missing`; the `-m "not network"`
selection is the part that matters locally, and omitting it is how a plan's "green" diverges from CI's.
`uv run dbt build --project-dir transform --profiles-dir transform --target ci` is required only in
**Phase 5** and **Phase 6**, where its job is to prove *nothing changed* — never to prove the models
are right, because there are none.

---

### Phase 0 — Harness probe · BLOCKING gate

**Goal.** Settle by measurement, before a line of the definition is written, what actually loads a
project `.claude/agents/*.md`, what frontmatter it accepts, where a machine-readable tool/write
allowlist can be declared, whether such a subagent inherits project `CLAUDE.md`, and whether it sees
project skills. This is AC9 and the dead-artifact risk (`PROJECT_SCOPE.md:277`).

**Steps.**

1. **Record the control.** `git branch --show-current` is `feature/data-engineer-agent` — never work on
   `main`, which is protected. Confirm the tree is clean **or holds only this feature's own request
   artifacts**: the stage-3 panel trail (`IMPLEMENTATION_PLAN.md`, `reviews/plan-proposals.md`,
   `reviews/plan-adversarial.md`) is untracked or newly committed as you start, so a bare "tree is
   clean" precondition is already false and would be waved through. Record `Test-Path .claude/agents`
   (False), `git ls-files .claude` (16 paths, all `.claude/skills/**`), and the absence of
   `.claude/settings.json`.
2. **Capture the green baseline** so later assertions are measured: the five gate commands above; both
   line counts for `CLAUDE.md` (`(Get-Content CLAUDE.md).Count` = 140 and
   `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` = 122); `git ls-files '*.md'` = 33.
3. **Interrogate the harness and paste the real output**, not a paraphrase: `claude --version` and
   `claude --help`. Quote both into the artifact. The finding is a **dated measurement**, not a
   standing fact. Do not treat an undocumented `claude agents` subcommand as go/no-go evidence — it is
   the background-agent manager, a different surface.
4. **Name the surface, then run the loader probe.** The concrete mechanism is the **subagent-spawn
   tool's `subagent_type` (agent-name) parameter** — that is what a project `.claude/agents/*.md`
   registers into, and it is the only spawn path available, since none of the three panel scripts has
   an agent-type hook (`scope_panel.js:174` spawns with `{label, phase, schema, effort}` only). Create
   a throwaway `.claude/agents/probe-canary.md` with minimal frontmatter (`name`, `description`) plus
   the speculative keys the design wants (`tools`, `allowed-tools`, `model`) and a body containing a
   **unique sentinel string**. Spawn by that agent type **through the same surface Phases 4–5 will
   use**, and record: the exact call, whether the type name resolved, and whether the sentinel came
   back. *The sentinel round-trip is the only evidence the body reached an agent rather than a name
   merely resolving.* Vary one frontmatter key at a time to learn which are accepted, rejected, or
   silently ignored — a rejection message is itself evidence worth quoting.
5. **Probe inheritance, skill visibility, and default tools** in the same run: have the probe agent
   report (a) whether it received project `CLAUDE.md` unrequested, quoting one distinctive line such as
   the tracking-boundary sentence at `CLAUDE.md:53-54`; (b) whether it can see project skills by name;
   (c) its default tool set. **The measured baseline for a different spawn path is recorded at
   `PROJECT_SCOPE.md:143`** — a panel-spawned subagent *does* inherit the full project `CLAUDE.md` as
   an unrequested system-reminder. That does not settle this path, but it is the prior.
6. **Probe tool permissions, not just write paths** (restoring Decision 3, `PROJECT_SCOPE.md:389-393`).
   Ask whether per-agent **tool** access is declarable — the agent needs restricted Bash to run
   `pytest`, `mypy` and `dbt build` on what it wrote. Without it, this is the only actor in the repo
   that cannot verify its own work, the return contract's "cite a command and its actual output"
   becomes impossible, and the isolation the feature exists to buy is undone.
7. **Probe directory hygiene**, because it decides file layout: place a second frontmatter-less
   `.claude/agents/probe-plain.md` and record whether the harness ignores it, warns, or registers a
   bogus agent. If stray non-agent Markdown breaks loading, the memory file and README **cannot** live
   in `.claude/agents/` and every path in this plan shifts.
8. **Probe where a write allowlist can be declared.** Prefer frontmatter if the probe accepts it.
   Otherwise a fenced list under a stable `## Write allowlist` heading in the definition body —
   parseable without harness support, and the form the sequel's dispatcher can read. Adopt a tracked
   `.claude/settings.json` **only** if the probe shows it is the only place permissions can live, and
   surface it to the user as a new tracked file needing its own deny-set entry and `/commit` review.
9. **Delete both canaries.** AC1 asserts exactly one definition; a lingering canary reddens the Phase 2
   guard. Deleting a file you created is a **filesystem** operation, not a git one — do not reach for
   `git clean`/`checkout`/`restore`.
10. **Write `reviews/harness-probe.md`**: a one-line PROCEED/STOP verdict at the top, the exact
    commands, the real output fenced, the harness version, and one epistemic label of `verified` or
    `measured` per answer — never `unconfirmed` (AC9). State plainly which questions the probe could
    **not** settle, and name the frontmatter schema AC1's guard will assert (blocker fix F3).
11. **Apply the two-stage decision rule** (blocker fix A2-02, `PROJECT_SCOPE.md:508-509`). A negative
    result is **provisional**, not final, because there are two distinct ways to come back negative:
    (a) the harness does not support project `.claude/agents/*.md` at all, and (b) the harness loads
    agent definitions at session start and has not re-scanned a file created mid-session. **(b) is a
    false negative** that would return a viable feature to scoping. So: re-run the probe in a **fresh
    session**, with the definition file existing *before* that session starts, and record both
    attempts. Only a negative surviving the fresh-session re-probe triggers the STOP — at which point
    stop, report to the user, and return the request to scoping. Do not soften a genuine negative into
    a note and proceed.

**Acceptance.**
- `reviews/harness-probe.md` exists, opens with an explicit PROCEED or STOP verdict, answers both
  halves of AC9 with `verified`/`measured` labels and quoted command output, and records both probe
  attempts if the first was negative.
- No answer position carries the word `unconfirmed`.
- The artifact names the exact frontmatter keys the harness accepted, where a write allowlist can be
  declared (or states plainly that no machine-readable allowlist exists and records the fenced-heading
  fallback), and whether per-agent tool permissions are declarable.
- No canary survives: if `.claude/agents/` exists at all, it contains no `probe-*.md`.
- `git status --porcelain` shows `reviews/harness-probe.md` as the only **new** path attributable to
  this phase.
- The five standing gate commands are green.

**Commit note.** Hand to the user for `/commit`. Exactly one new path. Never commit the canaries. This
is the phase most worth committing alone: it is the evidence the rest of the feature is worth building,
and **on a STOP verdict the probe is the whole deliverable**.

---

### Phase 1 — Land `.claude/agents/`

**Goal.** Create the directory and its three files, with the definition carrying the relocated
rulebook, the write allowlist and deny set, the tool allowlist, the return contract, the escalation
policy and the routing rule — in the `SKILL.md` register. `CLAUDE.md` stays untouched so the cut lands
as its own reviewable diff in Phase 3.

**Steps.**

1. Create `.claude/agents/data-engineer.md` with the frontmatter schema **Phase 0 confirmed**. Do not
   assume the eight `SKILL.md` files' `name` + trigger-rich `description` shape transfers — that is the
   SKILL format, and blocker fix F3 exists because AC1 originally asserted an unverified schema.
2. Write the body in this order: (1) manager/developer role framing; (2) an **override preamble**
   naming which inherited sections the agent ignores and which it obeys absolutely — write it whether
   or not the probe confirmed inheritance, since it costs a paragraph and the harness can change under
   a version bump; (3) the relocated **build rulebook** as two self-contained sections, `EXTRACTION &
   LANDING` and `DBT MODELING`; (4) **pointers** to `../../transform/models/bronze/README.md` and
   `../../transform/models/silver/README.md`; (5) the memory pointer as **inline code**
   `.claude/agents/data-engineer-memory.md`, never a markdown link; (6) the return contract; (7) the
   three-way escalation policy; (8) the write allowlist + deny set; (9) the **tool allowlist**;
   (10) git-read-only as an absolute with its recorded reason; (11) the prohibitions; (12) spec-triage
   (dry-run) mode with its invocation phrase.
3. **Compose the rulebook by moving, not re-typing,** the substance of `CLAUDE.md:84-103`: resolve by
   name; the landing zone is immutable; bronze is 1:1 with the source; silver declares its grain in
   `schema.yml` prose **and** proves it with a uniqueness test; facts `MERGE` on key because box scores
   get restated; layer promotion is gated on tests; no bulk data in git. Plus the four gotchas at
   `:107-109` (0.6s pacing with exponential backoff), `:110-112` (prefer bulk endpoints — **keep its
   `unconfirmed` label** so the agent does not build on it as fact), `:113-116` (affiliation resolves
   as-of the **game date**), and `:126` (Windows dev, Linux CI). Re-depth every relative link for the
   new location.
4. **Era boundaries: point, do not copy.** The definition needs the 2013-14 tracking boundary and the
   three irregular seasons, but those live in `CLAUDE.md:52-59` (Key Context) and **stay there** — that
   section is not part of the cut. Copying them creates a new unguarded duplicate, which is exactly
   what Decision 12 exists to prevent. The definition therefore **points** at `CLAUDE.md`'s Key Context
   for era boundaries, and the Phase 2 clause-presence guard asserts the pointer, not a copy.
5. **State the write allowlist as a bound, not a restatement of "the spec decides"** (blocker fix F1).
   Standing allowlist: the memory file `.claude/agents/data-engineer-memory.md` (the single `.claude/`
   carve-out, stated as an **exact path**) and `requests/<track>-requests/<slug>/reviews/` so the agent
   can write its own handoff. Task-scoped: the plan's declared target paths. Repo-level **deny** set,
   absolute: `tests/`, `.github/`, `ops/`, `.claude/` (memory excepted) — the four the scope names —
   **extended by three per gate #3**: `CLAUDE.md`, `docs/data-sources.md`, `docs/decisions/`. State the
   rationale inline: an agent that can edit the guards that catch it and report green is the 2026
   restaging of the recorded scar.
6. **State the tool allowlist**, distinct from the write allowlist (Decision 3, restored). The agent may
   run read/verify commands — `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`,
   `uv run mypy`, `uv run dbt build --target ci`, and read-only git. It may **not** run anything that
   spends money, hits `stats.nba.com` live, mutates the tree, or rewrites history. If Phase 0 found
   tool permissions are not declarable per-agent, this is a prose bound — say so explicitly rather than
   implying it is enforced.
7. **State git read-only absolutely**, naming the verbs literally so a substring guard can find them:
   never `checkout`, `reset`, `restore`, `clean`, `stash`, nor anything that discards working-tree
   state; and never `commit`, `merge`, `push`, `amend`. Quote the scar from
   `implement-plan/SKILL.md:123-125` so the rule carries its reason.
8. **State the return contract** as fixed prose sections — `track` (feature|bugfix) · built ·
   verified-with-evidence · assumed · surprised-me (memory candidates) · could-not-do · docs-delta ·
   still-open — written to `requests/<track>-requests/<slug>/reviews/`, at or under **120 lines**
   (gate #4), carrying **no diff hunks and no `---` horizontal rules**, with a first-line marker
   `<!-- handoff: v1 -->` so the linter finds handoffs without a brittle filename glob. Every row of
   the verified table must cite a concrete command and its **actual output** — a claim with no command
   is an `assumed` row, not a `verified` one.
9. **State the three-way spec-gap escalation policy**: a spec that **contradicts** an invariant stops
   the agent with a spec-gap report; a spec **silent** on an invariant is built to the invariant and
   flagged; an **ambiguous** requirement is built at the smaller interpretation and flagged. All three
   must be observable in the handoff — that is what makes the policy testable rather than a default.
10. **State the routing rule under its own `## Routing` heading**, naming `docs/data-sources.md`
    literally (AC13): any data, era, endpoint, availability or rate-limit fact goes to the handoff's
    `docs-delta` section for the main thread to route through `/update-docs` — never into memory, and
    the agent never edits `docs/data-sources.md` itself. Memory candidates of that shape are tagged
    `docs-candidate`. *The guard in Phase 2 asserts this heading and its content, not the bare presence
    of the string `docs/data-sources.md` — which the relocated pacing bullet already puts in the file,
    and which would make the guard pass vacuously (finding F4).*
11. Create `.claude/agents/data-engineer-memory.md` with **no frontmatter**: a header stating what
    belongs (implementation ergonomics — client shapes, casing surprises, tooling traps) and what
    routes elsewhere; the per-entry format (date · epistemic label · the claim · an evidence pointer ·
    a routing tag); the paths-as-inline-code convention **with its reason**; the 120-line cap named
    with its counting rule (**physical lines**, gate #1); and the **at-cap rule** (finding F3): at cap
    the agent **appends nothing** and instead reports the entry plus "memory at cap, pruning needed"
    under `still-open`/`docs-delta`. Pruning is a main-thread decision, never the agent's.
12. **Seed 2–4 entries the repo has already earned**, each with a citation, never invented: (a)
    `documented` — PS 5.1 `Set-Content`/`Out-File` mangle UTF-8, use the file-editing tools
    (`implement-plan/SKILL.md:111-112`); (b) `verified` — the bundled `.claude/skills/**/tests/*.mjs`
    guards are **not** run by CI, which has three jobs and no Node step; (c) `documented` — sqlfluff
    errors on an empty model selection, hence the conditional at `ci.yml:78-85`; (d) `measured` — the
    Phase 0 probe result. Do **not** label (a) or (c) `measured`; neither was run here. State in the
    header that **`CLAUDE.md:76-79`'s five labels govern** (gate #6), and note in one line that
    `update-docs/SKILL.md:105` names four and `docs/data-sources.md:5-10` names three, so the
    divergence is recorded rather than rediscovered.
13. Create `.claude/agents/README.md` (**no frontmatter**): what the directory is, the
    one-definition-per-agent rule, the memory carve-out as an exact path, and the **main-thread spawn
    protocol** — feature branch; clean-tree (or only-the-agent's-own-prior-work) precondition;
    pre-spawn capture; post-run comparison into `reviews/`. Reuse stage 4's procedure
    (`implement-plan/SKILL.md:120-125`, `:187-190`); do not invent a second mechanism and do not add
    executable tooling.
14. Write every file with the **Write/Edit tools**, never PowerShell `Set-Content`/`Out-File`.
    `.gitattributes` normalizes to LF.

**Acceptance.**
- `.claude/agents/` contains exactly three `.md` files, exactly one of which opens with `---` and whose
  frontmatter parses to non-empty `name` and `description`; the other two carry none.
- `uv run pytest tests/test_doc_links.py -q` green — every relative link in the three new files resolves
  at its new depth, and the **scanned** file count has risen from 33 toward 36 (this is the link
  checker's scanned set, which is not the same number as `git ls-files '*.md'`).
- Grep over the definition finds: all five git verbs; the never commit/merge/push/amend clause; a
  `## Routing` heading naming `docs/data-sources.md`; the seven deny-set paths; the tool-allowlist
  clause; and the memory file's literal path.
- The memory file is at or under **120 physical lines** and contains zero data/era/endpoint/rate-limit
  claims outside its header.
- The five standing gate commands are green (no Python changed — this is the no-regression baseline).

**Commit note.** Hand to the user for `/commit`. Three new paths. The `CLAUDE.md` cut is deliberately
held back to Phase 3. Point the user at the memory file as its own per-path staged entry — that is the
mechanism AC14 later asks a human to judge.

---

### Phase 2 — The pytest guard suite

**Goal.** Turn the guardrail clauses, the relocated rulebook, the frontmatter shape, the budgets, the
memory entry format and the handoff shape from trusted prose into **required-check CI failures** (AC1,
AC2, AC4, AC5, AC6, AC10, AC13) — with a negative control per guard so nothing passes vacuously.

**Steps.**

1. **`tests/test_repo_structure.py`** — add `test_agents_directory_holds_exactly_one_definition()`,
   reusing `REPO_ROOT` (`:19`) and the already-imported `yaml` (`:17`). Discover by glob, **never** by
   hardcoded filename. Narrow `yaml.safe_load`'s `Any` with an `isinstance` assert exactly as `:25-26`
   does. Model the assertion-message style on `test_every_layer_documents_itself` (`:77-84`).
2. **Create `tests/test_agent_contract.py`.** Structure **every** check as a module-level **pure
   function** over text — `_frontmatter(text)`, `_line_count(text)`, `_missing_clauses(text, required)`,
   `_entry_format_violations(text)` — so the same function can be pointed at a synthetic bad input
   built in a `tmp_path` fixture. *That factoring is what makes the negative controls cheap; without it
   they cannot be written at all.*
3. **Guard — guardrail clauses (AC2).** The definition contains the read-only-git clause naming
   `checkout`/`reset`/`restore`/`clean`/`stash` and the never commit/merge/push/amend clause. Substring
   assertions. Negative control: the same predicate over a synthetic definition with one clause removed
   must report it.
4. **Guard — relocated-rulebook clause presence.** This is the Decision-12 replacement for the withdrawn
   drift guard, and it is **Phase 3's regression test**. Phrase-presence, not verbatim (Decision 6):
   assert the definition names resolve-by-name / `ref()` / `source()`; the immutable landing zone;
   bronze 1:1; silver declares **and proves** its grain with a uniqueness test; facts `MERGE` on key;
   layer promotion gated on tests; the 0.6s pacing default; prefer-bulk-endpoints with its
   `unconfirmed` label; the Windows/LF rule; the **pointer** to `CLAUDE.md`'s Key Context for era
   boundaries; and — highest value — that affiliation resolves **as-of the game date**. The failure
   message must name `CLAUDE.md` as the source these were relocated from, so a red check says what to do.
5. **Guard — deny set.** The definition literally names `tests/`, `.github/`, `ops/` and `.claude/`,
   and states the memory file as the single `.claude/` carve-out. **Assert only these four** — the
   three-path extension from gate #3 is stated in prose in the definition but deliberately not asserted,
   so acceptance is not over-fit to a judgment call. Say plainly in the docstring that this asserts the
   **declaration**, not the behavior — detection, not prevention.
6. **Guard — tool allowlist.** The definition names the verify-commands clause, so the capability
   Decision 3 settled cannot be silently deleted.
7. **Guard — budgets (AC4 + the folded win).** The memory file exists at the exact path the definition
   names, is referenced **by that path** from the definition, and is at or under 120 lines; `CLAUDE.md`
   is under 200. Both assertion messages must name the **cap** and the **counting method**. Use
   **physical lines** — `len(text.splitlines())` — per gate #1. Measured: that counts 140 for
   `CLAUDE.md` while `(Get-Content | Measure-Object -Line).Lines` counts 122, because PowerShell drops
   the 18 blank lines. The memory-budget message must also name the **at-cap rule** so a red check says
   what to do. Negative controls: an over-budget synthetic file fails; a definition naming a memory path
   that does not exist fails.
8. **Guard — memory entry format + routing (AC13).** Every non-header entry line matches the declared
   shape and carries one of `CLAUDE.md:76-79`'s five labels. The routing half is a **narrow curated
   denylist implemented as an ordinary assertion** (gate #9), scanning **entries only and skipping the
   header block** — the header legitimately names `docs/data-sources.md`, rate limits and era
   boundaries as examples of what routes elsewhere, and a naive scan reddens against the very file this
   plan tells the implementer to write (finding A2-EX-11). Choose terms that cannot fire on the
   canonical **good** entry, "leaguegamelog returns a DataFrame, not JSON" — e.g. season-range strings,
   `rate limit`, `2013-14`, `82 games` — and record that reasoning in the test docstring. If a date is
   parsed, use `datetime.date.fromisoformat`, never `strptime` — ruff selects `DTZ`.
9. **Create `tests/test_handoff_contract.py`** exposing `lint_handoff(text: str) -> list[str]`, plus a
   walker over `requests/*-requests/*/reviews/*.md` that lints every file whose first line carries
   `<!-- handoff: v1 -->` and skips the rest — track-agnostic by construction. Enforce: all required
   sections present and **non-empty**; the 120-line cap, named in the message; and hunk-freeness.
   **Implementation trap:** a bare `^---` also matches YAML frontmatter and a Markdown thematic break,
   so match the unified-diff header **shapes** — `^@@ `, `^\+\+\+ `, `^--- ` (trailing space) and
   `^diff --git ` — and forbid `---` horizontal rules in the return contract so AC10's literal grep
   also comes back empty. Cover that distinction with an explicit test.
10. **Ship four synthetic negative controls now** — missing section, `^@@` hunk, over cap, and a
    thematic rule that must **pass** — so the linter is meaningfully exercised before any real handoff
    exists. The anti-vacuity **coverage** assertion lands in **Phase 4** and nowhere else, once a real
    artifact exists to find.
11. **Satisfy the real gates (AC6).** mypy is strict over `src` and `tests`, so annotate every test
    `-> None` and every fixture (`tmp_path: Path`); ruff selects `PTH` (pathlib only, never `os.path`),
    `DTZ`, `N`, `B`, `A` at line-length 100.
12. **Demonstrate the controls once**: temporarily invert one control's expectation, watch it redden,
    restore it. A control asserted but never seen red is itself unproven. Do not commit the inversion.

**Acceptance.**
- `uv run pytest tests/test_repo_structure.py tests/test_agent_contract.py tests/test_handoff_contract.py -q`
  green, with every guard carrying a paired `tmp_path` negative control that fails on synthetic bad input.
- The memory-budget and `CLAUDE.md`-budget assertion messages each contain the literal cap number **and**
  the counting method — grep for them.
- `lint_handoff` returns a non-empty violation list for each of the four synthetic bad inputs and an
  empty list for the synthetic good one, including the thematic-rule-passes case.
- The five standing gate commands are green.

**Commit note.** Hand to the user for `/commit`. Paths: `tests/test_repo_structure.py`,
`tests/test_agent_contract.py`, `tests/test_handoff_contract.py`. These land under `tests/` and not as
`.mjs` siblings because `ci.yml` has no Node step and `ops/branch-protection.json:4` makes pytest a
required check — that is the whole reason the guards are enforcement rather than etiquette.

---

### Phase 3 — Relocate the rulebook out of `CLAUDE.md`

**Goal.** Give the build rules **one owner** (Decision 12): cut the Data Layer section and four gotcha
bullets, leave a pointer that names what moved, add the map row, clarify the subagent bullet, and teach
the two skill bucket lists that `.claude/agents/` exists. Deliberately **before** the drills, so Phase
5's PASS/FAIL is attributable to the definition rather than to inherited manager context.

**Steps.**

1. **Add-then-remove, never the reverse.** Run `uv run pytest tests/test_agent_contract.py -q` **first**:
   the clause-presence guard from Phase 2 is exactly the check that every clause about to be cut already
   lives in the definition. A clause that fails there is **added to the definition in this same commit**
   — never dropped.
2. **Cut** `CLAUDE.md`'s `## Data Layer` section (`:84-103`) and the four relocated Constraints & Gotchas
   bullets (`:107-109`, `:110-112`, `:113-116`, `:126`). **Keep** `:117-119` (cost guardrail), `:120-121`
   (the `pre-commit` naming note) and `:122-125` (the CI-rename/branch-protection trap) — the agent is
   denied `.github/` and `ops/`, so those stay manager context. Keep the project map, Important
   Locations, **Key Context** (era boundaries stay here — see Phase 1 step 4), Project Conventions and
   How to Help.
3. **Insert the pointer** where the Data Layer section stood: one or two lines **naming what moved** —
   resolve-by-name, immutable landing zone, bronze 1:1, silver declares-and-proves its grain, facts
   `MERGE` on key, layer promotion gated on tests, 0.6s pacing, prefer-bulk-endpoints,
   affiliation-as-of-game-date, **and Windows/LF** (finding F10) — and naming
   `.claude/agents/data-engineer.md` as the authoritative rulebook. Phrase it for a main-thread agent
   building directly under the three carve-outs. Use a **markdown link** so `tests/test_doc_links.py`
   proves it resolves.
4. **Add a `.claude/agents/` row** to the project-map block (`:16-33`), directly under the
   `.claude/skills/` line at `:27`. The block is fenced, so map entries are exempt from link checking
   either way.
5. **Rewrite the subagent bullet** (`:73-75`) so read-only git and file-write permission are
   distinguishable: git stays read-only and absolute for every subagent, and **editing a tracked file is
   explicitly not a git operation** — so a write-capable builder with a declared allowlist is inside the
   rules, not an exception to them. Half a sentence, not a paragraph. This is what prevents a future
   agent refusing a legitimate instruction (AC7).
6. **Add `agents` to both bucket lists, carrying its own workaround.** At
   `implement-plan/SKILL.md:127-132` and `update-docs/SKILL.md:47-48`, write the entry as
   *`agents` (`.claude/agents/`) — `AREA_TO_SPEC` has no `agents` key yet, so **also pass `skills`** to
   draw the `skill-quality` lens.* **This wording is not optional** (findings F2 / A2-EX-03): verified,
   `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) has no `agents` key and `:207` resolves an unknown
   area to `[]` **silently, with no warning**. A bare `agents` entry would teach implementers to pick a
   bucket that draws *zero* specialists — strictly worse than today, where a `.claude/agents/` change
   buckets under `skills` and draws the `skill-quality` specialist (`:199`) whose every clause applies
   verbatim to an agent definition. Do **not** touch `acceptance_panel.js`: Decision 7 defers the JS
   half, and that file is covered by two `.mjs` guards CI does not run. Verify with
   `git diff HEAD --stat` that no `.js` file appears.
7. **Follow the moved content in `update-docs/SKILL.md`**: its CLAUDE.md checklist at `:71-73` audits
   "the rules", so point that check at the relocated rulebook too, and add one line so the gate also
   eyeballs the memory file's budget and its freedom from data facts. Keep it a **judgment** check — the
   mechanical half is Phase 2's guard.
8. **Reconcile the counting semantics at `update-docs/SKILL.md:76-78` in this same commit** (gate #1):
   replace or annotate the `Measure-Object -Line` one-liner so it agrees with the pytest guard's
   physical-line count, and name the pytest guard as the authority. Two checks of the same budget
   disagreeing by 18 lines is exactly the local-red/CI-green trap the scope worries about.
9. **Because `implement-plan/SKILL.md` changed**, run its two bundled self-verification guards **by
   hand** and record exit 0 for each: `node .claude/skills/implement-plan/tests/merge_fallback_guard.mjs`
   and `node .claude/skills/implement-plan/tests/verify_batching_guard.mjs`. CI has no Node step, which
   is exactly why this step is written down. *Note the limit honestly (finding A2-EX-13's sibling): these
   guards exercise the panel script, not the SKILL.md prose, so "both exit 0" is a no-regression signal,
   not proof the doc edit is right.*
10. **Add the AC3-replacement guard** to `tests/test_agent_contract.py` — `CLAUDE.md` contains the
    definition's literal path — with a negative control over a synthetic `CLAUDE.md` string lacking it.
    This guard lands **here, with its subject**, not in Phase 2.
11. **Re-read the trimmed `CLAUDE.md` end to end as prose**, and read `git diff HEAD -- CLAUDE.md` line
    by line rather than inferring it. The failure this phase can produce is **silent**: a rule the
    manager still needs now living where the manager does not look, or an orphaned lead-in sentence.
    No test catches that.

**Acceptance.**
- `uv run pytest tests/test_agent_contract.py -q` green, including the clause-presence guard (proving
  nothing was dropped in the move) and the new pointer guard.
- Both `CLAUDE.md` counts recorded before and after the cut, and the physical-line count is well under
  200 (AC7). Record the measured delta rather than asserting a predicted one.
- The project-map block contains a `.claude/agents/` entry, and the subagent bullet reads so a reader
  can tell that an agent editing a tracked file is not violating it (read-and-judged, not
  command-proven).
- Grep confirms the grain rule no longer appears in `CLAUDE.md` and **does** appear in the definition —
  this is what makes Phase 5's drill attributable.
- Grep confirms both bucket lists carry the `agents` entry **with its `also pass skills` workaround**;
  `git diff HEAD --stat` lists no `.js` file; both `.mjs` guards exited 0.
- The five standing gate commands are green.

**Commit note.** Hand to the user for `/commit`, and flag this as **the highest-judgment diff in the
feature**. It edits the file every agent reads on every task; a bad cut degrades every future session
rather than failing loudly. Ask the user to read the `CLAUDE.md` diff line by line before saying yes.
`/commit` should run the full `/update-docs` sweep here — a changed directory plus changed rules
sections are two of its triggers.

---

### Phase 4 — Proving run A: the faithful spec

**Goal.** Prove the capability end to end on a small, real, reversible, decoupled target: a genuine
diff produced by the agent, a handoff that passes the Phase 2 linter, and a committed tree-integrity
trail showing nothing outside the allowlist moved (AC10, AC12, AC14).

**Steps.**

1. **The target is settled (gate #2).** The agent adds a short section to root `README.md` describing
   `.claude/agents/` and the spawn protocol, **and** is handed one deliberately mis-routed candidate —
   a data fact such as the still-`unconfirmed` bulk-endpoint belief — which the routing rule requires it
   to place in `docs-delta` rather than memory. Measured: `README.md` is 117 lines with sections
   `Architecture` (`:18`), `Scope` (`:40`), `Data provenance` (`:58`), `Repo layout` (`:69`), `Setup`
   (`:82`), `Roadmap` (`:104`), `License` (`:115`), and mentions neither `.claude` nor "skill". **The
   spec must require the agent to keep the file internally consistent** (finding F9): a new subsection
   alone leaves `## Repo layout` silently stale, so the spec names both the new prose *and* the
   `Repo layout` entry. Binding constraints, restated so a substitute target can be checked against
   them: inside the write allowlist; outside the deny set; not `docs/data-sources.md`; not
   `transform/models/`; not `src/nba_platform/`; no dbt model, extractor or fixture.
   **`tests/fixtures/README.md` is explicitly forbidden** — denied path, and the scope says its known
   drift must not be silently absorbed (`PROJECT_SCOPE.md:307`).
   *Accepted cost (finding A2-EX-15): this makes the project's public-facing README the output of the
   agent's first run. The mitigation is that the diff is small, additive, and read by a human at
   `/commit` before it lands.*
2. **Pre-spawn.** Confirm the branch is `feature/data-engineer-agent`, not `main`. Confirm the tree is
   clean or holds only the agent's own prior work. Create the scratch directory first —
   `New-Item -ItemType Directory -Force var/tmp` — because `var/tmp/` does not exist on a fresh clone
   and the capture silently fails otherwise (finding A2-EX-06). Capture `git status --porcelain`, the
   untracked list, `git rev-parse HEAD`, `git stash list`, and
   `git diff HEAD --output=var/tmp/data-engineer-agent-run-a-pre.patch` — **use git's own `--output`
   rather than PowerShell redirection**, which would BOM the file. *Two honest notes: this reuses stage
   4's procedure (`implement-plan/SKILL.md:120-125`) **extended** with `rev-parse` and `stash list` —
   not five commands lifted verbatim (finding F8); and on a genuinely clean tree the patch is **empty**,
   so the load-bearing captures are the status, untracked list, HEAD and stash list (finding A2-EX-12).*
   `var/` is gitignored, so the patch is a safety net, not evidence.
3. **Spawn** by the mechanism Phase 0 confirmed, handing the agent: the faithful spec, its target paths,
   the handoff path `requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md`, and the
   reminder that git is **read-only** for it. **Do not narrate the edits** — the whole point of the run
   is that the main thread does not have to.
4. **Post-run**, reusing `implement-plan/SKILL.md:187-190`: re-run the same captures and diff them
   against the pre-spawn set. Confirm no tracked file outside the declared allowlist was modified or
   deleted, nothing pre-existing was reverted, `HEAD` is unchanged, and `git stash list` is unchanged.
   Grep for one symbol you knew existed before the spawn — a passing test does not prove your files are
   still there.
5. **Write `reviews/proving-run-a.md`**: the handoff itself (first line `<!-- handoff: v1 -->`, all
   required sections non-empty, every `verified` row citing a command and its real output), **plus** the
   pre/post tree-state pair pasted in as committed evidence and the comparison verdict. Evidence lands
   in committed `reviews/`, never only in gitignored `var/` (blocker fix F2). **Fence the captured
   output** — it contains paths and `---`-shaped lines that would otherwise trip both the link checker
   and the hunk guard.
6. **Score the handoff mechanically.** `uv run pytest tests/test_handoff_contract.py -q` must now be
   linting the **real** file; run AC10's literal greps and paste the empty result; confirm the line
   count is under 120; spot-check two rows of the verified table by re-running their commands yourself.
7. **Add the anti-vacuity coverage assertion** to `tests/test_handoff_contract.py`: at least one file
   carrying the handoff marker was found and linted, asserted on the **scanned-file list** rather than
   on a green exit. This lands here and nowhere else.
8. **Repetitions (gate #5): one faithful run**, with its evidence explicitly labelled **a single
   observation, not a proof**, in both the artifact and later in ADR 0007. That honesty requirement is
   not optional.
9. **Run `/commit` and observe** (AC14, **USER-RUN**) whether the memory delta appears as a visible
   per-path staged entry, and whether a human can tell the agent's writes from their own in the staged
   diff. A human reads and judges this; no command proves it. Record what was observed.

**Acceptance.**
- `reviews/proving-run-a.md` exists, carries the marker and every required section non-empty, has each
  verified row citing a command and its real output, contains no diff hunks, and is under 120 lines (AC10).
- `uv run pytest tests/test_handoff_contract.py -q` green over the real artifact, with the coverage
  assertion confirming at least one handoff was found and linted.
- The pre/post tree-integrity pair is saved in `reviews/` and shows: clean-or-own-work start, no writes
  outside the allowlist, nothing reverted, HEAD unchanged, stash list unchanged (AC12).
- **`git status --porcelain`** shows only the spec's target file, the new `reviews/` artifact, and at
  most the memory file — use `status`, not `git diff HEAD --stat`, which cannot see the untracked
  artifact this phase produces (finding A2-EX-13).
- The five standing gate commands are green over whatever the agent wrote. **If the agent's memory delta
  pushed the file over its cap, that is a real budget-guard failure, not a reason to raise the cap** —
  apply the at-cap rule.
- The artifact states the repetition count and labels the evidence an observation.
- **USER-RUN:** a `/commit` run displayed the memory delta as a per-path staged entry (AC14).

**Commit note.** Hand to the user for `/commit`. **This commit is acceptance criterion 14's
observation**: stage per-path, read the memory delta, and only then say yes. Nothing under `var/` may be
staged.

---

### Phase 5 — Proving run B: the OMISSION DRILL

**Goal.** Test whether the invariant set is **load-bearing or decorative** — the only criterion in the
feature that tests behavior rather than the existence of well-formed files (AC11). **A FAIL blocks the
feature.**

**Steps.**

1. **Build the drill target as a scratch dbt project under gitignored `var/scratch/omission-drill/`** —
   never `transform/`. Give it its own `dbt_project.yml` and `profiles.yml` targeting in-memory DuckDB
   (dbt-core, dbt-duckdb and duckdb are already in the `transform` dependency group) and two tiny seeds
   shaped so a silver-style model over them has a real grain — player-per-game with one traded player
   appearing twice is the honest fixture. CI's dbt job builds `--project-dir transform` only, and the
   layer guards read `transform/models/` only, so scratch under `var/` is invisible to both.
2. **Solve `dbt_utils` correctly.** `transform/packages.yml` declares `dbt-labs/dbt_utils` because
   `unique_combination_of_columns` is how every silver model proves its grain. **Verified and
   important:** `transform/dbt_packages/` exists locally but is **gitignored** (`.gitignore:50`) — it is
   **untracked local state**, not something a fresh clone has, and CI obtains it by running `dbt deps`
   (`ci.yml:70-71`) before `dbt build`. So: **copy** the vendored `dbt_utils` directory into the scratch
   project's `packages-install-path`. **Do not point `packages-install-path` at the real project's
   `transform/dbt_packages/`** — that invites dbt to write into the real project and is
   destructive-adjacent (finding A2-EX-07). If the local copy is absent, `dbt deps` is a **network
   call** the scope forbids for proving runs, so it is a user-run step or you fall back to a core
   `unique` test on a surrogate key as equivalent proof of grain — **recording the deviation in the
   artifact**. "dbt deps failed" must never be scored as "the agent failed".
3. **Write the drill spec**: a silver-shaped model over the scratch data with a stated grain,
   **deliberately omitting** "declare the grain in `schema.yml` and prove it with a uniqueness test".
   Do not hint at it anywhere else in the prompt. Save the exact spec text for the artifact so the
   omission is auditable. **Confirm before spawning that the grain rule is absent from `CLAUDE.md`**
   (Phase 3 removed it) — that confirmation is what makes a PASS attributable to the definition
   (blocker A2-01).
4. **Snapshot, spawn, snapshot** exactly as Phase 4, into
   `var/tmp/data-engineer-agent-run-b-pre.patch`. Let it run without correction.
5. **Score it, quoting verbatim.** PASS iff **either**:
   - the produced model carries a uniqueness test proving the declared grain — **and the scratch project
     actually builds**: `uv run dbt build --project-dir var/scratch/omission-drill --profiles-dir
     var/scratch/omission-drill --target ci` must be run and the uniqueness test must appear in that
     output as **PASS**, quoted into the artifact. A grep alone is satisfied by a `schema.yml` naming a
     test that never ran or cannot resolve (finding A2-EX-08). Additionally apply the grain-vs-test
     agreement check from `update-docs/SKILL.md:114-126`: the columns in the uniqueness test must match
     the grain the description claims, or it is a **FAIL**;
   - **or** the handoff explicitly flags the omission as a spec gap under the escalation policy's
     silent-on-an-invariant branch.

   A silent, untested grain is a **FAIL** and blocks the feature. Fix the grep patterns and the build
   command in advance so the score is not a judgment call after the fact.
6. **Copy the evidence into committed `reviews/proving-run-b.md`**: the spec text as given, the produced
   `schema.yml`/model excerpts **quoted** (not as diff hunks — the linter rejects hunks), the `dbt build`
   output showing the test result, the handoff's escalation section, the grep commands and their real
   output, the explicit PASS/FAIL verdict, the repetition count, and the pre/post tree state. The scratch
   project dies with `var/`; the artifact is the record.
7. **On a FAIL, do not paper over it and do not quietly re-spec until green** — that is the
   vacuous-selftest failure this repo already carries a scar for. The definition's invariant or
   escalation wording is not doing its job: strengthen it as in-scope repair, re-run, and **record every
   attempt**. A FAIL that is fixed and re-proven is a good outcome; a FAIL rerun until green is not.
8. **Repetitions (gate #5): run the omission drill twice.** This is where nondeterminism matters most
   and where a FAIL blocks the feature. Record both runs and both verdicts.
9. **Confirm the drill leaked nothing.** `git status --porcelain transform/ src/` is empty;
   `Get-ChildItem transform/models -Recurse -Filter *.sql` returns nothing — **PowerShell, not Unix
   `find`**, which does not exist on this box and would make the check pass vacuously (findings F1 /
   A2-EX-05 / M-07). A stray `.sql` would also flip the sqlfluff step at `ci.yml:78-85` from skipped to
   running and redden a later unrelated PR. Then
   `uv run dbt build --project-dir transform --profiles-dir transform --target ci` is still green.

**Acceptance.**
- `reviews/proving-run-b.md` records the drill with the spec text, verbatim-quoted produced artifacts,
  the `dbt build` output, the grep commands and their real output, and an explicit PASS/FAIL verdict per
  run (AC11).
- `uv run pytest tests/test_handoff_contract.py -q` green over run B's handoff; the linter now scans
  **both** proving-run artifacts.
- The pre/post tree-integrity pair for run B is in the `reviews/` trail (AC12).
- `git status --porcelain transform/ src/` empty and
  `Get-ChildItem transform/models -Recurse -Filter *.sql` returns nothing — the non-goal at
  `PROJECT_SCOPE.md:110` verified mechanically, not asserted.
- `uv run dbt build --project-dir transform --profiles-dir transform --target ci` green.
- The five standing gate commands are green.
- **A FAIL blocks the feature**: do not proceed to Phase 6 on an unresolved FAIL — return the finding to
  the user.

**Commit note.** Hand to the user for `/commit`. Stage `reviews/proving-run-b.md` only; everything under
`var/scratch/omission-drill/` is gitignored working material and `/commit` must refuse it. **If the
drill failed, commit the artifact anyway** — a recorded failure is the most valuable thing this feature
can produce, and hiding it is the overclaiming `CLAUDE.md:76-79` forbids.

---

### Phase 6 — ADR 0007, bookkeeping, and the hand-off

**Goal.** Record why the repo's first write-capable subagent exists and what honestly replaced "it can't
write", reconcile the status headers, run the full local gate, and hand the push and the PR to the user
(AC8, AC15, AC16).

**Steps.**

1. **Write `docs/decisions/0007-write-capable-implementation-subagent.md`** with the five required
   sections in the order `docs/decisions/README.md:19-25` states: Status (`accepted`) / Context /
   Decision / Consequences / Alternatives considered. Written **now**, after the proving runs, because
   `:29-32` makes accepted ADRs immutable (Decision 10).
2. **Make Consequences uncomfortable to write.** It must say plainly:
   - the substitute guard is **detection, not prevention** — feature branch, pre-spawn snapshot,
     post-run integrity check and `/commit`'s staged-list-then-yes all catch a bad write *after the
     fact*, and nothing stops it;
   - the premise is **inferred, not measured** — `/implement-plan` has never run in this repo;
   - the proving-run evidence is **N observations, not a property** — state the true counts (one
     faithful run, two omission drills);
   - the headline context savings are **deferred** until the dispatch sequel lands;
   - the feature rests on **harness behavior CI cannot test**, recorded as a dated measurement;
   - the relocation moved **one node of a four-way duplication** without collapsing it —
     `scope_panel.js:124`, `plan_panel.js:146` and `implement-plan/SKILL.md:100-112` still restate these
     rules with no check that they agree, and after Phase 3 `CLAUDE.md` no longer states them at all;
   - **`.claude/agents/` still draws no specialist reviewer automatically** — `AREA_TO_SPEC` has no
     `agents` key, the bucket-list workaround is a runtime argument, and closing it properly belongs to
     the sequel.
3. **Add the 0007 row** to the Index table at `docs/decisions/README.md:39-46` in the existing format,
   with a resolving relative link (AC8).
4. **Bookkeeping (AC16).** The `data-engineer-agent` Index row in `requests/feature-requests/README.md`
   advances to `implemented`, and `FEATURE_REQUEST.md`'s Status blockquote advances to match.
   **Do not edit `PROJECT_SCOPE.md`'s status blockquote** — AC16 pins it at
   `scoped · decided · next: plan`, so advancing it mechanically fails the criterion it is trying to
   satisfy (finding A2-EX-02). The artifact blockquote is the source of truth; the Index cell mirrors it.
5. **Run the full local gate** one last time and read the **actual output**, not the exit code: the five
   standing commands plus `uv run dbt build --project-dir transform --profiles-dir transform --target ci`,
   plus the two `.mjs` guards because `implement-plan/SKILL.md` was touched in Phase 3.
6. **Run `/update-docs`** as the judgment half: the map now names `.claude/agents/`, the rules moved and
   the pointer resolves, ADR 0007 is indexed, no accepted ADR was silently invalidated, `README.md` is
   still true after the agent's Phase 4 edit, and the memory file contains no `docs/data-sources.md`-shaped
   claims. **Route any `docs-candidate` entries** the handoffs queued in their `docs-delta` sections into
   `docs/data-sources.md` with a promoted epistemic label — through the gate, never by the agent.
7. **Re-verify tree integrity** one final time against the Phase 4/5 snapshots and confirm nothing under
   `var/` is staged.
8. **Hand off.** `/commit` stages per-path and asks; the **push and the PR stay the user's**. AC15 is
   USER-RUN: CI green on all three required contexts named at `ops/branch-protection.json:4` —
   `Lint, types, tests`, `dbt build`, `Secret scan` — with gitleaks covering the committed memory file
   per ADR 0006. **Do not rename any CI job** in this change. A red check is stop-and-fix, not a retry
   loop.
9. **Note for whoever launches stage 4 on this change:** pass `touchedAreas` explicitly as **`skills`
   and `docs`**. `AREA_TO_SPEC` has no `agents` key, so without `skills` the `skill-quality` specialist
   never spins up. Do **not** pass `tests` or `config` (findings F11 / A2-EX-17): `tests` maps to the
   `extraction` specialist, whose entire mandate is irrelevant to a change that lands no extraction
   code, and `config` maps to `infra-cost`, which is unearned here. This is a runtime argument, not a
   code change, so it does not breach Decision 7's deferral.

**Acceptance.**
- `docs/decisions/0007-*.md` exists with all five sections and status `accepted`; its Index row resolves
  under `uv run pytest tests/test_doc_links.py -q` (AC8).
- The Consequences section states, in plain words, that the guard is detection rather than prevention,
  that the premise is inferred rather than measured, and the actual repetition counts.
- `IMPLEMENTATION_PLAN.md` and `FEATURE_REQUEST.md` status blockquotes agree with the Index row (AC16),
  and `PROJECT_SCOPE.md`'s blockquote is **unchanged**.
- Full local gate green, including `dbt build` and both `.mjs` guards.
- `(Get-Content CLAUDE.md).Count` is under 200 (AC7).
- No `.sql` file and no `src/nba_platform/` module appears anywhere in the PR diff.
- **USER-RUN:** all three contexts in `ops/branch-protection.json:4` green on the PR (AC15).

**Commit note.** Final checkpoint — hand to the user for `/commit`, which should run the full
`/update-docs` sweep. No agent push, no agent merge, no agent amend — the PR is the user's.

---

## 4. Testing & verification

**Four layers, each doing a different job.**

**(1) Mechanical, CI-enforced** — the guard suite under `tests/`, where `ops/branch-protection.json:4`
makes it a required status check. Nine guard families: `.claude/agents/` structure + frontmatter
validity (AC1); guardrail-clause presence (AC2); relocated-rulebook clause presence, phrase-presence not
verbatim (Decision 6); the deny-set declaration (F1's four only); the tool-allowlist clause (Decision 3);
the `CLAUDE.md` pointer (AC3's replacement); budgets — memory ≤ 120 and `CLAUDE.md` < 200, cap **and**
counting method named (AC4 + the folded win); memory entry format plus the header-exempt routing
denylist (AC13, gate #9); and the handoff schema lint (AC10). **These check form only** — all of them
pass green in the dead-artifact failure case, and this plan says so rather than letting a green suite
read as a safe agent.

**(2) Anti-vacuity** — a **negative control per guard**, built from a synthetic bad input in `tmp_path`,
never by mutating a real repo file. Each check is a pure predicate over text so the same function serves
the real file and the synthetic one. Not optional decoration: `tests/test_doc_links.py:95-104` exists
because a link checker that scans nothing passes every time, and the recorded scar at
`implement-plan/SKILL.md:123-125` is a vacuous selftest passing green while work was destroyed.
Demonstrate each control once by inverting it and watching it redden, then restore.

**(3) Behavioral** — the two proving runs, the only tests of behavior in the feature. Phase 0 answers
"does anything load it"; Phase 5 answers "is the invariant set load-bearing when the spec forgets it"
(AC11). Neither can be dropped to save time, and a drill FAIL blocks the feature. **Attribution is
engineered**: the relocation (Phase 3) precedes the drill (Phase 5) so a PASS cannot be explained by
inherited `CLAUDE.md` context. The drill's PASS additionally requires the scratch project to **build**,
not merely to contain the right text.

**(4) Tree integrity** — both runs bracketed by stage 4's procedure, extended with `rev-parse HEAD` and
`git stash list`, and the comparison **copied into committed `reviews/`** because `/commit` refuses
`var/` and CI never sees it. This is **detection, not prevention** — say so in the artifacts and in ADR
0007.

**Regression safety.** Nothing here touches `src/`, `transform/models/`, `.github/workflows/`, or
`ops/`. Four named risks with their guards: (a) a new Markdown file with a dead relative link reddens
`tests/test_doc_links.py` — put forward references inside fences, which `:69` strips, and keep memory
paths as inline code, which `:56` never scans; (b) the drill leaving a `.sql` under `transform/models/`
would flip the sqlfluff conditional from skipped to running — Phase 5 asserts it did not, **in
PowerShell**; (c) Phase 3's `CLAUDE.md` cut has no mechanical net beyond the clause-presence guard, so
it is committed as its own reviewable diff and read line by line; (d) editing `implement-plan/SKILL.md`
obliges running its two `.mjs` guards by hand.

**Counting semantics are part of the test contract.** Measured: `(Get-Content CLAUDE.md).Count` = 140
while `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` = 122, because `Measure-Object -Line` drops
the 18 blank lines. The guards use **physical lines** and say so in every assertion message; Phase 3
reconciles `update-docs/SKILL.md:76-78` in the same commit.

**What no test covers, stated so the ledger stays honest.** AC9 (a human reads the recorded probe
evidence); AC10/AC11/AC12 (RECORDED-EVIDENCE — grep-assisted, human-adjudicated); AC14 (`/commit`
behaves as assumed — **USER-RUN**); AC15 (CI green on the user's PR — **USER-RUN**); and the judgment
half of Phase 3's cut. Mark each per `requests/feature-requests/README.md:57-59` so the stage-4
acceptance panel does not claim them. And **nothing here proves the agent will obey its definition on
the next task** — the drills are observations, not properties.

---

## 5. Decisions

Decisions 1–11 and the two post-panel amendments are settled upstream in
[`PROJECT_SCOPE.md`](PROJECT_SCOPE.md) `:367-490` and are **not re-opened here**. What follows is this
stage's additions and the disposition of the nine gates the planning panel raised.

### Gates disposed by the user, 2026-08-14

**G1 — Budgets count PHYSICAL lines** (`len(text.splitlines())`), with the counting method named in
every assertion message, and `update-docs/SKILL.md:76-78` reconciled in the same commit. Measured: 140
vs 122 for `CLAUDE.md`, an 18-line gap that made Decision 5's 120-line memory cap ambiguous by ~15%.
Physical lines are what a reader scrolls and what a Python guard counts natively; unreconciled, the
first red budget check would be dismissed as broken against the documented one-liner.

**G2 — The faithful run's target is a root `README.md` section plus a mis-routed routing candidate.**
Measured gap: 117 lines mentioning neither `.claude` nor "skill". Satisfies every binding constraint,
lands no pipeline code, and produces exactly the memory delta AC14 needs `/commit` to display. The spec
must also require the `## Repo layout` entry so the file stays internally consistent.

**G3 — The deny set extends by three** — `CLAUDE.md`, `docs/data-sources.md`, `docs/decisions/` — on
top of blocker F1's four. Those three are precisely what the routing rule and the manager/developer seam
depend on the agent not touching. `pyproject.toml`/`uv.lock`/`.gitignore` are deliberately **left out**:
they are legitimately task-scoped for a future extraction feature, and over-denying now would make the
sequel's routing table wrong. **The Phase 2 guard asserts only F1's four**, so acceptance is not
over-fit to a judgment call; the extension lives in the definition's prose.

**G4 — The handoff line cap is 120**, matching the memory cap, named in the assertion message and in the
return contract. A handoff longer than the memory file it feeds has stopped being a summary.

**G5 — Two omission drills, one faithful run.** The repetition budget goes where the evidence is
load-bearing and a FAIL blocks the feature. Run A's evidence is labelled **a single observation** in
both the artifact and ADR 0007 — whose Consequences section is immutable once accepted and must state
the true counts.

**G6 — `CLAUDE.md:76-79`'s five labels govern memory entries** (measured / verified / inferred /
assumed / unconfirmed), because memory is repo scar tissue and `CLAUDE.md` is the repo-wide convention.
`docs/data-sources.md` keeps its own three-label set; reconciling them is **out of scope**. The
divergence is named in one line of the memory header so it is recorded rather than rediscovered.

**G7 — The agent is `data-engineer`**: `.claude/agents/data-engineer.md` and
`.claude/agents/data-engineer-memory.md`, memory alongside the definition. **Contingent on the Phase 0
hygiene probe** — if the harness registers or chokes on frontmatter-less Markdown in that directory, the
memory file and README must move and every path in this plan shifts. Two special cases survive: AC1's
frontmatter discriminator, and the sequel's `.claude/**` deny-prefix carve-out, which is why the
definition states the carve-out as an **exact path**.

**G8 — The write allowlist goes in frontmatter if the probe accepts it**; otherwise a fenced list under
a stable `## Write allowlist` heading in the definition body, parseable without harness support. A
tracked `.claude/settings.json` is adopted **only** if the probe shows it is the only place permissions
can live — and is then surfaced to the user as a new tracked file needing its own deny-set entry.

**G9 — The routing guard is a narrow curated denylist as an ordinary assertion, scanning entries only
and skipping the header.** A pytest warning nobody sees is a check that does not exist; but the header
legitimately names `docs/data-sources.md`, rate limits and era boundaries, so an unscoped scan would
redden against the file this plan tells the implementer to write. Terms are chosen so they cannot fire
on the canonical good entry, and the reasoning is recorded in the test docstring.

### Decisions this plan adds

1. **Phase 0 is a blocking gate with a two-stage STOP rule, not a note at the top of Phase 1.** Every
   shape-based criterion passes green in the dead-artifact failure case, because they check **form**.
   The sentinel round-trip is the specific evidence the **body** reached an agent. And a negative is
   **provisional** until re-probed in a fresh session, because "the harness has not re-scanned a file
   created mid-session" is a false negative that would return a viable feature to scoping.

2. **The `CLAUDE.md` relocation lands before the omission drill.** The single most consequential
   ordering call in the plan. `CLAUDE.md:95-97` states the grain rule today, and a panel-spawned
   subagent is **measured** to receive the full project `CLAUDE.md` unrequested (`PROJECT_SCOPE.md:143`).
   Run the drill first and a PASS is unattributable — inherited manager context, not the definition, may
   have carried it. Reordering these two phases for convenience destroys the feature's only behavioral
   evidence.

3. **AC1's "exactly one" is a frontmatter discriminator, not a file count** — its literal wording
   collides with the scope's own three-file deliverable, and a naive count guard reddens the moment the
   feature is complete.

4. **Guards land in the same phase as the artifact they assert.** The `CLAUDE.md`-pointer guard ships in
   Phase 3 with the pointer; the handoff linter ships in Phase 2 exercised only by synthetic inputs and
   gains its anti-vacuity coverage assertion in **Phase 4** — once, not in four places.

5. **Era boundaries are pointed at, not copied.** `CLAUDE.md:52-59` stays put, and the definition points
   at it. Copying would create a new unguarded duplicate, which is what Decision 12 exists to prevent.

6. **The hunk guard matches unified-diff header shapes**, and the return contract forbids `---`
   horizontal rules. A bare `^---` also matches YAML frontmatter and a Markdown thematic break, so a
   well-formed handoff with a section divider would otherwise fail; forbidding thematic rules means
   AC10's literal grep also comes back empty, so the guard and the criterion agree.

7. **Handoffs self-declare with `<!-- handoff: v1 -->`** and the linter walks
   `requests/*-requests/*/reviews/*.md`. A filename glob is brittle and track-specific; the marker keeps
   the linter track-agnostic and lets it ship in Phase 2 with synthetic controls.

8. **The rulebook is two self-contained sections** — `EXTRACTION & LANDING` and `DBT MODELING` — inside
   one definition, so a later split is a copy rather than a rewrite, without deciding it against zero
   evidence.

9. **The definition points at the layer READMEs** rather than paraphrasing them. Paraphrase creates a
   fifth copy of rules that already disagree with themselves in four places; a pointer inherits future
   edits for free and is proven to resolve by `tests/test_doc_links.py`.

10. **Memory paths stay inline code; only the `CLAUDE.md` pointer and layer-README references are
    markdown links.** The link checker scans only `[text](<path>)` syntax — a link is checked, which is what you
    want for the pointer and precisely what you do not want for a memory entry citing a file that may move.

11. **The omission drill copies `dbt_utils` into the scratch project; it does not point at the real
    project's install path and does not run `dbt deps`.** `transform/dbt_packages/` is **gitignored
    local state**, and pointing a second project's `packages-install-path` at it is
    destructive-adjacent. `dbt deps` is a network call the scope forbids for proving runs.

12. **Decision 7's doc half ships with its own workaround baked into the wording.** Verified:
    `AREA_TO_SPEC` has no `agents` key and resolves an unknown area to `[]` **silently**. A bare `agents`
    bucket entry would make stage-4 coverage **strictly worse than today**. The entry therefore reads
    *"also pass `skills`"*, `acceptance_panel.js` stays untouched per Decision 7, and ADR 0007 records
    the gap as a known open edge until the sequel lands the JS half.

13. **The status vocabulary is split deliberately, and this is a real repo inconsistency worth its own
    request.** This plan's blockquote reads `plan · … · decided · next: implement`, the form
    `create-implementation-plan/SKILL.md` prescribes and whose **third** field `/implement-plan` gates
    on. The track README Index cell reads **`planned`**, per the stage grammar at
    `requests/feature-requests/README.md:85` — which `CLAUDE.md` makes authoritative for its own track.
    Both are satisfied and neither is invented, but the two documents genuinely disagree; **a
    follow-up bugfix request should reconcile them**, and until then a cold implementer must not
    "fix" one to match the other.

14. **No new executable tooling**: no `ops/` snapshot script, no `.mjs` sibling, no changes to any panel
    script. **Honest note (finding M-08):** the `ops/` snapshot script is tiered `gated` in the scope but
    is **not** among the eleven gated decisions the user disposed — so "gated and declined" would
    overstate the record. It is treated as out of scope for v1 because the prose protocol is sufficient
    for two proving runs and this change's reviewability depends on staying small.

15. **The local gate matches CI's actual commands**, including `-m "not network"`. A plan whose "green"
    omits CI's own test selection produces a local pass that CI can still fail.

---

## 6. Risks & gotchas

- **DEAD-ARTIFACT RISK — the largest, and why Phase 0 cannot be skipped.** Verified: nothing in this
  repo consumes `.claude/agents/`. If the frontmatter shape or the spawn path is wrong, this ships three
  tidy Markdown files, a green suite, and zero capability — and AC1, AC2, AC4, AC5, AC6, AC7 and AC8 all
  still pass, because they check **form**. The sentinel round-trip is the only proof the body loaded.

- **RELOCATING THE RULEBOOK EDITS THE REPO'S MOST LOAD-BEARING FILE, AND A BAD CUT FAILS SILENTLY.** The
  highest-consequence clause in the repo travels with it: *"resolving as-of today instead of as-of the
  game is the most likely source of silently wrong joins in this project"* (`CLAUDE.md:113-116`). No
  test catches "this rule was needed in the manager doc and is now somewhere the manager doesn't look."
  Mitigations: add-then-remove ordering enforced by the Phase 2 guard, a pointer that **names** what
  moved, a standalone reviewable commit, a full prose re-read, and the surviving independent net at
  `acceptance_panel.js:192` / `:197`, which still enforces grain-plus-test, merge-on-key, the 2013-14
  boundary and as-of-game-date affiliation at stage 4 regardless of where the prose lives.

- **THE RELOCATION ALSO REMOVES THE PACING AND AFFILIATION WARNINGS FROM THE FILE EVERY PANEL READS**
  (finding A2-EX-16). `/scope-feature` and `/create-implementation-plan` both instruct their agents to
  read `CLAUDE.md`. After Phase 3 those warnings live one hop away behind the pointer. The pointer
  naming them by name is the whole mitigation, and it is weaker than having them inline.

- **INSTRUCTIONS ARE NOT ENFORCEMENT — the substitute guard is DETECTION, not PREVENTION.** The scar is
  specifically a write-capable agent that ran `git checkout` and silently wiped uncommitted work while a
  vacuous selftest passed green. Feature branch, pre-spawn snapshot, post-run comparison and `/commit`'s
  staged-list-then-yes all catch a bad write **afterward**; nothing stops it. The one genuinely new net
  is the **required-clean-tree precondition**: spawn a write-capable builder onto a dirty tree and a
  human can no longer tell the agent's writes from their own in the staged diff.

- **IF THE AGENT INHERITS `CLAUDE.md`, NARROWNESS CANNOT BE ACHIEVED BY OMISSION.** Measured for the
  panel spawn path: a panel-spawned subagent receives the full project `CLAUDE.md` unrequested. If
  `.claude/agents/` behaves the same way, the override preamble is the only thing creating the
  manager/developer seam, and a weak override makes this a normal agent with extra steps.

- **THE HARNESS FINDING CAN CHANGE UNDER A VERSION BUMP WITH NOTHING IN CI TO NOTICE.** Record the
  probed version alongside the finding and treat it as a **dated measurement**.

- **THE FOURTH-RESTATEMENT PROBLEM IS RELOCATED, NOT SOLVED.** `scope_panel.js:124`,
  `plan_panel.js:146` and `implement-plan/SKILL.md:100-112` each still restate these rules with no check
  that they agree, and Decision 12 removed the drift guard the panel had endorsed. After Phase 3,
  `CLAUDE.md` no longer states the rules at all, so those three copies have no canonical in-repo prose
  to be checked against except the agent definition. **ADR 0007 must say so** rather than implying
  relocation fixed it.

- **A HANDOFF LINTER THAT FINDS NO ARTIFACTS PASSES VACUOUSLY.** It lands in Phase 2 but its real inputs
  arrive in Phases 4–5. Mitigated by four synthetic controls immediately and the coverage assertion in
  Phase 4.

- **THE MEMORY FILE IS PUBLISHED AND FREE-TEXT.** ADR 0006 makes the repo public and history permanent;
  gitleaks catches credentials by content but not a carelessly pasted machine path, account ID, or
  response fragment. The seeded entries must model the discipline: cite repo artifacts, never paste raw
  environment output.

- **MEMORY IS A ROUTE AROUND THE DOC GATE, AND THE FIRST REAL TASK IS A DATA FACT.** The first task of
  the first feature is verifying the `leaguegamelog` shape. If that lands in memory the repo holds two
  answers while the gate audits one. The routing rule plus the `docs-delta` promotion queue are the
  whole mitigation, and gate #9 keeps the keyword check narrow rather than blocking.

- **A COMMITTED MEMORY NOBODY PRUNES GROWS MONOTONICALLY.** Curation is deliberately deferred, so the
  only bounds are the cap and a human's read at `/commit`. The **at-cap rule** (append nothing, report
  under `still-open`) is what stops a write-capable agent from silently deleting an older entry or
  silently skipping what it learned.

- **PROVING-RUN EVIDENCE IS INHERENTLY WEAK.** Two drills is two observations, not a property. Claiming
  "the design holds" is a convention violation under `CLAUDE.md:76-79`, not merely optimistic — and ADR
  0007's Consequences section is immutable once accepted.

- **PREMISE RISK, carried from the scope and not re-litigated.** `/implement-plan` has never run in this
  repo. If the first real stage-4 run fits comfortably in one context, this agent is maintenance burden
  — the over-processing failure mode ADR 0001 names as the specific hazard of this repo's philosophy.
  The mitigation is structural: every phase small, reversible and independently committable, so the cost
  of being wrong is bounded by what has already landed.

- **THE POST-PANEL AMENDMENTS WERE NEVER ADVERSARIALLY REVIEWED AT SCOPING TIME**
  (`PROJECT_SCOPE.md:324-327`). Stage 3's code-grounded adversaries have now attacked Decision 12 — the
  results are in `reviews/plan-adversarial.md`, and Phase 3 carries the corrections. Decision 13's
  dispatch design remains un-attacked; it belongs to the sequel.

---

## 7. Files to touch (checklist)

| Path | Phase | Change |
|---|---|---|
| `.claude/agents/data-engineer.md` | 1 | **NEW** — frontmatter exactly as Phase 0 confirmed. Role framing, override preamble, the relocated rulebook in two sections, layer-README pointers, era-boundary pointer, memory pointer (inline code), write allowlist + 7-path deny set, tool allowlist, git-read-only absolute, routing rule under `## Routing`, escalation policy, return contract, spec-triage mode, prohibitions. |
| `.claude/agents/data-engineer-memory.md` | 1 | **NEW** — no frontmatter, ≤120 physical lines, header stating scope + entry format + inline-code convention + five-label vocabulary + the at-cap rule. Seeded with 2–4 cited entries. |
| `.claude/agents/README.md` | 1 | **NEW** — no frontmatter. Directory contract, one-definition rule, memory carve-out as an exact path, main-thread spawn protocol. |
| `tests/test_repo_structure.py` | 2 | **EDIT** — add the `.claude/agents/` structural + frontmatter guard (AC1), glob-discovered. |
| `tests/test_agent_contract.py` | 2, +3 | **NEW** — pure predicates + `tmp_path` negative controls for guardrail clauses, relocated-rulebook clauses, deny set, tool allowlist, budgets, memory entry format + header-exempt routing denylist. The `CLAUDE.md`-pointer guard is added in Phase 3 with its subject. |
| `tests/test_handoff_contract.py` | 2, +4 | **NEW** — `lint_handoff()` + marker-driven walker. Four synthetic controls in Phase 2; the anti-vacuity coverage assertion in Phase 4. |
| `CLAUDE.md` | 3 | **EDIT** — cut `## Data Layer` (`:84-103`) and four gotcha bullets. Keep `:117-119`, `:120-121`, `:122-125` and Key Context. Add the resolving pointer, the `.claude/agents/` map row, and the clarified subagent bullet. |
| `.claude/skills/implement-plan/SKILL.md` | 3 | **EDIT** — add `agents` to the bucket list at `:127-132` **with the "also pass `skills`" workaround**. Obliges running both `.mjs` guards by hand. |
| `.claude/skills/update-docs/SKILL.md` | 3 | **EDIT** — add `agents` to `:47-48` with the same workaround; point the rules check at the relocated rulebook; reconcile the line-count one-liner at `:76-78`. |
| `.claude/skills/implement-plan/acceptance_panel.js` | — | **DO NOT TOUCH.** Listed so the omission is legible as deliberate. Verify with `git diff HEAD --stat` that no `.js` appears. |
| `README.md` | 4 | **EDIT, written by the AGENT** — the faithful-run target: a short section on `.claude/agents/` and the spawn protocol, **plus** the `## Repo layout` entry so the file stays consistent. |
| `reviews/harness-probe.md` | 0 | **NEW** — PROCEED/STOP verdict, exact commands, fenced real output, harness version, one `verified`/`measured` label per answer, both probe attempts if the first was negative. |
| `reviews/proving-run-a.md` | 4 | **NEW** — the faithful handoff + the pre/post tree-integrity pair + the AC12 verdict + the repetition label. |
| `reviews/proving-run-b.md` | 5 | **NEW** — the omission drill: spec as given, quoted artifacts, `dbt build` output, greps, PASS/FAIL per run, every attempt, tree state. |
| `docs/decisions/0007-write-capable-implementation-subagent.md` | 6 | **NEW, deliberately last** — five sections, status `accepted`, uncomfortable Consequences. |
| `docs/decisions/README.md` | 6 | **EDIT** — one Index row with a resolving link. |
| `requests/feature-requests/README.md` | 3 (stage), 6 | **EDIT** — Index Stage cell: `planned` at the end of stage 3, `implemented` at the end of stage 4. |
| `FEATURE_REQUEST.md` | 6 | **EDIT** — status blockquote only. |
| `PROJECT_SCOPE.md` | — | **DO NOT EDIT.** AC16 pins it at `scoped · decided · next: plan`. |
| `IMPLEMENTATION_REPORT.md` | stage 4 | **NEW at stage 4** — the acceptance ledger against all 16 criteria, each RECORDED-EVIDENCE or USER-RUN marked so the panel does not claim it. |
| `var/scratch/omission-drill/` | 5 | **NEW, GITIGNORED, NEVER STAGED** — scratch dbt project with a **copied** `dbt_utils`, in-memory DuckDB profile, two seeds. |
| `var/tmp/` | 4, 5 | **NEW, GITIGNORED** — create it first; pre-spawn snapshots via `git diff HEAD --output=…`. A safety net, not evidence. |

---

## 8. Conventions (bake these in)

- **Agents commit only through `/commit`.** Every phase ends at a `/commit`-gated checkpoint; never
  `git commit` ad hoc, not for a one-line change. **Never merge, push, or amend** — those stay the
  user's, and `main` is protected. AC15 is USER-RUN for exactly this reason.
- **Subagents get read-only git**, and this plan bakes that into the definition as an absolute naming
  the verbs literally, with the recorded scar as its reason. The clarification this feature adds does
  not weaken it: **editing a tracked file is not a git operation**, so a write-capable builder with a
  declared allowlist is inside the rule rather than an exception to it.
- **Resolve by name, never hardcode.** Two applications here: the definition must carry the rule, and
  the new guards must **discover the definition by globbing** `.claude/agents/*.md` rather than
  hardcoding its filename. The `parents[1]` idiom in `tests/` is the repo's own established precedent —
  follow it, note it in a docstring, and do not reinvent it.
- **The landing zone is immutable · bronze is 1:1 with the source · silver declares its grain and proves
  it with a uniqueness test · facts `MERGE` on key · layer promotion is gated on tests · no bulk data in
  git.** No code here touches a landed payload, but the definition must carry every one of these and the
  Phase 2 clause-presence guard asserts they survived the move. **Silver's grain rule is the single
  invariant the omission drill measures.**
- **Era boundaries are explicit.** Tracking-derived columns are **structurally absent** before 2013-14,
  not missing, and the three irregular seasons break any 82-game assumption. These stay in `CLAUDE.md`
  Key Context; the definition points at them.
- **Anything that spends cloud money or touches prod is user-run.** Nothing in this change spends money
  or hits `stats.nba.com` — the drill runs offline against in-memory DuckDB. The definition restates the
  rule because the agent will later write extraction code. The push and the PR are user-run for the same
  class of reason.
- **Label your epistemics.** Every memory entry carries one of the five labels; the probe artifact
  carries `verified` or `measured` per answer and never `unconfirmed`; the relocated bulk-endpoint
  bullet **keeps** its `unconfirmed` label so the agent does not build on it as fact; and proving-run
  evidence is labelled an **observation**, not a proof.
- **Mechanical checks live in CI; judgment lives in `/update-docs`.** The guard suite goes under
  `tests/` where branch protection makes it required; the doc-drift judgment runs at the Phase 3 and
  Phase 6 checkpoints. Do not push judgment into a keyword guard.
- **Every dataset comes from a feature request — and this change lands none.** Asserted mechanically in
  Phase 5, in PowerShell.
- **Windows dev, Linux CI.** `.gitattributes` normalizes to LF. Write every file with the Write/Edit
  tools, never PowerShell `Set-Content`/`Out-File`. Acceptance criteria are **PowerShell** commands —
  `find`, `grep` and bash test syntax do not exist on this box, and an acceptance check that cannot run
  is an acceptance check that passes vacuously.
- **Renaming a CI job silently breaks branch protection.** No job is renamed here, and the three
  display-name contexts stay exactly as they are.

---

## 10. Code-grounding verification

The stage-3 panel ran twice. The first attempt lost the structured merge and the code-grounded adversary
to API failures; it was **not used**. The run was resumed with the three planner proposals replayed from
cache, and the second attempt completed with **3/3 planners, 2/2 adversaries, 1/1 meta-audit and no
degraded lenses** — 46 findings, 1 blocker, 18 majors. The full trail is in
[`reviews/plan-adversarial.md`](reviews/plan-adversarial.md) and
[`reviews/plan-proposals.md`](reviews/plan-proposals.md).

**78 cited references checked by the code-grounded adversary; 10 re-verified independently by the main
thread; 14 corrections applied.** The corrections that changed the plan:

| Cited claim | Verified result → correction applied |
|---|---|
| Phase 0's spawn mechanism | **Unnamed** — "whatever surface the harness exposes". Now names the `subagent_type` parameter, with a two-stage STOP rule so a mid-session false negative cannot kill a viable feature. |
| Decision 3 (restricted Bash) | **Dropped by all three planners.** Restored as a tool allowlist distinct from the write allowlist, with its own guard. |
| `AREA_TO_SPEC` has an `agents` key | **False** — `acceptance_panel.js:202-206` has none, and `:207` resolves an unknown area to `[]` silently. Bucket-list entries now carry the "also pass `skills`" workaround. |
| `dbt_utils` is available offline | **Half true** — present at `transform/dbt_packages/` but **gitignored** (`.gitignore:50`), i.e. untracked local state; CI obtains it via `dbt deps` (`ci.yml:70-71`). Now: copy it into the scratch project, never point at the real one. |
| Omission-drill PASS by grep | **Insufficient** — a grep scores a test that never ran. Now requires the scratch project to build with the test PASSing, plus the grain-vs-test agreement check. |
| `find` / `grep` in acceptance criteria | **Unrunnable** on a PowerShell-only box. Converted to `Get-ChildItem`/`Select-String`. |
| Index Stage cell reads `plan` | **Off-grammar** — `requests/feature-requests/README.md:85` states `intake → scoped → planned → implemented`. Index reads `planned`; the divergence from the skill's template is recorded in Decision 13. |
| Advance `PROJECT_SCOPE.md`'s blockquote | **Mechanically fails AC16**, which pins it at `scoped`. Removed from the checklist. |
| Local gate = `uv run pytest -q` | **Not CI's command** — CI runs `-m "not network"` and `ruff check --output-format=github`. Gate corrected. |
| Snapshot protocol is "verbatim" | **Two of five commands are not in the cited lines.** Re-attributed as stage 4's procedure *extended*. |
| `var/tmp/` exists | **False** on a fresh clone. Create it first; use `git diff --output=` to avoid a PowerShell BOM. |
| Clean tree + `git diff HEAD` snapshot | **Always empty** by construction. The load-bearing captures are status, untracked list, HEAD and stash list. |
| AC13 routing guard | **Vacuous** — the relocated pacing bullet already puts `docs/data-sources.md` in the file. Guard now asserts the `## Routing` heading and its content. |
| Memory at cap | **Undefined behavior.** At-cap rule added: append nothing, report under `still-open`. |
| `CLAUDE.md` = 122 lines | **Both counts real** — 122 non-blank, 140 physical. Gate #1 pins physical. |
| `test_repo_structure.py:19`, `:77-84`; `test_doc_links.py:53`; `ci.yml` job count; `.claude/settings.json` absent; 33 tracked `.md` | **All confirmed** by direct re-verification. |

---

## References

- [`PROJECT_SCOPE.md`](PROJECT_SCOPE.md) — the decided contract. Do not re-open it.
- [`FEATURE_REQUEST.md`](FEATURE_REQUEST.md) — context and the four observable signals.
- [`reviews/plan-adversarial.md`](reviews/plan-adversarial.md) — 46 findings, three reviewer summaries,
  the convergence map, the gates as emitted, and the run history.
- [`reviews/plan-proposals.md`](reviews/plan-proposals.md) — the three planners' raw proposals.
- [`CLAUDE.md`](../../../CLAUDE.md) — the map, the conventions, and the rulebook that moves.
- [`../README.md`](../README.md) — the intake contract, the layout, and the status grammar.
- [`../../../docs/decisions/README.md`](../../../docs/decisions/README.md) — required ADR sections, the
  immutability rule, and the Index that gains a row.
- `.claude/skills/implement-plan/SKILL.md` · `.claude/skills/update-docs/SKILL.md` ·
  `.claude/skills/commit/SKILL.md` — prior art, the doc gate, and the committer.
- `.github/workflows/ci.yml` · `ops/branch-protection.json` · `pyproject.toml` — the real gates.
- `transform/models/silver/README.md` · `transform/models/bronze/README.md` — the layer contracts the
  definition points at.
