"""Schema lint for agent handoffs.

The handoff is the agent's whole return contract. Its point is that the main thread does
NOT have to read every edit — so "was the contract honoured?" has to be a check rather
than a feeling. That is what this module makes mechanical: fixed sections, all non-empty,
under a line cap, and carrying no diff hunks.

Handoffs **self-declare** with a first-line marker rather than being found by filename.
A filename glob would be brittle and track-specific; the marker keeps this linter
track-agnostic by construction — it walks both `feature-requests/` and `bugfix-requests/`
and lints only what identifies itself, so it works the first time a bug is handed to the
agent without anyone rewriting it.

The hunk check matches unified-diff header **shapes**, not a bare `^---`. A bare `---` is
also YAML frontmatter and a Markdown thematic break, so matching it would fail a
well-formed handoff that merely used a section divider. The return contract closes the gap
from the other side by forbidding thematic rules outright, which is what makes the
criterion's literal `^---` grep and this guard agree instead of contradicting each other.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUESTS_DIR = REPO_ROOT / "requests"

HANDOFF_MARKER = "<!-- handoff: v1 -->"
HANDOFF_LINE_CAP = 120

REQUIRED_SECTIONS = (
    "track",
    "built",
    "verified",
    "assumed",
    "surprised-me",
    "could-not-do",
    "docs-delta",
    "still-open",
)

# Unified-diff header shapes. `--- ` carries a TRAILING SPACE deliberately: that is what
# separates a diff's old-file header from a Markdown thematic break.
DIFF_SHAPES = (
    re.compile(r"^@@ ", re.MULTILINE),
    re.compile(r"^\+\+\+ ", re.MULTILINE),
    re.compile(r"^--- ", re.MULTILINE),
    re.compile(r"^diff --git ", re.MULTILINE),
)

SECTION_HEADING = re.compile(r"^##\s+(?P<name>.+?)\s*$", re.MULTILINE)


def _sections(text: str) -> dict[str, str]:
    """Map each `## heading` to its body text, in one pass."""
    found: dict[str, str] = {}
    matches = list(SECTION_HEADING.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        found[match.group("name").strip().lower()] = text[match.end() : end]
    return found


def lint_handoff(text: str) -> list[str]:
    """Return every contract violation in a handoff. Empty list means it conforms."""
    violations: list[str] = []

    if not text.startswith(HANDOFF_MARKER):
        violations.append(
            f"first line must be exactly {HANDOFF_MARKER!r} — this is how the linter finds "
            "handoffs without a brittle filename glob"
        )

    sections = _sections(text)
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            violations.append(f"missing required section: ## {name}")
        elif not sections[name].strip():
            violations.append(
                f"section ## {name} is present but empty — write 'none' rather than "
                "leaving it blank, so a skipped section is distinguishable from a "
                "deliberate one"
            )

    count = len(text.splitlines())
    if count > HANDOFF_LINE_CAP:
        violations.append(
            f"handoff is {count} physical lines, over the cap of {HANDOFF_LINE_CAP}. "
            "Counted as len(text.splitlines()). A handoff longer than the memory file it "
            "feeds has stopped being a summary."
        )

    for shape in DIFF_SHAPES:
        if shape.search(text):
            violations.append(
                f"contains a diff hunk matching {shape.pattern!r}. The handoff reports what "
                "was built, never how it was patched — pasting a diff reconstitutes exactly "
                "the detail this agent exists to keep out of the main thread's context."
            )

    return violations


def _handoff_files() -> list[Path]:
    """Every self-declaring handoff under either track's reviews/ directory."""
    if not REQUESTS_DIR.is_dir():
        return []
    return sorted(
        path
        for path in REQUESTS_DIR.glob("*-requests/*/reviews/*.md")
        if path.read_text(encoding="utf-8").startswith(HANDOFF_MARKER)
    )


# ─── The real artifacts ───────────────────────────────────────────────────────


def test_every_committed_handoff_conforms() -> None:
    failures = {
        str(path.relative_to(REPO_ROOT)).replace("\\", "/"): problems
        for path in _handoff_files()
        if (problems := lint_handoff(path.read_text(encoding="utf-8")))
    }
    assert not failures, "Handoff contract violations:\n" + "\n".join(
        f"  {name}: {problems}" for name, problems in sorted(failures.items())
    )


# ─── Synthetic controls ───────────────────────────────────────────────────────
# These exercise the linter before any real handoff exists. A linter whose only inputs
# arrive two phases later is a linter nobody has watched work.


def _good_handoff(body_extra: str = "") -> str:
    sections = "\n".join(f"## {name}\ncontent for {name}.\n" for name in REQUIRED_SECTIONS)
    return f"{HANDOFF_MARKER}\n\n# Handoff\n\n{sections}{body_extra}"


def test_a_well_formed_handoff_passes() -> None:
    assert lint_handoff(_good_handoff()) == []


def test_control_missing_section_fails() -> None:
    text = _good_handoff().replace("## docs-delta\ncontent for docs-delta.\n", "")
    problems = lint_handoff(text)
    assert any("docs-delta" in p for p in problems), problems


def test_control_empty_section_fails() -> None:
    text = _good_handoff().replace("## assumed\ncontent for assumed.\n", "## assumed\n\n")
    problems = lint_handoff(text)
    assert any("empty" in p and "assumed" in p for p in problems), problems


def test_control_diff_hunk_fails() -> None:
    text = _good_handoff("\n@@ -1,4 +1,9 @@\n")
    problems = lint_handoff(text)
    assert any("diff hunk" in p for p in problems), problems


def test_control_diff_git_header_fails() -> None:
    text = _good_handoff("\ndiff --git a/README.md b/README.md\n")
    problems = lint_handoff(text)
    assert any("diff hunk" in p for p in problems), problems


def test_control_over_cap_fails() -> None:
    filler = "\n".join(f"padding line {n}" for n in range(HANDOFF_LINE_CAP + 5))
    problems = lint_handoff(_good_handoff("\n" + filler))
    assert any("over the cap" in p for p in problems), problems


def test_control_thematic_rule_passes() -> None:
    """A Markdown thematic break is NOT a diff header, and must not be flagged as one.

    This is the distinction the whole hunk check turns on. `--- ` with a trailing space is
    a diff's old-file header; a bare `---` is a section divider or YAML frontmatter. If
    this test ever fails, the guard has started rejecting well-formed handoffs — which is
    worse than not having it, because the fix people reach for is to stop running it.

    The return contract separately forbids thematic rules, so a conforming handoff has
    none anyway. That belt-and-braces is deliberate: it makes the criterion's literal
    `^---` grep come back empty without this guard having to false-positive to achieve it.
    """
    assert lint_handoff(_good_handoff("\n---\n")) == []


def test_control_missing_marker_fails() -> None:
    text = _good_handoff().replace(HANDOFF_MARKER + "\n", "", 1)
    problems = lint_handoff(text)
    assert any("first line" in p for p in problems), problems
