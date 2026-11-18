"""Whether anyone is at the Mac, so the daemon can stop streaming to an empty room.

Why this matters: every streamed frame is a round trip to the keyboard, and
over the 2.4 GHz dongle the keyboard has to stay awake to answer it. A daemon
that streams around the clock therefore keeps the keyboard from ever sleeping,
even overnight while an agent works with nobody watching.

The signal is the system-wide time since the last keyboard or mouse event,
the same clock the screensaver uses. The daemon's own raw-HID traffic does not
reset it, and reading it needs no Accessibility or Input Monitoring grant.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import functools
import sys

_HID_SYSTEM_STATE = 1          # kCGEventSourceStateHIDSystemState
_ANY_INPUT_EVENT = 0xFFFFFFFF  # kCGAnyInputEventType


@functools.lru_cache(maxsize=1)
def _idle_clock():
    if sys.platform != "darwin":
        return None
    path = ctypes.util.find_library("CoreGraphics")
    if not path:
        return None
    try:
        fn = ctypes.CDLL(path).CGEventSourceSecondsSinceLastEventType
    except (OSError, AttributeError):
        return None
    fn.restype = ctypes.c_double
    fn.argtypes = [ctypes.c_int32, ctypes.c_uint32]
    return fn


def seconds_since_input() -> float | None:
    """Seconds since the last key press or mouse event, or None if unknown."""
    fn = _idle_clock()
    return None if fn is None else float(fn(_HID_SYSTEM_STATE, _ANY_INPUT_EVENT))


def away(after: float) -> bool:
    """True once nobody has touched the Mac for `after` seconds.

    Never true when `after` is 0 or less (the check is off), or when the idle
    clock is unavailable - an unknown is treated as someone being there.
    """
    if after <= 0:
        return False
    idle = seconds_since_input()
    return idle is not None and idle >= after
