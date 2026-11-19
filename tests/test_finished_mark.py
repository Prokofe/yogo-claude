"""The green dot means "finished, and you haven't looked yet"."""

from yogo import bus
from yogo import daemon as dmn


def done(ts, source="a"):
    return bus.Signal(source=source, state="done", ts=ts)


def test_input_after_the_dot_has_been_seen_clears_it():
    m = dmn.FinishedMark()
    turns = [done(0.0)]
    assert m.update(turns, now=10.0, idle=30.0, visible=True)
    assert not m.update(turns, now=14.0, idle=0.5, visible=True)
    assert not m.update(turns, now=60.0, idle=40.0, visible=True)


def test_waking_the_screen_does_not_count_as_seeing_it():
    m = dmn.FinishedMark()
    turns = [done(0.0)]
    assert m.update(turns, now=100.0, idle=0.2, visible=True)
    assert m.update(turns, now=102.0, idle=0.1, visible=True)


def test_input_while_the_dot_is_hidden_does_not_count():
    m = dmn.FinishedMark()
    turns = [done(0.0)]
    assert m.update(turns, now=10.0, idle=30.0, visible=False)
    assert m.update(turns, now=14.0, idle=0.1, visible=False)
    assert m.update(turns, now=15.0, idle=1.0, visible=True)


def test_hiding_restarts_the_clock():
    m = dmn.FinishedMark()
    turns = [done(0.0)]
    m.update(turns, now=10.0, idle=30.0, visible=True)
    m.hide()
    assert m.update(turns, now=50.0, idle=0.1, visible=True)


def test_a_new_finished_turn_gets_its_own_dot():
    m = dmn.FinishedMark()
    a = done(0.0, "a")
    m.update([a], now=10.0, idle=30.0, visible=True)
    assert not m.update([a], now=14.0, idle=0.1, visible=True)
    b = done(15.0, "b")
    assert m.update([a, b], now=21.0, idle=7.0, visible=True)


def test_unknown_idle_time_never_clears_it():
    m = dmn.FinishedMark()
    turns = [done(0.0)]
    m.update(turns, now=10.0, idle=None, visible=True)
    assert m.update(turns, now=100.0, idle=None, visible=True)


def test_no_finished_turn_no_dot():
    assert not dmn.FinishedMark().update([], now=1.0, idle=0.0, visible=True)
