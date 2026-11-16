"""Terminal display width helpers.

Alignment is about what the eye sees, not how many code points a string has.
Wide East Asian characters take two columns and combining marks take none, so
padding is computed from display width rather than ``len``.
"""

import unicodedata


def display_width(text: str) -> int:
    """Return the number of terminal columns ``text`` occupies."""
    width = 0
    for ch in text:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad_right(text: str, width: int) -> str:
    """Pad ``text`` with spaces on the right up to ``width`` display columns."""
    return text + " " * max(0, width - display_width(text))


def pad_left(text: str, width: int) -> str:
    """Pad ``text`` with spaces on the left up to ``width`` display columns."""
    return " " * max(0, width - display_width(text)) + text


def pad_center(text: str, width: int) -> str:
    """Center ``text`` within ``width`` display columns (extra space goes right)."""
    gap  = max(0, width - display_width(text))
    left = gap // 2
    return " " * left + text + " " * (gap - left)
