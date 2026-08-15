"""Contract guards for the write-capable implementation agent.

`.claude/agents/data-engineer.md` is the single owner of this repo's build rulebook. The
rules were relocated there out of `CLAUDE.md` so they would stop existing in two places
that could drift. That relocation is what makes the definition load-bearing prose: nothing
in CI *executes* it, and an agent spawned against a silently-gutted definition fails by
building the wrong thing rather than by erroring.

So these guards assert the **declaration**, not the behaviour. They catch a clause being
deleted in a future edit; they cannot catch an agent ignoring one that is present.
Detection, not prevention — the same honesty ADR 0007 is required to state.

Every check is a pure function over text, so the same predicate can be pointed at a
synthetic bad input. Without that factoring the negative controls cannot be written at
all, and a guard with no negative control is how a suite passes green while proving
nothing — see `tests/test_doc_links.py:95-104`, which exists for exactly that reason.

`REPO_ROOT` uses the `parents[1]` idiom established at `tests/test_repo_structure.py:19`
rather than resolving through a config layer. That is deliberate: `CLAUDE.md`'s
resolve-by-name rule targets the Python config layer, which does not exist yet, and both
existing test modules already use this idiom. Everything below the root is discovered by
glob so a rename cannot quietly turn a guard vacuous.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

# Budgets. Both are counted as PHYSICAL lines — len(text.splitlines()) — which is what a
# reader scrolls and what Python counts natively. This deliberately differs from
# PowerShell's `(Get-Content | Measure-Object -Line).Lines`, which drops blank lines and
# reports ~18 fewer for CLAUDE.md. Every assertion message below names both the cap and
# the counting method, so a red check cannot be dismissed as "the other count says fine".
# The memory budget is deliberately TWO-TIER, and the split is the point.
#
# `MEMORY_CURATION_TARGET` is what the file should look like when work lands on `main`: short
# enough that an agent reads all of it before building. Whether a given entry has stopped
# earning its place is a *judgment*, so it is enforced by `/update-docs` at the doc sweep — the
# same sweep that already asks whether the prose still describes the repo.
#
# `MEMORY_RUNAWAY_CEILING` is what this mechanical guard enforces, and it is far looser. A build
# spanning many phases legitimately learns more than the target holds, and a hard stop at the
# target means the main thread prunes reactively mid-build — dropping entries a later phase still
# needs, purely to make room. That was measured on the box-score-foundation build: three prunes
# in one feature, each one a guess about what the remaining phases would want.
#
# So: the agent appends freely while it works and the file gets curated once, before merge. What
# stays absolute is that **the agent never prunes** — at the ceiling it reports rather than
# deletes, because it cannot see which entries have stopped earning their place.
MEMORY_CURATION_TARGET = 120
MEMORY_RUNAWAY_CEILING = 250
CLAUDE_MD_LINE_CAP = 200

COUNTING_NOTE = (
    "Counted as physical lines — len(text.splitlines()) — not PowerShell's "
    "`(Get-Content | Measure-Object -Line).Lines`, which drops blank lines."
)

EPISTEMIC_LABELS = ("measured", "verified", "inferred", "assumed", "unconfirmed")

# Git verbs that must be named literally, so a substring check can find them. Naming the
# verbs rather than paraphrasing is the point: "git is read-only" is easy to soften in an
# edit, "never `checkout`" is not.
DESTRUCTIVE_GIT_VERBS = ("checkout", "reset", "restore", "clean", "stash")
FORBIDDEN_GIT_ACTIONS = ("never `commit`", "never `merge`", "never `push`", "never `amend`")

# The rulebook clauses relocated out of CLAUDE.md's Data Layer section and Constraints &
# Gotchas. This guard is Phase 3's regression test: it proves the move dropped nothing.
# Phrase-presence, not verbatim (Decision 6) — verbatim matching would redden CI on any
# wording change and train people to route around the guard.
RELOCATED_RULEBOOK_CLAUSES = (
    "Resolve by name",
    "ref()",
    "source()",
    "landing zone is immutable",
    "Bronze is 1:1 with the source",
    "declares its grain and proves it",
    "uniqueness test",
    # Backticked and hyphenated deliberately. `_normalize` lowercases, so a bare "MERGE"
    # would be satisfied by the "never `merge`" clause in the git section and this check
    # would pass with the facts-merge-on-key rule deleted.
    "`MERGE`-on-key",
    "Layer promotion is gated on tests",
    "No bulk data in git",
    "0.6s",
    "leaguegamelog",
    "`unconfirmed`",
    ".gitattributes",
    "Key Context",
    "as-of the *game*",
)

# Only the four blocker-F1 paths are asserted. The definition's prose extends the deny set
# by three more (CLAUDE.md, docs/data-sources.md, docs/decisions/), but those came from a
# judgment call disposed at gate #3 — asserting them would over-fit acceptance to it.
DENY_SET_PATHS = ("tests/", ".github/", "ops/", ".claude/")

TOOL_ALLOWLIST_CLAUSES = ("uv run pytest", "uv run mypy", "uv run dbt build", "PowerShell")

# Narrow, curated terms for the routing check (gate #9). These are scanned over ENTRIES
# ONLY — never the header, which legitimately names `docs/data-sources.md`, rate limits
# and era boundaries as examples of what routes elsewhere. A naive whole-file scan would
# redden against the very file the memory format tells the agent to write.
#
# Every term below is chosen so it cannot fire on the canonical GOOD entry, "leaguegamelog
# returns a DataFrame, not JSON" — which is simultaneously the archetypal ergonomics note
# and the thing a careless keyword guard would flag. That is why this is a short denylist
# of unambiguous data-fact vocabulary rather than a pattern over endpoint names or a
# season-shaped regex (which would match the `YYYY-MM-DD` date every entry opens with).
ROUTING_DENYLIST = (
    "rate limit",
    "rate-limit",
    "2013-14",
    "82 games",
    "tracking-derived",
    "structurally absent",
    "docs/data-sources.md",
    "era boundary",
    "era boundaries",
)

ENTRY_OPENER = re.compile(
    r"^- \*\*(?P<day>\d{4}-\d{2}-\d{2})\*\* · `(?P<label>[a-z]+)` · \S",
)


# ─── Pure predicates ──────────────────────────────────────────────────────────
# Each takes text and returns a finding, so the real file and a synthetic bad string go
# through identical code.


def _frontmatter(text: str) -> str | None:
    """The raw YAML frontmatter block, or None if the file opens without one."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


def _line_count(text: str) -> int:
    """Physical lines — what a reader scrolls. See COUNTING_NOTE."""
    return len(text.splitlines())


def _normalize(text: str) -> str:
    """Collapse whitespace runs and case.

    Clause checks run against wrapped Markdown prose, where a phrase routinely straddles a
    line break — `never\\n`push`` is the same clause as `never `push``. Matching raw
    substrings would redden whenever a paragraph is re-wrapped, which is precisely the
    friction that teaches people to delete a guard instead of satisfying it.
    """
    return " ".join(text.split()).lower()


def _missing_clauses(text: str, required: Iterable[str]) -> list[str]:
    haystack = _normalize(text)
    return [clause for clause in required if _normalize(clause) not in haystack]


def _entry_lines(text: str, heading: str = "## Entries") -> list[str]:
    """Entry bullets only, with the header block excluded.

    The header is exempt by construction: it must be free to name the things entries may
    not contain. Splitting on the heading rather than filtering by content is what keeps
    that exemption honest and legible.
    """
    _, _, entries = text.partition(heading)
    return [line for line in entries.splitlines() if line.startswith("- ")]


def _entry_format_violations(text: str) -> list[str]:
    violations: list[str] = []
    for line in _entry_lines(text):
        match = ENTRY_OPENER.match(line)
        if match is None:
            violations.append(f"malformed opener: {line[:70]}")
            continue
        label = match.group("label")
        if label not in EPISTEMIC_LABELS:
            violations.append(f"label {label!r} is not one of {EPISTEMIC_LABELS}: {line[:70]}")
        try:
            date.fromisoformat(match.group("day"))
        except ValueError:
            violations.append(f"unparseable date: {line[:70]}")
    return violations


def _routing_violations(text: str) -> list[str]:
    lowered_entries = [line.lower() for line in _entry_lines(text)]
    return [
        f"{term!r} in entry: {line[:70]}"
        for line in lowered_entries
        for term in ROUTING_DENYLIST
        if term in line
    ]


def _definition_path() -> Path:
    """The one frontmatter-bearing file in .claude/agents/, found by glob."""
    definitions = [
        path for path in sorted(AGENTS_DIR.glob("*.md")) if _frontmatter(path.read_text("utf-8"))
    ]
    assert len(definitions) == 1, (
        f"Expected exactly one frontmatter-bearing agent definition in {AGENTS_DIR}, "
        f"found {[p.name for p in definitions]}."
    )
    return definitions[0]


def _definition_text() -> str:
    return _definition_path().read_text(encoding="utf-8")


def _memory_path() -> Path:
    return AGENTS_DIR / "data-engineer-memory.md"


# ─── Guardrail clauses (AC2) ──────────────────────────────────────────────────


def test_definition_states_git_is_read_only() -> None:
    """The five destructive verbs are named literally, not paraphrased."""
    missing = _missing_clauses(_definition_text(), [f"`{v}`" for v in DESTRUCTIVE_GIT_VERBS])
    assert not missing, (
        f"{_definition_path().name} no longer names destructive git verb(s): {missing}. "
        "These are named literally so a deleted guardrail reddens loudly. The reason is "
        "recorded: a write-capable agent once ran `git checkout` and silently wiped "
        "uncommitted work while a vacuous selftest passed green."
    )


def test_definition_forbids_commit_merge_push_amend() -> None:
    missing = _missing_clauses(_definition_text(), FORBIDDEN_GIT_ACTIONS)
    assert not missing, (
        f"{_definition_path().name} no longer forbids: {missing}. `/commit` is the only "
        "sanctioned committer in this repo and it belongs to the main thread."
    )


def test_guardrail_predicate_catches_a_removed_clause() -> None:
    """Negative control: the predicate must report a clause that was deleted."""
    gutted = "Git is read-only. Never `checkout`, never `reset`, never `restore`."
    missing = _missing_clauses(gutted, [f"`{v}`" for v in DESTRUCTIVE_GIT_VERBS])
    assert missing == ["`clean`", "`stash`"], (
        "The clause predicate failed to notice two deleted git verbs — it would pass "
        f"vacuously against a gutted definition. Reported: {missing}"
    )


# ─── Relocated rulebook (Phase 3's regression test) ───────────────────────────


def test_definition_carries_the_relocated_rulebook() -> None:
    """Every rule moved out of CLAUDE.md survived the move.

    Run this BEFORE cutting anything from CLAUDE.md: add-then-remove. A clause failing
    here is one to add to the definition in the same commit, never one to drop.
    """
    missing = _missing_clauses(_definition_text(), RELOCATED_RULEBOOK_CLAUSES)
    assert not missing, (
        f"{_definition_path().name} is missing rulebook clause(s): {missing}. These were "
        "relocated OUT of CLAUDE.md's Data Layer section and Constraints & Gotchas, so "
        "the definition is now their only owner — if they are not here they are nowhere. "
        "Restore them in the definition; do not re-add them to CLAUDE.md."
    )


def test_rulebook_clauses_are_not_satisfied_by_unrelated_prose() -> None:
    """Anti-vacuity: normalization lowercases, so near-collisions must still fail.

    A definition that says "never `merge`" (the git rule) but has lost "facts are
    `MERGE`-on-key" (the data rule) must be caught. These are different rules that share
    a word, and a case-insensitive check is exactly where they would blur together.
    """
    git_rule_only = "Git is read-only. Never `commit`, never `merge`, never `push`."
    assert "`MERGE`-on-key" in _missing_clauses(git_rule_only, RELOCATED_RULEBOOK_CLAUSES), (
        "The merge-on-key clause was satisfied by the unrelated git prohibition — the "
        "rulebook check would pass with the data rule deleted."
    )


def test_rulebook_predicate_catches_a_dropped_rule() -> None:
    """Negative control: a definition that lost the grain rule must fail."""
    without_grain = "Resolve by name with ref() and source(). Bronze is 1:1 with the source."
    missing = _missing_clauses(without_grain, RELOCATED_RULEBOOK_CLAUSES)
    assert "declares its grain and proves it" in missing, (
        "The rulebook predicate did not notice the missing grain rule — the single "
        f"invariant the omission drill measures. Reported: {missing}"
    )


# ─── Write allowlist / deny set (blocker F1) ──────────────────────────────────


def test_definition_declares_the_deny_set() -> None:
    """Asserts the DECLARATION, not the behaviour.

    Measured 2026-08-14: this harness has no path-level permission system, so nothing
    enforces the allowlist. This guard catches the bound being deleted from the prose. It
    cannot catch an agent writing outside it — that is what the pre/post tree-integrity
    comparison and `/commit`'s staged list are for.
    """
    missing = _missing_clauses(_definition_text(), DENY_SET_PATHS)
    assert not missing, (
        f"{_definition_path().name} no longer denies: {missing}. An agent that can edit "
        "the guards that catch it and then report green is the restaging of the scar "
        "this repo already carries."
    )


def test_definition_carves_out_only_the_memory_file_under_dot_claude() -> None:
    text = _definition_text()
    memory_rel = ".claude/agents/data-engineer-memory.md"
    assert memory_rel in text, (
        f"The definition must name its memory file by the exact path {memory_rel!r}, not "
        "as a prefix rule — a future dispatch table treats `.claude/` as every agent's "
        "deny prefix and would otherwise have to special-case this directory."
    )
    assert _memory_path().is_file(), (
        f"The definition names {memory_rel} but no such file exists. A memory pointer to "
        "nothing is a silently empty knowledge store."
    )


def test_deny_set_predicate_catches_a_removed_path() -> None:
    """Negative control."""
    permissive = "You may not write to .github/ or ops/."
    missing = _missing_clauses(permissive, DENY_SET_PATHS)
    assert "tests/" in missing and ".claude/" in missing, (
        f"The deny-set predicate missed two removed paths. Reported: {missing}"
    )


# ─── The CLAUDE.md pointer (AC3's replacement) ────────────────────────────────


def test_claude_md_points_at_the_definition() -> None:
    """A reader who starts at the map must still reach the rulebook.

    The rules were relocated out of CLAUDE.md so they would have a single owner. That
    trade is only safe while the pointer survives: without it the main thread — which
    still builds directly for the deny-set carve-outs — has no path to the rules at all,
    and the relocation has silently deleted them from everywhere anyone looks.

    Asserted as the definition's literal path, discovered by glob rather than hardcoded,
    so renaming the definition reddens here instead of leaving a dangling pointer.
    """
    rel_path = _definition_path().relative_to(REPO_ROOT).as_posix()
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert rel_path in claude_md, (
        f"CLAUDE.md no longer names {rel_path}. The build rulebook lives there and nowhere "
        "else — restore the pointer rather than re-inlining the rules, or the relocation "
        "has removed them from every file a reader actually opens."
    )


def test_pointer_predicate_catches_a_missing_pointer() -> None:
    """Negative control, over a synthetic CLAUDE.md — never by mutating the real one."""
    synthetic = "# NBA Data Platform\n\n## Project Map\n\nNo pointer here.\n"
    assert ".claude/agents/data-engineer.md" not in synthetic, (
        "The pointer predicate would pass against a CLAUDE.md that names no definition."
    )


# ─── Tool allowlist (Decision 3) ──────────────────────────────────────────────


def test_definition_grants_the_verify_commands() -> None:
    """The agent must be able to check its own work.

    Without this it is the only actor in the repo that cannot run its own tests, the
    return contract's "cite a command and its actual output" becomes impossible, and the
    isolation the agent exists to buy is undone. `PowerShell` is named deliberately:
    measured 2026-08-14, declaring `Bash` in agent frontmatter on this platform yields an
    agent with no shell at all, with no warning.
    """
    missing = _missing_clauses(_definition_text(), TOOL_ALLOWLIST_CLAUSES)
    assert not missing, f"{_definition_path().name} no longer grants verify command(s): {missing}."


# ─── Budgets (AC4 + the folded CLAUDE.md win) ─────────────────────────────────


def test_memory_file_is_under_the_runaway_ceiling() -> None:
    """The mechanical half. The curation target is `/update-docs`'s, not this file's."""
    count = _line_count(_memory_path().read_text(encoding="utf-8"))
    assert count <= MEMORY_RUNAWAY_CEILING, (
        f"{_memory_path().name} is {count} lines, over the runaway ceiling of "
        f"{MEMORY_RUNAWAY_CEILING}. {COUNTING_NOTE} "
        "This ceiling is not the curation target — that is "
        f"{MEMORY_CURATION_TARGET} lines and is enforced by /update-docs before merge. "
        "Being over THIS number means the file has run away, not merely that it is due a "
        "sweep. The agent still appends nothing here and reports 'memory at cap, pruning "
        "needed' under still-open: pruning is a main-thread decision, because the agent "
        "cannot see which entries have stopped earning their place. Raising the ceiling is "
        "not the fix."
    )


def test_claude_md_is_within_budget() -> None:
    count = _line_count((REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8"))
    assert count < CLAUDE_MD_LINE_CAP, (
        f"CLAUDE.md is {count} lines, at or over its cap of {CLAUDE_MD_LINE_CAP}. "
        f"{COUNTING_NOTE} "
        "Over budget means cutting, not reformatting — the file is a map, and a map that "
        "takes an hour to read is not a map."
    )


def test_budget_predicate_catches_an_over_cap_file(tmp_path: Path) -> None:
    """Negative control, built from a synthetic file — never by mutating a real one."""
    bloated = tmp_path / "over-budget.md"
    bloated.write_text("\n".join(f"line {n}" for n in range(MEMORY_RUNAWAY_CEILING + 5)), "utf-8")
    assert _line_count(bloated.read_text(encoding="utf-8")) > MEMORY_RUNAWAY_CEILING, (
        "The budget predicate failed to flag a file well over the ceiling."
    )
    # The curation target must stay meaningfully tighter than the ceiling, or the two-tier
    # split collapses back into one number and the sweep stops being a real step.
    assert MEMORY_CURATION_TARGET < MEMORY_RUNAWAY_CEILING


def test_budget_predicate_counts_physical_lines_including_blanks() -> None:
    """The counting method is part of the contract, not an implementation detail.

    Two checks of one budget that disagree by ~18 lines is how the first red budget check
    gets dismissed as broken against the documented one-liner.
    """
    assert _line_count("a\n\n\nb") == 4, (
        "Blank lines must count. If this drops to 2 the guard has silently adopted "
        "PowerShell's Measure-Object semantics and the cap means something different."
    )


# ─── Memory entry format + routing (AC13, gate #9) ────────────────────────────


def test_memory_entries_are_well_formed() -> None:
    violations = _entry_format_violations(_memory_path().read_text(encoding="utf-8"))
    assert not violations, (
        f"Malformed memory entries: {violations}. Every entry opens "
        "`- **YYYY-MM-DD** · `label` · <claim>` and carries one of CLAUDE.md's five "
        f"labels {EPISTEMIC_LABELS}. Note `documented` is NOT among them — a claim that "
        "is merely written down somewhere, not run, is `assumed`."
    )


def test_memory_entries_contain_no_data_facts() -> None:
    """Data facts route to docs/data-sources.md through the handoff, never into memory.

    Scans entries only. The header is exempt by construction — it must name the very
    vocabulary this list denies, in order to tell the agent what routes elsewhere.
    """
    violations = _routing_violations(_memory_path().read_text(encoding="utf-8"))
    assert not violations, (
        f"Data-fact vocabulary found in memory entries: {violations}. These belong in "
        "docs/data-sources.md, queued through the handoff's docs-delta section, because "
        "that file is audited by the doc gate and memory is not."
    )


def test_entry_format_predicate_catches_a_bad_label() -> None:
    """Negative control: `documented` is a real label elsewhere in the repo, and wrong here."""
    bad = "## Entries\n- **2026-08-14** · `documented` · something · evidence: `x.md`\n"
    violations = _entry_format_violations(bad)
    assert any("documented" in v for v in violations), (
        f"The entry predicate accepted a label outside the five. Reported: {violations}"
    )


def test_entry_format_predicate_catches_a_malformed_opener() -> None:
    """Negative control."""
    bad = "## Entries\n- just some prose with no date or label\n"
    assert _entry_format_violations(bad), "The entry predicate accepted a shapeless bullet."


def test_routing_predicate_exempts_the_header_but_not_entries() -> None:
    """Negative control, both directions — the exemption must be real AND bounded."""
    header_only = (
        "Do not record rate limit behaviour or the 2013-14 era boundary here.\n"
        "## Entries\n- **2026-08-14** · `verified` · tooling note · evidence: `ci.yml`\n"
    )
    assert not _routing_violations(header_only), (
        "The header is not exempt — this guard would redden against a correctly written "
        "memory file, which is worse than no guard."
    )

    in_an_entry = (
        "## Entries\n- **2026-08-14** · `measured` · the 2013-14 boundary · evidence: `x`\n"
    )
    assert _routing_violations(in_an_entry), (
        "A data fact inside an entry was not caught — the exemption is unbounded."
    )


def test_routing_denylist_does_not_fire_on_the_canonical_good_entry() -> None:
    """The entry this repo most wants recorded must not be flagged.

    "leaguegamelog returns a DataFrame, not JSON" is simultaneously the archetypal
    implementation-ergonomics note and exactly what a careless keyword guard would flag.
    If this ever fails, the denylist has grown too broad — narrow it, don't suppress it.
    """
    good = (
        "## Entries\n- **2026-08-14** · `verified` · `leaguegamelog` returns a DataFrame, "
        "not JSON, and its column casing differs from the docs · evidence: `x.md`\n"
    )
    assert not _routing_violations(good), (
        "The routing denylist fired on the canonical good memory entry."
    )
