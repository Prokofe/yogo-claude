import sys

import pytest

from yogo import presence


@pytest.fixture(autouse=True)
def fresh_clock():
    presence._idle_clock.cache_clear()
    yield
    presence._idle_clock.cache_clear()


def test_away_once_idle_reaches_the_threshold(monkeypatch):
    monkeypatch.setattr(presence, "seconds_since_input", lambda: 120.0)
    assert presence.away(120.0)
    assert presence.away(60.0)
    assert not presence.away(300.0)


def test_never_away_when_the_check_is_off(monkeypatch):
    monkeypatch.setattr(presence, "seconds_since_input", lambda: 86400.0)
    assert not presence.away(0)
    assert not presence.away(-1)


def test_unknown_idle_time_counts_as_present(monkeypatch):
    monkeypatch.setattr(presence, "seconds_since_input", lambda: None)
    assert not presence.away(1.0)


def test_no_idle_clock_off_macos(monkeypatch):
    monkeypatch.setattr(presence.sys, "platform", "linux")
    assert presence.seconds_since_input() is None


@pytest.mark.skipif(sys.platform != "darwin", reason="CoreGraphics is macOS only")
def test_idle_clock_reads_on_macos():
    idle = presence.seconds_since_input()
    assert idle is not None and idle >= 0.0
