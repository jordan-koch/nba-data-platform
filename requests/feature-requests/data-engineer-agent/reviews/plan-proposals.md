# Plan Panel - Raw Proposals (data-engineer-agent)

> Stage 3 provenance. The three divergent planners' raw, unfiltered proposals, as returned.
> Panel run `wf_7be42ca6-2f7`, 2026-08-13/14.
>
> **Panel health: 3/3 planners, 2/2 adversaries, 1/1 meta-audit, no degraded lenses.**
> These three proposals are from the FIRST attempt and were replayed from cache on the resume,
> so they are the same proposals both the failed and the successful merge consumed. See
> `plan-adversarial.md` for the run history, including the first attempt's degradation.
>
> Content below is fenced: it carries Markdown link syntax and file paths that do not resolve
> from `reviews/`, and `tests/test_doc_links.py` scans every tracked Markdown file.

~~~~~

===============================================================================
PLANNER: code-grounded
===============================================================================
architecture_notes:
  CURRENT STRUCTURE OF THE TOUCHED AREA (all measured today, 2026-08-13, against git ls-files and the filesystem)

  1. `.claude/` holds skills only: 16 tracked files under `.claude/skills/` — 8 `SKILL.md` files (commit, create-implementation-plan, diagnose-bug, implement-plan, make-bugfix-request, make-feature-request, scope-feature, update-docs), 3 panel scripts (`scope_panel.js`, `plan_panel.js`, `acceptance_panel.js`), 5 `.mjs` self-verification guards. `.claude/agents/` does NOT exist (Test-Path = False). There is no `.claude/settings.json` and no `.claude/settings.local.json`. `.gitignore` contains no `.claude` entry, so anything written there is tracked by default.

  2. The repo's own subagent machinery does not consume `.claude/agents/`. Spawning happens inside the panel scripts: `scope_panel.js:174` calls `runChecked(prompt, { label, phase, schema, effort }, ...)` which wraps `agent(prompt, opts)` (`scope_panel.js:105-115`) — there is no agent-type/subagent-type parameter anywhere in the three panel scripts. Narrowness is achieved today by prompt text, not by a definition file.

  3. HARNESS EVIDENCE (measured, this session, read-only): the installed `claude` CLI (`<user-profile>\AppData\Roaming\npm\claude.ps1`) exposes `--agent <agent>` ("Agent for the current session. Overrides the 'agent' setting"), `--agents <json>` (inline agent definitions with `description` + `prompt` keys), `--setting-sources <user,project,local>`, and a `claude agents` subcommand for background agents; its plugin blurb names "custom commands and agents" as plugin-provided content. So the harness has a first-class agent concept with a project-level settings source. What is still UNCONFIRMED and must be probed: whether a project `.claude/agents/*.md` file is discovered at all, the exact frontmatter schema it accepts (`name`/`description`/`tools`/`model`?), where a machine-readable tool allowlist is declared, whether such an agent inherits project `CLAUDE.md`, and whether it sees project skills. Also measured: no `~/.claude/agents/` directory exists, and `~/.claude/settings.json` carries only permissions/autoMode/tui/skipWorkflowUsageWarning/theme/agentPushNotifEnabled — no agent key. Nothing in this repo or the user profile proves the loader path; Phase 0 exists to settle it and to stop the build on a negative.

  4. ENFORCEMENT SEAM. `.github/workflows/ci.yml` has exactly three jobs — `Lint, types, tests` (:26-27), `dbt build` (:55-56), `Secret scan` (:87-88) — and no Node step, so the five `.claude/skills/**/tests/*.mjs` guards run only when an agent remembers. `ops/branch-protection.json:4` makes those three display names required contexts. Therefore every new guard goes into `tests/` where pytest is a required check. `tests/` today is two files: `test_repo_structure.py` (7 tests, REPO_ROOT via `parents[1]` at :19) and `test_doc_links.py` (2 tests).

  5. DOC SEAM. `CLAUDE.md` is 140 physical lines. Its `## Data Layer` section spans :84-103 (heading :84, seven bullets :86-103) and is the rulebook Decision 12 relocates. `## Constraints & Gotchas` spans :105-126; four bullets relocate (stats.nba.com pacing :107-109, prefer bulk endpoints :110-112, affiliation is date-dependent :113-116, Windows/LF :126) and three stay (cost guardrail :117-119, the `pre-commit` naming note :120-121, the CI-rename/branch-protection trap :122-125 — the agent is denied `.github/` and `ops/` anyway). The project map block is :16-33; the subagent bullet is :73-75. `README.md` (117 lines) mentions neither `.claude` nor skills, so it needs no map edit.

  6. LINK SEAM. `tests/test_doc_links.py` walks every `*.md` under the repo root except `EXCLUDED_PARTS` (:31-48 — no `.claude` entry), so the three new `.claude/agents/*.md` files and every `reviews/` artifact are link-checked automatically and for free. Consequence for the relocation: any relative link that moves out of `CLAUDE.md` into `.claude/agents/<agent>.md` must be rewritten two levels deeper (`docs/data-sources.md` -> `../../docs/data-sources.md`, `transform/models/silver/README.md` -> `../../transform/models/silver/README.md`). Memory-file paths stay INLINE CODE, never markdown links, because `MARKDOWN_LINK` (:56) only sees link syntax — a backticked path can never redden CI on an unrelated PR.

  7. WHERE THE CHANGE HOOKS IN — six seams, all additive except the CLAUDE.md cut:
     (a) filesystem: new `.claude/agents/` directory holding README + definition + memory;
     (b) enforcement: new guards in `tests/test_repo_structure.py` (structural/frontmatter, per AC1) and a new `tests/test_agent_contract.py` (clause presence, budgets, memory entry format, routing rule, handoff lint, all with negative controls);
     (c) doc: CLAUDE.md map row + subagent clarification + rulebook cut and pointer; `implement-plan/SKILL.md:127-132` and `update-docs/SKILL.md:47-48` bucket lists gain `agents` (Decision 7's doc half only — `acceptance_panel.js` AREA_TO_SPEC stays untouched);
     (d) decision record: `docs/decisions/0007-*.md` + the Index row at `docs/decisions/README.md:39-46`;
     (e) spawn protocol: prose in `.claude/agents/README.md` reusing `implement-plan/SKILL.md:120-125` and `:187-190` verbatim — no new executable tooling (the ops/ snapshot script was gated and declined for this request);
     (f) provenance: `requests/feature-requests/data-engineer-agent/reviews/` gains harness-probe.md, proving-run-a.md, proving-run-b.md.

  8. TWO NAMING/STRUCTURE FACTS THE IMPLEMENTER MUST SETTLE UP FRONT. First, AC1's literal wording ("`.claude/agents/` contains exactly one `*.md` agent definition") collides with the scope's own core deliverables, which put THREE `.md` files in that directory (definition, memory, README). The guard must discriminate by YAML frontmatter: exactly one `*.md` in `.claude/agents/` parses to a frontmatter mapping with non-empty `name` and `description`; `README.md` and the memory file must carry NO frontmatter, and the guard asserts that too. Second, the memory file lives under `.claude/`, which the sequel's dispatch rule (PROJECT_SCOPE.md:478-482) treats as every agent's deny prefix — the memory carve-out (Decision 11, blocker F1) is what keeps that consistent, and the definition must state the carve-out as an explicit path, not as a prefix rule.
code_references:
  - [1]
    claim:
      The pre-spawn snapshot protocol the write-guard package reuses verbatim — write `git diff HEAD` to gitignored scratch and record untracked files before spawning; it also records the scar (a write-capable review agent ran `git checkout` and wiped uncommitted work while a vacuous selftest passed green).
    ref: .claude/skills/implement-plan/SKILL.md:120-125
  - [2]
    claim:
      The post-run tree-integrity re-check ("Re-verify tree integrity" — re-check `git status` against the snapshot and grep for symbols you implemented; a passing selftest does not prove your code is still there).
    ref: .claude/skills/implement-plan/SKILL.md:187-190
  - [3]
    claim:
      The stage-4 invariant restatement the relocated rulebook must mirror without contradicting; :111-112 is the PowerShell 5.1 `Set-Content`/`Out-File` UTF-8 trap seeded into memory.
    ref: .claude/skills/implement-plan/SKILL.md:100-112
  - [4]
    claim:
      The touched-area bucket list (`transform` · `src` · `tests` · `skills` (`.claude/skills/`) · `infra` · `ci` · `config` · `orchestration` · `docs`) that gains an `agents` entry in Phase 2.
    ref: .claude/skills/implement-plan/SKILL.md:127-132
  - [5]
    claim: "The panel's subagents are read-only" — the rule this feature carves a deliberate, guarded exception to.
    ref: .claude/skills/implement-plan/SKILL.md:155-156
  - [6]
    claim:
      The two bundled `.mjs` self-verification guards that must be run by hand whenever this SKILL.md changes: `merge_fallback_guard.mjs` and `verify_batching_guard.mjs` (CI has no Node step).
    ref: .claude/skills/implement-plan/SKILL.md:271-273
  - [7]
    claim:
      `READONLY` — the absolute read-only-but-verification-capable mandate whose structure a write-capable allowlist inverts, carrying the recorded `git checkout` scar verbatim.
    ref: .claude/skills/implement-plan/acceptance_panel.js:161-163
  - [8]
    claim:
      The `skill-quality` specialist mandate (valid frontmatter with name + trigger-rich description, progressive disclosure, registration, convention honoring, resolving links) — applies verbatim to an agent definition.
    ref: .claude/skills/implement-plan/acceptance_panel.js:199
  - [9]
    claim: `AREA_TO_SPEC` — verified to have no `agents` key, so `.claude/agents/` draws no specialist reviewer unless `touchedAreas` includes `skills`.
    ref: .claude/skills/implement-plan/acceptance_panel.js:202-206
  - [10]
    claim:
      The spawn call — `runChecked(prompt, { label, phase, schema, effort }, ...)` wrapping `agent(prompt, opts)` — with no agent-type parameter, which is why nothing in this repo consumes `.claude/agents/` today.
    ref: .claude/skills/scope-feature/scope_panel.js:174
  - [11]
    claim:
      The recorded StructuredOutput placeholder-degeneration behavior and the `ANTISTUB`/`ANTISTUB_RETRY` apparatus — the grounded reason the return contract is prose sections in a linted file rather than a forced schema.
    ref: .claude/skills/scope-feature/scope_panel.js:27-34
  - [12]
    claim:
      The compressed, pointer-shaped invariant restatement whose SHAPE the definition's rulebook framing follows (one of the four existing restatements this relocation does not collapse).
    ref: .claude/skills/scope-feature/scope_panel.js:124
  - [13]
    claim: The `## Data Layer` section (heading at :84, seven bullets :86-103) that relocates into the agent definition under Decision 12.
    ref: CLAUDE.md:84-103
  - [14]
    claim:
      `## Constraints & Gotchas`: :107-109 pacing, :110-112 prefer-bulk-endpoints (still `unconfirmed`), :113-116 affiliation-is-date-dependent and :126 Windows/LF relocate; :117-119 cost, :120-121 `pre-commit` naming and :122-125 the CI-rename/branch-protection trap stay.
    ref: CLAUDE.md:105-126
  - [15]
    claim: The subagent read-only-git bullet that Phase 2 clarifies so a write-capable builder is legible as inside the rules rather than an exception.
    ref: CLAUDE.md:73-75
  - [16]
    claim: The project-map block that gains a `.claude/agents/` row, directly under the `.claude/skills/` line at :27.
    ref: CLAUDE.md:16-33
  - [17]
    claim:
      The five-label epistemic vocabulary (measured/verified/inferred/assumed/unconfirmed) the memory entries adopt — differing from `update-docs/SKILL.md:105`'s four and `docs/data-sources.md`'s three.
    ref: CLAUDE.md:76-79
  - [18]
    claim: `test_every_layer_documents_itself` — the structural-agreement analogue AC1 names, and the assertion-message style the new agents guard imitates.
    ref: tests/test_repo_structure.py:77-84
  - [19]
    claim: `import yaml` already present (pyyaml + types-PyYAML are dev deps at pyproject.toml:20-22), so the frontmatter guard needs no new dependency.
    ref: tests/test_repo_structure.py:17
  - [20]
    claim: `REPO_ROOT = Path(__file__).resolve().parents[1]` — the constant the new guards reuse rather than re-deriving.
    ref: tests/test_repo_structure.py:19
  - [21]
    claim:
      `EXCLUDED_PARTS` — verified to contain no `.claude` entry, so the three new `.claude/agents/*.md` files and every `reviews/` artifact are link-checked automatically.
    ref: tests/test_doc_links.py:31-48
  - [22]
    claim:
      `FENCED_BLOCK` (fenced content exempt — how to write a forward reference or quoted diff), `MARKDOWN_LINK` (only link syntax is scanned, which is why memory paths stay inline code), `LINE_SUFFIX` (a `file.py:123` citation suffix is stripped).
    ref: tests/test_doc_links.py:55-57
  - [23]
    claim: `test_the_guard_actually_covers_the_repo` — the anti-vacuity guard (`MIN_EXPECTED_FILES = 20` at :53) that every new guard's negative control imitates.
    ref: tests/test_doc_links.py:95-104
  - [24]
    claim: The `Lint, types, tests` job — ruff check, ruff format --check, mypy, pytest (:41-53). One of the three required contexts.
    ref: .github/workflows/ci.yml:26-27
  - [25]
    claim: The sqlfluff step guarded by a find for `*.sql`, because sqlfluff errors on an empty selection — a real, verifiable memory seed entry.
    ref: .github/workflows/ci.yml:78-85
  - [26]
    claim: Gitleaks — the secret scan that will cover the committed memory file, catching credentials by content but not a pasted path or machine detail.
    ref: .github/workflows/ci.yml:96-99
  - [27]
    claim:
      The three required status-check contexts matched by CI job DISPLAY NAME: `Lint, types, tests`, `dbt build`, `Secret scan` — why guards go under `tests/` rather than as a `.mjs` sibling.
    ref: ops/branch-protection.json:4
  - [28]
    claim:
      Ruff at line-length 100 selecting E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF — the new test code must use pathlib (PTH), avoid naive datetimes (DTZ), and not shadow builtins (A).
    ref: pyproject.toml:43-64
  - [29]
    claim: `mypy strict = true` over `files = ["src", "tests"]` — every new test function and fixture needs full annotations.
    ref: pyproject.toml:70-74
  - [30]
    claim:
      The `transform` dependency group already provides dbt-core, dbt-duckdb and duckdb, so the omission drill's scratch project under `var/` needs no new dependency.
    ref: pyproject.toml:24-30
  - [31]
    claim:
      The 200-line `CLAUDE.md` budget enforced today only by asking an agent to run `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` — the judgment rule the memory-budget guard mechanizes, and the source of the counting-method discrepancy (122 vs 140 measured).
    ref: .claude/skills/update-docs/SKILL.md:76-78
  - [32]
    claim: The doc gate's bucket list that gains `agents` in Phase 2.
    ref: .claude/skills/update-docs/SKILL.md:47-48
  - [33]
    claim: The `docs/data-sources.md` epistemic-label audit the memory routing rule must not route around; :105 names four labels where CLAUDE.md names five.
    ref: .claude/skills/update-docs/SKILL.md:103-112
  - [34]
    claim: The missing-ADR rule ("a choice someone would reasonably ask 'why did you do it that way' about") that makes ADR 0007 near-mandatory.
    ref: .claude/skills/update-docs/SKILL.md:100-101
  - [35]
    claim:
      Per-path staging and the refusal table — the actual review gate this design leans on; row :59 refuses anything under `var/`, which is why drill-B evidence must be quoted into committed `reviews/`.
    ref: .claude/skills/commit/SKILL.md:47-67
  - [36]
    claim: The branch check — `main` is protected, so both proving runs happen on a feature branch.
    ref: .claude/skills/commit/SKILL.md:42-45
  - [37]
    claim: The five required ADR sections (Status / Context / Decision / Consequences / Alternatives considered) ADR 0007 must carry.
    ref: docs/decisions/README.md:19-25
  - [38]
    claim: Accepted ADRs are immutable — write a superseding one — which is why ADR 0007 is written after the proving runs (Decision 10).
    ref: docs/decisions/README.md:29-32
  - [39]
    claim: The Index table (0001-0006, all `accepted`) that gains the 0007 row.
    ref: docs/decisions/README.md:39-46
  - [40]
    claim: "The failure mode is picking the wrong thing to inflate" — the standing over-processing risk this feature's premise risk instantiates.
    ref: docs/decisions/0001-deliberate-over-engineering.md:18-20
  - [41]
    claim:
      Testing, CI/CD, governance, incident process and documentation are turned all the way up because they are free of scale; what is explicitly declined is infrastructure over-reach — the register ADR 0007 must match.
    ref: docs/decisions/0001-deliberate-over-engineering.md:27-32
  - [42]
    claim: Getting silver wrong is the most expensive mistake available in this project — the grounded reason no proving run may target `transform/models/`.
    ref: transform/models/silver/README.md:5-7
  - [43]
    claim:
      The declare-the-grain-and-prove-it contract (a `dbt_utils.unique_combination_of_columns` example) that the omission drill tests and that the definition points at rather than paraphrasing.
    ref: transform/models/silver/README.md:9-25
  - [44]
    claim:
      What "testable" means here (a cold agent runs one command and gets pass/fail) and the rule that human-only criteria must be marked user-run — the basis for AC14 and AC15's marking.
    ref: requests/feature-requests/README.md:45-59
  - [45]
    claim: The `data-engineer-agent` Index row, currently at Stage `scoped`, that advances to `plan` then `implemented`.
    ref: requests/feature-requests/README.md:92
  - [46]
    claim:
      "Capture them with the recorder" — adjacent drift (no recorder exists; `src/nba_platform/` is one `__init__.py`) that must NOT be absorbed as a convenient proving-run target, since `tests/` is in the agent's deny set.
    ref: tests/fixtures/README.md:11-13
  - [47]
    claim:
      The epistemic-status blockquote naming only three labels (verified / documented / unconfirmed) and stating the catalog is `unconfirmed` throughout — the destination the memory routing rule protects.
    ref: docs/data-sources.md:5-10
files_to_touch:
  - [1]
    change:
      NEW — the agent definition. Frontmatter in the schema Phase 0 confirms. Body: role framing, override preamble, the relocated build rulebook in two self-contained sections (extraction/landing, dbt modeling), pointers to `../../transform/models/bronze/README.md` and `../../transform/models/silver/README.md`, the memory pointer as inline code, the return contract, the three-way escalation policy, the write allowlist + extended deny set, git-read-only as an absolute with its reason, the pipeline-skill and self-edit prohibitions, and spec-triage (dry-run) mode.
    path: .claude/agents/data-engineer.md
  - [2]
    change:
      NEW — committed, no frontmatter, ≤120 physical lines. Header stating what belongs and what routes elsewhere, the per-entry format (date · epistemic label · claim · evidence pointer · routing tag), the inline-code-paths convention, and 2-4 seeded entries each traceable to a repo artifact or the Phase 0 probe.
    path: .claude/agents/data-engineer-memory.md
  - [3]
    change:
      NEW — no frontmatter. What the directory is, the one-definition-per-agent rule, the memory carve-out, and the main-thread spawn protocol reproduced from `implement-plan/SKILL.md:120-125` and `:187-190` (feature branch, clean-tree precondition, pre-spawn snapshot to gitignored `var/`, post-run integrity comparison into `reviews/`).
    path: .claude/agents/README.md
  - [4]
    change:
      EDIT — delete `## Data Layer` (:84-103) and four Constraints & Gotchas bullets (:107-109, :110-112, :113-116, :126); keep :117-119, :120-121, :122-125. Add a resolving pointer to `.claude/agents/data-engineer.md`, add a `.claude/agents/` row to the project map (:16-33, under the `.claude/skills/` line at :27), and rewrite the subagent bullet (:73-75) so read-only git and file-write permission are distinguishable.
    path: CLAUDE.md
  - [5]
    change:
      EDIT — add the `.claude/agents/` structural + frontmatter guard (AC1), reusing `REPO_ROOT` (:19) and the already-imported `yaml` (:17), in the style of `test_every_layer_documents_itself` (:77-84). Exactly one frontmatter-bearing `*.md`; README and memory carry none.
    path: tests/test_repo_structure.py
  - [6]
    change:
      NEW — guardrail-clause presence (AC2), the CLAUDE.md pointer (AC3-replacement), memory + CLAUDE.md line budgets with the counting method named in the message (AC4), memory entry format and the warning-shaped routing check (AC13, Decision 9), and the handoff schema lint (sections present/non-empty, under cap, no diff-hunk headers) (AC10). Every check a pure function over text/path, each with a `tmp_path` negative control. Must satisfy `mypy --strict` and ruff's `PTH`/`DTZ`/`N`/`B`/`A` selection.
    path: tests/test_agent_contract.py
  - [7]
    change:
      EDIT — add `agents` to the touched-area bucket list at :127-132, alongside `skills` (`.claude/skills/`). Decision 7's doc half only. Changing this file obliges running both bundled `.mjs` guards by hand (CI has no Node step).
    path: .claude/skills/implement-plan/SKILL.md
  - [8]
    change:
      EDIT — add `agents` to the bucket list at :47-48, and one checklist item under the CLAUDE.md section so the doc gate's rules check follows the relocated content into `.claude/agents/data-engineer.md` and also eyeballs the memory file's budget and its freedom from data facts.
    path: .claude/skills/update-docs/SKILL.md
  - [9]
    change:
      NEW — Status `accepted` / Context / Decision / Consequences / Alternatives considered, per `docs/decisions/README.md:19-25`. Written after the proving runs (Decision 10) because accepted ADRs are immutable (:29-32). Consequences must state that the guard is detection rather than prevention, that the premise is inferred not measured, and label the proving-run evidence a single observation if each drill ran once.
    path: docs/decisions/0007-write-capable-implementation-subagent.md
  - [10]
    change: EDIT — add the 0007 row to the Index table at :39-46 with a resolving relative link.
    path: docs/decisions/README.md
  - [11]
    change: EDIT — the `data-engineer-agent` Index row at line 92 advances Stage to `plan` at the end of stage 3 and to `implemented` at the end of stage 4.
    path: requests/feature-requests/README.md
  - [12]
    change: NEW — this stage's deliverable, opening at `plan · created <today> · decided · next: implement`.
    path: requests/feature-requests/data-engineer-agent/IMPLEMENTATION_PLAN.md
  - [13]
    change:
      NEW — Phase 0's recorded finding: exact probe commands, real output (fenced), answers to both halves of AC9 labeled `measured`/`verified`, the harness version, and what the probe could not settle.
    path: requests/feature-requests/data-engineer-agent/reviews/harness-probe.md
  - [14]
    change:
      NEW — the faithful run's handoff (all required sections, evidence-carrying verified table, no diff hunks, under cap) plus the pre/post tree-integrity capture, fenced.
    path: requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md
  - [15]
    change:
      NEW — the omission drill: the spec text, the produced artifacts quoted verbatim out of gitignored `var/` scratch, the grep commands and real output, the PASS/FAIL verdict, and the pre/post tree-integrity capture.
    path: requests/feature-requests/data-engineer-agent/reviews/proving-run-b.md
  - [16]
    change: EDIT (bookkeeping only, AC16) — status blockquote advanced; its body is decided and must not be re-litigated.
    path: requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md
  - [17]
    change: EDIT (bookkeeping only, AC16) — status blockquote advanced.
    path: requests/feature-requests/data-engineer-agent/FEATURE_REQUEST.md
  - [18]
    change: NEW at stage 4 — the acceptance ledger against all 16 criteria, per `implement-plan/SKILL.md:237-265`.
    path: requests/feature-requests/data-engineer-agent/IMPLEMENTATION_REPORT.md
  - [19]
    change:
      NEW, GITIGNORED, NEVER STAGED — the scratch dbt project for proving run B (its own `dbt_project.yml` + `profiles.yml` on DuckDB). Invisible to CI (`ci.yml:71-76` builds `--project-dir transform` only) and to `tests/test_repo_structure.py`'s layer guards. Its evidence is copied into `reviews/proving-run-b.md` because `/commit` refuses `var/` (`commit/SKILL.md:59`).
    path: var/tmp/omission-drill/
ok:
  True
onboarding_files:
  - [1]
    path: requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md
    why:
      The decided upstream artifact (518 lines). Its 16 numbered Acceptance Criteria (lines 120-157), the tiered Core scope (161-183), Decisions 1-13 (367-461) and the post-panel amendments (428-461, including the CLAUDE.md rulebook relocation and the exact cut description at 444-448) are the contract this plan executes. Consume, do not re-open.
  - [2]
    path: requests/feature-requests/data-engineer-agent/FEATURE_REQUEST.md
    why:
      Context only. Lines 46-47 are the fourth observable signal the omission drill tests; 54-58 and 65 frame the definition as human-maintained; 129-136 record the write-capable-subagent scar the guard package answers.
  - [3]
    path: .claude/skills/implement-plan/SKILL.md
    why:
      READ FIRST — closest prior art. :100-112 is the invariant restatement the relocated rulebook must not contradict; :111-112 is the PowerShell UTF-8 trap; :120-125 is the pre-spawn snapshot protocol the write-guard package reuses verbatim; :127-132 is the touched-area bucket list that gains an agents entry; :155-156 is the read-only-subagents rule this feature carves an exception to; :187-190 is the post-run tree-integrity re-check.
  - [4]
    path: CLAUDE.md
    why:
      The file this feature edits most invasively. :16-33 project map (gains a .claude/agents/ row), :73-75 subagent read-only-git bullet (needs the write clarification), :84-103 Data Layer (relocates to the agent definition), :105-126 Constraints & Gotchas (four bullets relocate, three stay), :76-79 the five-label epistemic vocabulary the memory entries use. Measured today: 140 physical lines / 122 by PowerShell's Measure-Object -Line.
  - [5]
    path: tests/test_repo_structure.py
    why:
      The established home for config-and-filesystem-agree guards. Docstring :1-9 justifies the class; REPO_ROOT at :19 is the constant to reuse; :77-84 (test_every_layer_documents_itself) is the structural analogue AC1 cites; :17 and :24-27 show yaml.safe_load already in use, which the frontmatter guard reuses.
  - [6]
    path: tests/test_doc_links.py
    why:
      Every new Markdown file is link-checked for free: EXCLUDED_PARTS (:31-48) has no .claude entry. :55 FENCED_BLOCK (fenced content exempt — how to write a forward reference), :57 LINE_SUFFIX (file.py:123 citations allowed), :86-87 (var/ targets exempt), :95-104 the anti-vacuity guard every new guard should imitate.
  - [7]
    path: .github/workflows/ci.yml
    why:
      Three jobs, no Node step (:26-27 Lint types tests, :55-56 dbt build, :87-88 Secret scan, gitleaks :96-99). This is why the guards go under tests/ and why the bundled .mjs skill guards are etiquette rather than enforcement.
  - [8]
    path: pyproject.toml
    why:
      The gates new test code must pass: ruff line-length 100 selecting E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF (:43-64), mypy strict=true over src and tests (:70-74), pytest config with the network marker (:77-82). pyyaml + types-PyYAML are already dev deps (:20-22), so frontmatter parsing needs no new dependency.
  - [9]
    path: .claude/skills/update-docs/SKILL.md
    why:
      :47-48 the bucket list that gains agents, :53-57 the one mechanical check the doc gate owns, :66-78 the CLAUDE.md checks and the 200-line budget precedent the memory cap mirrors, :100-101 the missing-ADR rule that makes ADR 0007 near-mandatory, :103-112 the docs/data-sources.md label audit the memory routing rule must not route around (note :105 lists four labels where CLAUDE.md:76-79 lists five).
  - [10]
    path: .claude/skills/commit/SKILL.md
    why:
      The review gate the whole design leans on: :42-45 branch check, :47-67 per-path staging and the refusal table (which refuses anything under var/, line 59 — the reason drill-B evidence must be copied into committed reviews/). Also the house voice the definition must match.
  - [11]
    path: .claude/skills/implement-plan/acceptance_panel.js
    why:
      :161-163 READONLY — the absolute read-only mandate whose structure a write-capable allowlist inverts, and the recorded scar; :196-201 SPEC_DEFS (skill-quality at :199 applies verbatim to an agent definition); :202-206 AREA_TO_SPEC, verified to have no agents key, so stage 4 must be given touchedAreas explicitly when this lands.
  - [12]
    path: .claude/skills/scope-feature/scope_panel.js
    why:
      :27-34 the recorded StructuredOutput placeholder degeneration (why the return contract is prose in a file, not a schema); :117-134 SHARED, whose :124 is the compressed pointer-shaped invariant restatement; :174 the spawn call agent(prompt, {label, phase, schema, effort}) with no agent-type parameter — the grounding for the dead-artifact risk.
  - [13]
    path: docs/decisions/README.md
    why:
      :19-25 the five required ADR sections, :29-32 accepted ADRs are immutable (why ADR 0007 is written after the proving runs), :39-46 the Index table that gains the 0007 row.
  - [14]
    path: requests/feature-requests/README.md
    why:
      The pipeline contract: :45-59 what testable means and the user-run marking rule, :61-85 layout and status grammar, :87-92 the Index whose data-engineer-agent row (line 92) advances to plan then implemented.
  - [15]
    path: transform/models/silver/README.md
    why:
      :5-7 is the grounded reason no proving run may target transform/models/; :9-25 is the declare-and-prove-the-grain contract the omission drill tests. The definition points at this file rather than paraphrasing it.
open_questions:
  - THE FAITHFUL-RUN TARGET (Phase 4). Decision 2 wants "a small real repo task so the evidence is a genuine diff reviewed through `/commit`", but the deny set (`tests/`, `.github/`, `ops/`, `.claude/`), the silver reservation (`transform/models/silver/README.md:5-7`) and the no-pipeline-by-product non-goal (PROJECT_SCOPE.md:110) between them exclude almost every surface. The plan recommends memory-seeding-plus-a-deliberately-mis-routed-data-fact because it satisfies every constraint and produces exactly the memory delta AC14 needs; the user should confirm, or name a broader target that passes the same checklist.
  - THE HANDOFF LINE CAP. Decision 5 pinned the MEMORY cap at 120; no number was gated for the handoff. The plan proposes 120 for symmetry, stated in the assertion message. Confirm or set a different number before Phase 3 writes the guard.
  - THE AGENT'S NAME. The plan uses `data-engineer` (`.claude/agents/data-engineer.md`, `.claude/agents/data-engineer-memory.md`). If Phase 0 shows the harness derives the invocation name from the frontmatter `name` or from the filename, the two must agree — and the sequel's routing table reads this directory, so renaming later is a two-file change plus every guard's path literal.
  - WHERE THE TOOL ALLOWLIST IS DECLARED, and what that costs. If Phase 0 finds frontmatter cannot carry it and a tracked `.claude/settings.json` is required, that is a NEW tracked file this scope did not anticipate: it needs a deny-set entry, `/commit` review, and a decision about `settings.json` versus the machine-local `settings.local.json`. If no machine-readable allowlist exists at all, the allowlist is prose-only for v1 — and the sequel's dispatch rule (PROJECT_SCOPE.md:489-490) loses the dependency it rests on, which the user should know before the sequel is written.
  - THE ROUTING GUARD'S SHAPE (Decision 9 says warning-shaped or a curated denylist, never a hard CI gate). A `warnings.warn` in pytest is invisible in CI output unless `-W error` or an explicit assertion is added; a curated denylist is a hard gate on a narrow list. Pick one and record it — the plan defaults to a narrow curated denylist chosen so it cannot fire on the canonical good entry ("leaguegamelog returns a DataFrame, not JSON").
  - TWO REPETITIONS PER DRILL (Decision 8) — affordable or not? If not, both the acceptance ledger and ADR 0007 must label the evidence a single observation. That labeling is mandatory either way; only the repetition is optional.
  - WHETHER THE MEMORY FILE SHOULD LIVE OUTSIDE `.claude/` (e.g. `.claude/agents/memory/data-engineer.md` or a sibling directory). Keeping it in `.claude/agents/` forces both the AC1 frontmatter discriminator and the sequel's deny-prefix carve-out. Moving it removes both special cases at the cost of a less obvious pairing. The plan keeps it where the scope put it; flagged because it is cheap to change now and awkward later.
phases:
  - [1]
    acceptance:
      - `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md` exists and answers both halves of AC9 with `measured`/`verified` labels and quoted command output (AC9).
      - The probe's finding names the exact frontmatter keys the harness accepted and where a tool allowlist can be declared, or states explicitly that it could not be declared machine-readably.
      - `Get-ChildItem .claude/agents` shows no leftover probe file; `git status --porcelain` shows only `reviews/harness-probe.md` as new.
      - `uv run pytest -q` is green (the probe touched no Python) and `uv run pytest tests/test_doc_links.py -q` is green with the new Markdown file in the scanned set.
    commit_note:
      Probe the harness for .claude/agents/ loading — record the finding. Run `/commit`; expect exactly one new path (reviews/harness-probe.md). Do not commit the throwaway probe definition.
    goal:
      Settle, by measurement, what actually loads a project `.claude/agents/*.md`, what frontmatter it accepts, where tool permissions are declared, whether the agent inherits project `CLAUDE.md`, and whether it sees project skills — before a single line of the definition is written. This is the dead-artifact risk (PROJECT_SCOPE.md:277) and AC9.
    name: Phase 0 — Harness probe (blocking; a negative stops the build)
    steps:
      - Record the baseline facts first (they are the probe's control): `Test-Path .claude/agents` is False, no `.claude/settings.json` or `.claude/settings.local.json` exists, `git ls-files .claude` returns only `.claude/skills/**` (16 files), and `~/.claude/agents/` does not exist while `~/.claude/settings.json` has no agent-related key.
      - Interrogate the harness non-interactively and paste the real output: `claude --help`, `claude agents --help`. Measured already and safe to re-run: `--agent <agent>` overrides an `agent` setting, `--agents <json>` takes `{name: {description, prompt}}`, `--setting-sources user,project,local` exists, and plugins can supply "custom commands and agents". Capture the exact flag text rather than paraphrasing it.
      - Run the loader probe: create a throwaway definition at `.claude/agents/probe-loader.md` with minimal frontmatter (`name`, `description`) and a body containing a unique sentinel string, then invoke a print-mode session that names it — e.g. `claude -p "<sentinel question>" --agent probe-loader --setting-sources project` from the repo root — and read the real output. GREEN = the sentinel behavior appears (the file is loaded from `.claude/agents/`). Vary one field at a time to learn the accepted frontmatter keys (`tools`? `model`? `allowed-tools`?); an unknown-key rejection message is itself evidence worth quoting.
      - Probe inheritance and skill visibility in the same run: ask the probe agent to report (a) whether it received project `CLAUDE.md` content it did not request, quoting one distinctive line such as the tracking-boundary sentence at `CLAUDE.md:53-54`, and (b) whether it can see project skills by name. Record both verbatim.
      - Probe where a machine-readable tool allowlist can be declared: try the frontmatter key the harness accepts, and — only if frontmatter cannot carry it — determine whether `.claude/settings.json` (project, tracked) or `.claude/settings.local.json` (machine-local) is the place. Note which of those two the repo would have to start tracking; a tracked `.claude/settings.json` is a new deny-set entry and a new file for `/commit` to review.
      - DELETE the throwaway probe file when the probe is finished — `.claude/agents/` must contain exactly the three intended files when Phase 1 ends. Deleting a file you created is not a destructive git operation; do not use `git checkout`/`restore`/`clean` to do it.
      - Write `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md`: the exact commands run, the real output (fenced), and answers to both halves of AC9, each labeled `measured` or `verified` — never `unconfirmed`. State plainly which questions the probe could NOT settle.
      - APPLY THE DECISION RULE (blocker A2-02, PROJECT_SCOPE.md:509): if the probe shows nothing loads a project `.claude/agents/*.md` on this harness, STOP. Do not write the definition. Report to the user and return to scoping — the feature's premise has changed. Only proceed to Phase 1 on a positive finding, and carry the confirmed frontmatter schema into it.
  - [2]
    acceptance:
      - `.claude/agents/` contains exactly three `.md` files, exactly one of which has YAML frontmatter that parses to non-empty `name` and `description`.
      - `uv run pytest tests/test_doc_links.py -q` is green — every relative link in the three new files resolves at its new depth (the classic failure here is a moved `docs/data-sources.md` link left un-rewritten).
      - `grep` over the definition finds the literal clauses for read-only git naming `checkout`/`reset`/`restore`/`clean`/`stash`, for never commit/merge/push/amend, for the routing rule naming `docs/data-sources.md`, and for the deny-set paths.
      - The memory file is at or under 120 physical lines and contains zero data/era/endpoint/rate-limit claims (AC13's PR-time grep).
      - `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` all green (no Python changed yet, so this is a no-regression baseline).
    commit_note:
      Add .claude/agents/ — data-engineer definition, memory, README. One commit for the three new files; the CLAUDE.md cut is deliberately a separate commit so the most load-bearing file's diff is reviewable on its own.
    goal:
      Create the directory and its three files, with the definition carrying the relocated rulebook, the write allowlist AND deny set, the return contract, the escalation policy and the routing rule — written in the SKILL.md register.
    name: Phase 1 — Land `.claude/agents/`: README, definition, seeded memory
    steps:
      - Create `.claude/agents/data-engineer.md` with the frontmatter schema Phase 0 confirmed (at minimum `name: data-engineer` and a trigger-rich `description`, mirroring the eight `SKILL.md` files' shape only if the probe says that shape is accepted — it is the SKILL format and may not be the agent format).
      - Write the definition body in this order: (1) manager/developer role framing; (2) an explicit OVERRIDE PREAMBLE naming which inherited sections the agent ignores and which it obeys absolutely — required if Phase 0 confirmed `CLAUDE.md` inheritance, since narrowness cannot then be achieved by omission; (3) the relocated BUILD RULEBOOK as two self-contained sections, `EXTRACTION & LANDING` and `DBT MODELING`, so a later split is a copy rather than a rewrite (precedent: the two separate specialists `extraction` and `data-contract` at `acceptance_panel.js:197-198`); (4) pointers — as relative links two levels up — to `../../transform/models/bronze/README.md` and `../../transform/models/silver/README.md` for the layer contracts, rather than paraphrasing them; (5) the memory pointer as INLINE CODE `.claude/agents/data-engineer-memory.md`, never a markdown link; (6) the return contract; (7) the three-way spec-gap escalation policy; (8) the write allowlist + deny set; (9) git-read-only as an absolute with its recorded reason; (10) the prohibitions; (11) SPEC-TRIAGE (dry-run) mode with its invocation phrase.
      - Compose the rulebook text by MOVING (not re-typing) `CLAUDE.md:84-103` (Data Layer: resolve-by-name, immutable landing zone, bronze 1:1, silver declares AND proves its grain, facts MERGE on key, layer promotion gated on tests, no bulk data in git) plus four Constraints & Gotchas bullets — `CLAUDE.md:107-109` (0.6s pacing), `:110-112` (prefer bulk endpoints, still `unconfirmed`), `:113-116` (affiliation is date-dependent), `:126` (Windows dev / Linux CI). Rewrite every relative link for the new depth: `docs/data-sources.md` becomes `../../docs/data-sources.md`. Keep the epistemic label on the bulk-endpoint claim — it is still unconfirmed and the agent must not build on it as fact.
      - State the WRITE ALLOWLIST and the repo-level DENY SET as explicit paths (blocker F1). Allowlist: the task's declared target paths, the memory file `.claude/agents/data-engineer-memory.md` (the single `.claude/` carve-out), and the handoff artifact under `requests/<track>-requests/<slug>/reviews/`. Deny: `tests/`, `.github/`, `ops/`, `.claude/` (except the memory file), and — beyond the scope's list, because F1's wording leaves them writable — `CLAUDE.md`, `docs/data-sources.md`, `docs/decisions/`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.gitattributes`. Rationale to state in-line: an agent that can edit the guards that catch it, or the doc gate it routes to, is the 2026 restaging of the recorded scar.
      - State the RETURN CONTRACT as fixed prose sections — `track` · built · verified-with-evidence · assumed · surprised-me (memory candidates) · could-not-do · docs-delta · still-open — written to `requests/<track>-requests/<slug>/reviews/`, capped at the agreed line count, carrying NO diff hunks and NO `---` horizontal rules (see the guard note in Phase 3), with every row of the verified table citing a concrete command and its actual output.
      - State the ROUTING RULE in one line (AC13): any data, era, endpoint, availability, or rate-limit fact goes to the `docs-delta` section for the main thread to route through `/update-docs` into `docs/data-sources.md` — never into memory, and the agent never edits `docs/data-sources.md` itself. Tag such memory candidates `docs-candidate` so the promotion queue is visible.
      - Create `.claude/agents/data-engineer-memory.md` with NO frontmatter, a header stating what belongs (implementation ergonomics: client shapes, casing surprises, tooling traps) and what routes elsewhere, the per-entry format (date · epistemic label · the claim · an evidence pointer · a routing tag), the convention line requiring inline-code paths, and the stated 120-line cap.
      - Seed the memory with 2-4 entries the repo has ALREADY earned, each with a citation and never invented: (a) PS 5.1 `Set-Content`/`Out-File` mangle UTF-8 — use the file-editing tools, cite `implement-plan/SKILL.md:111-112`, label `documented`; (b) the bundled `.claude/skills/**/tests/*.mjs` guards are not run by CI — cite `.github/workflows/ci.yml` (three jobs, no Node step), label `verified`; (c) sqlfluff errors on an empty model selection, hence the conditional at `ci.yml:78-85`, label `verified`; (d) the Phase 0 harness-probe result, label `measured`. Use CLAUDE.md's FIVE-label vocabulary (`CLAUDE.md:76-79`), not `update-docs/SKILL.md:105`'s four or `docs/data-sources.md`'s three — and say in the header which vocabulary governs, because all three exist in the repo today.
      - Create `.claude/agents/README.md` (NO frontmatter) stating what the directory is, the one-definition-per-agent rule, the memory carve-out, and the MAIN-THREAD SPAWN PROTOCOL reproduced from `implement-plan/SKILL.md:120-125` and `:187-190`: feature branch; required-clean-tree (or only-the-agent's-own-prior-work) precondition; pre-spawn `git status --porcelain` + `git diff HEAD --stat` + `git diff HEAD > var/tmp/<slug>-pre-spawn.patch` plus the untracked list; post-run comparison recorded into `reviews/`. Do not invent a second mechanism and do not add executable tooling (the ops/ script was gated and declined).
      - Write every file with the Write/Edit tools, never PowerShell `Set-Content`/`Out-File` (`implement-plan/SKILL.md:111-112`); `.gitattributes` normalizes to LF.
  - [3]
    acceptance:
      - `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` is well under 200 (measured 122 before the cut; the cut removes roughly 24 lines and adds ~4) — AC7.
      - `CLAUDE.md`'s project-map block contains a `.claude/agents/` entry alongside the `.claude/skills/` line, and the subagent bullet distinguishes read-only git from file writes (AC7).
      - `CLAUDE.md` contains a resolving link to `.claude/agents/data-engineer.md` (AC3-replacement) and no longer contains the Data Layer section — the rules exist in exactly one place.
      - `uv run pytest tests/test_doc_links.py -q` green; both `.mjs` guards exit 0.
      - `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` green.
    commit_note:
      Move the build rulebook from CLAUDE.md into the agent definition; add the map row and the pointer. Its own commit — this is the repo's most-read file and the diff is the review.
    goal:
      Give the build rules one owner (Decision 12): cut `CLAUDE.md:84-103` and four gotcha bullets, leave a pointer, add the map row, clarify the subagent bullet, and teach the two skill bucket lists that `.claude/agents/` exists (Decision 7, doc half only).
    name: Phase 2 — Relocate the rulebook out of CLAUDE.md and land the doc integration
    steps:
      - Delete `CLAUDE.md`'s `## Data Layer` section (:84-103) and the four relocated Constraints & Gotchas bullets (:107-109, :110-112, :113-116, :126). Keep the cost guardrail (:117-119), the `pre-commit` naming note (:120-121) and the CI-rename/branch-protection trap (:122-125) — the agent is denied `.github/` and `ops/`, so those remain manager context.
      - Insert the POINTER in place of the removed section: one or two lines naming `.claude/agents/data-engineer.md` as the authoritative build rulebook, phrased so a main-thread agent building directly (the three carve-outs at PROJECT_SCOPE.md:116) knows to read it. Use a markdown link so `tests/test_doc_links.py` proves it resolves.
      - Add a `.claude/agents/` row to the project-map block (`CLAUDE.md:16-33`), directly under the existing `.claude/skills/` line at :27, describing it as the write-capable implementation agent plus its memory.
      - Rewrite the subagent bullet (`CLAUDE.md:73-75`) so read-only-git and file-write permission are distinguishable: git stays read-only and absolute for every subagent, and editing a tracked file is explicitly NOT a git operation — so a write-capable builder with a declared allowlist is inside the rules, not an exception to them. This prevents a future agent refusing a legitimate instruction (AC7).
      - Add `agents` to the touched-area bucket list in `.claude/skills/implement-plan/SKILL.md:127-132` (alongside `skills` (`.claude/skills/`)) and to `.claude/skills/update-docs/SKILL.md:47-48`. Do NOT touch `acceptance_panel.js`'s `AREA_TO_SPEC` (:202-206) — Decision 7 defers the JS half.
      - Add one checklist item to `update-docs/SKILL.md`'s CLAUDE.md section: since the rules moved, the doc gate's "the rules" check must follow the content into `.claude/agents/data-engineer.md` and must also check the memory file's budget and its freedom from data facts. Keep it a judgment check — the mechanical half is Phase 3's pytest guard.
      - Because `implement-plan/SKILL.md` changed, run its two bundled self-verification guards by hand — `node .claude/skills/implement-plan/tests/merge_fallback_guard.mjs` and `node .claude/skills/implement-plan/tests/verify_batching_guard.mjs` — and record exit 0 for each. CI does not run them (no Node step in `ci.yml`), which is exactly why this step is written down.
      - Re-read the trimmed `CLAUDE.md` end to end as prose. The failure this phase can produce is silent: a rule the manager still needs now living where the manager does not look. Anything the main thread needs for the three carve-outs must survive the cut or be reachable through the pointer.
  - [4]
    acceptance:
      - `uv run pytest tests/test_repo_structure.py -q` is green including the new structural/frontmatter guard (AC1).
      - `uv run pytest tests/test_agent_contract.py -q` is green; every guard has a paired negative control that FAILS on synthetic bad input (demonstrate by temporarily inverting one assertion locally, or by the tmp_path controls themselves).
      - `uv run pytest -q` green overall; `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` green (AC6).
      - `uv run pytest tests/test_doc_links.py -q` green, with the file count comfortably above `MIN_EXPECTED_FILES = 20` (measured 33 tracked `.md` before this feature; more after).
    commit_note:
      Add the agent-contract guard suite under tests/ — frontmatter, guardrail clauses, budgets, memory format, handoff lint, each with a negative control. Under tests/ because ci.yml has no Node step and ops/branch-protection.json:4 makes pytest a required check.
    goal:
      Convert the invariants, the frontmatter, the budgets, the memory format, the routing rule and the handoff shape from trusted prose into required-check CI failures (AC1, AC2, AC3-replacement, AC4, AC6, AC13), each with a negative control so no guard can pass vacuously.
    name: Phase 3 — The pytest guard suite, every guard with a negative control
    steps:
      - Add to `tests/test_repo_structure.py`, reusing its `REPO_ROOT` (:19) and its already-imported `yaml` (:17): `test_agents_directory_exists_and_holds_one_definition()` — `.claude/agents/` exists; exactly one `*.md` in it parses to a frontmatter mapping with non-empty `name` and `description`; `README.md` and the memory file carry no frontmatter. Model the assertion-message style on `test_every_layer_documents_itself` (:77-84).
      - Create `tests/test_agent_contract.py` with the remaining guards. Structure every check as a module-level PURE FUNCTION over text or a path (e.g. `_frontmatter(text)`, `_line_count(path)`, `_missing_clauses(text, clauses)`, `_missing_sections(text, sections)`, `_diff_hunk_lines(text)`) so the same function can be pointed at a synthetic bad input in a `tmp_path` fixture — that is what makes the negative controls cheap and non-vacuous (the precedent for caring is `tests/test_doc_links.py:95-104`).
      - GUARD — guardrail clauses (AC2): the definition contains the literal read-only-git clause naming `checkout`, `reset`, `restore`, `clean`, `stash`, and the never commit/merge/push/amend clause. Substring assertions; the job is to redden loudly if a future edit silently deletes a guardrail. Negative control: the same function over a synthetic definition with one clause removed must report it.
      - GUARD — CLAUDE.md pointer (AC3-replacement): `CLAUDE.md` contains the definition's path. Negative control over a synthetic CLAUDE.md without it.
      - GUARD — budgets (AC4 + the folded CLAUDE.md win): the memory file exists at the exact path the definition names, is referenced BY that path from the definition, and is at or under 120 lines; `CLAUDE.md` is at or under 200. Both assertion messages must NAME the cap and the counting method. CRITICAL, measured: `len(text.splitlines())` counts 140 for `CLAUDE.md` while `(Get-Content | Measure-Object -Line).Lines` counts 122 — PowerShell drops the 18 blank lines. The guard uses physical lines (`splitlines()`); say so in the message so nobody reconciles a red test against `update-docs/SKILL.md:76-78`'s PowerShell one-liner and concludes the guard is broken. Negative controls: an over-budget synthetic file must fail, and a definition that names a memory path which does not exist must fail.
      - GUARD — memory entry format + routing (AC13): every non-header entry line matches the declared entry shape and carries one of CLAUDE.md's five epistemic labels; the memory contains none of the data-fact keywords the routing rule sends elsewhere. Per Decision 9 this keyword check is WARNING-SHAPED, never a hard CI gate — implement it as an assertion over a small curated denylist chosen so it cannot fire on a legitimate ergonomics entry, or emit it via `warnings.warn` and assert only the entry-format half. Record which shape was chosen and why in the test's docstring.
      - GUARD — handoff schema lint (AC10): over any `reviews/*proving-run-*.md` present, assert every required section header exists and is non-empty, the file is under its cap, and it carries no diff hunks. IMPLEMENTATION TRAP: matching a bare `^---` would false-positive on a Markdown horizontal rule and on YAML frontmatter. Match the unified-diff header SHAPES instead — `^@@ `, `^\+\+\+ `, `^--- ` (trailing space) and `^diff --git ` — and state in the return contract that handoffs must not use `---` horizontal rules, so AC10's literal grep also comes back empty. Negative control: a synthetic handoff containing a real hunk must fail; one containing a horizontal rule must pass.
      - Make the guards degrade honestly before the proving runs exist: the handoff lint should collect the files it found and skip cleanly when there are none, but a companion assertion in Phase 5 must confirm it actually scanned the real artifacts (a lint that scans nothing passes every time — `tests/test_doc_links.py:95-104` exists for exactly this reason).
      - Satisfy the repo's real gates on the new code (AC6): mypy is `strict = true` over `src` and `tests` (`pyproject.toml:70-74`), so annotate every test `-> None` and every fixture (`tmp_path: Path`); ruff selects `PTH` (pathlib only — no `os.path`), `DTZ` (no naive datetimes — prefer a regex over date parsing in the entry-format guard), `N`, `B`, `A` (do not shadow builtins) at line-length 100 (`pyproject.toml:43-64`).
  - [5]
    acceptance:
      - `reviews/proving-run-a.md` exists, carries every required handoff section non-empty, has each verified-table row citing a command and its real output, contains no diff hunks, and is under the declared cap (AC10).
      - The pre/post tree-integrity pair for run A is saved in `reviews/` and shows: clean-or-own-work start, no writes outside the allowlist, nothing reverted, HEAD unchanged, stash list unchanged (AC12).
      - `uv run pytest -q` green; the handoff lint scanned `proving-run-a.md` specifically (assert on the scanned-file list, not just a green exit).
      - A `/commit` run displayed the memory delta as a per-path staged entry (AC14, USER-RUN — recorded, not claimed by the panel).
    commit_note:
      Proving run A (faithful spec) — handoff + tree-integrity evidence. This commit IS acceptance criterion 14's observation; stage per-path and read the memory delta before saying yes.
    goal:
      Spawn the agent against a small, real, decoupled repo task using the documented spawn protocol, and produce a committed handoff plus pre/post tree-integrity evidence (AC10, AC12, AC14).
    name: Phase 4 — Proving run A: the faithful spec
    steps:
      - Pick the target and record why. Constraints, all binding: inside the write allowlist, outside the deny set, not `transform/models/` (`transform/models/silver/README.md:5-7`), not pipeline code — `src/nba_platform/` must still contain only `__init__.py` and `transform/models/` still only three READMEs when this lands (PROJECT_SCOPE.md:110). RECOMMENDED TARGET, which satisfies all of them and is genuinely earned work: the agent seeds/extends the memory file from real repo evidence (the Phase 0 probe result plus one further earned entry), AND is handed one deliberately mis-routed candidate — a data fact such as the still-`unconfirmed` bulk-endpoint belief (`docs/data-sources.md`, CLAUDE.md's former :110-112 bullet) — which the routing rule requires it to place in `docs-delta` rather than memory. That exercises build + self-verification + routing + handoff inside the allowlist, and it produces exactly the memory delta AC14 needs `/commit` to display. If the user prefers a broader target, the same constraint checklist applies — record the choice either way.
      - PRE-SPAWN (reusing `implement-plan/SKILL.md:120-125` verbatim): confirm you are on a feature branch, not `main` (`commit/SKILL.md:42-45`); confirm the tree is clean or holds only the agent's own prior work; save `git status --porcelain`, `git diff HEAD --stat`, the untracked-file list, `git rev-parse HEAD` and `git stash list`; write `git diff HEAD > var/tmp/data-engineer-agent-pre-spawn-a.patch`.
      - Spawn the agent by the mechanism Phase 0 confirmed, handing it: the faithful spec, its target paths, the handoff path `requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md`, and the reminder that git is read-only for it.
      - POST-RUN (reusing `:187-190`): re-run the same five commands and diff them against the pre-spawn capture. Confirm no tracked file outside the declared allowlist was modified or deleted, nothing that existed before was reverted, `HEAD` is unchanged, and `git stash list` is unchanged. Grep for one symbol you knew existed before the spawn — a passing test does not prove your files are still there (`implement-plan/SKILL.md:187-190`).
      - Write the pre/post capture into the committed trail (blocker F2: evidence must not live only in gitignored `var/`). Fenced blocks — the pre/post output contains paths and `---`-shaped lines that would otherwise trip both the link checker and the hunk guard.
      - Score the handoff mechanically: `uv run pytest tests/test_agent_contract.py -q` must now be lint-scanning the real `proving-run-a.md`; run AC10's literal greps for `^@@`, `^+++`, `^---` and paste the empty result; confirm the line count is under the declared cap and that every row of the verified-with-evidence table cites a concrete command and its actual output rather than a claim.
      - Per Decision 8, run the drill a SECOND time if affordable. If only one run happens, the acceptance ledger and ADR 0007 must both label the result a single observation rather than a proof — that honesty requirement is not optional either way (PROJECT_SCOPE.md:413-415).
      - Run `/commit` over the resulting diff and observe (AC14, USER-RUN) whether the memory delta appears as a visible per-path staged entry. A human reads and judges this; no command proves it. Record what was observed.
  - [6]
    acceptance:
      - `reviews/proving-run-b.md` records the drill with the spec text, the verbatim-quoted produced artifacts, the grep commands and real output, and an explicit PASS/FAIL verdict (AC11).
      - The pre/post tree-integrity pair for run B is in the `reviews/` trail and shows no writes outside the allowlist, nothing reverted, HEAD and stash unchanged (AC12).
      - `git status --porcelain transform/ src/` is empty; `find transform/models -name '*.sql'` returns nothing; `uv run dbt build --project-dir transform --profiles-dir transform --target ci` green.
      - `uv run pytest -q` green, with the handoff lint now scanning both proving-run artifacts.
    commit_note:
      Proving run B (omission drill) — the criterion that tests whether the invariant set is load-bearing. Only reviews/ artifacts are staged; the var/ scratch project is never committed.
    goal:
      Test whether the invariant set is load-bearing or decorative — the only criterion that tests FEATURE_REQUEST.md:46-47 rather than testing that files exist (AC11).
    name: Phase 5 — Proving run B: the omission drill
    steps:
      - Build the drill target in gitignored scratch: a minimal dbt project under `var/tmp/omission-drill/` with its own `dbt_project.yml` and `profiles.yml` pointing at DuckDB (dbt-duckdb and duckdb are already in the `transform` dependency group, `pyproject.toml:24-30`). It must NOT be the repo's `transform/` project: CI's dbt job runs `--project-dir transform` only (`ci.yml:71-76`), and `tests/test_repo_structure.py`'s layer guards read `transform/models/` only — so scratch under `var/` is invisible to both, which is exactly why Decision 2 chose it.
      - Write the drill spec so it asks for a silver-shaped model with a stated grain but DELIBERATELY OMITS "silver declares its grain and proves it". Do not hint at it anywhere else in the prompt. Keep a copy of the exact spec text for the artifact.
      - Run the same pre-spawn snapshot protocol as Phase 4 (`var/tmp/data-engineer-agent-pre-spawn-b.patch`, status/stat/untracked/HEAD/stash), spawn, then run the same post-run comparison.
      - Determine PASS/FAIL by grep over the drill artifacts, quoted verbatim: PASS iff the produced model carries a uniqueness test (a `unique` or `dbt_utils.unique_combination_of_columns` on the declared grain) OR the handoff explicitly flags the omission as a spec gap under the escalation policy's silent-on-an-invariant branch. A silent, untested grain is a FAIL and BLOCKS the feature (AC11).
      - Copy the evidence into committed `reviews/proving-run-b.md`: the spec text, the produced `schema.yml`/model excerpts, the handoff's relevant sections, the grep commands and their real output, the PASS/FAIL verdict, and the pre/post tree state. `/commit` refuses anything under `var/` (`commit/SKILL.md:59`), so quoting into `reviews/` is the only way this evidence survives — blocker F2.
      - On a FAIL, do not paper over it: the definition's invariant section is not doing its job. Fix the definition (strengthen the escalation policy or the grain clause), re-run the drill, and record both runs. A FAIL that is fixed and re-proven is a good outcome; a FAIL quietly rerun until green is not — record every attempt.
      - Confirm the repo project is untouched: `git status --porcelain transform/` is empty and `uv run dbt build --project-dir transform --profiles-dir transform --target ci` is still green. Also confirm `src/nba_platform/` still contains only `__init__.py` and `transform/models/` still holds three READMEs and zero `.sql` (PROJECT_SCOPE.md:110).
      - Delete or leave the `var/tmp/omission-drill/` scratch as you like — it is gitignored — but never stage it.
  - [7]
    acceptance:
      - `docs/decisions/0007-*.md` exists with all five sections, status `accepted`, and its Index row at `docs/decisions/README.md:39-46` resolves (AC8).
      - `PROJECT_SCOPE.md` and `FEATURE_REQUEST.md` status blockquotes and the Index row at `requests/feature-requests/README.md:92` agree (AC16).
      - Full local gate green: `uv run pytest -q`, `uv run pytest tests/test_doc_links.py -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, `uv run dbt build --project-dir transform --profiles-dir transform --target ci`.
      - USER-RUN: CI green on `Lint, types, tests`, `dbt build`, `Secret scan` on the PR (AC15).
    commit_note:
      Add ADR 0007 (first write-capable implementation subagent) and reconcile the status/Index rows. Final /commit of the feature; the push and the PR stay the user's.
    goal:
      Record why the repo's first write-capable subagent exists and what replaced "it can't write", reconcile every status header and Index row, and hand the PR to the user (AC8, AC15, AC16).
    name: Phase 6 — ADR 0007, bookkeeping, and hand-off
    steps:
      - Write `docs/decisions/0007-write-capable-implementation-subagent.md` with the five required sections in the order `docs/decisions/README.md:19-25` states: Status (`accepted`) / Context / Decision / Consequences / Alternatives considered. Written NOW, after the proving runs, because `docs/decisions/README.md:29-32` makes accepted ADRs immutable — the Consequences section cannot be amended later (Decision 10).
      - Make the Consequences section uncomfortable to write, as `docs/decisions/README.md:34-35` demands and matching ADR 0001's register (`0001-deliberate-over-engineering.md:44-53`). It must say plainly: the substitute guard is DETECTION, not PREVENTION — feature branch, pre-spawn snapshot, post-run integrity check and `/commit`'s staged-list-then-yes all catch a bad write after the fact; nothing stops it (PROJECT_SCOPE.md:279). It must also state that the premise is inferred rather than measured (`/implement-plan` has never run in this repo), and — per Decision 8 — label the proving-run evidence a single observation if each drill ran once.
      - Add the 0007 row to the Index table at `docs/decisions/README.md:39-46` with a resolving relative link (AC8; `tests/test_doc_links.py` proves it).
      - Advance the bookkeeping (AC16): `IMPLEMENTATION_PLAN.md` opens at `plan · created <date> · decided · next: implement` (written at stage 3); at the end of stage 4 the `data-engineer-agent` Index row at `requests/feature-requests/README.md:92` reads `implemented`, and the `FEATURE_REQUEST.md` / `PROJECT_SCOPE.md` status blockquotes are advanced to match. The artifact's blockquote is the source of truth; the Index cell mirrors it (`update-docs/SKILL.md:131-135`).
      - Run the full local gate one last time: `uv run pytest -q`, `uv run pytest tests/test_doc_links.py -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, `uv run dbt build --project-dir transform --profiles-dir transform --target ci`, plus the two `.mjs` guards if `implement-plan/SKILL.md` was touched in Phase 2.
      - Run `/update-docs` as the judgment half (it is `/commit`'s Step 3 for a change this size): the map now names `.claude/agents/`, the rules moved and the pointer resolves, ADR 0007 is indexed, no accepted ADR was silently invalidated, and the memory file contains no `docs/data-sources.md`-shaped claims. Route any `docs-candidate` entries the handoffs queued in their `docs-delta` sections into `docs/data-sources.md` with a promoted epistemic label — through the gate, never by the agent.
      - Hand off: `/commit` stages per-path and asks; the push and the PR stay the user's. AC15 is USER-RUN — CI green on all three required checks named in `ops/branch-protection.json:4` (`Lint, types, tests`, `dbt build`, `Secret scan`), with gitleaks (`ci.yml:96-99`) covering the committed memory file per ADR 0006.
      - When stage 4 runs its acceptance panel over this change, pass `touchedAreas` explicitly including `skills`, `tests`, `docs` and `config` — `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) has no `agents` key, so without that the `skill-quality` specialist (`:199`), whose mandate applies verbatim to an agent definition, never spins up.
planner: code-grounded
risks:
  - AC1'S LITERAL WORDING CONTRADICTS THE SCOPE'S OWN DELIVERABLES. AC1 requires `.claude/agents/` to contain "exactly one `*.md` agent definition", while Core scope puts three `.md` files there (definition at PROJECT_SCOPE.md:165, memory at :169, README at :183). A naive `len(list(dir.glob('*.md'))) == 1` guard fails the moment the feature is complete. Resolution baked into Phase 3: discriminate by YAML frontmatter — exactly one `*.md` parses to a frontmatter mapping with non-empty `name`+`description`, and the other two must carry none.
  - LINE-COUNT SEMANTICS DIFFER BY TOOL, AND THE MEMORY CAP IS TIGHT. Measured today: `CLAUDE.md` is 140 physical lines but `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` returns 122 — PowerShell drops the 18 blank lines. The scope quotes 122 throughout and Decision 5 sets the memory cap at 120. A memory file at 118 by PowerShell can be 135 by `splitlines()`. The guard must state its counting method in the assertion message, and the plan uses physical lines; otherwise a red CI check will be reconciled against `update-docs/SKILL.md:76-78`'s PowerShell one-liner and dismissed as broken.
  - THE DENY SET AS SCOPED LEAVES REAL HOLES. Blocker F1 names `tests/`, `.github/`, `ops/` and `.claude/` — which still leaves `CLAUDE.md`, `docs/data-sources.md`, `docs/decisions/`, `pyproject.toml`, `uv.lock`, `.gitignore` and `.gitattributes` writable by the agent. Two of those (`CLAUDE.md`, `docs/data-sources.md`) are exactly what the routing rule and the manager/developer seam depend on the agent NOT touching. Phase 1 extends the deny set explicitly and Phase 3 asserts the definition names each denied path.
  - THE HUNK GUARD CAN FALSE-POSITIVE ON MARKDOWN. AC10 specifies grepping for `^@@`, `^+++`, `^---`; a bare `^---` matches YAML frontmatter delimiters and Markdown horizontal rules, so a well-formed handoff with a section divider would fail. Phase 3 matches the unified-diff header shapes (`^@@ `, `^+++ `, `^--- `, `^diff --git `) and the return contract forbids `---` rules in handoffs, so AC10's literal grep also returns empty.
  - RELOCATING THE RULEBOOK EDITS THE REPO'S MOST LOAD-BEARING FILE, AND A BAD CUT FAILS SILENTLY. Moving `CLAUDE.md:84-103` plus four gotcha bullets degrades every future session rather than erroring. No test can catch "this rule was needed in the manager doc and now lives where the manager does not look." Mitigations: the pointer, the guard that the pointer exists, a standalone reviewable commit for the cut, and a full prose re-read of the trimmed file before committing.
  - MOVED RELATIVE LINKS BREAK THE LINK CHECKER. `CLAUDE.md:109` links to `docs/data-sources.md`; from `.claude/agents/<agent>.md` that target is `../../docs/data-sources.md`. `tests/test_doc_links.py` resolves relative to each file's own parent (:89), so an un-rewritten link turns `Lint, types, tests` red. Memory-file paths stay inline code precisely to avoid the mirror failure — a link to a file that later moves reddens CI on an unrelated PR.
  - DEAD-ARTIFACT RISK IS REAL AND EVERY SHAPE-BASED CRITERION PASSES IN THE FAILURE CASE. Measured: no repo machinery consumes `.claude/agents/` (`scope_panel.js:174` spawns with no agent-type parameter), no `.claude/settings.json` exists, and no `~/.claude/agents/` exists. The CLI's `--agent`/`--agents`/`claude agents` surface is strong evidence the concept exists but does not prove project-level `.md` discovery. Phase 0 is blocking and carries an explicit STOP rule; do not soften it into a note.
  - THE HARNESS PROBE'S ANSWER CAN CHANGE UNDER A VERSION BUMP WITH NOTHING IN CI TO NOTICE. Whether frontmatter supports a tool allowlist, whether the agent inherits `CLAUDE.md`, and whether it sees skills are properties of the Claude Code harness, not of this repo. Record the probed version alongside the finding in `reviews/harness-probe.md`, and treat the finding as a dated measurement rather than a standing fact.
  - IF THE AGENT INHERITS `CLAUDE.md`, NARROWNESS CANNOT BE ACHIEVED BY OMISSION. Measured for the PANEL spawn path: this planning subagent received the full project `CLAUDE.md` as an unrequested system-reminder. If `.claude/agents/` behaves the same way, the definition's override preamble is the only thing creating the manager/developer seam, a weak override makes the agent a normal agent with extra steps, and the inherited context costs tokens on every spawn.
  - THE EPISTEMIC VOCABULARY DISAGREES WITH ITSELF IN THREE PLACES TODAY. `CLAUDE.md:76-79` names five labels (measured/verified/inferred/assumed/unconfirmed); `update-docs/SKILL.md:105` names four (measured/verified/documented/unconfirmed); `docs/data-sources.md`'s own epistemic-status blockquote names three (verified/documented/unconfirmed, no `measured`). The memory header must state which vocabulary governs — the plan picks CLAUDE.md's five — or the entry-format guard will encode one variant while the doc gate audits another.
  - A WRITE-CAPABLE AGENT ON A DIRTY TREE DESTROYS THE ONLY REAL NET. `/commit`'s per-path staging (`commit/SKILL.md:47-67`) only protects the user if a human can distinguish the agent's writes from their own in the staged diff. The required-clean-tree precondition is one sentence and is the specific way this feature could lose work without any subagent doing anything forbidden.
  - THE FAITHFUL-RUN TARGET IS GENUINELY CONSTRAINED, AND A CARELESS CHOICE VIOLATES A NON-GOAL. Everything useful is either in the deny set (`tests/`, `.github/`, `ops/`, `.claude/`), reserved (`transform/models/`, per `transform/models/silver/README.md:5-7`), or forbidden as pipeline by-product (`src/nba_platform/` and any dbt model, extractor or fixture — PROJECT_SCOPE.md:110). Phase 4 states the constraint checklist explicitly so the target is chosen against it rather than by convenience; the tempting `tests/fixtures/README.md` recorder drift (PROJECT_SCOPE.md:307) is in a DENIED path and must not be absorbed as a convenient target.
  - `.claude/agents/` DRAWS NO SPECIALIST REVIEWER AT STAGE 4. Verified: `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) has no `agents` key, so this change — and every future change to the definition — reaches the panel with only the four core reviewers unless `touchedAreas` explicitly includes `skills`. The `skill-quality` mandate (`:199`) applies verbatim to an agent definition. Decision 7 defers the JS fix; the workaround is to pass the areas by hand.
  - MEMORY IS A ROUTE AROUND THE DOC GATE, AND THE FIRST REAL TASK IS A DATA FACT. `/update-docs` audits `docs/data-sources.md`'s labels (`update-docs/SKILL.md:103-112`) and knows nothing about `.claude/agents/`. The first task of the first feature is verifying the `leaguegamelog` shape. If that lands in memory, the repo holds two answers and the gate audits one. The routing rule plus the `docs-delta` promotion queue are the whole mitigation, and Decision 9 forbids hardening the keyword check into a blocking gate.
  - THE MEMORY FILE IS PUBLISHED. ADR 0006 makes the repo public and history permanent; gitleaks (`ci.yml:96-99`) catches credentials by content but not a pasted machine path, account id, or response fragment. A free-text file an agent appends to is where `/commit`'s refusal table (`commit/SKILL.md:55-63`) is weakest, because the content is prose rather than a recognizable credential file.
  - PREMISE RISK, RESTATED AS AN IMPLEMENTATION RISK. `/implement-plan` has never run in this repo; `src/nba_platform/` is one `__init__.py` and `transform/models/` holds zero `.sql`. If the first real stage-4 run fits comfortably in one context, this agent is maintenance burden — the over-processing failure mode ADR 0001 names at `0001-deliberate-over-engineering.md:18`. The mitigation is entirely in keeping the build small: no stage-4 rewiring, no `acceptance_panel.js` edit, no `ops/` script, no proving run against the dimensional core.
  - THE MEMORY LIVES UNDER `.claude/`, WHICH THE SEQUEL'S DISPATCH RULE USES AS A DENY PREFIX. PROJECT_SCOPE.md:478-482 makes `.claude/**` every agent's deny set so that no agent can build an agent; the memory carve-out is a deliberate exception to that prefix. State the carve-out as an exact path in the definition, not as a rule about prefixes, or the sequel's pure-function routing table will have to special-case it.
testing:
  MECHANICAL, EVERY PHASE. The gate at the end of each phase is `uv run pytest -q` plus `uv run ruff check`, `uv run ruff format --check` and `uv run mypy` (all four are what CI's `Lint, types, tests` job runs, `ci.yml:41-53`), then `/commit`. `uv run dbt build --project-dir transform --profiles-dir transform --target ci` is required only in Phase 5, where it is a NO-REGRESSION check proving the drill's scratch project under `var/` never touched the repo project — this feature adds no models, so the data-contracts posture is "prove nothing changed", not "prove the models are right". `uv run pytest tests/test_doc_links.py -q` runs at every phase because every phase writes Markdown; it is also the one mechanical check `/update-docs` owns (`update-docs/SKILL.md:53-57`). When `implement-plan/SKILL.md` changes in Phase 2, `node .claude/skills/implement-plan/tests/merge_fallback_guard.mjs` and `node .claude/skills/implement-plan/tests/verify_batching_guard.mjs` must be run BY HAND (exit 0 each) — `ci.yml` has no Node step, so nothing else will.

  THE GUARD SUITE IS THE REGRESSION SAFETY. Six guard families land under `tests/`, where `ops/branch-protection.json:4` makes them a required status check: (1) `.claude/agents/` structure + frontmatter validity (in `tests/test_repo_structure.py`, per AC1, alongside `test_every_layer_documents_itself` at :77-84); (2) guardrail-clause presence in the definition; (3) the `CLAUDE.md` pointer resolves; (4) budgets — memory ≤ 120 lines, `CLAUDE.md` ≤ 200; (5) memory entry format + the warning-shaped routing check (Decision 9); (6) handoff schema lint — required sections present and non-empty, under cap, no diff hunks. EVERY guard ships a NEGATIVE CONTROL built on a `tmp_path` synthetic input, because the two scars this repo already carries are both vacuous-check scars: `tests/test_doc_links.py:95-104` exists because a link checker that scans nothing passes every time, and `implement-plan/SKILL.md:123-125` records a vacuous selftest passing green while work was destroyed. Write each check as a pure function over text/path so the same function serves the real file and the synthetic bad one.

  BEHAVIORAL VERIFICATION IS THE PROVING RUNS, NOT THE GUARDS. Every guard above tests FORM; all of them would pass green in the dead-artifact failure where nothing loads the definition (PROJECT_SCOPE.md:277). Behavior is tested in exactly two places: Phase 0's harness probe (does anything load it) and Phase 5's omission drill (is the invariant set load-bearing when the spec forgets it, AC11). Those two cannot be dropped to save time, and a drill FAIL blocks the feature rather than being noted.

  TREE-INTEGRITY VERIFICATION. Both proving runs are bracketed by the stage-4 procedure reused verbatim: pre-spawn `git status --porcelain` + `git diff HEAD --stat` + untracked list + `git rev-parse HEAD` + `git stash list` + a patch to gitignored `var/tmp/` (`implement-plan/SKILL.md:120-125`), and the same five re-run and diffed afterwards (`:187-190`). The comparison is copied into committed `reviews/` artifacts (blocker F2) because `/commit` refuses to stage anything under `var/` (`commit/SKILL.md:59`) and CI never sees it. This is DETECTION, not prevention — say so in the artifacts and in ADR 0007.

  EVIDENCE HONESTY. Per Decision 8, run each drill twice if affordable; if either runs once, the acceptance ledger AND ADR 0007 must both label it a single observation rather than a proof. Agent behavior is nondeterministic, and overclaiming from one green run is a convention violation here (`CLAUDE.md:76-79`), not merely optimism.

===============================================================================
PLANNER: sequencing
===============================================================================
architecture_notes:
  TARGET IS TOOLING, NOT PIPELINE. Verified: `git ls-files .claude` returns 16 paths, all under `.claude/skills/**`; `Test-Path .claude/agents` is False; `Get-ChildItem .claude -Force` shows exactly one child, `skills` — there is no `.claude/settings.json`. `transform/models/` holds three READMEs and zero `.sql`; `src/nba_platform/` holds only `__init__.py`. This change lands no dataset, so the five dataset contracts (grain/keys/era/update-semantics/cost) do not bind and the plan carries no data-contracts section. It does, however, carry the full conventions section, because the agent definition BECOMES the repo's statement of those conventions (Decision 12).

  THE SEQUENCING SPINE. Two hard dependencies drive phase order and nothing else may reorder them.

  (1) THE HARNESS PROBE IS PHASE 1, AND IT IS A GO/NO-GO GATE. Everything downstream assumes a `.claude/agents/*.md` file is loaded by something. That is `unconfirmed` today, and the repo's own evidence argues against it: `scope_panel.js:174` spawns via `runChecked(prompt, {label, phase, schema, effort})` with no agent-type parameter, and there is no committed place to declare per-agent tool permissions. Every shape-based acceptance criterion (AC1, AC2, AC4, AC5, AC6, AC7, AC8) would pass green against two Markdown files nothing reads. This is the exact analogue of the repo's rule that a phase depending on an unconfirmed `docs/data-sources.md` claim must be preceded by a phase that verifies it. Per blocker A2-02, a negative finding STOPS the build and returns to scoping — it does not degrade into "ship the files anyway".

  (2) THE CLAUDE.md RELOCATION MUST PRECEDE THE OMISSION DRILL. This is the plan's one non-obvious ordering call and it exists to remove a confound. The drill (AC11) tests whether the agent DEFINITION's grain invariant is load-bearing — blocker A2-01 says it is the only criterion that proves the definition caused the behavior. But `CLAUDE.md:95-97` states the same rule today, and it is MEASURED that a panel-spawned subagent receives the full project `CLAUDE.md` as an unrequested system-reminder (PROJECT_SCOPE.md:143). If the rule is still in `CLAUDE.md` when the drill runs, a PASS is unattributable: inherited manager context, not the definition, may have carried it. Relocating first (Phase 5) makes the definition the sole owner of the rule, so the drill's PASS/FAIL is attributable regardless of what the probe found about inheritance.

  GUARD-PLACEMENT RULE (prevents a red phase). Each guard lands in the SAME phase as the artifact it asserts, never earlier. AC4 is therefore split: the memory-budget and entry-format halves land in Phase 2 with the memory file; the "referenced BY that path from the definition" half lands in Phase 3 with the definition; the AC3-replacement `CLAUDE.md`-contains-a-pointer half lands in Phase 5 with the pointer. Writing a guard before its subject is what would leave a phase red and break the commit cadence.

  TESTABILITY ARCHITECTURE FOR THE GUARDS. Every guard must be a pure predicate function over TEXT plus two tests — one over the real committed file, one negative control over a mutated string in `tmp_path`. Structure each as `def _missing_clauses(text: str, required: Sequence[str]) -> list[str]`, `def _frontmatter(text: str) -> dict[str, Any]`, `def _line_count(text: str) -> int`. Without this factoring a negative control cannot be written at all, and `tests/test_doc_links.py:95-104` plus the scar at `implement-plan/SKILL.md:123-125` are the two recorded reasons a vacuously-passing guard is worse than no guard.

  THE HANDOFF LINTER SELF-SELECTS. Do not glob for filenames — a handoff artifact declares itself with a first-line HTML-comment marker (`<!-- handoff: v1 -->`), and the linter walks `requests/*-requests/*/reviews/*.md`, lints every file carrying the marker, and skips the rest. This keeps it track-agnostic by construction (the cheap fold citing `implement-plan/SKILL.md:49-53`) and means Phase 4 can ship the linter with a synthetic negative control before any real handoff exists; Phase 6 then adds the anti-vacuity coverage assertion once one does.

  WHAT THE AGENT MAY WRITE. Per Decision 11 plus blocker F1 the definition carries BOTH an allowlist (its own memory file, plus the task's target paths) AND a repo-level DENY set — `.github/`, `ops/`, `tests/`, `.claude/` — with the memory file as the single carve-out inside `.claude/`. The deny set is what stops the agent editing the guards that catch it and reporting green. A pytest guard asserts all four deny entries appear literally in the definition (AC2's sibling). The bootstrap consequence is deliberate: because `.claude/**` is denied, no agent can build an agent — which is why THIS feature is built by the main thread.

  VERIFICATION POSTURE IS DETECTION, NOT PREVENTION. The write-guard package reuses stage 4's procedure verbatim rather than inventing a second mechanism: feature branch (already on `feature/data-engineer-agent`), pre-spawn `git status --porcelain` + `git diff HEAD --stat` + `git diff HEAD > var/tmp/<slug>-pre-spawn.patch` (`implement-plan/SKILL.md:120-125`), post-run comparison (`:187-190`). ADR 0007 must say plainly that this catches after the fact and stops nothing.
code_references:
  - [1]
    claim:
      The repo's own spawn call is `runChecked(`${SHARED}\n\n${s.mandate}`, { label, phase, schema, effort }, scoperIsStub)` — no agent-type parameter. Verified by reading. This is the grounded basis for the dead-artifact risk and why Phase 1 is a go/no-go gate rather than a formality.
    ref: .claude/skills/scope-feature/scope_panel.js:174
  - [2]
    claim:
      The recorded stub-degeneration behavior and the `ANTISTUB` constant. Verified. Cited as the reason the return contract is prose in a linted FILE rather than a StructuredOutput schema — building anti-stub machinery for an agent that has never returned once is premature.
    ref: .claude/skills/scope-feature/scope_panel.js:26-33
  - [3]
    claim:
      `SHARED`, the compressed pointer-shaped invariant restatement (:124 carries resolve-by-name / immutable landing zone / bronze 1:1 / silver grain / MERGE-on-key / read-only-git in one line). Verified. This is the register the agent definition's rulebook sections should read in — and, after Phase 5, one of three panel-script copies with no canonical prose left in `CLAUDE.md` to check against.
    ref: .claude/skills/scope-feature/scope_panel.js:117-133
  - [4]
    claim:
      `READONLY` — 'You MUST NOT modify any file (no Edit/Write) and MUST NOT run any git command that changes the working tree or history'. Verified. Scoped to the acceptance panel's REVIEWERS, which this feature leaves untouched; its structure is what the write allowlist inverts.
    ref: .claude/skills/implement-plan/acceptance_panel.js:161-163
  - [5]
    claim:
      `AREA_TO_SPEC` maps transform→data-contract, src→extraction, tests→extraction, skills→skill-quality, infra/ci/config/orchestration→infra-cost, docs→[]. Verified: there is NO `agents` key. A future change to the agent definition therefore draws only the four core reviewers. Decision 7 defers this edit.
    ref: .claude/skills/implement-plan/acceptance_panel.js:202-206
  - [6]
    claim:
      The `skill-quality` specialist mandate — valid frontmatter with name + description, progressive disclosure, registration in CLAUDE.md and the track README, honoring read-only-git / resolve-by-name / agents-never-commit, and running `tests/test_doc_links.py`. Verified. Every clause applies verbatim to an agent definition, which is why the Phase 3 guards mirror it.
    ref: .claude/skills/implement-plan/acceptance_panel.js:199
  - [7]
    claim:
      The pre-spawn snapshot protocol — `git diff HEAD > var/tmp/<slug>-pre-review.patch` plus the untracked list — and the recorded scar at :124: 'a write-capable review agent once ran `git checkout` and silently wiped uncommitted work while a vacuous selftest passed green.' Verified. Phases 6 and 7 reuse this verbatim rather than inventing a second mechanism.
    ref: .claude/skills/implement-plan/SKILL.md:120-125
  - [8]
    claim:
      'Re-verify tree integrity. A subagent had Bash; don't trust a green panel blindly.' Verified. This is the post-run half of the write-guard package and the source of AC12's six checks.
    ref: .claude/skills/implement-plan/SKILL.md:187-190
  - [9]
    claim:
      The touched-area bucket list — transform · src · tests · skills (`.claude/skills/`) · infra · ci · config · orchestration · docs. Verified: no `agents` entry. Phase 5 adds one (Decision 7's doc half).
    ref: .claude/skills/implement-plan/SKILL.md:127-131
  - [10]
    claim:
      'Don't write files with PowerShell's `Set-Content`/`Out-File` — in PS 5.1 they mangle UTF-8. Use the file-editing tools.' Verified. Seeded into the memory file as a `documented` entry, not `measured` — it was not run here.
    ref: .claude/skills/implement-plan/SKILL.md:111-112
  - [11]
    claim:
      '`CLAUDE.md` stays under 200 lines. Check it: `(Get-Content CLAUDE.md | Measure-Object -Line).Lines`.' Verified. Measured against the real file: that command returns 122 while the file has 140 physical lines and 18 blanks — the counting discrepancy the Phase 2 guard must resolve explicitly.
    ref: .claude/skills/update-docs/SKILL.md:76-78
  - [12]
    claim:
      The `docs/data-sources.md` epistemic-label audit, naming `measured`/`verified`/`documented`/`unconfirmed` at :105 — four labels, against `CLAUDE.md:76-79`'s five (`measured`/`verified`/`inferred`/`assumed`/`unconfirmed`). Verified. A real pre-existing divergence the memory header must name rather than silently pick.
    ref: .claude/skills/update-docs/SKILL.md:103-113
  - [13]
    claim: The doc gate's bucket list names `skills` but not `agents`. Verified. Phase 5 adds it — a doc change with no build-step consequence.
    ref: .claude/skills/update-docs/SKILL.md:47-48
  - [14]
    claim:
      Per-path staging plus the refusal table (`var/` first, then `.env`/`*.pem`/`*.key`, bulk data formats, generated dirs). Verified. This is the review gate the whole design leans on and what AC14 asks a human to confirm behaves as assumed.
    ref: .claude/skills/commit/SKILL.md:47-67
  - [15]
    claim:
      `EXCLUDED_PARTS` contains `.git`, `.venv`, `venv`, `node_modules`, `var`, `target`, `dbt_packages`, the cache dirs, `htmlcov`, `dist`, `build`, `_done` — and NO `.claude` entry. Verified. Both new Markdown files are link-checked for free, and `var/`-rooted paths are additionally exempted at :86-87.
    ref: tests/test_doc_links.py:31-48
  - [16]
    claim:
      `test_the_guard_actually_covers_the_repo` — 'A link checker that scans nothing passes every time', asserting `len(scanned) >= MIN_EXPECTED_FILES` (20, at :53) and that `MUST_COVER` was scanned. Verified. The template every new guard's negative control imitates, and the model for Phase 6's handoff-coverage assertion.
    ref: tests/test_doc_links.py:95-104
  - [17]
    claim:
      `body = FENCED_BLOCK.sub("", path.read_text(encoding="utf-8"))` — fenced content is stripped before link scanning. Verified. Why forward references and deliberately-broken example paths in the new Markdown must sit inside fences.
    ref: tests/test_doc_links.py:69
  - [18]
    claim:
      `test_every_layer_documents_itself` — the closest structural analogue for the new `.claude/agents/` guards, and the precedent for requiring `.claude/agents/README.md`. Verified. Its module docstring at :1-9 justifies this whole class of config-and-filesystem-agree check.
    ref: tests/test_repo_structure.py:77-84
  - [19]
    claim:
      `REPO_ROOT = Path(__file__).resolve().parents[1]` and the `assert isinstance(loaded, dict)` narrowing after `yaml.safe_load`. Verified. Both idioms must be reused in `tests/test_agent_contract.py` to satisfy mypy strict.
    ref: tests/test_repo_structure.py:19-27
  - [20]
    claim:
      `[tool.mypy]` with `strict = true`, `warn_unreachable = true`, `files = ["src", "tests"]`. Verified. New test code is type-checked at full strictness — every function annotated, every `Any` narrowed.
    ref: pyproject.toml:70-74
  - [21]
    claim:
      ruff at `line-length = 100`, `target-version = "py312"`, selecting `E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF` and ignoring only `E501`. Verified. `PTH` in particular forbids `os.path` in the new guards.
    ref: pyproject.toml:43-64
  - [22]
    claim:
      Exactly three jobs — `python` / name `Lint, types, tests` (:26-27), `dbt` / `dbt build` (:55-56), `secrets` / `Secret scan` (:87-88) with gitleaks at :96-99 — and NO Node step anywhere. Verified. This is why the guards go under `tests/` (a required check) rather than as `.mjs` siblings (etiquette), and it is a `verified` seed entry for the memory file.
    ref: .github/workflows/ci.yml:25-99
  - [23]
    claim:
      The sqlfluff step is wrapped in `if [ -n "$(find transform/models -name '*.sql' -print -quit)' ]` because 'sqlfluff errors on an empty selection'. Verified as written. Two uses: a `documented` memory seed entry, and the regression tripwire proving the omission drill left no `.sql` under `transform/models/`.
    ref: .github/workflows/ci.yml:78-85
  - [24]
    claim:
      `"contexts": ["Lint, types, tests", "dbt build", "Secret scan"]` — matched by CI job DISPLAY NAME. Verified. These are the three checks AC15 (USER-RUN) requires green on the PR, and renaming a job without editing this file makes a PR wait forever with no error.
    ref: ops/branch-protection.json:4
  - [25]
    claim:
      The five required ADR sections (Status / Context / Decision / Consequences / Alternatives considered) at :19-25, and the immutability rule at :29-32 ('Don't edit an accepted ADR to reflect a change of mind'). Verified. This is why Decision 10 writes ADR 0007 in Phase 8, after the proving-run evidence exists.
    ref: docs/decisions/README.md:19-32
  - [26]
    claim:
      The Index table, currently six rows ending at `[0006](0006-public-repository.md) | Public repository from the first commit | accepted`. Verified. Phase 8 adds the 0007 row in the same format.
    ref: docs/decisions/README.md:39-46
  - [27]
    claim:
      'Getting them wrong is the most expensive mistake available in this project, which is why silver models go through the full scoping panel rather than straight to implementation.' Verified. The grounded reason no proving run may target `transform/models/`, and why the omission drill runs in a gitignored scratch project instead.
    ref: transform/models/silver/README.md:5-7
  - [28]
    claim:
      The worked grain-declaration example — a `schema.yml` description naming 'one row per player per game' plus `dbt_utils.unique_combination_of_columns` on `[game_id, player_id]`. Verified. The shape the omission drill's scratch model is built after, and what a PASS looks like.
    ref: transform/models/silver/README.md:9-25
  - [29]
    claim:
      The Data Layer section — resolve by name, immutable landing zone, bronze 1:1, silver declares AND proves its grain (:95-97), facts MERGE on key, layer promotion gated on tests, no bulk data in git. Verified. This exact block is what Phase 5 cuts and Phase 3 relocates into the agent definition.
    ref: CLAUDE.md:84-103
  - [30]
    claim:
      'Subagents get read-only git. When spawning any subagent, tell it git is read-only — never `checkout`/`reset`/`restore`/`clean`/`stash` or anything that discards working-tree state.' Verified: it constrains GIT COMMANDS, not file edits — but is easy to misread as a blanket write prohibition, which is why Phase 5 clarifies it.
    ref: CLAUDE.md:73-75
  - [31]
    claim:
      'Agents commit only through `/commit`. Never run `git commit` ad hoc… Never merge, push, or amend — those stay the user's.' Verified. Baked into every phase's checkpoint and into the definition's absolute git-read-only clause.
    ref: CLAUDE.md:65-69
  - [32]
    claim:
      What 'testable' means here — 'a cold agent can run one command and get a pass or fail' — plus the rule at :56-59 that criteria only a human can prove must be marked USER-RUN so the acceptance panel does not claim them. Verified. Governs how AC9/10/11/12 (RECORDED-EVIDENCE) and AC14/15 (USER-RUN) are labeled.
    ref: requests/feature-requests/README.md:45-59
  - [33]
    claim:
      The Index row `| [data-engineer-agent](data-engineer-agent/) | scoped | **Tooling, not pipeline** … |`. Verified. Phase 8's bookkeeping edits this Stage cell to match the artifacts' Status blockquotes (AC16).
    ref: requests/feature-requests/README.md:92
  - [34]
    claim:
      'As of Phase 0, no endpoint has been called from this repo — the catalog is `unconfirmed` throughout.' Verified. This feature reads no endpoint and depends on none of it; the file's only role here is as the DESTINATION the memory routing rule names (AC13), which the memory file must never become a second, unaudited home for.
    ref: docs/data-sources.md:5-10
files_to_touch:
  - [1]
    change:
      NEW (Phase 1). The go/no-go artifact: the exact probe procedure, verbatim evidence, and one `verified`/`measured` label per answer for both halves of AC9. Zero `unconfirmed` labels in its Answers section.
    path: requests/feature-requests/data-engineer-agent/reviews/harness-probe.md
  - [2]
    change:
      NEW (Phase 2). Committed, bounded memory. Header states what belongs and what routes elsewhere, the per-entry format (date / epistemic label / claim / evidence pointer / routing tag), the five-label vocabulary from `CLAUDE.md:76-79` with the `update-docs/SKILL.md:105` divergence noted, and the inline-code-paths convention. Seeded with 2-4 entries, each citing a real repo artifact.
    path: .claude/agents/data-engineer-memory.md
  - [3]
    change:
      NEW, grown across Phases 2/3/5. Pure predicate functions plus paired negative controls for: memory budget (cap named in the message), memory entry format, `CLAUDE.md` 200-line budget, frontmatter validity and exactly-one-definition, guardrail clauses (AC2), the four-entry deny set, the definition-names-the-memory-path reference, and the `CLAUDE.md`-contains-the-pointer guard.
    path: tests/test_agent_contract.py
  - [4]
    change:
      NEW (Phase 3). Frontmatter in the shape the probe confirmed. Body: role framing, override preamble, the RELOCATED rulebook in two self-contained sections (extraction / dbt), pointers to the bronze and silver layer READMEs, the memory pointer, the write allowlist plus repo-level deny set, git-read-only as an absolute with its recorded reason, the memory-vs-docs routing rule naming `docs/data-sources.md`, the three-way spec-gap escalation policy, the seven-section handoff template with a `track` field, spec-triage dry-run mode, and the two prohibitions (no pipeline skills, no editing its own definition).
    path: .claude/agents/data-engineer.md
  - [5]
    change:
      NEW (Phase 4, extended Phase 6). `lint_handoff(text) -> list[str]` plus a walker over `requests/*-requests/*/reviews/*.md` that self-selects on the `<!-- handoff: v1 -->` marker. Enforces seven non-empty sections, no `^@@`/`^+++`/`^---` diff hunks (with the YAML-fence and thematic-break distinction explicitly tested), and the line cap. Four synthetic negative controls; the anti-vacuity coverage assertion lands in Phase 6.
    path: tests/test_handoff_contract.py
  - [6]
    change:
      EDIT (Phase 5). CUT: the Data Layer section (:84-103) and four implementation-facing gotchas (:107-116, :126). KEEP: map, Important Locations, Key Context, Project Conventions, cost guardrail (:117-119), `pre-commit` naming note (:120-121), CI-rename trap (:122-125), How to Help. ADD: a `.claude/agents/` row in the fenced project map beside the `.claude/skills/` line at :27, and a pointer line naming the definition's path. CLARIFY: the subagent bullet at :73-75 so read-only-git and file-write permission are distinguishable.
    path: CLAUDE.md
  - [7]
    change:
      NEW (Phase 5). What the directory is, the spawn protocol (clean tree → snapshot → spawn → post-run integrity comparison), and the deny set. Matches the self-documenting-directory norm the repo already enforces for dbt layers at `tests/test_repo_structure.py:77-84`.
    path: .claude/agents/README.md
  - [8]
    change:
      EDIT (Phase 5), doc half of Decision 7 only. Add `agents` to the touched-area bucket list at :127-131. Do NOT touch `acceptance_panel.js` — its `AREA_TO_SPEC` change is the deferred JS half, and its two `.mjs` guards are not run by CI.
    path: .claude/skills/implement-plan/SKILL.md
  - [9]
    change:
      EDIT (Phase 5). Add `agents` to the bucket list at :47-48; follow the rulebook relocation in the CLAUDE.md checklist at :66-78; and point the line-budget check at :76-78 at the new pytest guard so local, CI, and the doc use one counter instead of two that disagree by 18 lines.
    path: .claude/skills/update-docs/SKILL.md
  - [10]
    change:
      EDIT (Phase 6) — the default faithful-spec target, WRITTEN BY THE AGENT, not the main thread. A short section (~15 lines) describing `.claude/agents/` and the spawn protocol. Real, small, reversible, outside the deny set, lands no pipeline code.
    path: README.md
  - [11]
    change:
      NEW (Phase 6). The run-A handoff (marker line + seven non-empty sections, `verified` rows citing commands and their real output) plus the pre/post tree-state pair pasted in as committed evidence and the AC12 comparison verdict. Under the cap, no diff hunks.
    path: requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md
  - [12]
    change:
      NEW (Phase 7). The omission drill: the spec as given, the grep results, verbatim quotes of the model/`schema.yml` excerpts and the handoff's spec-gap section, the explicit PASS/FAIL verdict, the tree-integrity pair, and the repetition count with an honest evidence label.
    path: requests/feature-requests/data-engineer-agent/reviews/proving-run-b.md
  - [13]
    change:
      NEW (Phase 8, deliberately last — accepted ADRs are immutable per `docs/decisions/README.md:29-32`). All five sections. Consequences must state that the guard is detection rather than prevention, that the premise is inferred rather than observed, that the evidence is N observations, that the context savings are deferred to the dispatch sequel, and that the whole feature rests on harness behavior CI cannot test.
    path: docs/decisions/0007-write-capable-implementation-subagent.md
  - [14]
    change: EDIT (Phase 8). One new row in the Index table at :39-46, matching the existing format and status column.
    path: docs/decisions/README.md
  - [15]
    change: EDIT (Phase 8). The `data-engineer-agent` Index row at :92 — Stage cell advanced to match the artifacts' Status blockquotes (AC16).
    path: requests/feature-requests/README.md
  - [16]
    change: EDIT (Phase 8), status blockquote only (line 1). Do not touch its body — it is decided.
    path: requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md
  - [17]
    change: EDIT (Phase 8), status blockquote only (line 1).
    path: requests/feature-requests/data-engineer-agent/FEATURE_REQUEST.md
  - [18]
    change:
      NEW, GITIGNORED (Phase 7). Scratch dbt project for the omission drill — its own `dbt_project.yml`, `profiles.yml` on in-memory DuckDB, two tiny seed CSVs, and the model the agent produces. Never staged; `/commit`'s refusal table names `var/` first. Committed evidence lives in `reviews/proving-run-b.md` instead.
    path: var/scratch/omission-drill/
  - [19]
    change:
      NEW, GITIGNORED (Phases 6-7). Pre-spawn snapshots: `data-engineer-agent-run-a-pre.patch`, the run-B equivalent, and the captured `git status --porcelain` / `--stat` / `rev-parse HEAD` / `stash list` output, per `implement-plan/SKILL.md:120-125`.
    path: var/tmp/
ok:
  True
onboarding_files:
  - [1]
    path: requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md
    why:
      The decided upstream artifact. Read in full — its 16 numbered Acceptance Criteria (lines 120-157), the Core tier (lines 161-183), the 13 Decisions (lines 367-461) and the two post-panel amendments (Decision 12 relocates the rulebook; Decision 13 sequences dispatch into a sequel) are the contract this plan executes. Do not re-open it.
  - [2]
    path: requests/feature-requests/data-engineer-agent/FEATURE_REQUEST.md
    why:
      Context only. Lines 39-47 hold the four observable signals — signal four (line 46-47, 'silver declares its grain and proves it holds even when the spec forgets') is what Phase 7's omission drill tests. Lines 148-199 are the nine open questions the scope disposed.
  - [3]
    path: .claude/skills/implement-plan/SKILL.md
    why:
      Closest prior art and the source of the central tension. :100-112 the invariant restatement, :111-112 the PowerShell UTF-8 trap (a seeded memory entry), :120-125 the pre-spawn snapshot protocol and the recorded scar this feature re-admits, :127-131 the touched-area bucket list that has no `agents` key, :155-156 the read-only-subagents rule, :187-190 the post-run tree-integrity re-check that Phases 6-7 reuse verbatim.
  - [4]
    path: CLAUDE.md
    why:
      The file Phase 5 cuts. :16-33 project map (gains a `.claude/agents/` row), :73-75 the subagent read-only-git bullet needing clarification, :84-103 the Data Layer section that MOVES into the agent definition, :105-126 Constraints & Gotchas (four implementation-facing bullets move). 140 physical lines; 122 by `Measure-Object -Line`, which skips blanks — see Open Questions.
  - [5]
    path: tests/test_repo_structure.py
    why:
      The established home for config-and-filesystem-agree guards. Docstring :1-9 justifies the class; :77-84 `test_every_layer_documents_itself` is the closest structural analogue for the new `.claude/agents/` guards; :19 shows the `REPO_ROOT = Path(__file__).resolve().parents[1]` idiom every new guard must reuse.
  - [6]
    path: tests/test_doc_links.py
    why:
      Both a constraint and a model. :31-48 `EXCLUDED_PARTS` has no `.claude` entry, so every new Markdown file is link-checked automatically; :86-87 exempts `var/` targets, which is why proving-run artifacts may cite scratch paths; :95-104 is the anti-vacuity guard every new guard must imitate with its own negative control.
  - [7]
    path: .claude/skills/implement-plan/acceptance_panel.js
    why:
      :161-163 `READONLY` — the absolute read-only mandate whose structure the write-allowlist inverts; :196-201 `SPEC_DEFS` (the `skill-quality` mandate at :199 applies verbatim to an agent definition); :202-206 `AREA_TO_SPEC` — verified to have no `agents` key, which is why a future edit to the definition draws no specialist reviewer.
  - [8]
    path: .claude/skills/scope-feature/scope_panel.js
    why:
      :26-33 the recorded stub-degeneration behavior and the ANTISTUB apparatus (why the return contract is prose in a linted file, not a StructuredOutput schema); :117-133 `SHARED` — the compressed, pointer-shaped invariant restatement whose register the definition copies; :174 the spawn signature `runChecked(prompt, {label, phase, schema, effort})` with no agent-type parameter, which is the dead-artifact risk Phase 1 probes.
  - [9]
    path: .claude/skills/update-docs/SKILL.md
    why:
      :47-48 the bucket list naming `.claude/skills/` only (Decision 7's doc half), :53-57 the one mechanical check the doc gate owns, :66-78 the CLAUDE.md checks and the 200-line budget precedent the memory cap reuses (:76-78 names the PowerShell one-liner Phase 2 mechanizes), :103-113 the `docs/data-sources.md` epistemic-label audit the memory routing rule must not route around (:105 names a four-label set that differs from CLAUDE.md:76-79's five).
  - [10]
    path: .claude/skills/commit/SKILL.md
    why:
      :42-45 the branch check, :47-67 per-path staging and the refusal table — the actual review gate this whole design leans on, and what AC14 (USER-RUN) exercises. Also the house voice the definition and README must match.
  - [11]
    path: pyproject.toml
    why:
      The real gates new guard code must satisfy: :43-64 ruff at line-length 100 selecting `E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF` (PTH means pathlib, never os.path); :70-74 mypy `strict = true` over `files = ["src", "tests"]` — every new test function needs `-> None` and `yaml.safe_load`'s `Any` must be narrowed; :77-82 pytest config.
  - [12]
    path: .github/workflows/ci.yml
    why:
      Three jobs and NO Node step — verified (:26-27 `Lint, types, tests`, :55-56 `dbt build`, :87-88 `Secret scan`, gitleaks :96-99). This is why the guards go under `tests/` and not as a `.mjs` sibling. :78-85 the sqlfluff conditional is a regression tripwire for Phase 7.
  - [13]
    path: transform/models/silver/README.md
    why:
      :5-7 is the grounded reason no proving run may target `transform/models/`; :9-25 the grain-declaration-plus-uniqueness-test example the omission drill's scratch model is shaped after.
  - [14]
    path: docs/decisions/README.md
    why:
      :19-25 the five required ADR sections, :29-32 accepted ADRs are immutable (why Decision 10 writes ADR 0007 after the proving runs), :39-46 the Index table that gains the 0007 row.
open_questions:
  - WHAT COUNTS AS A LINE, for both caps? `Measure-Object -Line` (the command AC7 and `update-docs/SKILL.md:77` name) returns 122 for `CLAUDE.md`; `len(text.splitlines())` returns 140, because the file has 18 blank lines. The memory cap of 120 (Decision 5) is therefore ambiguous by roughly 15%. RECOMMENDATION: count total physical lines via `len(text.splitlines())`, state the rule in the assertion message, and have Phase 5 point `update-docs/SKILL.md:76-78` at the pytest guard so one counter governs. Needs a yes before Phase 2 writes the assertion.
  - WHERE DO THE MEMORY FILE AND README LIVE, given AC1 asserts `.claude/agents/` holds exactly one `*.md` agent definition? The scope places all three in that directory (PROJECT_SCOPE.md:165, :169, :183). RECOMMENDATION: keep the paths and define 'agent definition' in the guard as a frontmatter-carrying `.md` excluding `README.md` and `*-memory.md`. But Phase 1's probe (c) can override this: if the harness registers or chokes on frontmatter-less Markdown in that directory, the memory file must move (e.g. `.claude/agent-memory/data-engineer.md`) and every path in this plan shifts. Answered by the probe, not by preference.
  - THE FAITHFUL RUN'S TARGET (Phase 6). The plan defaults to a short `README.md` section describing `.claude/agents/` — real, small, outside the deny set, no pipeline code, reviewable through `/commit`. Alternatives considered and rejected: `tests/fixtures/README.md` (inside the deny set, and the scope at :307 explicitly forbids absorbing that known drift as a convenient target); anything under `src/` or `transform/models/` (non-goal at :110); `docs/data-sources.md` (the routing rule forbids the agent editing it). If the user prefers a different target, it must satisfy the same four constraints.
  - REPETITIONS PER DRILL (Decision 8 left this conditional on affordability). Two runs each is four agent spawns plus four tree-integrity comparisons. RECOMMENDATION: two for the omission drill (the behavioral one, where nondeterminism matters most) and one for the faithful run, with the artifact and ADR 0007 labeling run A's evidence a single observation. The honesty requirement is not optional either way.
  - WHICH EPISTEMIC VOCABULARY GOVERNS MEMORY ENTRIES — `CLAUDE.md:76-79`'s five labels (`measured`/`verified`/`inferred`/`assumed`/`unconfirmed`) or `update-docs/SKILL.md:105`'s four (`measured`/`verified`/`documented`/`unconfirmed`)? RECOMMENDATION: the five-label set for memory (it is the repo-wide convention), leaving `docs/data-sources.md` on its four, with the divergence named in one line of the memory header. A cold implementer will otherwise pick one silently and create a third variant.
  - WHERE THE WRITE ALLOWLIST IS DECLARED MACHINE-READABLY — frontmatter, or a fenced list under a stable `## Write allowlist` heading? This is the dependency the dispatch sequel rests on (PROJECT_SCOPE.md:489-490). Phase 1 answers it; the plan's fallback is the fenced-list-under-stable-heading form, which is parseable without harness support. Worth confirming the heading text now so the sequel does not have to rename it later.
  - DOES THE DENY SET NEED A MECHANICAL COMPANION, or is phrase-presence in the definition plus `/commit`'s per-path staging enough? Blocker F1's concern is an agent editing the guards that catch it and reporting green — which phrase-presence in the definition does not prevent, only documents. RECOMMENDATION for v1: keep it as declared-plus-guarded-for-presence, and record in ADR 0007 that the real net is `/commit`'s staged-list-then-yes plus the post-run tree comparison. A pre-spawn tool-permission mechanism, if the probe found one, would be strictly better and should be used instead.
  - THE MEMORY-VS-DOCS ROUTING GUARD (Decision 9: yes, but warning-shaped, never a hard CI gate). This plan implements the routing RULE in the definition and the grep-at-review-time check in AC13, but ships no automated keyword guard — because 'leaguegamelog returns a DataFrame, not JSON' is simultaneously the canonical GOOD memory entry and exactly what a keyword guard would flag. Confirm that deferring the mechanical half to the curation request (where real entries will exist to design against) is the intended reading of Decision 9.
phases:
  - [1]
    acceptance:
      - `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md` exists and answers BOTH halves of AC9: (a) what loads a `.claude/agents/*.md`, what frontmatter it accepts, where tool permissions are declared; (b) whether such a subagent inherits project `CLAUDE.md` and whether it sees project skills.
      - Every answer in that file carries an epistemic label of `verified` or `measured`. Mechanical check: `Select-String -Path requests/feature-requests/data-engineer-agent/reviews/harness-probe.md -Pattern 'unconfirmed'` returns no hit inside the Answers section.
      - The artifact states the exact probe used (the literal spawn call) and quotes the raw evidence, including whether the sentinel string round-tripped.
      - An explicit GO or NO-GO line appears at the top.
      - `Test-Path .claude/agents/probe-canary.md` and `.claude/agents/probe-plain.md` are both False — the canaries are gone.
      - `uv run pytest -q` is green (the new Markdown file enters `tests/test_doc_links.py`'s scanned set for free — `EXCLUDED_PARTS` at :31-48 has no `.claude` entry, and `MIN_EXPECTED_FILES = 20` at :53 against 33 tracked `.md` files today).
    commit_note:
      Checkpoint: hand to the user for `/commit`. One artifact only — `reviews/harness-probe.md`. This is the phase most worth committing alone: it is the evidence that the rest of the feature is worth building, and if the answer is NO-GO the probe is the whole deliverable. Do not stage anything under `var/`.
    goal:
      Turn the two unconfirmed harness beliefs into `verified`/`measured` facts recorded in a committed artifact, and decide go/no-go BEFORE a line of the definition is written. Nothing downstream is safe to build until this returns.
    name: Phase 1 — Harness probe (go/no-go gate)
    steps:
      - Confirm you are on branch `feature/data-engineer-agent` (`git branch --show-current`). Do NOT create or switch branches; do NOT commit — that is the user's gate at the end of every phase.
      - Create a THROWAWAY probe definition at `.claude/agents/probe-canary.md`. Give it (a) YAML frontmatter with `name`, `description`, and speculative keys the design would want — `tools`, `allowed-tools`, `model` — so you learn which are accepted vs rejected vs ignored; (b) a body containing a unique sentinel string (e.g. `PROBE-SENTINEL-7F3A`) and an instruction to report back a fixed checklist.
      - PROBE (a) — WHAT LOADS IT. Attempt to spawn a subagent BY THAT AGENT TYPE using whatever spawn surface this harness exposes (the Task/Agent tool's agent-type or subagent_type parameter; the skills listing; any settings file the harness documents). Record verbatim: the exact call made, whether the type name resolved, and whether the sentinel string came back — the sentinel is the only proof the BODY reached the agent rather than just the name resolving.
      - PROBE (a) continued — WHERE PERMISSIONS ARE DECLARED. Record whether the frontmatter keys were accepted, rejected with an error, or silently ignored. This is the dependency the sequel's dispatch rule rests on (PROJECT_SCOPE.md:463-490): if no machine-readable allowlist can live in frontmatter, record that fact and note the fallback (a fenced list under a stable `## Write allowlist` heading in the body, parseable by a future dispatcher).
      - PROBE (b) — INHERITANCE AND SKILL VISIBILITY. Have the probe agent report: whether it received project `CLAUDE.md` as an unrequested system-reminder (quote the first line it saw), whether it can see project skills by name, and what its default tool set is. The MEASURED baseline to compare against is recorded at PROJECT_SCOPE.md:143 — the panel spawn path does inherit; this is a different spawn path.
      - PROBE (c) — DIRECTORY HYGIENE, added because it decides file layout. Put a second `.md` file in `.claude/agents/` with NO frontmatter (e.g. `.claude/agents/probe-plain.md`) and record whether the harness ignores it, warns, or registers a bogus agent. If stray non-agent Markdown breaks loading, the memory file and README CANNOT sit in `.claude/agents/` and the plan's paths change (see Open Questions).
      - Write `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md`: the exact probe procedure, the verbatim evidence, and one epistemic label per answer — `verified` or `measured` only, never `unconfirmed`. Where an answer is genuinely unobtainable, say so explicitly and label it, rather than guessing.
      - Record the GO/NO-GO line explicitly at the top of the artifact. NO-GO (nothing loads `.claude/agents/*.md` and no frontmatter shape is accepted) → STOP the build, do not proceed to Phase 2, and return the request to scoping per blocker A2-02 (PROJECT_SCOPE.md:509).
      - DELETE both probe canary files before the checkpoint. AC1 asserts `.claude/agents/` holds exactly one agent definition; a lingering canary reddens that guard in Phase 3. Deleting an untracked file you created is a filesystem operation, not a git operation — do not reach for `git clean`.
  - [2]
    acceptance:
      - `uv run pytest tests/test_agent_contract.py -q` is green.
      - Every guard in the file has a paired negative control that FAILS on mutated input — verified by temporarily inverting one control and watching it redden, then restoring it. A guard without a negative control is not accepted (`tests/test_doc_links.py:95-104` is the precedent).
      - The memory-budget assertion message contains the literal cap number (grep the file for it).
      - `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` are all green.
      - `uv run pytest -q` is green overall — `tests/test_repo_structure.py` and `tests/test_doc_links.py` unaffected.
      - The memory file contains zero data/era/endpoint/availability/rate-limit claims (AC13's memory half): grep it for `season`, `leaguegamelog`, `2013-14`, `rate limit` and confirm each hit is an ergonomics claim, not a fact an analyst would act on.
    commit_note:
      Checkpoint: hand to the user for `/commit`. Two paths — `.claude/agents/data-engineer-memory.md` and `tests/test_agent_contract.py`. This is the first commit where the memory delta appears as a per-path staged entry, which is the mechanism AC14 later asks a human to judge; point the user at it.
    goal:
      Land the committed, bounded memory file together with the guards that bound it — including the negative controls that stop any guard passing vacuously — and mechanize `CLAUDE.md`'s 200-line budget in the same assertion.
    name: Phase 2 — Guard-suite foundation and the memory file
    steps:
      - Create `.claude/agents/data-engineer-memory.md` (rename the slug consistently if the probe forced a different layout). Header states: what belongs (implementation ergonomics — client shapes, casing surprises, tooling traps), and what routes elsewhere (`docs/data-sources.md` for anything an analyst would act on, `CLAUDE.md` Constraints & Gotchas for repo-wide scar tissue, `docs/decisions/` for decisions).
      - State the per-entry format in the header: date / epistemic label / the claim / an evidence pointer / a routing tag. Use CLAUDE.md:76-79's five-label vocabulary (`measured`/`verified`/`inferred`/`assumed`/`unconfirmed`) and note in one line that `docs/data-sources.md` uses a different four-label set per `update-docs/SKILL.md:105`, so the divergence is recorded rather than discovered.
      - State the paths-as-inline-code convention in the header, with its reason: `tests/test_doc_links.py:72-91` scans only markdown-link syntax, so a backticked path is invisible to it while a `[text](path)` link to a file that later moves reddens CI on an unrelated PR.
      - Seed 2-4 entries, each traceable to a repo artifact — never an invented gotcha. Recommended set with HONEST labels: (1) `documented` — PowerShell 5.1 `Set-Content`/`Out-File` mangle UTF-8; use the file-editing tools (cite `.claude/skills/implement-plan/SKILL.md:111-112`); (2) `verified` — the bundled `.claude/skills/**/tests/*.mjs` guards are NOT run by CI, which has three jobs and no Node step (cite `.github/workflows/ci.yml:25-99`); (3) `documented` — sqlfluff errors on an empty model selection, hence the conditional guard (cite `.github/workflows/ci.yml:78-85`); (4) `measured` — the harness-probe result from Phase 1 (cite `reviews/harness-probe.md`). Do NOT label (1) or (3) `measured`; neither was run here.
      - Create `tests/test_agent_contract.py`. Reuse the `REPO_ROOT = Path(__file__).resolve().parents[1]` idiom from `tests/test_repo_structure.py:19`. Write the checks as PURE PREDICATE FUNCTIONS over text — `_line_count(text) -> int`, `_missing_clauses(text, required) -> list[str]`, `_entry_format_violations(text) -> list[str]` — so each can be exercised against synthetic input.
      - Ship in this phase: the memory-budget guard (line count at or under the cap, with the CAP NAMED IN THE ASSERTION MESSAGE per AC4) and its negative control (an over-budget synthetic string fails the same predicate); the memory entry-format guard and its negative control; the `CLAUDE.md` budget guard (under 200) reusing the same `_line_count` predicate, and its negative control.
      - State the counting rule in a module docstring and in the assertion message — `len(text.splitlines())`, counting blank lines. Do this deliberately: `Measure-Object -Line` (the one-liner at `update-docs/SKILL.md:77`) skips blanks and returns 122 for `CLAUDE.md`, while the file has 140 physical lines. Two counters that disagree by 18 lines is exactly the drift a guard exists to kill.
      - Satisfy the real gates while writing: mypy is `strict = true` over `files = ["src", "tests"]` (`pyproject.toml:70-74`) so every test needs `-> None` and any `yaml.safe_load` result must be narrowed with an `isinstance` assert; ruff selects `PTH` (`pyproject.toml:49-61`) so use `pathlib`, never `os.path`.
  - [3]
    acceptance:
      - `uv run pytest tests/test_agent_contract.py -q` is green, now covering frontmatter validity, guardrail clauses, the deny set, the memory pointer, the memory budget and format, and the `CLAUDE.md` budget.
      - Every new guard has a paired negative control demonstrated to fail on mutated input.
      - The definition's frontmatter parses under `yaml.safe_load` to a mapping with non-empty `name` and `description` (AC1), and its shape matches what `reviews/harness-probe.md` recorded — a reader can see the design followed the probe (AC9's last clause).
      - AC2's substrings are present verbatim: `checkout`, `reset`, `restore`, `clean`, `stash`, and the never commit/merge/push/amend clause.
      - AC13's definition half: the routing rule names `docs/data-sources.md` literally, grep-confirmed.
      - `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, and `uv run pytest -q` are all green.
      - `uv run pytest tests/test_doc_links.py -q` is green — every relative link in the new definition resolves (put any forward-referenced or deliberately-broken example path inside a fenced block; fenced content is exempt per `tests/test_doc_links.py:69`).
    commit_note:
      Checkpoint: hand to the user for `/commit`. Paths: `.claude/agents/data-engineer.md` and `tests/test_agent_contract.py`. The capability now exists but nothing has proven it — say so when handing off; the definition is still a well-formed Markdown file until Phase 6 runs it.
    goal:
      Land the one write-capable agent definition — in whatever frontmatter shape Phase 1 CONFIRMED — carrying the relocated rulebook, the write allowlist plus deny set, the return contract, and the escalation policy; and the guards that redden if any guardrail clause is ever silently deleted.
    name: Phase 3 — The agent definition and its structural guards
    steps:
      - Write `.claude/agents/data-engineer.md`. Frontmatter EXACTLY as the probe confirmed — do not copy the SKILL.md `name` + trigger-rich `description` shape on the assumption it transfers; that is the SKILL format and AC-blocker F3 exists because the original criterion asserted an unverified schema.
      - Body, in the house register of `.claude/skills/commit/SKILL.md`: the manager/developer role framing; an explicit OVERRIDE PREAMBLE naming which inherited sections the agent ignores and which it obeys absolutely (load-bearing only if Phase 1 confirmed inheritance — write it either way, it costs a paragraph and the harness can change under a version bump).
      - THE RELOCATED RULEBOOK (Decision 12) — this definition is now the single owner, not a compressed non-authoritative echo: resolve by name (`ref()`/`source()`, never a literal path; in Python through the config layer, never `parents[N]`); the landing zone is immutable; bronze is 1:1 with the source; silver declares its grain in `schema.yml` prose AND proves it with a uniqueness test; facts MERGE on key because box scores get restated; layer promotion is gated on tests; tracking-derived columns are structurally absent before 2013-14, not null; the three irregular seasons (2011-12 66g, 2019-20 unequal, 2020-21 72g) break any 82-game assumption.
      - Structure the rulebook as TWO self-contained sections — extraction rules and dbt-modeling rules — so a later split into two specialists is a copy rather than a rewrite. Precedent: `acceptance_panel.js:197-198` already models these as distinct specialists (`data-contract`, `extraction`).
      - POINT, don't paraphrase, for the layer contracts: link `transform/models/bronze/README.md` and `transform/models/silver/README.md` (the latter's :5-7 is why an unproven builder never touches the dimensional core).
      - THE WRITE-GUARD PACKAGE: a `## Write allowlist` section (fenced list, stable heading, parseable) covering the memory file plus the task's declared target paths; a repo-level DENY set naming `.github/`, `ops/`, `tests/`, `.claude/` with the memory file as the single carve-out (blocker F1); the required-clean-tree precondition; and the main-thread spawn protocol reusing `implement-plan/SKILL.md:120-125` and `:187-190` verbatim.
      - GIT READ-ONLY AS AN ABSOLUTE with its recorded reason: never `checkout`/`reset`/`restore`/`clean`/`stash` or anything discarding working-tree state; never commit, merge, push, or amend; `/commit` is the only committer (`CLAUDE.md:65-69`, `commit/SKILL.md:47-67`). Quote the scar from `implement-plan/SKILL.md:124` so the rule carries its reason.
      - THE MEMORY POINTER by literal path, and THE ROUTING RULE in one line (AC13): any data, era, endpoint, availability, or rate-limit fact goes to `docs/data-sources.md` via the handoff's `docs-delta` section and the main thread's `/update-docs` — never into memory, and the agent never edits `docs/data-sources.md` itself.
      - THE THREE-WAY SPEC-GAP ESCALATION POLICY: a spec that CONTRADICTS an invariant stops the agent with a spec-gap report; a spec SILENT on an invariant is built to the invariant and flagged; an AMBIGUOUS requirement is built at the smaller interpretation and flagged. All three must be observable in the handoff.
      - PROHIBITIONS: never invoke `/scope-feature`, `/create-implementation-plan`, or `/implement-plan` (nesting panels inside a subagent multiplies cost with no return); never edit its own definition. Plus the SPEC-TRIAGE (DRY-RUN) mode: one paragraph plus the documented invocation phrase — read the plan, report gaps against the invariant set, build nothing.
      - Extend `tests/test_agent_contract.py` with, each plus a negative control: the frontmatter guard (exactly one agent definition in `.claude/agents/`, opening with YAML frontmatter parsing to a non-empty `name` and `description` — define 'agent definition' explicitly as a `.md` in that directory with frontmatter, EXCLUDING `README.md` and `*-memory.md`, otherwise the memory file counts and the guard reddens); the guardrail-clause guard (AC2 — literal substrings for `checkout`/`reset`/`restore`/`clean`/`stash` and for never commit/merge/push/amend); the deny-set guard (all four denied paths present); and the memory-reference guard (the definition names the memory file by its literal path — AC4's second half).
  - [4]
    acceptance:
      - `uv run pytest tests/test_handoff_contract.py -q` is green, with all four negative controls demonstrated (missing section, diff hunk, over cap, and the frontmatter-vs-`^---` distinction).
      - `lint_handoff` returns a non-empty violation list for each synthetic bad input and an empty list for the synthetic good one.
      - The seven-section template plus the `track` field and the `<!-- handoff: v1 -->` marker appear in the agent definition (grep).
      - `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` are all green.
      - The linter finds zero handoff files today and says so honestly rather than passing silently — the anti-vacuity coverage assertion is deferred to Phase 6 and a TODO comment in the test names that dependency.
    commit_note:
      Checkpoint: hand to the user for `/commit`. Paths: `tests/test_handoff_contract.py` and the definition edit. Note in the handoff to the user that the linter is currently exercised only by synthetic controls; Phase 6 is what points it at a real artifact.
    goal:
      Make 'the main thread did not have to read every edit' objectively checkable BEFORE any proving run produces a handoff, so the drills are scored by a linter that already existed rather than one written to fit their output.
    name: Phase 4 — The return contract: handoff template and schema lint
    steps:
      - Define the handoff's fixed sections in the agent definition (a fenced template block): `built` / `verified` (with evidence) / `assumed` / `surprised-me (memory candidates)` / `could-not-do` / `docs-delta` / `still-open`. Add a `track` field (`feature` | `bugfix`) — one line now, and it is what keeps the contract track-agnostic when a bug is first handed to the agent (`implement-plan/SKILL.md:49-53` already auto-detects track from the artifact path).
      - Require a first-line self-declaring marker: `<!-- handoff: v1 -->`. This is what lets the linter find handoffs without a brittle filename glob.
      - Require the `verified` section to be a table whose every row cites a concrete command and its actual output — a claim with no command is an `assumed` row, not a `verified` one.
      - Require `docs-delta` to list every memory entry tagged `docs-candidate`, so the promotion queue surfaces to `/update-docs` without the agent ever touching `docs/data-sources.md`.
      - Create `tests/test_handoff_contract.py`. Expose `lint_handoff(text: str) -> list[str]` returning violation strings, then a test that walks `requests/*-requests/*/reviews/*.md`, lints every file whose first line carries the marker, and skips the rest.
      - The linter enforces: all seven sections present and NON-EMPTY; no diff hunks — no line matching `^@@`, `^\+\+\+`, or `^---` (be careful: `^---` also matches a YAML frontmatter fence and a Markdown thematic break, so anchor the check to the three-dash-plus-space/path form or skip line 1, and cover that distinction with an explicit test); line count at or under the declared cap, with the cap named in the message.
      - Ship the negative controls in the same phase: a synthetic handoff missing a section fails; one containing a `^@@` hunk fails; one over the cap fails; a well-formed one passes. These run against strings, not files, so they work before any real handoff exists.
      - Do NOT build a StructuredOutput schema, a validating wrapper, or anti-stub retry machinery — explicitly out of scope (PROJECT_SCOPE.md:98), grounded in `scope_panel.js:26-33`. Enforcement lands on the ARTIFACT, not the agent's output schema.
  - [5]
    acceptance:
      - `uv run pytest tests/test_agent_contract.py -q` is green, now including the `CLAUDE.md`-contains-the-pointer guard and its negative control.
      - The `CLAUDE.md` budget guard is green and the file is well under 200 lines (it shrinks from 140 physical / 122 by `Measure-Object -Line`; AC7's stated command `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` must return under 200).
      - `CLAUDE.md`'s project-map block contains a `.claude/agents/` entry alongside the `.claude/skills/` line.
      - The subagent bullet reads so a reader can tell an agent editing a tracked file is not violating it (AC7's second half — a human reads this; state it as read-and-judged, not command-proven).
      - Grep confirms the grain rule ('silver declares its grain and proves it') NO LONGER appears in `CLAUDE.md` and DOES appear in the agent definition — this is what makes Phase 7's drill attributable.
      - `uv run pytest -q` and `uv run pytest tests/test_doc_links.py -q` are green; every relative link in the new `.claude/agents/README.md` resolves.
      - `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` are green.
    commit_note:
      Checkpoint: hand to the user for `/commit`, and flag this one as the highest-judgment diff in the feature. This edits the file every agent reads on every task — a bad cut degrades every future session rather than failing loudly, and no test can catch 'this rule was needed in the manager doc and is now somewhere the manager does not look.' The user should read the `CLAUDE.md` diff line by line before saying yes. `/commit` will very likely want the full `/update-docs` sweep here (a changed directory, a changed convention, a changed rules section).
    goal:
      Make the definition the SOLE owner of the build rules by cutting them out of `CLAUDE.md`, and land the doc integration the change earns — deliberately BEFORE the drills, so the omission drill's result is attributable to the definition rather than to inherited manager context.
    name: Phase 5 — Relocate the rulebook, integrate the docs
    steps:
      - Cut from `CLAUDE.md`: the whole **Data Layer** section (`CLAUDE.md:84-103`) and the four implementation-facing gotchas — 0.6s pacing (`:107-109`), prefer bulk endpoints (`:110-112`), affiliation is date-dependent (`:113-116`), Windows dev / Linux CI (`:126`). Confirm each cut clause already exists verbatim-in-substance in the definition BEFORE deleting it; add-then-remove, never the reverse.
      - KEEP in `CLAUDE.md`: the project map, Important Locations, Project Conventions, Key Context, How to Help, the cost guardrail (`:117-119`), the `pre-commit` naming note (`:120-121`), and the CI-rename/branch-protection trap (`:122-125`) — the agent is denied `.github/` and `ops/` anyway, so those rules belong to the manager.
      - Add the pointer `CLAUDE.md` keeps: one line naming `.claude/agents/data-engineer.md` as where the build rulebook now lives, so a reader who starts at the map still reaches it. This is AC3's replacement.
      - Add `.claude/agents/` to the project-map block (`CLAUDE.md:16-33`) alongside the existing `.claude/skills/` line at `:27`. The block is fenced, so entries there are exempt from link checking either way.
      - Clarify the subagent bullet at `CLAUDE.md:73-75` so git-read-only and file-write permission are distinguishable — a half-sentence making clear that editing a tracked file is not a git operation, so 'subagents get read-only git' does not mean 'subagents may not write'. Without this a future agent refuses a legitimate instruction.
      - Write `.claude/agents/README.md`: what the directory is, what the spawn protocol is (clean tree, snapshot, spawn, post-run integrity comparison), and the deny set. The repo already enforces self-documenting directories for dbt layers at `tests/test_repo_structure.py:77-84`; this matches that norm.
      - Decision 7's doc half (no JS changes): add `agents` to the touched-area bucket lists at `.claude/skills/implement-plan/SKILL.md:127-131` and `.claude/skills/update-docs/SKILL.md:47-48`. Leave `acceptance_panel.js:202-206` ALONE — that is the deferred JS half, and its two `.mjs` guards are not run by CI (`ci.yml` has no Node step), so an unreviewed edit there is a silent regression.
      - Follow the rulebook's own relocation in `update-docs/SKILL.md`: its CLAUDE.md checklist at `:66-78` says 'the rules sections' — update it so it audits what `CLAUDE.md` now actually holds, and point its line-budget check (`:76-78`) at the pytest guard from Phase 2 instead of the PowerShell one-liner, so local, CI, and doc all use one counter.
      - Add the AC3-replacement guard to `tests/test_agent_contract.py`: `CLAUDE.md` contains the definition's literal path. Negative control: a synthetic `CLAUDE.md` string without the pointer fails the same predicate.
  - [6]
    acceptance:
      - `reviews/proving-run-a.md` contains all seven handoff sections, each non-empty, and every row in the `verified` table cites a concrete command and its actual output.
      - `uv run pytest tests/test_handoff_contract.py -q` is green over that real file, and the coverage assertion confirms at least one handoff was found.
      - Grep for `^@@`, `^\+\+\+`, `^---` over `reviews/proving-run-a.md` returns nothing (excluding a frontmatter fence if present), and its line count is under the declared cap.
      - The tree-integrity comparison (AC12) is recorded IN the artifact and shows: the tree was clean or held only the agent's own prior work before the spawn; no tracked file outside the declared allowlist was modified or deleted; nothing pre-existing was reverted; HEAD unchanged; `git stash list` unchanged.
      - The produced diff is real and small — `git diff HEAD --stat` shows only the spec's target file plus, at most, the memory file.
      - `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` are green. If the agent's memory delta pushed the file over its cap, that is a REAL failure of the budget guard, not a reason to raise the cap.
      - The artifact states the number of repetitions and, if one, labels the evidence a single observation.
    commit_note:
      Checkpoint: hand to the user for `/commit`. This is the run AC14 (USER-RUN) judges: confirm the memory delta appears as a visible per-path staged entry and that a human can tell the agent's writes from their own in the staged diff (`commit/SKILL.md:47-67`). Refuse to stage anything under `var/` — `/commit`'s refusal table (`commit/SKILL.md:57-63`) names it first.
    goal:
      Prove the capability end to end on a small, real, reversible, decoupled target: a genuine diff produced by the agent, a handoff that passes the linter written in Phase 4, and a tree-integrity trail showing nothing outside the allowlist moved.
    name: Phase 6 — Proving run A (the faithful spec)
    steps:
      - PRE-SPAWN, main thread. Confirm the tree is clean or holds only the agent's own prior work (`git status --porcelain`), then snapshot exactly as `implement-plan/SKILL.md:120-125` prescribes: `git diff HEAD > var/tmp/data-engineer-agent-run-a-pre.patch`, plus `git status --porcelain` and `git diff HEAD --stat` captured to the same scratch dir, plus the untracked list. Record `git rev-parse HEAD` and `git stash list` for the post-run comparison. `var/` is gitignored — this is scratch, not evidence.
      - Write the faithful spec — a small, decided, self-contained task OUTSIDE the deny set and outside `transform/models/` and `src/nba_platform/`. DEFAULT TARGET: a short `README.md` section describing `.claude/agents/` and the spawn protocol, capped at roughly 15 lines. It is real, reviewable through `/commit`, touches no data, and lands no pipeline code — which the scope's non-goal at PROJECT_SCOPE.md:110 requires. Explicitly forbid `tests/fixtures/README.md` as a target: it carries known adjacent drift the scope says must not be silently absorbed (PROJECT_SCOPE.md:307).
      - Spawn the agent by the type Phase 1 confirmed, handing it the spec and nothing else. Do not narrate the work for it; the point of the run is that you do not read every edit.
      - POST-RUN, main thread. Capture `git status --porcelain`, `git diff HEAD --stat`, `git rev-parse HEAD`, `git stash list` again and compare against the pre-spawn pair.
      - Write `requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md`: the handoff itself (all seven sections, non-empty, first line carrying the `<!-- handoff: v1 -->` marker), plus the pre/post tree-state pair pasted in as evidence, plus the comparison verdict. Evidence lands in COMMITTED `reviews/`, never only in `var/` (blocker F2) — paste the captured output, do not link to the scratch patch as the sole record.
      - Add the anti-vacuity coverage assertion to `tests/test_handoff_contract.py`: at least one file carrying the handoff marker was found and linted. A linter that scans nothing passes every time — the same failure `tests/test_doc_links.py:95-104` exists to prevent.
      - Per Decision 8, run the drill TWICE if affordable. If only once, the artifact must label the result a single observation rather than a proof — agent behavior is nondeterministic and one green run is one observation.
  - [7]
    acceptance:
      - `reviews/proving-run-b.md` records the drill and states PASS or FAIL explicitly, determined by grep over the drill artifacts and quoted verbatim (AC11).
      - `uv run pytest tests/test_handoff_contract.py -q` is green over run B's handoff, and the hunk-freeness and cap checks pass.
      - The tree-integrity comparison for run B is recorded and clean by the same six checks as Phase 6 (AC12).
      - `git status --porcelain transform/` is empty — the drill wrote nothing into the real dbt project.
      - `uv run dbt build --project-dir transform --profiles-dir transform --target ci` is green — regression proof that the real warehouse is untouched.
      - `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` are green.
      - The artifact states the repetition count and labels single-run evidence as an observation, not a proof.
      - A FAIL blocks the feature: the plan does not proceed to Phase 8 on a FAIL — it returns the finding to the user, because a definition whose invariants are decorative is the failure this drill was built to catch.
    commit_note:
      Checkpoint: hand to the user for `/commit`. Stage `reviews/proving-run-b.md` only — everything under `var/scratch/omission-drill/` is gitignored working material and `/commit` must refuse it. If the drill FAILED, commit the artifact anyway: a recorded failure is the most valuable thing this feature can produce, and hiding it would be the exact overclaiming `CLAUDE.md`'s epistemics rule forbids.
    goal:
      Test whether the definition's invariant set is LOAD-BEARING or decorative — the only criterion in the whole feature that tests behavior rather than the existence of well-formed files.
    name: Phase 7 — Proving run B (the omission drill)
    steps:
      - Build the drill target as a SCRATCH dbt project under gitignored `var/scratch/omission-drill/` — never in `transform/`. Give it its own `dbt_project.yml` and `profiles.yml` targeting in-memory DuckDB, and two tiny seed CSVs shaped so a silver-style model over them has a real, non-trivial grain (a player-per-game shape with one traded player appearing twice is the honest fixture). If the model needs `dbt_utils.unique_combination_of_columns`, copy `transform/packages.yml` and run `dbt deps` inside the scratch project; otherwise a built-in `unique` on a surrogate key is sufficient for the drill.
      - Write the OMISSION SPEC: it asks for a silver-shaped model with a stated grain, and DELIBERATELY omits 'declare the grain in schema.yml and prove it with a uniqueness test'. Do not hint at it anywhere else in the spec. Confirm before spawning that the grain rule is absent from `CLAUDE.md` (Phase 5 removed it) so a PASS is attributable to the definition rather than to inherited manager context — this is blocker A2-01's whole point.
      - Snapshot pre-spawn exactly as in Phase 6 (`git status --porcelain`, `git diff HEAD`, `git diff HEAD --stat`, `git rev-parse HEAD`, `git stash list`) into `var/tmp/`.
      - Spawn the agent with the omission spec. Let it run without correction.
      - SCORE THE DRILL, quoting verbatim: PASS iff the produced model carries a uniqueness test proving the declared grain, OR the handoff explicitly flags the omission as a spec gap (the 'silent on an invariant → build to the invariant and flag' branch of the escalation policy). A silent, untested grain is a FAIL and BLOCKS the feature — do not soften it into a partial.
      - Write `reviews/proving-run-b.md`: the spec as given, the grep results over the drill artifacts, verbatim quotes of the relevant model/`schema.yml` excerpts and the handoff's spec-gap section (QUOTES, not diff hunks — the linter rejects hunks), the PASS/FAIL verdict, and the pre/post tree-integrity pair. The drill output lives in gitignored `var/`, so the committed artifact must carry enough quoted evidence to stand alone.
      - Post-run, verify the drill leaked nothing into `transform/`: `git status --porcelain transform/` must be empty. A stray `.sql` under `transform/models/` would also flip the sqlfluff step at `ci.yml:78-85` from skipped to running, which is a silent way to redden CI on an unrelated PR.
      - Repeat per Decision 8 if affordable; otherwise label the result a single observation in both this artifact and ADR 0007.
  - [8]
    acceptance:
      - `docs/decisions/0007-<slug>.md` exists with all five sections (AC8), its row appears in the Index at `docs/decisions/README.md:39-46`, and `uv run pytest tests/test_doc_links.py -q` proves the index link resolves.
      - The ADR's Consequences section contains an explicit statement that the guard is detection rather than prevention, and labels the proving-run evidence by its actual repetition count.
      - `PROJECT_SCOPE.md`, `FEATURE_REQUEST.md`, `IMPLEMENTATION_PLAN.md` and the Index row at `requests/feature-requests/README.md:92` all agree (AC16), grep-checkable.
      - `uv run pytest -q` green — including `tests/test_repo_structure.py`, `tests/test_doc_links.py`, `tests/test_agent_contract.py`, `tests/test_handoff_contract.py`, every negative control among them.
      - `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` green.
      - `uv run dbt build --project-dir transform --profiles-dir transform --target ci` green — the dbt job is a required check and must not have regressed.
      - `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` returns under 200 (AC7).
      - USER-RUN and marked as such per `requests/feature-requests/README.md:56-59`: the user's PR shows all three `ops/branch-protection.json:4` contexts green, with gitleaks covering the committed memory file per ADR 0006.
    commit_note:
      Final checkpoint: hand to the user for `/commit`, which should run the full `/update-docs` sweep here — this change adds a directory, alters conventions, adds an ADR, and advances request statuses, which is four of the six triggers at `commit/SKILL.md:83-93`. Then the push and the PR are the user's. A red CI check is stop-and-fix, not a retry loop.
    goal:
      Record why the repo's first write-capable subagent exists and what it honestly costs, reconcile every status row, and leave the branch in a state where CI's three required checks pass on the PR.
    name: Phase 8 — ADR 0007, bookkeeping, and the full green sweep
    steps:
      - Write `docs/decisions/0007-<slug>.md` carrying all five required sections per `docs/decisions/README.md:19-25`: Status (`accepted`), Context, Decision, Consequences, Alternatives considered. Written NOW and not earlier because `docs/decisions/README.md:29-32` makes accepted ADRs immutable — the Consequences section cannot be amended later, so it has to be written once the proving-run evidence exists (Decision 10).
      - State plainly in Consequences what the guard actually is: DETECTION, not prevention. Feature branch, pre-spawn snapshot, post-run integrity check, and `/commit`'s staged-list-then-yes all catch a bad write after the fact; nothing stops it. Cite the scar at `implement-plan/SKILL.md:120-125`. Do not imply the package is equivalent to read-only.
      - Also record honestly: the premise is inferred, not observed (`/implement-plan` has never run in this repo); the proving-run evidence is N observations, not a proof; the headline context savings are deferred until the dispatch sequel lands; and the feature rests on harness behavior this repo cannot test, which can change under a version bump with nothing in CI to notice.
      - Add the 0007 row to the Index table at `docs/decisions/README.md:39-46`, matching the existing row format.
      - Bookkeeping (AC16): advance `PROJECT_SCOPE.md`'s and `FEATURE_REQUEST.md`'s Status blockquotes per the grammar at `requests/feature-requests/README.md:81-85`, write `IMPLEMENTATION_PLAN.md`'s own status, and set the Index row at `requests/feature-requests/README.md:92` so the Stage cell matches the artifacts. The artifact's blockquote is the source of truth; the Index mirrors it.
      - Run the FULL local gate one final time and read the real output, not the exit code alone: `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`, `uv run pytest -q`, `uv run pytest tests/test_doc_links.py -q`, and `uv run dbt build --project-dir transform --profiles-dir transform --target ci`.
      - Re-verify tree integrity one last time against the Phase 6/7 snapshots (`implement-plan/SKILL.md:187-190`) and confirm nothing under `var/` is staged.
      - Hand the push and the PR to the user. AC15 is USER-RUN: CI green on all three required contexts named at `ops/branch-protection.json:4` — `Lint, types, tests`, `dbt build`, `Secret scan`. Do not push, do not open the PR, do not merge.
planner: sequencing
risks:
  - DEAD-ARTIFACT RISK — the largest, and the reason Phase 1 exists and cannot be skipped to save time. `scope_panel.js:174` spawns via `runChecked(prompt, {label, phase, schema, effort})` with no agent-type parameter, and `Get-ChildItem .claude -Force` shows no `settings.json`. If the frontmatter shape or the spawn path is wrong, this ships two Markdown files, a green test suite, and zero working capability — and AC1, AC2, AC4, AC5, AC6, AC7, AC8 all still pass, because they check FORM. Mitigation: Phase 1's sentinel round-trip is the only evidence that the BODY reached an agent rather than a name merely resolving. A NO-GO stops the build (blocker A2-02); it does not degrade into shipping the files anyway.
  - AC1's 'exactly one `*.md` agent definition' COLLIDES WITH THE MEMORY FILE AND README, both of which the scope also places in `.claude/agents/` (PROJECT_SCOPE.md:169, :183). A naive `len(list(dir.glob('*.md'))) == 1` guard reddens the moment the memory file lands. Mitigation: define 'agent definition' explicitly in the guard as a `.md` carrying YAML frontmatter with `name` + `description`, excluding `README.md` and `*-memory.md`, and say so in the assertion message. Phase 1's probe (c) additionally checks whether the harness chokes on frontmatter-less Markdown in that directory — if it does, the memory file must move out and every path in this plan changes.
  - TWO LINE-COUNTERS THAT DISAGREE BY 18 LINES. `CLAUDE.md` is 140 physical lines but `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` — the command AC7 names and `update-docs/SKILL.md:77` documents — returns 122, because `Measure-Object -Line` does not count blank lines. A pytest guard using `len(text.splitlines())` therefore measures something different from the documented check. Mitigation: the guard states its counting rule in the assertion message, Phase 5 updates `update-docs/SKILL.md:76-78` to name the pytest guard as the authority, and the memory cap of 120 is interpreted the same way. Left unresolved, the memory cap is ambiguous by roughly 15% and the first over-budget failure becomes an argument instead of a fix.
  - THE OMISSION DRILL IS CONFOUNDED IF PHASE 5 IS REORDERED AFTER IT. `CLAUDE.md:95-97` states the grain rule today, and a panel-spawned subagent is MEASURED to receive the full project `CLAUDE.md` as an unrequested system-reminder (PROJECT_SCOPE.md:143). Run the drill before the relocation and a PASS proves nothing about the definition — which is the exact thing blocker A2-01 says the drill is the only criterion able to prove. This ordering is load-bearing; an implementer who reorders phases for convenience destroys the feature's only behavioral evidence.
  - INSTRUCTIONS ARE NOT ENFORCEMENT, and the substitute guard is DETECTION rather than prevention. The scar at `implement-plan/SKILL.md:120-125` is a write-capable agent that ran `git checkout` and silently wiped uncommitted work while a vacuous selftest passed green. Feature branch, pre-spawn snapshot, post-run integrity check, and `/commit`'s staged-list-then-yes all catch it afterward; nothing stops it. ADR 0007 must say this plainly. The single genuinely new net is the REQUIRED-CLEAN-TREE PRECONDITION: spawn a write-capable builder onto a dirty tree and a human can no longer tell the agent's writes from their own in the staged diff, which is the specific way this feature loses work without any subagent doing anything forbidden.
  - PHASE 5 EDITS THE REPO'S MOST LOAD-BEARING FILE AND NO TEST CAN CATCH A BAD CUT. Moving the Data Layer section out of `CLAUDE.md` degrades every future session rather than failing loudly if something the main thread needs goes with it. The pointer guard proves a pointer exists, not that the cut was correct. Mitigation: add-then-remove ordering (confirm each clause is in the definition before deleting it), a standalone reviewable commit, and the user reading that diff line by line. This risk was introduced by post-panel Decision 12 and was never adversarially reviewed.
  - THE FOURTH RESTATEMENT PROBLEM IS RELOCATED, NOT SOLVED. `scope_panel.js:124`, `plan_panel.js:146`, and `implement-plan/SKILL.md:100-112` each still restate the same rules with no check that they agree, and Decision 12 removed the drift guard the panel had endorsed. After Phase 5, `CLAUDE.md` no longer states the rules at all — so the three panel-script copies now have NO canonical in-repo prose to be checked against except the agent definition. Nothing in this plan closes that; the honest position is to say so in ADR 0007 rather than imply relocation fixed it.
  - PROVING-RUN EVIDENCE IS INHERENTLY WEAK. Agent behavior is nondeterministic; one green drill is one observation. Decision 8 asks for two repetitions per drill if affordable, and makes a single run acceptable ONLY if both the artifact and ADR 0007 label it an observation rather than a proof. Claiming 'the design holds' off one run is a convention violation under `CLAUDE.md`'s epistemics rule, not merely optimistic.
  - `.claude/agents/` DRAWS NO SPECIALIST REVIEWER. Verified: `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) has no `agents` key, so the first future change to the definition or memory goes through the stage-4 panel with only the four core reviewers — the exact blind spot the `skill-quality` mandate (`acceptance_panel.js:199`) exists to close for `.claude/skills/`. Decision 7 deliberately defers the JS half; Phase 5 does the doc half only. Editing `acceptance_panel.js` is doubly risky here because its two `.mjs` guards are NOT run by CI (three jobs, no Node step), so a regression there is silent.
  - THE MEMORY FILE IS PUBLISHED AND FREE-TEXT. ADR 0006 makes the repo public and git history permanent; gitleaks (`ci.yml:96-99`) catches credentials by content but not a carelessly pasted machine path, account ID, or response fragment. A prose file an agent appends to is the surface `/commit`'s refusal table (`commit/SKILL.md:57-63`) is weakest against, because the content is not a recognizable credential file. The seeded entries must model the discipline: cite repo artifacts, never paste raw environment output.
  - PREMISE RISK, carried from the scope and not re-litigated here. The problem is inferred, not observed: `/implement-plan` has never run in this repo, `src/nba_platform/` holds only `__init__.py`, `transform/models/` holds three READMEs and zero `.sql`. If the first real stage-4 run fits comfortably in one context, this agent is maintenance burden. The plan's response is structural — keep every phase small, reversible, and independently committable, so the cost of being wrong is bounded by what has already landed.
testing:
  THE COMMANDS, AND WHAT EACH ACTUALLY PROVES.

  `uv run pytest -q` — the whole suite. `addopts = "-q --strict-markers --strict-config"` is already set at `pyproject.toml:79`, so `-q` is redundant but harmless. This is the required-check job `Lint, types, tests` (`ci.yml:26-27`, `ops/branch-protection.json:4`).

  `uv run pytest tests/test_agent_contract.py -q` — NEW. Frontmatter validity (AC1), guardrail-clause presence (AC2), the `CLAUDE.md` pointer (AC3's replacement), the memory budget and reference (AC4), the memory entry format, the deny set (blocker F1), and the `CLAUDE.md` 200-line budget (the cheap fold that converts `update-docs/SKILL.md:76-78` from a human-run one-liner into a CI failure).

  `uv run pytest tests/test_handoff_contract.py -q` — NEW. Section presence, non-emptiness, hunk-freeness, the line cap, and — from Phase 6 onward — the anti-vacuity assertion that at least one real handoff was found and linted.

  `uv run pytest tests/test_doc_links.py -q` — EXISTING, and the one mechanical check `/update-docs` owns (`update-docs/SKILL.md:53-57`). Every new Markdown file enters its scanned set automatically: `EXCLUDED_PARTS` (`:31-48`) has no `.claude` entry, and `MIN_EXPECTED_FILES = 20` (`:53`) sits against 33 tracked `.md` files today, rising by roughly six.

  `uv run ruff check` / `uv run ruff format --check` / `uv run mypy` — the other three steps of the required job. mypy is `strict = true` over `files = ["src", "tests"]` (`pyproject.toml:70-74`), so every new test function needs `-> None`, `tmp_path: Path` must be annotated, and `yaml.safe_load`'s `Any` must be narrowed with an `isinstance` assert exactly as `tests/test_repo_structure.py:23-27` already does. ruff selects `PTH` (`pyproject.toml:49-61`) — pathlib only, never `os.path`.

  `uv run dbt build --project-dir transform --profiles-dir transform --target ci` — EXISTING, the `dbt build` required check (`ci.yml:55-76`). This feature changes no models, so its role here is REGRESSION PROOF, run in Phase 7 (after the omission drill, to prove nothing leaked into `transform/`) and again in Phase 8. The `ci` target is in-memory DuckDB — no credentials, no cost.

  THE NEGATIVE-CONTROL DISCIPLINE, which is what makes any of this mean anything. Every new guard ships with a paired control proving it FAILS on mutated input. `tests/test_doc_links.py:95-104` exists precisely because a link checker that scans nothing passes every time, and the recorded scar at `implement-plan/SKILL.md:123-125` is a vacuous selftest passing green while work was destroyed. Concretely: an over-budget synthetic string must fail the budget predicate; a definition string with the `checkout` clause deleted must fail the guardrail predicate; a `CLAUDE.md` string without the pointer must fail the pointer predicate; a handoff string with a `^@@` line must fail the linter. Demonstrate each once by inverting the control and watching it redden, then restore it — a control asserted but never seen red is itself unproven.

  WHAT NO TEST COVERS, stated so the ledger stays honest. AC9's probe (a human reads the recorded evidence and judges it), AC11's PASS/FAIL scoring (grep-assisted, human-adjudicated), AC12's tree-integrity comparison (recorded evidence, not an assertion), AC14 (`/commit` behaves as assumed — explicitly USER-RUN), AC15 (CI green on the user's PR — USER-RUN), and the judgment half of Phase 5's `CLAUDE.md` cut. Mark each as RECORDED-EVIDENCE or USER-RUN per `requests/feature-requests/README.md:56-59` so the stage-4 acceptance panel does not claim them.

  REGRESSION SAFETY. Nothing in this change touches `src/`, `transform/models/`, `.github/workflows/`, or `ops/`. The three risks worth naming: (1) a new Markdown file with a dead relative link reddens `tests/test_doc_links.py` — put forward references and deliberately-broken example paths inside fences, which `:69` exempts; (2) the omission drill leaving a `.sql` under `transform/models/` would flip the sqlfluff conditional at `ci.yml:78-85` from skipped to running, reddening a later unrelated PR — Phase 7 asserts `git status --porcelain transform/` is empty; (3) Phase 5's `CLAUDE.md` cut is the one change with no mechanical safety net, which is why it is committed as its own reviewable diff.

===============================================================================
PLANNER: domain-convention
===============================================================================
architecture_notes:
  TRACK / SHAPE. Feature track, `requests/feature-requests/data-engineer-agent/`. This is a TOOLING change with NO data surface: `transform/models/` holds three layer READMEs and zero `.sql` files (verified via `git ls-files 'transform/*'`), `src/nba_platform/` holds only `__init__.py`, and the scope says so at PROJECT_SCOPE.md:42-44. The five dataset contracts (grain, keys, era coverage, update semantics, extraction cost) DO NOT BIND this change and must not be manufactured for it. My lens therefore pivots to PROJECT-CONVENTION correctness — with one genuine data-correctness exception, described below, which is the single most consequential thing in this build.

  WHAT GETS BUILT, STRUCTURALLY. Four new artifacts plus four edits. New: `.claude/agents/README.md` (directory contract + the main-thread spawn protocol), `.claude/agents/<agent>.md` (the definition — role framing, override preamble, relocated rulebook, write allowlist + deny set, escalation policy, routing rule, return contract), `.claude/agents/<agent>-memory.md` (committed, capped at 120 lines per Decision 5, seeded with 2-4 entries the repo has already earned), and a pytest guard suite under `tests/`. Edits: `CLAUDE.md` (map row, subagent-bullet clarification, and the Decision-12 relocation), `docs/decisions/0007-*.md` + its Index row, the bucket lists in `update-docs/SKILL.md:47-48` and `implement-plan/SKILL.md:129-131` (Decision 7 doc half only — `acceptance_panel.js` is NOT touched), and the track README Index row.

  THE ONE PLACE DATA CORRECTNESS IS AT STAKE. Decision 12 moves `CLAUDE.md`'s Data Layer block (:84-103) and four implementation gotchas (:105-126: 0.6s pacing, prefer bulk endpoints, date-dependent player affiliation, Windows/LF) OUT of the file every agent reads on every task and INTO a file only the developer agent is guaranteed to read. `CLAUDE.md:113-116` — *"Resolving as-of today instead of as-of the game is the most likely source of silently wrong joins in this project"* — is the highest-value warning in the repo, and after the cut the main thread only reaches it by following a pointer. This build therefore must treat the relocation as a load-bearing data-correctness edit, not a doc tidy: every relocated clause gets a phrase-presence assertion in the guard suite (Decision 6: phrase-presence, not verbatim), `CLAUDE.md` keeps a pointer line that NAMES what moved rather than gesturing at it, and the plan records that the independent safety net survives — `acceptance_panel.js:197` (`data-contract`) and `:203` still enforce grain/merge/era/affiliation at stage 4 regardless of where the prose lives.

  WHY THE GUARDS GO WHERE THEY GO. `.github/workflows/ci.yml` has exactly three jobs (:26-27, :55-56, :87-88) and no Node step, so the five existing `.claude/skills/**/tests/*.mjs` guards are etiquette. `tests/` is enforcement, because `ops/branch-protection.json:4` makes `Lint, types, tests` a required context. Guard code inherits real gates: `mypy strict` covers `files = ["src", "tests"]` (pyproject.toml:70-74), so every test needs `-> None` and typed helpers; ruff selects `PTH` (pathlib only), `DTZ` (no naive datetimes — parse memory dates with `datetime.date.fromisoformat`, never `strptime`), `A` (don't shadow builtins), `N`, `B` (pyproject.toml:48-61). `yaml` is already a dev dependency (pyproject.toml:20-22) and already imported by `tests/test_repo_structure.py:17`, so frontmatter parsing adds nothing.

  THE RESOLVE-BY-NAME RULE, APPLIED HONESTLY. `CLAUDE.md:86-88` forbids literal paths and `parents[N]` walks — but that rule is aimed at the Python config layer, which does not exist yet, and both existing test modules deliberately use `REPO_ROOT = Path(__file__).resolve().parents[1]` (`tests/test_repo_structure.py:19`, `tests/test_doc_links.py:27`). The new guards follow that established idiom and the plan must say so explicitly, otherwise a cold implementer either invents a config layer or gets flagged by a reviewer for copying the repo's own precedent. Inside the repo root, resolve BY NAME: discover the definition by globbing `.claude/agents/*.md`, never by hardcoding a filename, so renaming the agent doesn't silently turn the guard vacuous.

  DISCOVERY RULE FOR "EXACTLY ONE DEFINITION" (AC1). `.claude/agents/*.md` will match three files — README, definition, memory. The crisp mechanical rule: a DEFINITION is a `.claude/agents/*.md` whose first line is `---` (YAML frontmatter). Assert exactly one such file; assert `README.md` and the memory file do NOT open with `---`. This makes AC1 checkable without hardcoding names and matches how a harness would plausibly discover agents — but it is contingent on the Phase 0 probe, which may report a different required layout.

  WHAT THE GUARDS CAN AND CANNOT DO. Every mechanical guard here checks FORM (a clause is present, a file is under budget, a section exists). None checks BEHAVIOR. The behavioral evidence is the two proving runs, and the write-guard package is DETECTION, not prevention — exactly as the scope states at PROJECT_SCOPE.md:279. The plan must state this in the same breath as the guard list so a cold implementer does not mistake a green suite for a safe agent.
code_references:
  - [1]
    claim:
      The Data Layer section Decision 12 relocates into the agent definition: resolve-by-name (:86-88), immutable landing zone (:89-92), bronze 1:1 (:93-94), silver declares AND proves its grain (:95-97), facts MERGE on key (:98-99), layer promotion gated on tests (:100), no bulk data in git (:101-103).
    ref: CLAUDE.md:84-103
  - [2]
    claim:
      The as-of-game-date player-affiliation warning — 'the most likely source of silently wrong joins in this project'. This is the single highest-consequence clause in the relocation and must carry its own phrase-presence assertion.
    ref: CLAUDE.md:113-116
  - [3]
    claim: 'Subagents get read-only git' — the bullet the scope clarifies so a write-capable builder is legible as inside the rules, not an exception to them.
    ref: CLAUDE.md:73-75
  - [4]
    claim: Agents commit only through `/commit`; never merge, push, or amend. Every phase in this plan ends at `/commit`, and the push/PR stay the user's.
    ref: CLAUDE.md:65-69
  - [5]
    claim:
      'Anything that spends cloud money or touches prod is a user-run action, not an agent one' — stays in CLAUDE.md after the cut and is restated in the definition, since the agent will later write extraction code.
    ref: CLAUDE.md:117-119
  - [6]
    claim:
      `REPO_ROOT = Path(__file__).resolve().parents[1]` — the established test idiom the new guards copy, and the reason a `parents[N]` walk in `tests/` is precedent rather than a resolve-by-name violation.
    ref: tests/test_repo_structure.py:19
  - [7]
    claim: `import yaml` already present; pyyaml + types-PyYAML are dev dependencies (pyproject.toml:20-22), so frontmatter parsing needs no new dependency.
    ref: tests/test_repo_structure.py:17
  - [8]
    claim: `test_every_layer_documents_itself` — the closest structural analogue for asserting `.claude/agents/` carries a README.
    ref: tests/test_repo_structure.py:77-84
  - [9]
    claim:
      `EXCLUDED_PARTS` contains no `.claude` entry, so all three new Markdown files are link-checked automatically; it does contain `var` (:38), so a `var/` scratch dbt project is invisible to the checker.
    ref: tests/test_doc_links.py:31-48
  - [10]
    claim: `MIN_EXPECTED_FILES = 20` against 33 tracked `.md` files today (measured via `git ls-files '*.md'`), rising to 36 — the anti-vacuity floor stays satisfied.
    ref: tests/test_doc_links.py:53
  - [11]
    claim: `MARKDOWN_LINK` matches only `[text](path)`, which is why memory paths and forward references use inline code — a backticked path cannot rot a link check.
    ref: tests/test_doc_links.py:56
  - [12]
    claim:
      `test_the_guard_actually_covers_the_repo` — the anti-vacuity control every new guard imitates, and the direct precedent for requiring a negative control per guard.
    ref: tests/test_doc_links.py:95-104
  - [13]
    claim: `mypy strict = true` over `files = ["src", "tests"]` — new guard code must be fully annotated, including `-> None` on every test function.
    ref: pyproject.toml:70-74
  - [14]
    claim: ruff selects E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF — pathlib only, no naive datetimes (use `datetime.date.fromisoformat`, not `strptime`), no builtin shadowing.
    ref: pyproject.toml:48-61
  - [15]
    claim: Exactly three jobs — `Lint, types, tests`, `dbt build`, `Secret scan` — and no Node step, which is why guards go under `tests/` rather than as `.mjs` siblings.
    ref: .github/workflows/ci.yml:26-27, :55-56, :87-88
  - [16]
    claim: CI's dbt build runs `--project-dir transform --profiles-dir transform --target ci`, so a scratch dbt project under `var/` can never reach CI.
    ref: .github/workflows/ci.yml:76
  - [17]
    claim: The sqlfluff step self-skips on an empty model selection — stays true because this change adds no `.sql` file. Also a verified memory-seed candidate.
    ref: .github/workflows/ci.yml:78-85
  - [18]
    claim: Gitleaks with `fetch-depth: 0` (:93-94) scans full history and now covers the committed memory file (ADR 0006's public-repo posture).
    ref: .github/workflows/ci.yml:96-99
  - [19]
    claim: `contexts: ["Lint, types, tests", "dbt build", "Secret scan"]` — matched by job DISPLAY NAME, which is what makes a guard under `tests/` a required check.
    ref: ops/branch-protection.json:4
  - [20]
    claim:
      The pre-spawn snapshot protocol and the recorded scar (a write-capable review agent ran `git checkout` and wiped uncommitted work while a vacuous selftest passed green). The spawn protocol reuses this verbatim.
    ref: .claude/skills/implement-plan/SKILL.md:120-125
  - [21]
    claim: The post-run tree-integrity re-check — the second half of the write-guard package, and the source of AC12's comparison.
    ref: .claude/skills/implement-plan/SKILL.md:187-190
  - [22]
    claim: The stage-4 invariant restatement the definition must mirror without contradicting; :111-112 is the PowerShell UTF-8 trap, a verified memory-seed candidate.
    ref: .claude/skills/implement-plan/SKILL.md:100-112
  - [23]
    claim: The touched-area bucket list with no `agents` key — the Decision-7 doc-half edit.
    ref: .claude/skills/implement-plan/SKILL.md:129-131
  - [24]
    claim: Track auto-detection from the artifact path — the grounded reason the handoff contract carries a `track` field and the linter globs both tracks.
    ref: .claude/skills/implement-plan/SKILL.md:49-53
  - [25]
    claim:
      `READONLY` — the absolute read-only mandate, scoped to the acceptance panel's reviewers. A write-capable builder does not contradict it; the scope's fit argument rests on this distinction.
    ref: .claude/skills/implement-plan/acceptance_panel.js:163
  - [26]
    claim:
      The `data-contract` specialist mandate: grain declared in schema.yml AND proven by a uniqueness test, merge-on-key, the 2013-14 era boundary. This survives the relocation and is the independent net for the moved rules.
    ref: .claude/skills/implement-plan/acceptance_panel.js:197
  - [27]
    claim:
      The `skill-quality` mandate — every clause applies verbatim to an agent definition, so passing `skills` in `touchedAreas` gets the right lens without a code change.
    ref: .claude/skills/implement-plan/acceptance_panel.js:199
  - [28]
    claim: `AREA_TO_SPEC` — verified to have no `agents` key (:204 maps `skills` → `skill-quality`). Deferred by Decision 7; do not edit.
    ref: .claude/skills/implement-plan/acceptance_panel.js:202-206
  - [29]
    claim:
      `agent(prompt, {label, phase, schema, effort})` — the panel spawn path has no agent-type parameter, which is the grounded reason the harness probe is core and blocking.
    ref: .claude/skills/scope-feature/scope_panel.js:174
  - [30]
    claim: The compressed, pointer-shaped invariant restatement whose SHAPE the definition's rulebook sections follow.
    ref: .claude/skills/scope-feature/scope_panel.js:118-130
  - [31]
    claim:
      The 200-line budget check `(Get-Content CLAUDE.md | Measure-Object -Line).Lines`. MEASURED: it returns 122 while the file is 141 physical lines, because `Measure-Object -Line` drops blank lines — the guard must pin one semantic or the two checks disagree.
    ref: .claude/skills/update-docs/SKILL.md:76-78
  - [32]
    claim:
      The `docs/data-sources.md` epistemic-label audit the memory routing rule must not route around; :105 names four labels where CLAUDE.md:76-79 names five and docs/data-sources.md:5-7 names three.
    ref: .claude/skills/update-docs/SKILL.md:103-112
  - [33]
    claim: The requests/ Index-vs-Status-blockquote reconciliation that AC16 makes greppable.
    ref: .claude/skills/update-docs/SKILL.md:131-136
  - [34]
    claim: Per-path staging and the refusal table — the review gate AC14 exercises, and the reason the memory file must be committed rather than gitignored.
    ref: .claude/skills/commit/SKILL.md:47-67
  - [35]
    claim: The branch check: `main` is protected, so every phase's `/commit` runs on a feature branch.
    ref: .claude/skills/commit/SKILL.md:42-45
  - [36]
    claim:
      'Getting them wrong is the most expensive mistake available in this project' — the grounded reason the omission drill targets `var/` scratch and never `transform/models/`.
    ref: transform/models/silver/README.md:5-7
  - [37]
    claim: The declare-then-prove pattern (`dbt_utils.unique_combination_of_columns` on `[game_id, player_id]`) whose ABSENCE the omission drill detects.
    ref: transform/models/silver/README.md:9-25
  - [38]
    claim:
      Declares `dbt-labs/dbt_utils >=1.1.0,<2.0.0` because `unique_combination_of_columns` is how every silver model proves its grain — and the reason the offline `var/` drill must fall back to a core `unique` test rather than run `dbt deps`.
    ref: transform/packages.yml
  - [39]
    claim:
      `var/` is the gitignored scratch root, so pre-spawn patches and the drill project never enter git — and why AC10-AC12 evidence must be copied into committed `reviews/` (blocker fix F2).
    ref: .gitignore:16
  - [40]
    claim: The five required ADR sections, and the immutability rule that forces ADR 0007 to be written after the proving runs (Decision 10).
    ref: docs/decisions/README.md:19-25 and :29-32
  - [41]
    claim:
      The three-label epistemic vocabulary (`verified` / `documented` / `unconfirmed`) and the standing 'unconfirmed throughout' status — the third point of the vocabulary drift the memory entry format must choose among.
    ref: docs/data-sources.md:5-8
  - [42]
    claim: The user-run marking rule that AC14 and AC15 invoke so the acceptance panel does not claim them.
    ref: requests/feature-requests/README.md:56-59
  - [43]
    claim: The `data-engineer-agent` Index row at stage `scoped`, which this plan advances to `plan`.
    ref: requests/feature-requests/README.md:92
files_to_touch:
  - [1]
    change:
      NEW. Directory contract + the main-thread spawn protocol (clean-tree precondition, pre-spawn snapshot to gitignored `var/`, post-run tree-integrity comparison), reusing implement-plan/SKILL.md:120-125 and :187-190 verbatim rather than inventing a second mechanism. Mirrors the self-documenting-directory precedent at tests/test_repo_structure.py:77-84.
    path: D:/projects/nba-analysis/.claude/agents/README.md
  - [2]
    change:
      NEW — exact filename set by the Phase 0 probe. The definition: frontmatter per the probe; override preamble; the relocated build rulebook in two self-contained sections (EXTRACTION / DBT MODELING); pointers to transform/models/bronze/README.md and transform/models/silver/README.md; the memory pointer as inline code; the return contract with a `track` field; the three-way spec-gap escalation policy; the write allowlist and the repo-level deny set; git-read-only as an absolute naming checkout/reset/restore/clean/stash; never commit/merge/push/amend; billable-work-is-user-run; the docs/data-sources.md routing rule; spec-triage dry-run mode; and prohibitions on invoking pipeline skills or editing its own definition.
    path: D:/projects/nba-analysis/.claude/agents/<agent>.md
  - [3]
    change:
      NEW. Committed, capped at 120 physical lines (Decision 5) with the cap stated in the header. Header declares what belongs, what routes elsewhere, the per-entry format (date / epistemic label / claim / evidence pointer / routing tag), and the inline-code-paths convention with its reason. Seeded with 2-4 entries the repo has already earned, each citing a real artifact — no invented gotchas.
    path: D:/projects/nba-analysis/.claude/agents/<agent>-memory.md
  - [4]
    change:
      NEW. Definition discovery by glob (a definition = a `.claude/agents/*.md` opening with `---`; assert exactly one), frontmatter validity via `yaml.safe_load`, guardrail-clause presence (nine git/commit verbs), relocated-rulebook clause presence (phrase-presence per Decision 6, including the as-of-game-date affiliation rule and the 0.6s pacing default), CLAUDE.md pointer presence, write-allowlist/deny-set declaration, and the routing rule naming docs/data-sources.md. Each with a negative control built in `tmp_path`. Follows tests/test_repo_structure.py's idiom; every test annotated `-> None` for mypy strict.
    path: D:/projects/nba-analysis/tests/test_agent_definition.py
  - [5]
    change:
      NEW. Physical-line budget assertions for CLAUDE.md (< 200) and the memory file (<= 120), cap named in the assertion message, counting semantic pinned in the docstring. Negative control proves an over-budget file fails. Converts update-docs/SKILL.md:76-78's human one-liner into a CI failure.
    path: D:/projects/nba-analysis/tests/test_doc_budgets.py
  - [6]
    change:
      NEW. Handoff schema lint over `requests/*-requests/*/reviews/proving-run-*.md` (track-agnostic by glob): all seven sections present and non-empty, no `^@@` / `^+++` / `^---` outside fenced blocks, line count under the declared cap. Inline-fixture assertion until Phase 4 lands a real artifact, so it cannot pass vacuously.
    path: D:/projects/nba-analysis/tests/test_agent_handoff.py
  - [7]
    change:
      EDIT. Add a `.claude/agents/` row to the project-map block (near :27). Clarify the subagent bullet (:73-75) so read-only GIT and file-write permission are distinguishable. Decision 12 cut: move the Data Layer section (:84-103) and the pacing/bulk-endpoint/affiliation/Windows-LF gotchas (:107-116, :126) into the definition, leaving a pointer that NAMES what moved. Keep the cost guardrail (:117-119), the pre-commit naming note (:120-121) and the CI-rename trap (:122-125). Currently 141 physical lines (122 by Measure-Object).
    path: D:/projects/nba-analysis/CLAUDE.md
  - [8]
    change:
      NEW. ADR in the five required sections (docs/decisions/README.md:19-25), status `accepted`, written AFTER the proving runs (Decision 10, because :29-32 makes accepted ADRs immutable). Consequences must state plainly that the guard is detection not prevention, that the premise is inferred not measured, and how many drill observations back the claim.
    path: D:/projects/nba-analysis/docs/decisions/0007-<slug>.md
  - [9]
    change: EDIT. Add the 0007 row to the Index table at :39-46 with a resolving link.
    path: D:/projects/nba-analysis/docs/decisions/README.md
  - [10]
    change:
      EDIT (Decision 7 doc half). Add `agents` to the bucket list at :47-48; point the CLAUDE.md 'rules' check (:71-75) at the relocated rulebook as well; and fix or annotate the line-count one-liner at :76-78 so the human check and the CI guard use the same counting semantic.
    path: D:/projects/nba-analysis/.claude/skills/update-docs/SKILL.md
  - [11]
    change:
      EDIT (Decision 7 doc half). Add `agents` to the touched-area bucket list at :129-131. Do NOT touch Step 3, the snapshot protocol, or the acceptance panel — the scope fences stage-4 rewiring.
    path: D:/projects/nba-analysis/.claude/skills/implement-plan/SKILL.md
  - [12]
    change:
      DO NOT TOUCH. `AREA_TO_SPEC` (:202-206) gaining an `agents` key is explicitly deferred by Decision 7, and the file is covered by two `.mjs` guards CI does not run. Listed here so the implementer knows the omission is deliberate; verify with `git diff HEAD --stat`.
    path: D:/projects/nba-analysis/.claude/skills/implement-plan/acceptance_panel.js
  - [13]
    change: NEW (Phase 0). Both probe halves answered with `verified`/`measured` labels, the exact probe command, its real output, and a PROCEED/STOP verdict (AC9).
    path: D:/projects/nba-analysis/requests/feature-requests/data-engineer-agent/reviews/harness-probe.md
  - [14]
    change:
      NEW (Phase 4). The faithful-run handoff, all seven sections non-empty, every `verified` row citing a command and its actual output, hunk-free, under the cap, with the pre/post tree-state comparison included or in a sibling artifact (AC10, AC12).
    path: D:/projects/nba-analysis/requests/feature-requests/data-engineer-agent/reviews/proving-run-a.md
  - [15]
    change:
      NEW (Phase 5). The omission drill: the spec text with the grain requirement removed, the produced artifacts quoted verbatim, the grep command and output, an explicit PASS/FAIL, and the pre/post tree comparison (AC11, AC12).
    path: D:/projects/nba-analysis/requests/feature-requests/data-engineer-agent/reviews/proving-run-b.md
  - [16]
    change:
      NEW — this stage's deliverable. Opens at `plan · created <today> · decided · next: implement`. Write forward references to `.claude/agents/...` as INLINE CODE, never `[text](path)` — tests/test_doc_links.py:56/:72 scans only Markdown-link syntax, so a link to a not-yet-created file turns CI red.
    path: D:/projects/nba-analysis/requests/feature-requests/data-engineer-agent/IMPLEMENTATION_PLAN.md
  - [17]
    change:
      EDIT. Advance the `data-engineer-agent` Index row Stage cell at :92 — `scoped` → `plan` now, `implemented` after stage 4. Match the row by its `[data-engineer-agent]` link.
    path: D:/projects/nba-analysis/requests/feature-requests/README.md
  - [18]
    change: EDIT (AC16). Advance the Status blockquote so it agrees with the Index row and the plan's own header.
    path: D:/projects/nba-analysis/requests/feature-requests/data-engineer-agent/FEATURE_REQUEST.md
ok:
  True
onboarding_files:
  - [1]
    path: D:/projects/nba-analysis/requests/feature-requests/data-engineer-agent/PROJECT_SCOPE.md
    why:
      The decided upstream artifact. 16 acceptance criteria (lines 127-157), the tiered scope (159-211), 13 decisions + 2 post-panel amendments (367-490), and the F1-F3/A2 blocker fixes (492-509). Decision 12 (line 434) and Decision 13 (456) post-date the adversarial panel and are the riskiest parts of the build.
  - [2]
    path: D:/projects/nba-analysis/requests/feature-requests/data-engineer-agent/FEATURE_REQUEST.md
    why:
      Context only. The four observable signals at :39-47 (signal four — 'silver declares its grain and proves it holds even when the spec forgets' — is what the omission drill measures) and the nine open questions at :148-199.
  - [3]
    path: D:/projects/nba-analysis/CLAUDE.md
    why:
      The file this change edits most dangerously. Project map 16-33 (gains a `.claude/agents/` row), Project Conventions 63-82 (the subagent bullet at 73-75 needs the write/git clarification), Data Layer 84-103 and Constraints & Gotchas 105-126 (the sections Decision 12 relocates). 141 physical lines; `Measure-Object -Line` reports 122 — see the risks.
  - [4]
    path: D:/projects/nba-analysis/.claude/skills/implement-plan/SKILL.md
    why:
      Closest prior art and the source of the central tension. :100-112 the invariant restatement, :120-125 the snapshot protocol and the recorded scar (a write-capable agent ran `git checkout` and wiped uncommitted work), :127-131 the bucket list with no `agents` key, :155-156 the read-only-subagents rule, :187-190 the post-run tree-integrity re-check the guard package reuses verbatim.
  - [5]
    path: D:/projects/nba-analysis/tests/test_repo_structure.py
    why:
      The idiom every new guard copies: module docstring :1-9 justifies config-and-filesystem-agree checks; `REPO_ROOT = Path(__file__).resolve().parents[1]` at :19; `yaml` already imported at :17 (so frontmatter parsing needs no new dependency); `test_every_layer_documents_itself` :77-84 is the structural analogue for `.claude/agents/README.md`.
  - [6]
    path: D:/projects/nba-analysis/tests/test_doc_links.py
    why:
      `EXCLUDED_PARTS` :31-48 has no `.claude` entry (both new Markdown files are link-checked for free) and does contain `var` :38; `MIN_EXPECTED_FILES = 20` :53 against 33 tracked `.md` today; only `[text](path)` is scanned :56/:72 — a backticked path is invisible, which is why memory and forward references use inline code; :95-104 is the anti-vacuity control every new guard imitates.
  - [7]
    path: D:/projects/nba-analysis/.claude/skills/update-docs/SKILL.md
    why:
      The doc gate this change perturbs. :47-48 bucket list names `.claude/skills/` only; :53-57 the one mechanical check it owns; :76-78 the 200-line budget one-liner the memory cap reuses (and whose counting semantics disagree with a naive Python line count); :103-112 the `docs/data-sources.md` epistemic-label audit the routing rule must not route around.
  - [8]
    path: D:/projects/nba-analysis/.claude/skills/implement-plan/acceptance_panel.js
    why:
      `READONLY` at :163 (the absolute mandate a write-capable allowlist inverts, scoped to reviewers), `SPEC_DEFS` :196-201 with the `data-contract` :197, `extraction` :198 and `skill-quality` :199 mandates, and `AREA_TO_SPEC` :202-206 — verified to have no `agents` key, so the first future edit to the definition draws no specialist lens.
  - [9]
    path: D:/projects/nba-analysis/pyproject.toml
    why:
      The gates new test code must pass: ruff line-length 100 selecting E,W,F,I,N,UP,B,A,C4,DTZ,PTH,RUF at :43-64; `mypy strict = true` over `files = ["src", "tests"]` at :70-74; pytest `testpaths`/`addopts`/`network` marker at :77-82; pyyaml + types-PyYAML already in the dev group at :20-22.
  - [10]
    path: D:/projects/nba-analysis/.github/workflows/ci.yml
    why:
      Exactly three jobs and no Node step — `Lint, types, tests` :26-27, `dbt build` :55-56, `Secret scan` :87-88 with gitleaks :96-99. This is the grounded reason guards go under `tests/` (enforced via ops/branch-protection.json:4) rather than as `.mjs` siblings, which run only when an agent remembers.
  - [11]
    path: D:/projects/nba-analysis/transform/models/silver/README.md
    why:
      The grain contract the omission drill is built around: :5-7 ('the most expensive mistake available in this project') is why the drill must not target `transform/models/`; :9-25 is the declare-then-prove pattern whose absence the drill detects; :31-33 the as-of-game-date affiliation rule.
  - [12]
    path: D:/projects/nba-analysis/.claude/skills/commit/SKILL.md
    why:
      The only sanctioned committer and the review gate the whole design leans on: branch check :42-45, per-path staging and the refusal table :47-67, proportional doc-drift step :78-90. Also the house voice the agent definition must match.
  - [13]
    path: D:/projects/nba-analysis/requests/feature-requests/README.md
    why:
      The pipeline contract: what 'testable' means and the user-run marking rule :45-59, layout and status grammar :61-85, and the Index row for `data-engineer-agent` at :92 that must advance to `plan` then `implemented`.
  - [14]
    path: D:/projects/nba-analysis/docs/decisions/README.md
    why:
      ADR 0007's required sections :19-25, the accepted-ADRs-are-immutable rule :29-32 (which is why Decision 10 writes it after the proving runs), and the Index table :39-46 that gains a row.
open_questions:
  - FAITHFUL-RUN TARGET (needs a user decision before Phase 4). Decision 2 wants 'a small real repo task', but the F1 deny set (`tests/`, `.github/`, `ops/`, `.claude/`), the no-pipeline-code non-goal (`transform/models/`, `src/nba_platform/`), and the routing rule (`docs/data-sources.md`) leave very little writable. Recommendation: a `docs/` prose task plus the handoff under `reviews/`, with `requests/<track>-requests/<slug>/reviews/` added to the standing allowlist so the agent can write its own return contract at all. Do NOT widen the deny set to make the drill convenient.
  - LINE-COUNT SEMANTIC. `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` = 122; `(Get-Content CLAUDE.md).Count` = 141. Pin one for both the CI guard and `update-docs/SKILL.md:76-78`. Recommendation: physical lines everywhere, and correct the skill's one-liner in the same commit — otherwise the 120-line memory cap means two different things depending on who checks it.
  - EPISTEMIC VOCABULARY FOR MEMORY ENTRIES. Five labels (CLAUDE.md:76-79), four (update-docs/SKILL.md:105), or three (docs/data-sources.md:5-7)? Recommendation: CLAUDE.md's five, because memory is repo scar tissue rather than a data-source catalog — and record the drift as a memory seed rather than fixing `docs/data-sources.md`, which is out of scope.
  - DEFINITION DISCOVERY RULE. AC1 says 'exactly one `*.md` agent definition', but `.claude/agents/*.md` will match README, definition, and memory. Recommendation: a definition is a file whose first line is `---`; assert exactly one and assert the other two do not open with `---`. Contingent on Phase 0 — if the harness mandates a different layout (one file per directory, no sibling README), AC1's wording needs restating against the probe's finding, per blocker fix F3.
  - DRILL PASS RULE, PRECISELY. Is a core dbt `unique` test on a surrogate key accepted as 'proves its grain', or must it be `dbt_utils.unique_combination_of_columns` to count? The offline constraint argues for accepting the core test. Fix the grep patterns in the plan so the score is not a judgment call after the fact.
  - DRILL REPETITIONS (Decision 8). Two runs per drill if affordable; one is acceptable ONLY if `reviews/` and ADR 0007 both label the result a single observation rather than a proof. Decide before Phase 4, because ADR 0007's Consequences section is immutable once accepted (docs/decisions/README.md:29-32).
  - STAGE-4 REVIEWER ROSTER FOR THIS VERY CHANGE. With no `agents` key in `AREA_TO_SPEC` (acceptance_panel.js:202-206), the acceptance panel needs `touchedAreas` set deliberately — recommend `["skills","tests","docs","config"]` so `skill-quality` (:199) and `infra-cost` (:200) are on the roster. Confirm at launch; it is a runtime argument, not a code change, so it does not breach Decision 7's deferral.
  - POST-PANEL AMENDMENTS WERE NEVER ADVERSARIALLY REVIEWED (PROJECT_SCOPE.md:324-327). Decisions 12 and 13 changed the scope after the panel returned; the relocation removes a guard the adversaries had endorsed. Stage 3's code-grounded adversaries are the first place either can be attacked — this plan's Phase 3 is where that attack should land.
phases:
  - [1]
    acceptance:
      - `reviews/harness-probe.md` exists; `grep -i unconfirmed` over it returns nothing in an answer position, and both halves (a) and (b) carry a `verified` or `measured` label with the probe command and its real output quoted.
      - `uv run pytest tests/test_doc_links.py -q` is green (the new Markdown file is scanned automatically — `EXCLUDED_PARTS` at tests/test_doc_links.py:31-48 has no `.claude` entry).
      - A one-line PROCEED/STOP verdict is written at the top of the probe artifact, with the frontmatter schema AC1 will assert named explicitly.
    commit_note:
      docs(data-engineer-agent): record harness probe for .claude/agents loading + CLAUDE.md inheritance — run `/commit`, never `git commit` ad hoc. Docs-only; expect `/commit` to run the proportional doc check, not the full sweep.
    goal:
      Settle, before a line of the definition is written, what actually loads a `.claude/agents/*.md` on this harness, what frontmatter it accepts, where a machine-readable tool/write allowlist can be declared, and whether such a subagent inherits project `CLAUDE.md` and sees project skills. A negative finding STOPS the build (blocker fix A2-02, PROJECT_SCOPE.md:509).
    name: Phase 0 — Harness probe and baseline capture (blocking gate, no product code)
    steps:
      - Confirm the working tree is clean and you are on a feature branch, not `main` (`git status --porcelain`, `git branch --show-current`). Per CLAUDE.md:65-69 and commit/SKILL.md:42-45 the branch is the implementer's; `main` is protected.
      - Capture the baseline so later assertions are measured, not assumed: `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` all green; record `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` (122) AND `(Get-Content CLAUDE.md).Count` (141) — they disagree, see Risks; record `git ls-files '*.md' | Measure-Object -Line` (33) against `MIN_EXPECTED_FILES = 20` at tests/test_doc_links.py:53.
      - Probe half (a): what loads `.claude/agents/*.md`. Grounded starting facts to disprove or confirm — `scope_panel.js:174` spawns via `agent(prompt, {label, phase, schema, effort})` with no agent-type parameter, and there is no `.claude/settings.json` in the repo (`Get-ChildItem .claude -Force` returns only `skills`). Consult the harness's own documentation/tooling, then TEST it: write a throwaway definition under gitignored `var/` scratch if the harness supports a path override, or land a minimal definition, attempt one spawn, and observe. Record the exact probe command and its actual output.
      - Probe half (b): inheritance and skill visibility. Spawn the probe agent and have it report whether it received project `CLAUDE.md` unrequested and whether project skills are listed. Record verbatim. Note the already-MEASURED datum for a DIFFERENT spawn path: a `scope_panel.js`-spawned subagent receives the full project `CLAUDE.md` as an unrequested system-reminder (PROJECT_SCOPE.md:143), which does not settle (b).
      - Write `requests/feature-requests/data-engineer-agent/reviews/harness-probe.md`. Every answer carries an epistemic label of `verified` or `measured` — never `unconfirmed` (AC9). State the probe used, the raw output, and the design consequence for each answer.
      - Apply the decision rule. If nothing loads `.claude/agents/*.md`, or no machine-readable allowlist location exists, STOP: record the finding, do not write the definition, and return the request to `/scope-feature`. Do not proceed on a hopeful reading — the dead-artifact failure mode passes every shape-based criterion green (PROJECT_SCOPE.md:277).
      - Reconcile AC1's frontmatter assertion with what the probe actually found (blocker fix F3, PROJECT_SCOPE.md:505). If the harness demands a schema other than `name` + `description`, the guard asserts THAT schema.
  - [2]
    acceptance:
      - `uv run pytest -q` green; `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` green (no Python changed yet, so this is a no-regression check).
      - `uv run pytest tests/test_doc_links.py -q` green with all three new files in the scanned set — verify by asserting the scanned count rose (33 tracked `.md` → 36) and that no relative link in the new files is dead.
      - `grep` over the definition finds all five git verbs (`checkout`, `reset`, `restore`, `clean`, `stash`) and all four commit verbs (`commit`, `merge`, `push`, `amend`); finds the literal string `docs/data-sources.md` in the routing rule; and finds the memory file's path.
      - `grep -c` over the memory file for a data/era/endpoint/rate-limit claim returns zero (AC13's PR-time check, run now as a self-check).
      - The memory file is at or under 120 physical lines; the seeded entries each carry a citation that resolves.
    commit_note:
      feat(agents): add .claude/agents/ with the data-engineer definition, spawn-protocol README, and a seeded memory file. Land via `/commit` — it stages per-path and will surface the memory file as its own entry, which is the review gate this design leans on (commit/SKILL.md:47-67).
    goal:
      Land the three Markdown artifacts in the frontmatter schema the probe confirmed, with the write allowlist + deny set, the escalation policy, the routing rule and the return contract stated — but leave `CLAUDE.md` untouched, so the relocation lands as its own reviewable diff.
    name: Phase 1 — Stand up `.claude/agents/`: README, definition, memory (no CLAUDE.md relocation yet)
    steps:
      - Write `.claude/agents/README.md`: what the directory is, the one-agent-today rule, and the MAIN-THREAD SPAWN PROTOCOL reusing stage 4's procedure verbatim rather than inventing a second mechanism — feature branch; required-clean-tree (or only-the-agent's-own-prior-work) precondition; pre-spawn `git status --porcelain` + `git diff HEAD --stat` + `git diff HEAD > var/tmp/<slug>-pre-spawn.patch` plus the untracked list (implement-plan/SKILL.md:120-125); post-run tree-integrity comparison (implement-plan/SKILL.md:187-190). `var/` is gitignored at .gitignore:16, so the patch never enters git.
      - Write `.claude/agents/<agent>.md`. Frontmatter per the probe. Body sections, in order: (1) role framing — main thread is manager, this agent is developer; (2) an explicit OVERRIDE PREAMBLE naming which inherited `CLAUDE.md` sections the agent ignores and which it obeys absolutely (needed if the probe confirmed inheritance, since narrowness cannot then be achieved by omission); (3) the build rulebook, structured as TWO self-contained sections — EXTRACTION and DBT MODELING — so a later split is a copy rather than a rewrite (mirrors the two specialists at acceptance_panel.js:198 and :197); (4) pointers to `transform/models/bronze/README.md` and `transform/models/silver/README.md` rather than paraphrase; (5) the memory pointer, as INLINE CODE not a Markdown link; (6) the return contract; (7) the three-way spec-gap escalation policy; (8) the write allowlist and the repo-level deny set; (9) git-read-only stated absolutely with its recorded reason; (10) prohibitions on invoking `/scope-feature`, `/create-implementation-plan`, `/implement-plan`, and on editing its own definition.
      - State the WRITE ALLOWLIST as a bound, not a restatement of 'the spec decides' (blocker fix F1, PROJECT_SCOPE.md:496-500). Standing allowlist: the memory file, and `requests/<track>-requests/<slug>/reviews/` so the agent can write its own handoff. Task-scoped allowlist: the plan's declared target paths. DENY set, absolute: `.claude/**` (memory file the single carve-out), `tests/**`, `.github/**`, `ops/**`, and `docs/data-sources.md`. The deny set is what stops the agent editing the guards that catch it and reporting green.
      - State git read-only ABSOLUTELY, naming the five verbs literally so a substring guard can find them: never `checkout`, `reset`, `restore`, `clean`, `stash`, nor anything that discards working-tree state; and never `commit`, `merge`, `push`, `amend`. Cite the scar (implement-plan/SKILL.md:123-125) and CLAUDE.md:73-75. Add the billable-work rule: anything that spends cloud money, hits `stats.nba.com` live, or touches prod is USER-RUN — stage it as a script and hand it up (implement-plan/SKILL.md:109-110).
      - State the THREE-WAY ESCALATION POLICY: a spec that CONTRADICTS an invariant → stop with a spec-gap report; a spec SILENT on an invariant → build to the invariant and flag it; an AMBIGUOUS requirement → build the smaller interpretation and flag it. All three must be observable in the handoff.
      - State the MEMORY-VERSUS-DOCS ROUTING RULE in one line, naming `docs/data-sources.md` literally: any data, era, endpoint, availability or rate-limit fact goes in the handoff's `docs-delta` section for the main thread to route through `/update-docs` — never into memory, and never by the agent editing `docs/data-sources.md` itself (AC13).
      - State the RETURN CONTRACT: fixed sections — built / verified-with-evidence / assumed / surprised-me (memory candidates) / could-not-do / docs-delta / still-open — plus a `track` field (feature|bugfix, mirroring implement-plan/SKILL.md:49-53), written to `requests/<track>-requests/<slug>/reviews/`, under a declared line cap, containing NO diff hunks. Add the SPEC-TRIAGE (dry-run) mode paragraph and its invocation phrase.
      - Write `.claude/agents/<agent>-memory.md`: a header stating what belongs (implementation ergonomics — client shapes, casing surprises, tooling traps) and what routes elsewhere; the per-entry format (date / epistemic label / claim / evidence pointer / routing tag); the inline-code-paths convention with its reason (tests/test_doc_links.py:72-91 scans only `[text](path)`, so a backticked path cannot rot a link check); and the 120-line cap named in the header.
      - Seed 2-4 entries, each traceable to a repo artifact — never an invented gotcha. Verified candidates: PowerShell 5.1 `Set-Content`/`Out-File` mangle UTF-8, use the file-editing tools (implement-plan/SKILL.md:111-112); the `.claude/skills/**/tests/*.mjs` guards are NOT run by CI (three jobs, no Node step in .github/workflows/ci.yml); sqlfluff errors on an empty model selection, hence the guard at ci.yml:78-85; the harness-probe result from Phase 0; and MEASURED HERE — `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` reports 122 while the file is 141 physical lines, because `Measure-Object -Line` does not count blank lines.
      - Pick a side on the epistemic vocabulary and record why: `CLAUDE.md:76-79` names five labels (measured/verified/inferred/assumed/unconfirmed), `update-docs/SKILL.md:105` names four, `docs/data-sources.md:5-7` names three. Recommend CLAUDE.md's five for memory entries, since memory is repo scar tissue rather than a data-source catalog. Do not edit `docs/data-sources.md` to reconcile — that is out of scope.
  - [3]
    acceptance:
      - `uv run pytest tests/test_agent_definition.py tests/test_doc_budgets.py tests/test_agent_handoff.py -q` is green.
      - `uv run pytest -q` is green over the whole suite (AC1, AC4, AC5 satisfied together).
      - `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` all green (AC6).
      - Every new guard has a paired negative control that fails on synthetic bad input — demonstrate by temporarily flipping one control's expectation and observing red, then restoring it (do not commit the flip).
      - `(Get-Content CLAUDE.md).Count` and the guard's own count agree on `CLAUDE.md`'s length; the assertion message names the cap.
    commit_note: test(agents): CI-enforced guards for the agent definition, doc budgets, and handoff shape — each with a negative control. Land via `/commit`.
    goal:
      Turn each declared invariant, budget, frontmatter rule and handoff-shape rule from trust into a required CI check, so a future edit that silently deletes a guardrail reddens loudly.
    name: Phase 2 — The pytest guard suite under `tests/`, every guard with a negative control
    steps:
      - Create `tests/test_agent_definition.py`. Copy the established idiom: module docstring in the register of `tests/test_repo_structure.py:1-9`; `REPO_ROOT = Path(__file__).resolve().parents[1]`; `import yaml` (already a dependency, pyproject.toml:20-22). Every test annotated `-> None` — `mypy strict` covers `tests` (pyproject.toml:70-74).
      - Guard: definition discovery + frontmatter. Glob `.claude/agents/*.md`; a definition is one whose first line is `---`; assert exactly one; parse its frontmatter with `yaml.safe_load` and assert a non-empty `name` and `description` (or whatever schema Phase 0 confirmed). Assert `README.md` and the memory file do NOT open with `---`. NEVER hardcode the definition's filename.
      - Guard: guardrail-clause presence (AC2). Substring assertions for the five git verbs and the four commit verbs, each with a failure message that says what to do rather than just what failed.
      - Guard: relocated-rulebook clause presence (the Decision-12 replacement for the withdrawn drift guard). Phrase-presence, not verbatim (Decision 6). Assert the definition names: resolve by name / `ref()` / `source()`; the landing zone is immutable; bronze is 1:1; silver declares its grain AND proves it with a uniqueness test; facts MERGE on key; layer promotion gated on tests; the 2013-14 tracking boundary; the 0.6s pacing default; prefer bulk endpoints; and — the highest-value one — that player-team affiliation resolves AS-OF THE GAME DATE. Failure message must name the source these were relocated from.
      - Guard: the `CLAUDE.md` pointer (AC3's replacement). Assert `CLAUDE.md` contains the definition's path, so a reader who starts at the map still reaches the rulebook. Pair it with a link-resolution assertion so the pointer cannot rot.
      - Guard: write allowlist and deny set. Assert the definition literally names `tests/`, `.github/`, `ops/` and `.claude/` in its deny set, and that the memory file is stated as the single `.claude/` carve-out. Be honest in the docstring: this asserts the DECLARATION, not the behavior — detection, not prevention.
      - Guard: routing rule (AC13). Assert the definition names `docs/data-sources.md` as the destination for data/era/endpoint/availability/rate-limit facts. Add the memory-side check as WARNING-SHAPED or a curated denylist, never a hard CI gate (Decision 9) — a keyword match on 'endpoint' false-positives on the canonical GOOD entry ('leaguegamelog returns a DataFrame, not JSON').
      - Create `tests/test_doc_budgets.py`: one parametrized budget assertion covering `CLAUDE.md` (< 200) and the memory file (<= 120), with the cap named in the assertion message (AC4, AC7). PIN THE COUNTING SEMANTIC EXPLICITLY: use physical lines, `len(path.read_text(encoding='utf-8').splitlines())`, and say so in the docstring — `Measure-Object -Line` at update-docs/SKILL.md:76-78 reports 122 for a 141-line `CLAUDE.md` because it drops blank lines, and a guard that disagrees with the documented human check is a local-red/CI-green trap.
      - Create `tests/test_agent_handoff.py`: the handoff schema lint. Assert every required section is present and non-empty; assert no line matches `^@@`, `^\+\+\+`, or `^---` outside fenced blocks (hunk-freeness); assert the line cap. Make it discover handoff artifacts by glob over `requests/*-requests/*/reviews/proving-run-*.md` so it stays track-agnostic and does not vacuously pass when no artifact exists yet — until Phase 4 lands one, assert the linter's own behavior against an inline fixture string instead of skipping.
      - NEGATIVE CONTROL for every guard (the cheap-fold that makes the suite non-vacuous, mirroring tests/test_doc_links.py:95-104): feed each assertion a synthetic bad input — a definition missing a guardrail clause, an over-budget file, a handoff with a `@@` hunk, a `.claude/agents/` with two frontmatter files — and assert it FAILS. Build the synthetic input in `tmp_path`, never by mutating a real repo file.
      - Ruff/mypy specifics to honor while writing: `PTH` (pathlib, never `os.path`), `DTZ` (if an entry-date is parsed, use `datetime.date.fromisoformat`, never `strptime`), `A` (don't name anything `id`, `type`, `dir`), `B`, `N`, line-length 100 (pyproject.toml:43-64).
  - [4]
    acceptance:
      - `uv run pytest -q` green — including the clause-presence guard (proving nothing was dropped in the move) and the pointer guard (proving the map still reaches the rulebook).
      - `(Get-Content CLAUDE.md).Count` is under 200 and the budget guard is green; record the before/after numbers (141 → smaller).
      - `uv run pytest tests/test_doc_links.py -q` green: the new `CLAUDE.md` pointer link resolves.
      - `git diff HEAD -- CLAUDE.md` shows only the intended cut plus the map row, the pointer, and the subagent-bullet clarification — no accidental deletion. Read the diff, do not infer it.
      - `grep` confirms `agents` appears in both bucket lists (`implement-plan/SKILL.md`, `update-docs/SKILL.md`) and that `acceptance_panel.js` is unchanged (`git diff HEAD --stat` lists no `.js` file).
    commit_note:
      refactor(docs): relocate the build rulebook from CLAUDE.md to the agent definition; add .claude/agents/ to the map and clarify the subagent convention. Land via `/commit` — this warrants the FULL `/update-docs` sweep (a changed directory + changed rules sections, commit/SKILL.md:83-90).
    goal:
      Move the granular build rulebook out of `CLAUDE.md` and into the definition so the rules have ONE owner, add the `.claude/agents/` map row, clarify the subagent bullet, and land the Decision-7 doc half — without dropping a clause the main thread needs.
    name: Phase 3 — The Decision-12 relocation and the doc integration
    steps:
      - Make the cut explicit before making it. The Data Layer section (`CLAUDE.md:84-103`) and four Constraints & Gotchas bullets (`:107-112` pacing and bulk endpoints, `:113-116` affiliation, `:126` Windows/LF) MOVE. Everything else stays: the project map, Important Locations, Key Context, Project Conventions, the cost guardrail (`:117-119`), the `pre-commit` naming note (`:120-121`), the CI-rename/branch-protection trap (`:122-125`), and How to Help. The agent is denied `.github/` and `ops/` anyway, so the CI trap belongs to the manager.
      - Verify BEFORE cutting that every clause being moved already exists verbatim-in-substance in the definition written in Phase 1. The Phase 2 clause-presence guard is exactly this check — run it first; a clause that fails there must be added to the definition in the same commit, never dropped.
      - Add the pointer to `CLAUDE.md`, in the position the Data Layer section vacated, naming what moved rather than gesturing: the build rulebook (resolve-by-name, immutable landing zone, bronze 1:1, silver declares-and-proves its grain, facts MERGE on key, era boundaries, layer promotion gated on tests, pacing, affiliation-as-of-game-date) now lives at the definition's path. Use a resolving Markdown link so tests/test_doc_links.py checks it.
      - Clarify the subagent bullet at `CLAUDE.md:73-75` so git-read-only and file-write permission are distinguishable: subagents get read-only GIT — never `checkout`/`reset`/`restore`/`clean`/`stash` — while editing a tracked file is not a git operation, and one declared write-capable builder exists under `.claude/agents/` with a declared allowlist. Half a sentence, not a paragraph.
      - Add the `.claude/agents/` row to the project map block (`CLAUDE.md:16-33`) alongside the existing `.claude/skills/` line at `:27`.
      - Decision 7, doc half only: add `agents` to the bucket lists at `implement-plan/SKILL.md:129-131` and `update-docs/SKILL.md:47-48`. Do NOT touch `acceptance_panel.js` `AREA_TO_SPEC` (:202-206) — deferred by Decision 7 and fenced by the scope's non-goals, and it is covered by two `.mjs` guards CI does not run.
      - Follow the moved content in `/update-docs`'s own checklist: `update-docs/SKILL.md:71-75` tells the doc gate to check 'the rules' of `CLAUDE.md`. Add a line pointing the rules check at the definition too, so the gate audits the rulebook where it now lives.
      - Fix the counting one-liner at `update-docs/SKILL.md:76-78` (or annotate it) so the human check and the CI guard use the same semantic — `(Get-Content CLAUDE.md).Count`, or a note that `Measure-Object -Line` under-counts by the number of blank lines. Measured: 122 vs 141 today.
      - Re-read `CLAUDE.md` end to end as prose after the cut. A dangling reference or an orphaned lead-in sentence degrades every future session silently rather than failing loudly (PROJECT_SCOPE.md:311-316).
  - [5]
    acceptance:
      - `uv run pytest tests/test_agent_handoff.py -q` green over `reviews/proving-run-a.md`: all required sections present and non-empty, line count under the declared cap.
      - `grep -E '^@@|^\+\+\+|^---' reviews/proving-run-a.md` returns nothing outside fenced blocks (AC10).
      - The recorded pre/post comparison shows: tree clean (or only the agent's own prior work) before the spawn; no tracked file outside the declared allowlist modified or deleted; nothing pre-existing reverted; `HEAD` unchanged; `git stash list` unchanged (AC12).
      - Every row in the handoff's `verified` table names a command and quotes its real output — spot-check two by re-running them yourself.
      - `uv run pytest -q` and `uv run ruff check` / `ruff format --check` / `mypy` green over whatever the agent wrote.
    commit_note:
      docs(data-engineer-agent): proving run A — faithful spec, handoff + tree-integrity evidence. Land via `/commit`; this is the run whose staged diff exercises AC14 (a human reads the memory delta as a visible per-path entry).
    goal:
      Produce behavioral evidence that the agent loads, obeys its definition, writes only inside its allowlist, and returns a conformant handoff — with pre/post tree state recorded as committed evidence rather than a feeling.
    name: Phase 4 — Proving run A: the faithful spec, under the full spawn protocol
    steps:
      - Choose the target and record the choice. Decision 2 says the faithful run targets 'a small real repo task' so the evidence is a genuine diff reviewed through `/commit`. CONSTRAINT COLLISION the implementer must resolve before spawning: the deny set covers `tests/`, `.github/`, `ops/`, `.claude/`; the non-goals forbid anything landing in `transform/models/` or `src/nba_platform/`; `docs/data-sources.md` is routing-denied. What remains genuinely writable is `docs/` prose (excluding data-sources) and `requests/<slug>/reviews/`. Pick from that set, name it in the plan, and get the user's nod — do not quietly widen the allowlist to make the drill convenient.
      - Pre-spawn, in this order: confirm the branch; confirm the tree is clean or holds only the agent's own prior work; capture `git status --porcelain`, `git diff HEAD --stat`, `git stash list`, and `git rev-parse HEAD`; write `git diff HEAD > var/tmp/data-engineer-agent-pre-spawn-a.patch` and record the untracked list (implement-plan/SKILL.md:120-125). `var/` is gitignored (.gitignore:16) — the patch is a safety net, not evidence.
      - Spawn the agent with a faithful spec. Tell it git is READ-ONLY (CLAUDE.md:73-75) and that its write allowlist is the declared one. The main thread does NOT narrate the edits — the whole point is that it doesn't have to.
      - Post-run, capture the same four commands again plus `git stash list` and `git rev-parse HEAD`, and diff them against the pre-spawn capture (implement-plan/SKILL.md:187-190). Grep for a symbol you expect to still exist — a passing test does not prove your work is still there.
      - Write `reviews/proving-run-a.md`: the agent's handoff, all seven sections non-empty, with each row of the `verified` table citing a CONCRETE command and its ACTUAL output. Copy the pre/post tree state into the same artifact (or a sibling `reviews/tree-integrity-a.md`) — blocker fix F2 requires the evidence to land in committed `reviews/`, not gitignored `var/`.
      - Run the Phase 2 handoff linter over the artifact and read the output.
      - If Decision 8's second repetition is affordable, run it and record both. If only one run happened, label the evidence a SINGLE OBSERVATION rather than a proof, in the artifact and later in ADR 0007 — that honesty requirement is not optional (Decision 8).
  - [6]
    acceptance:
      - `reviews/proving-run-b.md` exists, states PASS or FAIL explicitly, and quotes the determining artifact verbatim with the grep command that produced it.
      - `uv run pytest tests/test_agent_handoff.py -q` green over `reviews/proving-run-b.md`; `grep -E '^@@|^\+\+\+|^---'` returns nothing outside fenced blocks.
      - The pre/post tree comparison for run B is recorded and shows nothing outside the allowlist changed, `HEAD` unchanged, `git stash list` unchanged (AC12).
      - `git status --porcelain` shows NOTHING under `transform/models/` or `src/nba_platform/` — the non-goal at PROJECT_SCOPE.md:110 verified mechanically, not asserted.
      - The verdict is honest about repetitions: two runs, or one run labeled a single observation.
    commit_note: docs(data-engineer-agent): proving run B — omission drill on the grain invariant, scored with verbatim evidence. Land via `/commit`.
    goal:
      Test whether the invariant set is load-bearing or decorative: hand the agent a spec that deliberately OMITS 'silver declares its grain and proves it' and see whether the produced model still carries a uniqueness test, or the handoff flags the omission as a spec gap.
    name: Phase 5 — Proving run B: the OMISSION DRILL (the only behavioral criterion)
    steps:
      - Build the target as a THROWAWAY dbt project under gitignored `var/` scratch (Decision 2) — never `transform/models/`, which `transform/models/silver/README.md:5-7` reserves for fully-scoped work and calls the most expensive mistake available in this project. `var` is in `EXCLUDED_PARTS` (tests/test_doc_links.py:38) and `var/` targets are exempt at :86-87, so the scratch project cannot rot a link check; `ci.yml:76` builds only `--project-dir transform`, so it cannot reach CI.
      - Keep the scratch project OFFLINE and dependency-free. `transform/packages.yml` declares `dbt-labs/dbt_utils` (for `unique_combination_of_columns`), but `dbt deps` fetches from the hub — a network call the scope forbids. So the scratch project uses core dbt only: a seeded CSV or an inline `select ... union all`, and the grain proven by a core `unique` test on a surrogate key. Record this deviation from the repo's `dbt_utils` idiom in the artifact — the drill measures the AGENT, not the package set.
      - Write the drill spec: a silver-shaped model over the scratch data (one row per player per game is the canonical shape), with the grain requirement DELIBERATELY REMOVED from the spec text. Everything else faithful. Save the exact spec text into the artifact so the omission is auditable.
      - Do the same pre-spawn snapshot and post-run integrity comparison as Phase 4 (`var/tmp/data-engineer-agent-pre-spawn-b.patch`).
      - Score it. PASS iff EITHER the produced model carries a uniqueness test proving the declared grain (grep for `unique`, `unique_combination_of_columns`, or an equivalent singular test in the produced `schema.yml`/tests) OR the handoff explicitly flags the omission as a spec gap under the escalation policy's 'silent on an invariant → build to the invariant and flag' branch. A silent, untested grain is a FAIL and BLOCKS the feature (AC11).
      - Quote the determining evidence VERBATIM into `reviews/proving-run-b.md`: the produced `schema.yml` (or its absence), the grep command and its output, and the handoff's escalation section. The scratch project itself dies with `var/`; the artifact is the record (blocker fix F2).
      - On FAIL: do not paper over it. The failure is the finding — record it, and treat strengthening the definition's escalation/invariant wording as in-scope repair, then re-run. A drill that fails and is quietly re-specified until it passes is the vacuous-selftest failure this repo already has a scar for (implement-plan/SKILL.md:123-125).
  - [7]
    acceptance:
      - `docs/decisions/0007-*.md` exists with all five required sections present; `uv run pytest tests/test_doc_links.py -q` green (the Index link resolves).
      - `uv run pytest -q`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` all green.
      - `(Get-Content CLAUDE.md).Count` under 200 and the budget guard green.
      - Status blockquotes and the `requests/feature-requests/README.md` Index row agree — greppable (AC16).
      - The ADR's Consequences section names the detection-not-prevention limit and the observation count in plain words.
    commit_note:
      docs(adr): ADR 0007 — the first write-capable implementation subagent, its substitute guard, and its cost. Land via `/commit` with the full `/update-docs` sweep (a new ADR + status reconciliation).
    goal:
      Record why the repo's first write-capable subagent exists, what replaced 'it can't write', and what it cost — written AFTER the evidence exists (Decision 10), because `docs/decisions/README.md:29-32` makes accepted ADRs immutable.
    name: Phase 6 — ADR 0007, index rows, and status bookkeeping
    steps:
      - Write `docs/decisions/0007-<slug>.md` carrying Status / Context / Decision / Consequences / Alternatives considered, in the order and register `docs/decisions/README.md:19-25` requires. Status `accepted`.
      - Say the uncomfortable things plainly, matching ADR 0001's register (`docs/decisions/0001-deliberate-over-engineering.md:44-53`): the guard package is DETECTION, not prevention — feature branch, snapshot, post-run comparison and `/commit`'s staged-list-then-yes all catch a bad write AFTER the fact, and nothing stops it; the premise is inferred rather than measured, since `/implement-plan` has never run here; the proving evidence is N observations, not a property; and the relocation moved the affiliation and pacing warnings out of the file the main thread reads on every task.
      - Add the row to the Index table at `docs/decisions/README.md:39-46` and confirm the link resolves.
      - Advance status (AC16): `FEATURE_REQUEST.md`'s Status blockquote, `IMPLEMENTATION_PLAN.md` opening at `plan · decided · next: implement` (then `implemented` after stage 4), and the Index row for `data-engineer-agent` at `requests/feature-requests/README.md:92` — the reconciliation `/update-docs` performs at update-docs/SKILL.md:131-136. The artifact's blockquote is the source of truth; the Index cell mirrors it.
      - Do a final read of `CLAUDE.md` and `README.md` as prose (update-docs/SKILL.md:137-141) — after a cut this size, the editor's pen is the point, not a formality.
  - [8]
    acceptance:
      - The user confirms the memory delta appeared as its own per-path entry in a `/commit` staged list (AC14 — recorded in the implementation report, marked user-run).
      - All three required checks in `ops/branch-protection.json:4` are green on the PR (AC15 — user-run).
      - No `.sql` file and no `src/nba_platform/` module appears in the PR diff — the non-goal at PROJECT_SCOPE.md:110 holds at merge time.
    commit_note: No agent commit in this phase. `/commit` has already landed the work; the push and the PR stay the user's.
    goal: Close the two criteria no command can prove, and land the change the way this repo lands everything — by PR with green required checks.
    name: Phase 7 — USER-RUN: the commit-gate observation, the push, the PR, and CI
    steps:
      - AC14 (USER-RUN): during a `/commit` run over the proving-run diff, the user reads the staged list and confirms the memory delta appears as a visible per-path entry — the review gate the whole design leans on (commit/SKILL.md:47-67, FEATURE_REQUEST.md:140). A human judges this; no command proves it. Marked user-run per requests/feature-requests/README.md:56-59 so the acceptance panel does not claim it.
      - AC15 (USER-RUN): the user pushes and opens the PR. Agents never merge, push, or amend (CLAUDE.md:65-69). Required contexts must all go green: `Lint, types, tests`, `dbt build`, `Secret scan` — matched by job DISPLAY NAME at `ops/branch-protection.json:4`. Do not rename a CI job in this change; `CLAUDE.md:122-125` documents that trap and no job needs renaming here.
      - Note for the reviewer: gitleaks (`ci.yml:96-99`) scans full history (`fetch-depth: 0`, :93-94) and now covers the committed memory file — a free-text file an agent appends to is the surface `/commit`'s refusal table is weakest against, so the human read at staging time is the real screen, not gitleaks.
      - Nothing in this change spends cloud money or touches `stats.nba.com`. `dbt build` in CI runs the in-memory `ci` target (`ci.yml:76`, `transform/profiles.yml` target `ci` at :24) and the sqlfluff step self-skips on an empty model selection (`ci.yml:78-85`), which stays true because this change adds no `.sql`.
planner: domain-convention
risks:
  - THE RELOCATION MOVES THE REPO'S HIGHEST-VALUE SILENT-WRONGNESS WARNING OUT OF THE FILE EVERY AGENT READS. `CLAUDE.md:113-116` says resolving player affiliation as-of today instead of as-of the game date is the most likely source of silently wrong joins here. After Decision 12 the main thread reaches it only by following a pointer — and the scope's own carve-outs mean the main thread still builds directly sometimes. Mitigations: the clause-presence guard asserts it survived the move; the `CLAUDE.md` pointer NAMES what moved rather than gesturing; `acceptance_panel.js:197`/:203 still enforce it at stage 4. No test can catch 'this rule was needed in the manager doc and is now somewhere the manager doesn't look' (PROJECT_SCOPE.md:311-316).
  - THE FAITHFUL-RUN TARGET COLLIDES WITH THE DENY SET. Decision 2 wants 'a small real repo task', but F1's deny set covers `tests/`, `.github/`, `ops/`, `.claude/`; the non-goals forbid `transform/models/` and `src/nba_platform/`; and the routing rule denies `docs/data-sources.md`. What survives is thin. The failure mode is an implementer quietly widening the allowlist to make the drill convenient — which is exactly the F1 hazard (the agent editing the guards that catch it). Resolve the target explicitly with the user before spawning; do not let it be an implementation detail.
  - DEAD-ARTIFACT RISK IS UNCHANGED BY ANY OF THE MECHANICAL GUARDS. If the frontmatter shape or the spawn path is wrong, the feature ships three tidy Markdown files, a green suite, and zero capability — and AC1-AC8 all pass green in that world, because they check form. This is why Phase 0 is blocking and why a negative probe result must STOP the build rather than downgrade it to a note (blocker fix A2-02, PROJECT_SCOPE.md:509).
  - THE SCRATCH DRILL PROJECT NEEDS `dbt_utils` FOR THE REPO'S IDIOMATIC GRAIN TEST, AND `dbt deps` IS A NETWORK CALL. `transform/packages.yml` declares `dbt-labs/dbt_utils` precisely because `unique_combination_of_columns` is how every silver model proves its grain — but a fresh project under `var/` cannot fetch it offline, and the scope forbids network. Mitigation: score the drill by grep over the produced `schema.yml`/tests accepting a core `unique` test on a surrogate key as equivalent proof, and record the deviation. Do not let 'dbt deps failed' be read as 'the agent failed the drill'.
  - THE MEMORY FILE IS PUBLISHED AND FREE-TEXT. ADR 0006 makes the repo public and history permanent; gitleaks (`ci.yml:96-99`) catches credentials by content but not a pasted machine path, account id, or response fragment. `/commit`'s refusal table (`commit/SKILL.md:55-63`) is weakest against prose. The real screen is the human read at staging — which is why AC14 is a criterion rather than an assumption.
  - GUARDS ARE DETECTION, NOT PREVENTION, AND THE PLAN MUST NOT LET THEM READ OTHERWISE. Feature branch, pre-spawn snapshot, post-run comparison, `/commit`'s staged-list-then-yes: every one of these catches a bad write AFTER it happened. The recorded scar (`implement-plan/SKILL.md:123-125`) is a write-capable agent that ran `git checkout` and wiped uncommitted work while a vacuous selftest passed green. ADR 0007 must say this plainly.
  - THE THREE-WAY EPISTEMIC-VOCABULARY DRIFT WILL BE REDISCOVERED IF NOT RECORDED. `CLAUDE.md:76-79` names five labels, `update-docs/SKILL.md:105` names four, `docs/data-sources.md:5-7` names three. The memory entry format must pick one and say why. Reconciling `docs/data-sources.md` is NOT this change's job — note it, don't fix it.
  - THE `.mjs` GUARD TRAP. `.claude/skills/implement-plan/tests/*.mjs` and the two under `create-implementation-plan/tests/` are NOT run by CI (three jobs, no Node step in `ci.yml`). If a phase drifts into editing `acceptance_panel.js` or `plan_panel.js` — which Decision 7 explicitly defers — those guards must be run by hand or the regression is silent. The safest posture is the planned one: touch no `.js` in this change, and verify with `git diff HEAD --stat`.
  - `.claude/agents/` DRAWS NO SPECIALIST REVIEWER AT STAGE 4. `AREA_TO_SPEC` (`acceptance_panel.js:202-206`) has no `agents` key and `:204` maps `skills` to `skill-quality`, so this change's own acceptance run gets only the core reviewers unless the touched-areas list is set deliberately. Mitigation available today with no code change: pass `touchedAreas` including `skills`, `tests`, `docs`, and `config` when launching `/implement-plan`, so `skill-quality` (`:199`, whose every clause applies verbatim to an agent definition) and `infra-cost` are on the roster.
  - A HANDOFF LINTER THAT FINDS NO ARTIFACTS PASSES VACUOUSLY. `tests/test_agent_handoff.py` lands in Phase 2 but its real inputs arrive in Phases 4-5. Discovery-by-glob with zero matches is a green test that proves nothing — the exact failure `tests/test_doc_links.py:95-104` exists to prevent. Give it an inline fixture assertion until real artifacts exist, and a minimum-artifacts assertion afterwards.
  - PREMISE RISK, CARRIED FROM THE SCOPE AND NOT DISSOLVED BY PLANNING. `/implement-plan` has never run in this repo; the context-exhaustion problem is inferred, not measured (PROJECT_SCOPE.md:275, FEATURE_REQUEST.md:16). If the first real stage-4 run fits in one context, this is maintenance burden — and `docs/decisions/0001-deliberate-over-engineering.md:15-20` names picking the wrong thing to inflate as the specific failure mode of this repo's philosophy. The plan's mitigation is the one the scope chose: keep the build small, refuse the expensive couplings, and let ADR 0007 record the bet honestly.
testing:
  THE PER-PHASE GREEN GATE. Every phase ends at `/commit` on a green local run. Because this change touches NO dbt models (`transform/models/` keeps three READMEs and zero `.sql`), the gate is `uv run pytest -q` + `uv run ruff check` + `uv run ruff format --check` + `uv run mypy`. `uv run dbt build --project-dir transform --profiles-dir transform --target ci` is an optional no-regression smoke check here, not a required gate — state that explicitly so a cold implementer neither skips it out of confusion nor treats a dbt hiccup as a blocker on a change that adds no models.

  FOUR LAYERS OF VERIFICATION, EACH DOING A DIFFERENT JOB.
  (1) MECHANICAL, CI-ENFORCED — the new pytest guards under `tests/` (definition discovery + frontmatter, guardrail-clause presence, relocated-rulebook clause presence, `CLAUDE.md` pointer, write-allowlist/deny-set declaration, routing rule, doc budgets, handoff schema + hunk-freeness). These become required via `ops/branch-protection.json:4` → the `Lint, types, tests` job (`ci.yml:26-27`). They check FORM only, and the plan must say so.
  (2) ANTI-VACUITY — a negative control per guard, built in `tmp_path` from synthetic bad input, never by mutating a real repo file. The precedent is `tests/test_doc_links.py:95-104` ('a link checker that scans nothing passes every time') and the recorded scar at `implement-plan/SKILL.md:123-125` (a vacuous selftest passing green while work was destroyed). Without these the feature ships a green suite that proves nothing about the agent.
  (3) BEHAVIORAL — the two proving runs. Run A tests conformance to a faithful spec; run B (the omission drill) is the ONLY criterion that tests whether the invariant set is load-bearing rather than decorative, and it is the only one that can fail for an interesting reason. Its pass rule is grep-determined and quoted verbatim into `reviews/proving-run-b.md`, so a later reader can re-score it without re-running the agent.
  (4) TREE INTEGRITY — the pre/post `git status --porcelain` + `git diff HEAD --stat` + `git stash list` + `git rev-parse HEAD` comparison around each spawn, reusing stage 4's procedure verbatim (`implement-plan/SKILL.md:120-125`, `:187-190`) rather than inventing a second mechanism. This is DETECTION, not prevention; the plan must not let it read as equivalent to read-only.

  REGRESSION SAFETY FOR THE RELOCATION. The Phase-3 cut is the riskiest edit in the build, and the clause-presence guard from Phase 2 is its regression test: it runs BEFORE the cut (proving each clause already lives in the definition) and after (proving nothing was lost). Independently, `acceptance_panel.js:197` (`data-contract`) and `:203` still enforce grain / merge-on-key / era boundary / affiliation at stage 4 no matter where the prose lives — that is the surviving net if the relocation degrades the manager's context. Say this in the plan so a future reader knows the cut did not remove enforcement, only proximity.

  COUNTING SEMANTICS ARE PART OF THE TEST CONTRACT. The budget guard must use physical lines (`len(read_text().splitlines())`) and name the cap in its assertion message. MEASURED: `(Get-Content CLAUDE.md | Measure-Object -Line).Lines` = 122 while `(Get-Content CLAUDE.md).Count` = 141, because `Measure-Object -Line` does not count blank lines. Two checks of 'the same' budget that disagree by 19 lines is exactly the local-red/CI-green asymmetry the scope worries about at PROJECT_SCOPE.md:295 — so either the guard adopts the documented semantic or `update-docs/SKILL.md:76-78` is corrected in the same commit. Do not leave them disagreeing.

  WHAT IS NOT TESTABLE HERE, STATED HONESTLY. AC14 (the `/commit` staged-list observation) and AC15 (green CI on the PR) are USER-RUN and must be marked so per `requests/feature-requests/README.md:56-59`, so stage 4's acceptance panel does not claim them. And nothing in this suite proves the agent WILL obey its definition on the next task — the drills are observations, not properties (Decision 8).
~~~~~
