"""Link-drift guard for every Markdown file in the repo.

Docs here are read as authoritative — by agents on every task, and by anyone evaluating
the project. A dead relative link doesn't fail loudly: it silently sends the reader
somewhere that doesn't exist, and an agent invents something plausible instead. So links
are checked mechanically rather than by hope.

Originally this covered only `requests/` and `.claude/skills/`. It now covers all
Markdown, because the files most likely to be *followed* — CLAUDE.md's project map,
README's layout, the ADR index, ops/ runbooks — were exactly the ones going unchecked.

Exempt, deliberately:
  - fenced code blocks, so a doc can quote a dead or forward-referenced path
  - `<placeholder>` targets, so a skill can show the shape of a link it tells you to write
  - absolute URLs and bare `#anchors` (no network in CI; anchor validation is a different job)
  - generated, vendored, and gitignored trees — see EXCLUDED_PARTS

Archived (`_done/`) artifacts are skipped: they describe the repo as it was, and rewriting
history to satisfy a link checker would destroy the provenance trail.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Directory names that disqualify a path at any depth. Covers gitignored trees (which
# rglob still walks locally), vendored packages, and the archive.
EXCLUDED_PARTS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "var",
        "target",
        "dbt_packages",
        ".ruff_cache",
        ".mypy_cache",
        ".pytest_cache",
        "htmlcov",
        "dist",
        "build",
        "_done",
    }
)

# Files that must be covered. Guards against an exclusion bug quietly turning this
# whole check into a no-op — the "passes vacuously" failure mode is worse than no check.
MUST_COVER = ("CLAUDE.md", "README.md")
MIN_EXPECTED_FILES = 20

FENCED_BLOCK = re.compile(r"^([ \t>]*)(`{3,}|~{3,}).*?^\1\2.*?$", re.DOTALL | re.MULTILINE)
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
LINE_SUFFIX = re.compile(r":\d+(-\d+)?$")


def _scanned_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.rglob("*.md")
        if not EXCLUDED_PARTS.intersection(path.relative_to(REPO_ROOT).parts)
    )


def _dead_links(path: Path) -> list[str]:
    body = FENCED_BLOCK.sub("", path.read_text(encoding="utf-8"))
    dead: list[str] = []

    for raw_target in MARKDOWN_LINK.findall(body):
        # Strip an optional link title: [text](path "Title")
        target = raw_target.split()[0].strip()

        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # `[<slug>](<slug>/)` — a template showing the shape of a link, not a link.
        if "<" in target and ">" in target:
            continue
        # Drop an anchor fragment, then a `file.py:123` citation suffix.
        target = target.split("#", 1)[0]
        if not target:
            continue
        target = LINE_SUFFIX.sub("", target)
        if target.startswith("var/") or "/var/" in target:
            continue

        if not (path.parent / target).resolve().exists():
            dead.append(raw_target)

    return dead


def test_the_guard_actually_covers_the_repo() -> None:
    """A link checker that scans nothing passes every time."""
    scanned = {str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in _scanned_files()}

    assert len(scanned) >= MIN_EXPECTED_FILES, (
        f"Only {len(scanned)} Markdown file(s) scanned, expected at least "
        f"{MIN_EXPECTED_FILES}. An exclusion rule is probably too broad."
    )
    missing = [name for name in MUST_COVER if name not in scanned]
    assert not missing, f"These must be link-checked and were not scanned: {missing}"


def test_no_dead_relative_links() -> None:
    failures = {
        str(path.relative_to(REPO_ROOT)).replace("\\", "/"): dead
        for path in _scanned_files()
        if (dead := _dead_links(path))
    }

    assert not failures, "Dead relative links:\n" + "\n".join(
        f"  {file}: {targets}" for file, targets in sorted(failures.items())
    )
