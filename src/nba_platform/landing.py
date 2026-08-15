"""The write-once landing-zone writer — the module that makes immutability executable.

Everything this package writes under the landing root goes through here, and nothing here
ever opens an existing file for writing. That is enforced structurally rather than by
convention: a capture directory is claimed with an exclusive `mkdir` and its two files are
opened in exclusive-create binary mode (`"xb"`), so an overwrite raises instead of
succeeding quietly. If the bytes already exist, this module cannot touch them.

**Why immutability, in one line each.** Bronze that disagrees with the landed JSON is wrong
and can be diffed against a fresh pull; history replays without re-hitting a rate-limited
API; and a backfill that died at call four resumes at call four.

**Skip-if-present IS the checkpoint.** At six calls for the pilot there is no checkpoint
store, and building one would be inventing state that the filesystem already holds:
`write_capture` looks for a completed capture under the
(source, endpoint, season, grain, season_type) prefix and, finding one, writes nothing and
reports the skip. A deliberate re-pull passes `recapture=True`, which writes a **new**
`capture=<stamp>/` directory *beside* the first and never touches it. That is how an
immutable landing zone and after-the-fact stat corrections coexist.

**A capture is complete when its manifest exists.** The payload is written first and the
manifest second, so a capture directory holding `payload.json` and no `manifest.json` is an
aborted write. It is not counted as present — the next run lands a fresh capture beside it.
Removing the orphan is a human action: nothing in this package deletes from the landing
zone.

**The path never spells anything.** The landing root and the key shape both come from the
config layer (`get_settings().landing_root`, `landing_key(...)`), so relocating the zone or
changing the partition shape is a config change and this module does not notice.

**Second-resolution stamps can collide.** The capture stamp is colon-free compact UTC
because a colon is illegal in a Windows path, which leaves it one-second resolution — and a
`--recapture` run seconds after the first would render the same directory name. Rather than
overwrite (forbidden) or fail (useless), the reservation loop advances the *stamp* by a
second until a free directory is claimed. The manifest records the true `captured_at`
alongside the possibly-advanced `capture` segment, so the two never silently disagree.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

from nba_platform.config import CAPTURE_STAMP_FORMAT, get_settings, landing_key

__all__ = [
    "MANIFEST_FILENAME",
    "MANIFEST_VERSION",
    "PAYLOAD_FILENAME",
    "RUNS_DIRNAME",
    "RUN_MANIFEST_FILENAME",
    "CaptureResult",
    "LandingError",
    "Partition",
    "existing_capture_result",
    "existing_captures",
    "partition_dir",
    "row_count",
    "write_capture",
    "write_run_manifest",
]


class LandingError(RuntimeError):
    """The landing zone refused a write, or could not claim a directory to write into."""


PAYLOAD_FILENAME: Final = "payload.json"
MANIFEST_FILENAME: Final = "manifest.json"
MANIFEST_VERSION: Final = 1

# Run manifests are audit records of a run, not landed data. The leading underscore marks
# the directory as "not a landing partition": the bronze source globs
# `<source>/<endpoint>/season=*/...`, so nothing here is ever picked up by a model.
RUNS_DIRNAME: Final = "_runs"
RUN_MANIFEST_FILENAME: Final = "run_manifest.json"
RUN_DIR_PREFIX: Final = "run="

# Where the row count lives inside the endpoint's envelope. Read defensively: an error body
# has neither key, and a capture of one should still land with a row count of zero rather
# than raising inside the writer.
RESULT_SETS_KEY: Final = "resultSets"
ROW_SET_KEY: Final = "rowSet"

# One second is the resolution of the capture stamp, so it is also the collision stride.
STAMP_STRIDE: Final = timedelta(seconds=1)
MAX_STAMP_ADVANCES: Final = 120

# Only ever used to render a *partition* prefix, whose capture segment is discarded. The
# value is irrelevant; what matters is that config stays the single owner of the key shape,
# so this module never spells one itself.
_PREFIX_STAMP_ANCHOR: Final = datetime(1970, 1, 1, tzinfo=UTC)

_ENCODING: Final = "utf-8"


@dataclass(frozen=True, slots=True)
class Partition:
    """The five components that identify one landing partition, before any capture of it."""

    source: str
    endpoint: str
    season: str
    grain: str
    season_type: str


@dataclass(frozen=True, slots=True)
class CaptureResult:
    """What one `write_capture` call did.

    When `written` is False the capture was skipped because a completed one already existed:
    `capture_dir` then points at that pre-existing capture and the write-only facts
    (`sha256`, `row_count`, `payload_bytes`) are None, because this call did not compute
    them and will not read someone else's manifest to invent them.
    """

    partition: Partition
    capture_dir: Path
    payload_path: Path
    manifest_path: Path
    written: bool
    captured_at: datetime | None = None
    sha256: str | None = None
    row_count: int | None = None
    payload_bytes: int | None = None


def row_count(payload: Mapping[str, Any]) -> int:
    """Rows in the envelope's first result set, or 0 if it has none to count."""
    result_sets = payload.get(RESULT_SETS_KEY)
    if not isinstance(result_sets, list) or not result_sets:
        return 0
    first = result_sets[0]
    if not isinstance(first, Mapping):
        return 0
    rows = first.get(ROW_SET_KEY)
    return len(rows) if isinstance(rows, list) else 0


def _resolve_landing_root(landing_root: Path | None) -> Path:
    return get_settings().landing_root if landing_root is None else landing_root


def partition_dir(partition: Partition, *, landing_root: Path | None = None) -> Path:
    """The directory holding every capture of one partition.

    Rendered by asking the config layer for a full landing key and dropping its capture
    segment, so the key shape has exactly one owner and this module has no opinion on it.
    """
    key = landing_key(
        source=partition.source,
        endpoint=partition.endpoint,
        season=partition.season,
        grain=partition.grain,
        season_type=partition.season_type,
        captured_at=_PREFIX_STAMP_ANCHOR,
    )
    return (_resolve_landing_root(landing_root) / key).parent


def existing_captures(
    partition: Partition, *, landing_root: Path | None = None
) -> tuple[Path, ...]:
    """Completed captures of `partition`, oldest first — the checkpoint, read from disk.

    Completed means the manifest is present. The capture stamp is fixed-width compact UTC,
    so sorting the directory names lexicographically sorts them chronologically.
    """
    directory = partition_dir(partition, landing_root=landing_root)
    if not directory.is_dir():
        return ()
    captures = [
        candidate
        for candidate in directory.iterdir()
        if candidate.is_dir() and (candidate / MANIFEST_FILENAME).is_file()
    ]
    return tuple(sorted(captures, key=lambda candidate: candidate.name))


def existing_capture_result(
    partition: Partition, *, landing_root: Path | None = None
) -> CaptureResult | None:
    """The skip result for `partition`, or None if nothing complete has been landed yet.

    Called by the backfill *before* it issues a request — the skip has to save the API call,
    not merely the write — and by `write_capture` itself, so the two cannot answer the same
    question differently.
    """
    already = existing_captures(partition, landing_root=landing_root)
    if not already:
        return None
    newest = already[-1]
    return CaptureResult(
        partition=partition,
        capture_dir=newest,
        payload_path=newest / PAYLOAD_FILENAME,
        manifest_path=newest / MANIFEST_FILENAME,
        written=False,
    )


def _serialize(document: Any) -> bytes:
    """UTF-8 bytes for one JSON document, compact and newline-terminated.

    Serialised here rather than written through a text handle on purpose: bytes are what
    gets hashed and what gets written, so the manifest's sha256 describes the file exactly,
    and no platform newline translation can get between the two.
    """
    text = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
    return f"{text}\n".encode(_ENCODING)


def _reserve(render: Callable[[datetime], Path], stamp_at: datetime) -> tuple[Path, datetime]:
    """Claim the first free directory `render` produces, advancing the stamp on collision.

    `mkdir(exist_ok=False)` is the claim: it either creates the directory or tells us
    someone already holds it. Nothing is ever overwritten to make room.
    """
    at = stamp_at
    for _ in range(MAX_STAMP_ADVANCES):
        candidate = render(at)
        try:
            candidate.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            at += STAMP_STRIDE
            continue
        return candidate, at
    raise LandingError(
        f"Could not claim a free directory near {render(stamp_at)} within "
        f"{MAX_STAMP_ADVANCES} one-second steps. Nothing was overwritten; inspect the "
        "landing zone by hand."
    )


def write_capture(
    *,
    partition: Partition,
    payload: Mapping[str, Any],
    captured_at: datetime,
    parameters: Mapping[str, str] | None = None,
    status_code: int | None = None,
    elapsed_seconds: float = 0.0,
    request_url: str | None = None,
    client_name: str = "",
    client_version: str = "",
    landing_root: Path | None = None,
    recapture: bool = False,
) -> CaptureResult:
    """Land one raw response, exactly once, with a manifest beside it.

    Returns a skipped `CaptureResult` when a completed capture of `partition` already
    exists and `recapture` is False. With `recapture=True` a new capture directory is
    written beside the existing ones and no existing byte is read, moved or changed.
    """
    root = _resolve_landing_root(landing_root)
    if not recapture:
        skipped = existing_capture_result(partition, landing_root=root)
        if skipped is not None:
            return skipped

    def render(at: datetime) -> Path:
        return root / landing_key(
            source=partition.source,
            endpoint=partition.endpoint,
            season=partition.season,
            grain=partition.grain,
            season_type=partition.season_type,
            captured_at=at,
        )

    payload_data = _serialize(payload)
    rows = row_count(payload)
    digest = hashlib.sha256(payload_data).hexdigest()

    capture_dir, _ = _reserve(render, captured_at)
    payload_path = capture_dir / PAYLOAD_FILENAME
    manifest_path = capture_dir / MANIFEST_FILENAME

    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "source": partition.source,
        "endpoint": partition.endpoint,
        "season": partition.season,
        "grain": partition.grain,
        "season_type": partition.season_type,
        "capture": capture_dir.name,
        "landing_key": capture_dir.relative_to(root).as_posix(),
        "captured_at": captured_at.astimezone(UTC).isoformat(),
        "parameters": dict(parameters or {}),
        "request_url": request_url,
        "http_status": status_code,
        "row_count": rows,
        "payload_filename": PAYLOAD_FILENAME,
        "payload_bytes": len(payload_data),
        "payload_sha256": digest,
        "client": client_name,
        "client_version": client_version,
        "elapsed_seconds": elapsed_seconds,
    }

    # Exclusive-create, binary: an existing file raises FileExistsError rather than being
    # truncated. Payload first, manifest last — the manifest is the completeness marker.
    with payload_path.open("xb") as handle:
        handle.write(payload_data)
    with manifest_path.open("xb") as handle:
        handle.write(_serialize(manifest))

    return CaptureResult(
        partition=partition,
        capture_dir=capture_dir,
        payload_path=payload_path,
        manifest_path=manifest_path,
        written=True,
        captured_at=captured_at,
        sha256=digest,
        row_count=rows,
        payload_bytes=len(payload_data),
    )


def write_run_manifest(
    manifest: Mapping[str, Any],
    *,
    started_at: datetime,
    landing_root: Path | None = None,
) -> Path:
    """Record one run's measured cost under `_runs/run=<stamp>/`, write-once like a capture.

    Deliberately *not* a landing partition: the bronze source glob never reaches it, and a
    run that landed nothing writes nothing here — a run with no measured cost has no cost
    to record, and inventing a file would break the byte-for-byte re-run comparison that
    proves the landing zone immutable.
    """
    root = _resolve_landing_root(landing_root)
    runs_root = root / RUNS_DIRNAME

    def render(at: datetime) -> Path:
        stamp = at.astimezone(UTC).strftime(CAPTURE_STAMP_FORMAT)
        return runs_root / f"{RUN_DIR_PREFIX}{stamp}"

    run_dir, _ = _reserve(render, started_at)
    path = run_dir / RUN_MANIFEST_FILENAME
    with path.open("xb") as handle:
        handle.write(_serialize(manifest))
    return path
