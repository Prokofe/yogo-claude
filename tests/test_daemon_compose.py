"""What the daemon draws for a state, including the finished-turn mark."""

from yogo import daemon as dmn


def marked(frame):
    return frame[dmn.FINISHED_DOT] == dmn.FINISHED_GREEN


def test_mark_stays_on_top_of_another_sessions_work():
    for state in ("thinking", "tool", "waiting", "error"):
        assert marked(dmn.compose(state, 1.0, "breathe", finished=True)), state


def test_mark_shows_on_every_idle_look():
    for style in ("breathe", "off", "firmware"):
        assert marked(dmn.compose("idle", 1.0, style, finished=True)), style


def test_mark_waits_for_the_done_animation():
    assert not marked(dmn.compose("done", 6.0, "breathe", finished=True))


def test_no_mark_without_a_finished_turn():
    assert not marked(dmn.compose("thinking", 1.0, "breathe", finished=False))
    assert not marked(dmn.compose("idle", 1.0, "breathe", finished=False))


def test_firmware_idle_hands_the_screen_back_only_without_a_mark():
    assert dmn.compose("idle", 1.0, "firmware", finished=False) is None
