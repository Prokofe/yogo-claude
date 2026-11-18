"""Warm "Claude" palette for the status display: clay, peach and cream.

Same states and motion language as the classic theme, recoloured. Select with
YOGO_THEME=claude, or YOGO_THEME=classic for the original look.
Tune the colour constants below if the LEDs render them too pink or too white.
"""

from __future__ import annotations

import math

from . import protocol as p
from .frame import Frame

# Tuned for the keyboard's LEDs, not a monitor: the diffuser glass washes out
# anything with much green/blue, so these are far more saturated than the
# screen colours they stand in for. (Screen originals: clay #D97757.)
CLAY = (255, 62, 10)       # terracotta orange - the main accent
DEEP = (140, 22, 0)        # darker clay for tails and glows
PEACH = (255, 105, 22)
CREAM = (255, 150, 55)     # warm highlight - stays orange, not white
ERR = (255, 0, 0)


def _mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


def _dim(c, v):
    v = max(0.0, min(1.0, v))
    return tuple(int(x * v) for x in c)


def _ring():
    cells = [(x, 0) for x in range(6)]
    cells += [(5, y) for y in range(1, 6)]
    cells += [(x, 5) for x in range(4, -1, -1)]
    cells += [(0, y) for y in range(4, 0, -1)]
    return cells


RING = _ring()
CORE = [(2, 2), (3, 2), (2, 3), (3, 3)]


def _comet(t, head_c, tail_c, speed, tail, core_v):
    f = Frame()
    n = len(RING)
    head = (t * speed) % n
    for i, (x, y) in enumerate(RING):
        d = (head - i) % n
        if d < tail:
            k = d / tail
            f[x, y] = _dim(_mix(head_c, tail_c, k), (1.0 - k) ** 1.5)
    for xy in CORE:
        f[xy] = _dim(CLAY, core_v)
    return f


def render_idle(t: float, style: str = "off") -> Frame:
    if style == "off":
        return Frame()
    v = 0.05 + 0.06 * (0.5 + 0.5 * math.sin(t * 1.1))     # slow clay breathe
    return Frame.solid(_dim(CLAY, v))


def render_thinking(t: float) -> Frame:
    # clay comet with a softly pulsing core - "mulling it over"
    core = 0.10 + 0.12 * (0.5 + 0.5 * math.sin(t * 3.0))
    return _comet(t, CLAY, DEEP, speed=8.0, tail=7, core_v=core)


def render_tool(t: float) -> Frame:
    # faster, brighter comet: cream head fading into clay
    return _comet(t, CREAM, CLAY, speed=15.0, tail=5, core_v=0.08)


def render_waiting(t: float) -> Frame:
    # whole screen pulses clay at ~2 Hz with a cream centre - look at me
    on = (t * 2.2) % 1.0 < 0.5
    f = Frame.solid(_dim(CLAY, 1.0 if on else 0.12))
    for xy in CORE:
        f[xy] = CREAM if on else _dim(CLAY, 0.2)
    return f


def render_done(t: float) -> Frame:
    f = Frame()
    for idx in range(p.PIXELS):
        x, y = idx % p.WIDTH, idx // p.WIDTH
        d = math.hypot(x - 2.5, y - 2.5)
        if t < 0.8:                                        # cream bloom outward
            v = 1.0 - abs(d - (t / 0.8) * 4.6) * 0.8
            f.pixels[idx] = _dim(_mix(CREAM, PEACH, d / 3.6), v)
        else:                                              # settle to clay glow
            k = min(1.0, (t - 0.8) / 4.0)
            f.pixels[idx] = _dim(_mix(PEACH, CLAY, k), (1.0 - k) * (0.8 - d * 0.06))
    return f


def render_error(t: float) -> Frame:
    if t < 0.9:
        v = 1.0 if (t * 6.0) % 1.0 < 0.5 else 0.05         # double flash
    else:
        v = (1.0 - min(1.0, (t - 0.9) / 4.0)) * 0.5
    return Frame.solid(_dim(ERR, v))


RENDERERS = {
    "thinking": render_thinking,
    "tool": render_tool,
    "waiting": render_waiting,
    "done": render_done,
    "error": render_error,
}
