<!-- handoff: v1 -->

Follow-up to `phase-3-handoff.md`. **Separate file rather than an appended section**, because that
one sits at 119 of the 120-line cap — appending anything to it turns the contract guard red. Its
`could-not-do` bullet about provenance is edited in place to point here and now describes code that
no longer exists in the sibling-file form.

## track

feature

## built

`src/nba_platform/landing.py` gains one keyword: `write_capture(provenance=...)`, a JSON-able mapping
landing under the manifest's `provenance` key. Nested, never merged, and specifically never folded
into `parameters` — that field is the wire parameter dict bronze reads, and trim metadata mixed into
it would be indistinguishable from something the endpoint was asked for. The key is **always
present**, holding `null` when there is none, so a consumer tells "this capture was never trimmed"
from "trimmed, and it happened to retain everything" (an object whose two counts are equal) without
having to know the key can be absent. `PROVENANCE_KEY` is exported so writer and reader resolve the
name instead of both spelling it. No existing manifest field was renamed, moved or removed.

One ordering change came with it: the manifest is now serialised **before** the payload handle opens,
so both documents are rendered before either is written. Previously a value that could not be
serialised would leave a payload on disk with no manifest beside it — an aborted capture — and
caller-supplied provenance is exactly the field that could do that. Now it fails with nothing landed.
Write-once is otherwise untouched: still two files, still `"xb"`, and `payload_sha256` still describes
the payload rather than the manifest.

`src/nba_platform/fixtures.py` passes trim provenance through that keyword and **no longer writes
`trim_provenance.json`**; the constant and the sibling write are gone. The nested document was
narrowed at the same time, to what the manifest does not already say one level up: `case`, `reason`,
`trim_rule`, `original_row_count`, `retained_row_count`, `game_ids`, `game_count`, `recapture`,
`edits`. Source, endpoint, season, grain, season type, capture stamp, `parameters`, request URL, HTTP
status, client and version were duplicated in the old sidecar and are dropped — two answers to one
question inside a single file is worse than a reader looking one level up. Step 9's remaining two
facts, request parameters and capture timestamp, are the manifest's own `parameters` and `captured_at`.

`FixtureCapture.provenance_path: Path | None` is replaced by `provenance: dict[str, Any] | None`,
holding the document that went into the manifest, or None when the capture was skipped. That is the
only API break; every other signature in the `phase-3-handoff.md` surface section still stands.

`record_error_case()` keeps its `<case>.provenance.json` sidecar — see `assumed`.

## verified

"proof" rows re-ran the same scratchpad script as phase 3, extended with the new assertions.

| Claim | Command and actual output |
|---|---|
| Lint, format, types | `uv run ruff check` -> `All checks passed!`; `uv run ruff format --check` -> `67 files already formatted`; `uv run mypy` -> `Success: no issues found in 15 source files` |
| Suite green | `uv run pytest -m "not network" --cov=nba_platform --cov-report=term-missing` -> `78 passed, 2 deselected in 0.92s`; `landing.py 114 stmts, 4 miss, 96%` |
| **Regression guard untouched and green** | `uv run pytest tests/test_landing_immutability.py -v` -> `6 passed in 0.23s` |
| Provenance is in the manifest | proof -> `manifest keys: [... 'parameters', 'payload_bytes', 'payload_filename', 'payload_sha256', 'provenance', 'request_url', 'row_count', ...]`; `provenance: {'case': '2019-20-bubble-restart', 'original_row_count': 18, 'retained_row_count': 12, 'game_ids': ['0021900001','0021900002']}` |
| Step 9's other facts sit one level up | proof -> `manifest parameters: {'Season': '2019-20'} captured_at: 2026-08-15T12:00:00+00:00`; `manifest row_count: 12` |
| Two files per capture, no third | proof -> `files in the capture dir: ['manifest.json', 'payload.json']`; `OUT.rglob("trim_provenance.json")` is empty |
| sha256 still describes the payload | proof -> recomputed `sha256(payload.json bytes)` equals `manifest["payload_sha256"]` (`931666ed3d2b...`) |
| Untrimmed capture reads cleanly | proof -> a plain `write_capture` with no provenance -> `untrimmed capture provenance: None`, key present |
| Nothing else regressed | proof -> whole-games, headers-untouched, name-not-ordinal, six raise paths, write-once skip, recapture-beside, single-cell edit and error-case placement all still `ALL PROOFS PASSED` |

## assumed

- **The error case keeps its sidecar.** It lands outside the partitioned tree and has no capture
  manifest to nest into — there is no `write_capture` call in that path at all. Its two files are
  `<case>.json` and `<case>.provenance.json`, and `_error_cases/` is never globbed by a source, so it
  does not widen the Phase 4 glob problem. Deleting it would leave the one fixture whose whole point
  is "captured, not hand-authored" with nothing recording that.
- Nesting an extra key is compatible with `tests/test_landing_immutability.py`'s required-key set,
  which is a subset check. Verified by running it, not by reading it alone.
- `dict(provenance)` is a shallow copy: nested values are shared with the caller's mapping. Fine for
  every current caller, which builds the document immediately before the call.

## surprised-me

- The old sidecar duplicated eleven fields the manifest already carried. Moving provenance inside the
  manifest did not just remove a file, it removed the duplication that a separate file invites — the
  sidecar had to repeat identity fields to stand alone, and nested it does not.
- Serialise-before-write was a latent bug the new keyword would have made reachable: the writer
  rendered the manifest inline at its own `open("xb")`, so the payload was already on disk by then.

## could-not-do

- **A committed test for the non-null provenance path.** `tests/` stays denied. Statement coverage on
  `landing.py` is unchanged at 96% because the ternary is one line, but only the `None` branch is
  exercised by the committed suite; the populated branch is proven solely by my scratch script.
  `tests/test_fixture_recorder.py` should assert both branches.
- Nothing else was blocked. Both target paths were inside this dispatch's allowlist.

## docs-delta

- No new data facts: still no request issued.
- Worth a line in ADR 0008 or wherever the capture shape is recorded: a manifest may now carry a
  nested `provenance` object, always present and `null` for a plain backfill capture. Proposed label
  `measured`. This is a contract a bronze model or an incident triage reader can rely on, so it
  should not live only in a module docstring.
- Memory is at 168 lines after three more entries — above the ~120 curation target, far below the 250
  ceiling, and appended freely per the budget section as it now reads. One of the three explicitly
  **supersedes** my earlier "write_capture cannot take extra fields" entry rather than deleting it.

## still-open

- The `phase-3-handoff.md` `api-surface` block still lists `FixtureCapture(... provenance_path ...)`.
  That one field name is now wrong there; the rest of the block is current. Flagging rather than
  rewriting a committed handoff.
- If a future caller wants provenance on a *backfill* capture (a trailing-window re-pull recording
  why it re-pulled, say), the keyword is already there and `backfill.py` need only pass it.
- Unchanged from phase 3: the bronze source glob must name `payload.json` explicitly. This change
  narrows that risk from three files per capture back to two, but does not remove it — `manifest.json`
  is still a sibling.
