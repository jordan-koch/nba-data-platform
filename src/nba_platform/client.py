"""The paced, retrying `stats.nba.com` client — this package's one untyped boundary.

Every `nba_api` import in the repo lives in this module, inside the transport function at
the bottom of it. That import is deliberately *local*: importing `nba_platform.client`
must stay free of `nba_api` (and of the pandas it drags in), so a `--dry-run` that issues
no request pays for no transport, and an offline test can inject its own transport without
the real client library ever loading. The scoped `[[tool.mypy.overrides]]` block in
`pyproject.toml` names `nba_api.*` and `pandas.*` for this module and no other — if
`landing.py` or `backfill.py` ever imports either, that one declared boundary has leaked.

**Pacing is not a tuning knob.** `stats.nba.com` blocks impolite clients rather than
throttling them, and a block is hard to tell apart from a transient failure. The minimum
inter-request gap and the retry ceiling are read from `get_settings()` **on every call** —
never captured at import time, never spelled as a literal here — so an operator changes
them by name through the environment and a test can prove they are config-driven.

Retry shape, stated once so nothing has to infer it: a call makes at most
``max_retries + 1`` attempts, and the sleep after the *i*-th failure (0-based) is
``request_delay_seconds * BACKOFF_FACTOR**i``. With the defaults that is one attempt plus
five retries, sleeping 0.6s, 1.2s, 2.4s, 4.8s, 9.6s. `max_retries = 0` means one attempt
and no retry. The pacing gap and the backoff sleep compose safely: every backoff is at
least one delay long, so the gap is already satisfied when the retry is issued.

**Raw in, raw out.** `fetch()` returns the endpoint's own JSON envelope
(`resource` / `parameters` / `resultSets`) and never a `get_data_frames()` round-trip: a
pandas re-serialisation would mean the "immutable raw" landing zone is not raw, and would
weaken the diff-against-raw invariant bronze rests on. The honest limit, recorded rather
than glossed — `nba_api` hands the body back already parsed
(`NBAResponse.get_dict()` is `json.loads` over the response text), so what lands is a
re-serialisation of the parsed body, not the literal wire bytes.

Injection seams. All of them are constructor parameters, never module-level globals a test
has to monkeypatch:

| seam | type | default |
|---|---|---|
| `transport` | `Callable[[Mapping[str, str]], RawResponse]` | `nba_api_transport` |
| `clock` | `Callable[[], float]` | `time.monotonic` |
| `sleep` | `Callable[[float], None]` | `time.sleep` |
| `environ` | mapping or `None` | the live process environment |
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib import metadata
from types import MappingProxyType
from typing import Any, Final

from nba_platform.config import get_settings

__all__ = [
    "BACKOFF_FACTOR",
    "CLIENT_NAME",
    "DEFAULT_GRAINS",
    "DEFAULT_SEASON_TYPE",
    "ENDPOINT_NAME",
    "GRAIN_ABBREVIATIONS",
    "HTTP_ERROR_THRESHOLD",
    "LEAGUE_ID_NBA",
    "SEASON_TYPES",
    "SOURCE_NAME",
    "ClientError",
    "GameLogClient",
    "GameLogResponse",
    "RawResponse",
    "client_version",
    "nba_api_transport",
    "request_kwargs",
]


class ClientError(RuntimeError):
    """A request could not be completed within the configured retry ceiling."""


# ─── Names, all resolved by name downstream rather than re-spelled ────────────────────
# SOURCE_NAME and ENDPOINT_NAME are *landing-key components*, not wire values: the wire
# endpoint is nba_api's own "leaguegamelog". Keeping the two apart is what lets the landing
# layout stay stable if the upstream route is renamed.
SOURCE_NAME: Final = "nba_stats"
ENDPOINT_NAME: Final = "league_game_log"

CLIENT_NAME: Final = "nba_api"
UNKNOWN_VERSION: Final = "unknown"
LEAGUE_ID_NBA: Final = "00"

# The grain vocabulary is this repo's ("player"/"team", as they appear in the landing key);
# the values are what the endpoint's PlayerOrTeam parameter expects.
GRAIN_ABBREVIATIONS: Final[Mapping[str, str]] = MappingProxyType({"player": "P", "team": "T"})
DEFAULT_GRAINS: Final[tuple[str, ...]] = ("player", "team")

# Likewise: the keys are landing-key components, the values are the endpoint's own strings.
# Playoffs are extracted in a later phase; the mapping carries the key now so they arrive
# as rows rather than as a migration.
SEASON_TYPES: Final[Mapping[str, str]] = MappingProxyType(
    {"regular": "Regular Season", "playoffs": "Playoffs"}
)
DEFAULT_SEASON_TYPE: Final = "regular"

# The base of the exponent, not a delay: every actual duration is config-derived.
BACKOFF_FACTOR: Final = 2.0

# Any status at or above this is treated as a failed attempt and retried with backoff. A
# block from this source is not obviously distinguishable from a transient failure, so
# backing off politely is the correct response to both.
HTTP_ERROR_THRESHOLD: Final = 400

# MEASURED 2026-08-15 by reading the installed nba_api 1.11.4 source: `NBAResponse` stores
# the HTTP status on this private attribute and exposes NO public accessor for it
# (`get_response`, `get_dict`, `get_json`, `valid_json`, `get_url` are the whole surface).
# The capture manifest wants the status, so it is read defensively by name here and degrades
# to None rather than raising if a future release renames it.
STATUS_CODE_ATTRIBUTE: Final = "_status_code"


def client_version() -> str:
    """The installed `nba_api` version, for the capture manifest's provenance field."""
    try:
        return metadata.version(CLIENT_NAME)
    except metadata.PackageNotFoundError:
        return UNKNOWN_VERSION


@dataclass(frozen=True, slots=True)
class RawResponse:
    """What a transport hands back: the parsed envelope plus what the wire said about it.

    `parameters` is the *wire* parameter dict as the endpoint object recorded it, which is
    richer than the kwargs the client sent (it includes the values nba_api defaulted). A
    stubbed transport may leave it empty; the client then falls back to the kwargs it sent,
    so the manifest always records a full parameter dict either way.
    """

    payload: Mapping[str, Any]
    status_code: int | None = None
    parameters: Mapping[str, str] = field(default_factory=dict)
    request_url: str | None = None


@dataclass(frozen=True, slots=True)
class GameLogResponse:
    """One successful `leaguegamelog` call, ready to be landed verbatim.

    Everything but `season`, `grain`, `season_type` and `payload` carries a default, so a
    test stub can build one in a line without pretending to know an elapsed time or a
    status code it never had.
    """

    season: str
    grain: str
    season_type: str
    payload: Mapping[str, Any]
    parameters: Mapping[str, str] = field(default_factory=dict)
    status_code: int | None = None
    request_url: str | None = None
    elapsed_seconds: float = 0.0
    attempts: int = 1
    client_version: str = field(default_factory=client_version)


Clock = Callable[[], float]
Sleeper = Callable[[float], None]
Transport = Callable[[Mapping[str, str]], RawResponse]


def request_kwargs(*, season: str, grain: str, season_type: str) -> dict[str, str]:
    """The exact keyword arguments one `LeagueGameLog` construction takes.

    Built here rather than inside the transport so the planned request is inspectable
    without a network call, and so an unknown grain or season type fails before any
    request is paced, let alone issued.
    """
    abbreviation = GRAIN_ABBREVIATIONS.get(grain)
    if abbreviation is None:
        raise ClientError(
            f"grain={grain!r} is not one of {sorted(GRAIN_ABBREVIATIONS)}. The grain is a "
            "landing-key component, so an unknown one would land rows under a partition "
            "nothing reads."
        )
    endpoint_season_type = SEASON_TYPES.get(season_type)
    if endpoint_season_type is None:
        raise ClientError(
            f"season_type={season_type!r} is not one of {sorted(SEASON_TYPES)}. The endpoint "
            "takes its own spelling verbatim and returns an empty result set for anything else."
        )
    return {
        "league_id": LEAGUE_ID_NBA,
        "season": season,
        "season_type_all_star": endpoint_season_type,
        "player_or_team_abbreviation": abbreviation,
        "direction": "ASC",
        "sorter": "DATE",
        "date_from_nullable": "",
        "date_to_nullable": "",
    }


class GameLogClient:
    """A politely paced, exponentially backing-off wrapper over one bulk endpoint.

    The client owns pacing state (when it last issued a request) but owns no settings: it
    re-reads `get_settings()` inside every `fetch()` so the delay and the retry ceiling are
    whatever the environment says at that moment.
    """

    def __init__(
        self,
        *,
        transport: Transport | None = None,
        clock: Clock = time.monotonic,
        sleep: Sleeper = time.sleep,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self._transport: Transport = nba_api_transport if transport is None else transport
        self._clock: Clock = clock
        self._sleep: Sleeper = sleep
        self._environ = environ
        self._issued_at: list[float] = []
        self._last_issued: float | None = None

    @property
    def issued_at(self) -> tuple[float, ...]:
        """Clock readings at the moment each attempt was issued, oldest first."""
        return tuple(self._issued_at)

    @property
    def request_count(self) -> int:
        """Attempts issued over this client's lifetime, retries included."""
        return len(self._issued_at)

    @property
    def observed_spacing_seconds(self) -> tuple[float, ...]:
        """Gaps between consecutive issued attempts — the measured half of AC 17."""
        return tuple(
            later - earlier
            for earlier, later in zip(self._issued_at, self._issued_at[1:], strict=False)
        )

    def fetch(self, *, season: str, grain: str, season_type: str) -> GameLogResponse:
        """One season-grain call: paced, retried, and returned as its raw envelope."""
        settings = get_settings(self._environ)
        kwargs = request_kwargs(season=season, grain=grain, season_type=season_type)
        total_attempts = settings.max_retries + 1
        last_error: Exception | None = None

        for attempt in range(total_attempts):
            self._wait_for_slot(settings.request_delay_seconds)
            issued_at = self._clock()
            self._issued_at.append(issued_at)
            self._last_issued = issued_at
            try:
                raw = self._transport(kwargs)
            except Exception as exc:
                last_error = exc
            else:
                if raw.status_code is not None and raw.status_code >= HTTP_ERROR_THRESHOLD:
                    last_error = ClientError(
                        f"{ENDPOINT_NAME} answered HTTP {raw.status_code} for "
                        f"season={season!r} grain={grain!r}"
                    )
                else:
                    return GameLogResponse(
                        season=season,
                        grain=grain,
                        season_type=season_type,
                        payload=raw.payload,
                        parameters=dict(raw.parameters) if raw.parameters else dict(kwargs),
                        status_code=raw.status_code,
                        request_url=raw.request_url,
                        elapsed_seconds=self._clock() - issued_at,
                        attempts=attempt + 1,
                        client_version=client_version(),
                    )
            if attempt < total_attempts - 1:
                self._sleep(settings.request_delay_seconds * BACKOFF_FACTOR**attempt)

        raise ClientError(
            f"{ENDPOINT_NAME} failed after {total_attempts} attempt(s) for "
            f"season={season!r} grain={grain!r}, retry ceiling {settings.max_retries}: "
            f"{last_error!r}"
        ) from last_error

    def _wait_for_slot(self, delay_seconds: float) -> None:
        """Sleep off whatever is left of the minimum gap since the last issued attempt."""
        if self._last_issued is None:
            return
        remaining = delay_seconds - (self._clock() - self._last_issued)
        if remaining > 0:
            self._sleep(remaining)


def nba_api_transport(request_parameters: Mapping[str, str]) -> RawResponse:
    """Issue one live `leaguegamelog` request. **The only line in this repo that hits the API.**

    `get_request=False` at construction is load-bearing: `LeagueGameLog.__init__` defaults
    it to True and performs the HTTP call as a *side effect of constructing the object*, so
    the network moment would otherwise be invisible. Split apart, it is the one named
    `endpoint.get_request()` line below.

    Known limit, recorded rather than worked around: `get_request()` also runs
    `load_response()`, which indexes the envelope's `LeagueGameLog` result set. An error or
    empty body therefore raises here instead of being returned — so this transport retries
    it and ultimately fails, and it cannot be used to *land* an error response. Capturing an
    error body for the fixture corpus needs the lower-level `NBAStatsHTTP.send_api_request`.
    """
    from nba_api.stats.endpoints import leaguegamelog

    endpoint = leaguegamelog.LeagueGameLog(**request_parameters, get_request=False)
    endpoint.get_request()

    payload: dict[str, Any] = endpoint.get_dict()
    raw_status = getattr(endpoint.nba_response, STATUS_CODE_ATTRIBUTE, None)
    url = endpoint.get_request_url()
    parameters = {str(key): str(value) for key, value in endpoint.parameters.items()}

    return RawResponse(
        payload=payload,
        status_code=raw_status if isinstance(raw_status, int) else None,
        parameters=parameters,
        request_url=str(url) if url else None,
    )
