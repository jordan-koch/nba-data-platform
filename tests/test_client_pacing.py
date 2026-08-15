"""Acceptance criterion 17 — pacing and exponential backoff, proven against a stubbed clock.

`stats.nba.com` blocks impolite clients rather than throttling them, and a block is hard to
tell apart from a transient failure. So the minimum inter-request gap and the retry ceiling
are the two values most worth proving, and proving them by *waiting* would make the suite
take minutes. Every test here drives an injected clock and sleeper instead: `FakeClock.sleep`
advances the clock it hands back, so a 9.6-second backoff costs nothing and is still
observable.

Both values are set through the **environment** rather than passed in, because that is what
makes them config-driven rather than literal. A client that captured its delay at import
time, or spelled `0.6` inline, passes none of these.
"""

from __future__ import annotations

from typing import Any

import pytest

from nba_platform.client import BACKOFF_FACTOR, ClientError, GameLogClient, RawResponse

DELAY = 0.25
PAYLOAD: dict[str, Any] = {
    "resource": "leaguegamelog",
    "resultSets": [{"name": "LeagueGameLog", "headers": ["GAME_ID"], "rowSet": [["0020300001"]]}],
}


class FakeClock:
    """A monotonic clock that only moves when something sleeps.

    That coupling is the whole trick: the client's pacing is `sleep(remaining)` followed by a
    clock reading, so a sleeper that advances the clock makes the resulting gap observable
    without any real time passing.
    """

    def __init__(self) -> None:
        self.now = 0.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


class RecordingTransport:
    """A transport that answers with a canned envelope and counts what it was asked."""

    def __init__(self, *, status_code: int | None = 200) -> None:
        self.calls: list[dict[str, str]] = []
        self.status_code = status_code

    def __call__(self, request_parameters: Any) -> RawResponse:
        self.calls.append(dict(request_parameters))
        return RawResponse(payload=PAYLOAD, status_code=self.status_code)


class FailingTransport:
    """Fails `failures` times, then succeeds — or forever, when `failures` is None."""

    def __init__(self, *, failures: int | None) -> None:
        self.failures = failures
        self.attempts = 0

    def __call__(self, request_parameters: Any) -> RawResponse:
        self.attempts += 1
        if self.failures is None or self.attempts <= self.failures:
            raise ConnectionError(f"simulated transport failure {self.attempts}")
        return RawResponse(payload=PAYLOAD, status_code=200)


@pytest.fixture
def paced_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """A known delay and retry ceiling, set by name so a literal in the client would fail."""
    monkeypatch.setenv("NBA_ENV", "local")
    monkeypatch.setenv("NBA_REQUEST_DELAY_SECONDS", str(DELAY))
    monkeypatch.setenv("NBA_MAX_RETRIES", "5")
    return monkeypatch


def _fetch(client: GameLogClient, season: str = "2003-04") -> Any:
    return client.fetch(season=season, grain="player", season_type="regular")


# ─── Pacing ───────────────────────────────────────────────────────────────────────────


def test_sequential_calls_are_never_faster_than_the_configured_delay(
    paced_env: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    transport = RecordingTransport()
    client = GameLogClient(transport=transport, clock=clock, sleep=clock.sleep)

    for _ in range(4):
        _fetch(client)

    assert transport.calls and len(transport.calls) == 4
    assert client.request_count == 4
    spacing = client.observed_spacing_seconds
    assert len(spacing) == 3, "three gaps between four calls"
    assert all(gap >= DELAY for gap in spacing), f"a gap fell under the floor: {spacing}"


def test_the_first_call_waits_for_nothing(paced_env: pytest.MonkeyPatch) -> None:
    """Pacing is a floor between calls, not a startup tax — a one-call run sleeps zero."""
    clock = FakeClock()
    client = GameLogClient(transport=RecordingTransport(), clock=clock, sleep=clock.sleep)

    _fetch(client)

    assert clock.slept == []
    assert client.observed_spacing_seconds == ()


def test_the_delay_is_reread_from_the_environment_on_every_call(
    paced_env: pytest.MonkeyPatch,
) -> None:
    """Raising the delay mid-run changes the very next gap.

    This is the test a client that captured its settings at construction time fails, and it
    is why `fetch()` calls `get_settings()` rather than holding a `Settings`.
    """
    clock = FakeClock()
    client = GameLogClient(transport=RecordingTransport(), clock=clock, sleep=clock.sleep)

    _fetch(client)
    _fetch(client)
    assert client.observed_spacing_seconds[-1] == pytest.approx(DELAY)

    paced_env.setenv("NBA_REQUEST_DELAY_SECONDS", str(DELAY * 6))
    _fetch(client)

    assert client.observed_spacing_seconds[-1] == pytest.approx(DELAY * 6)


# ─── Backoff ──────────────────────────────────────────────────────────────────────────


def test_a_failure_backs_off_exponentially_up_to_the_retry_ceiling(
    paced_env: pytest.MonkeyPatch,
) -> None:
    """max_retries=3 means four attempts and three sleeps, each double the last."""
    paced_env.setenv("NBA_MAX_RETRIES", "3")
    clock = FakeClock()
    transport = FailingTransport(failures=None)
    client = GameLogClient(transport=transport, clock=clock, sleep=clock.sleep)

    with pytest.raises(ClientError, match="4 attempt"):
        _fetch(client)

    assert transport.attempts == 4, "one attempt plus three retries"
    expected = [DELAY * BACKOFF_FACTOR**index for index in range(3)]
    assert clock.slept == pytest.approx(expected)
    # Doubling, stated independently of the formula above so a sign error is visible.
    assert clock.slept == pytest.approx([0.25, 0.5, 1.0])


def test_the_retry_ceiling_is_reread_from_the_environment(
    paced_env: pytest.MonkeyPatch,
) -> None:
    """max_retries=0 means exactly one attempt and no backoff sleep at all."""
    paced_env.setenv("NBA_MAX_RETRIES", "0")
    clock = FakeClock()
    transport = FailingTransport(failures=None)
    client = GameLogClient(transport=transport, clock=clock, sleep=clock.sleep)

    with pytest.raises(ClientError, match="1 attempt"):
        _fetch(client)

    assert transport.attempts == 1
    assert clock.slept == []


def test_a_transient_failure_recovers_without_exhausting_the_ceiling(
    paced_env: pytest.MonkeyPatch,
) -> None:
    clock = FakeClock()
    transport = FailingTransport(failures=2)
    client = GameLogClient(transport=transport, clock=clock, sleep=clock.sleep)

    response = _fetch(client)

    assert transport.attempts == 3
    assert response.attempts == 3
    assert response.payload == PAYLOAD
    assert clock.slept == pytest.approx([DELAY, DELAY * 2])


def test_an_http_error_status_is_retried_rather_than_returned(
    paced_env: pytest.MonkeyPatch,
) -> None:
    """A 429 or a 5xx is a failed attempt, not a payload — landing one would land garbage."""
    paced_env.setenv("NBA_MAX_RETRIES", "2")
    clock = FakeClock()
    transport = RecordingTransport(status_code=429)
    client = GameLogClient(transport=transport, clock=clock, sleep=clock.sleep)

    with pytest.raises(ClientError, match="429"):
        _fetch(client)

    assert len(transport.calls) == 3, "one attempt plus two retries"


def test_backoff_sleeps_already_satisfy_the_pacing_floor(
    paced_env: pytest.MonkeyPatch,
) -> None:
    """A retry must never be issued faster than the pacing floor either.

    The two mechanisms compose rather than stack: every backoff is at least one delay long,
    so the gap is already paid when the retry goes out. If they stacked, the observed gap
    would exceed the backoff and a long outage would sleep for far longer than intended.
    """
    paced_env.setenv("NBA_MAX_RETRIES", "3")
    clock = FakeClock()
    client = GameLogClient(
        transport=FailingTransport(failures=None), clock=clock, sleep=clock.sleep
    )

    with pytest.raises(ClientError):
        _fetch(client)

    spacing = client.observed_spacing_seconds
    assert all(gap >= DELAY for gap in spacing), spacing
    assert spacing == pytest.approx([DELAY, DELAY * 2, DELAY * 4]), (
        "gaps should equal the backoff exactly — anything larger means pacing stacked on top"
    )


def test_an_unknown_grain_fails_before_anything_is_issued(
    paced_env: pytest.MonkeyPatch,
) -> None:
    """The grain is a landing-key component, so a bad one must not cost a request."""
    clock = FakeClock()
    transport = RecordingTransport()
    client = GameLogClient(transport=transport, clock=clock, sleep=clock.sleep)

    with pytest.raises(ClientError, match="grain"):
        client.fetch(season="2003-04", grain="referee", season_type="regular")

    assert transport.calls == []
    assert client.request_count == 0
