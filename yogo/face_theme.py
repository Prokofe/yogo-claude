"""Robot-face theme: glowing eyes on a dark screen, one expression per state.

Uses the warm clay / peach / cream palette from claude_theme. Select with
YOGO_THEME=face (default), claude (comet rings) or classic (original).

Grid is 6x6, f[x, y] with x = column, y = row, origin top-left.
"""

from __future__ import annotations

import math

from .claude_theme import CLAY, CREAM, ERR, PEACH, _dim, _mix
from .font import lit_indices
from .frame import Frame


def _put(f, cells, color):
    for x, y in cells:
        if 0 <= x < 6 and 0 <= y < 6:
            f[x, y] = color
    return f


def _blinking(t, period=3.2, length=0.16):
    return (t % period) > period - length


# --- expressions ---------------------------------------------------------
def _eyes_open(dx=0, top=1):
    """Two 1x2 eyes, columns 1 and 4, shifted by gaze dx."""
    return [(1 + dx, top), (1 + dx, top + 1), (4 + dx, top), (4 + dx, top + 1)]


def _eyes_closed(row=2):
    return [(0, row), (1, row), (4, row), (5, row)]


def _happy_eyes(top=2):
    """^^ - two 3-wide carets, peaks on row `top`."""
    return [(1, top), (0, top + 1), (2, top + 1),
            (4, top), (3, top + 1), (5, top + 1)]


def _smile(top=4):
    """A wide grin, corners on row `top`."""
    return [(0, top), (5, top), (1, top + 1), (2, top + 1), (3, top + 1), (4, top + 1)]


CHECK = [(0, 2), (1, 3), (2, 4), (3, 3), (4, 2), (5, 1)]               # ✓, drawing order
X_EYES = [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2),
          (3, 0), (5, 0), (4, 1), (3, 2), (5, 2)]                      # x x
FROWN = [(1, 5), (2, 4), (3, 4), (4, 5)]
QUESTION = lit_indices("?")


def render_idle(t: float, style: str = "off") -> Frame:
    if style == "off":
        return Frame()
    v = 0.10 + 0.12 * (0.5 + 0.5 * math.sin(t * 1.1))     # asleep, breathing
    return _put(Frame(), _eyes_closed(row=3), _dim(CLAY, v))


def render_thinking(t: float) -> Frame:
    # eyes glance around, "..." ripples along the mouth line
    gaze = (0, -1, 0, 1)[int(t / 0.7) % 4]
    f = Frame()
    if _blinking(t):
        _put(f, [(1 + gaze, 2), (4 + gaze, 2)], CLAY)
    else:
        _put(f, _eyes_open(gaze), CLAY)
    for i, x in enumerate((1, 2, 3, 4)):
        v = 0.15 + 0.85 * max(0.0, math.sin(t * 5.0 - i * 0.9)) ** 3
        f[x, 4] = _dim(CREAM, v)
    return f


def render_tool(t: float) -> Frame:
    # focused squint, a scanner sweeps back and forth below
    f = _put(Frame(), [(0, 2), (1, 2), (4, 2), (5, 2)], PEACH)
    pos = 2.5 + 2.5 * math.sin(t * 6.0)
    for x in range(6):
        v = max(0.0, 1.0 - abs(x - pos) * 0.7)
        if v > 0:
            f[x, 4] = _dim(_mix(CREAM, CLAY, 1.0 - v), v)
    return f


def render_waiting(t: float) -> Frame:
    # a big "?" pulsing ~2 Hz - a question is waiting for you
    on = (t * 2.2) % 1.0 < 0.5
    f = Frame()
    for idx in QUESTION:
        f.pixels[idx] = CLAY if on else _dim(CLAY, 0.25)
    return f


def render_done(t: float) -> Frame:
    # a checkmark draws itself in cream, then turns into a clay ^^ face with a
    # grin that hops twice for joy and fades
    f = Frame()
    if t < 1.4:
        step = 0.5 / len(CHECK)
        out = 1.0 - max(0.0, t - 1.2) / 0.2
        for i, (x, y) in enumerate(CHECK):
            age = t - i * step
            if age >= 0:
                f[x, y] = _dim(_mix(CREAM, CLAY, age / 0.4), out)
        return f
    s = t - 1.4
    hop = 1 if s < 1.2 and s % 0.6 < 0.25 else 0
    c = _dim(CLAY, 1.0 - 0.75 * min(1.0, s / 3.6))
    return _put(_put(f, _happy_eyes(1 - hop), c), _smile(4 - hop), c)


def render_error(t: float) -> Frame:
    if t < 0.9:
        v = 1.0 if (t * 6.0) % 1.0 < 0.5 else 0.08         # double flash
    else:
        v = 0.25 + 0.75 * (1.0 - min(1.0, (t - 0.9) / 4.0))
    c = _dim(ERR, v)
    return _put(_put(Frame(), X_EYES, c), FROWN, c)


RENDERERS = {
    "thinking": render_thinking,
    "tool": render_tool,
    "waiting": render_waiting,
    "done": render_done,
    "error": render_error,
}
