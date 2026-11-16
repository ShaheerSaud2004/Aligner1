"""Markdown table alignment.

Turns a ragged pipe table into one whose columns line up, honouring the
``:---``, ``:---:`` and ``---:`` alignment markers in the separator row.
Tables inside fenced code blocks are left untouched.
"""

import re
from typing import List, Optional

from .width import display_width, pad_center, pad_left, pad_right

_SEPARATOR_CELL = re.compile(r"^\s*:?-+:?\s*$")
_FENCE          = re.compile(r"^\s*(```|~~~)")


def split_row(line: str) -> List[str]:
    """Split a table row into cell texts, respecting ``\\|`` and code spans."""
    cells: List[str] = []
    buf: List[str]   = []
    in_code          = False
    i                = 0
    s                = line.strip()
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            buf.append(s[i : i + 2])
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf))
    if s.startswith("|"):
        cells = cells[1:]
    if s.endswith("|") and not s.endswith("\\|") and cells:
        cells = cells[:-1]
    return [c.strip() for c in cells]


def _is_row(line: str) -> bool:
    return line.lstrip().startswith("|")


def _is_separator(line: str) -> bool:
    if not _is_row(line):
        return False
    cells = split_row(line)
    return bool(cells) and all(_SEPARATOR_CELL.match(c) for c in cells)


def _alignment(cell: str) -> str:
    c = cell.strip()
    if c.startswith(":") and c.endswith(":"):
        return "center"
    if c.endswith(":"):
        return "right"
    if c.startswith(":"):
        return "left"
    return "none"


def _separator(align: str, width: int) -> str:
    if align == "center":
        return ":" + "-" * (width - 2) + ":"
    if align == "right":
        return "-" * (width - 1) + ":"
    if align == "left":
        return ":" + "-" * (width - 1)
    return "-" * width


def format_table(rows: List[str]) -> List[str]:
    """Format a table given as raw lines (header, separator, body...)."""
    indent = rows[0][: len(rows[0]) - len(rows[0].lstrip())]
    parsed = [split_row(r) for r in rows]
    ncols  = max(len(r) for r in parsed)
    for r in parsed:
        r.extend([""] * (ncols - len(r)))

    aligns = [_alignment(c) for c in parsed[1]]
    widths = [3] * ncols
    for ri, row in enumerate(parsed):
        if ri == 1:
            continue
        for ci, cell in enumerate(row):
            widths[ci] = max(widths[ci], display_width(cell))

    out: List[str] = []
    for ri, row in enumerate(parsed):
        if ri == 1:
            cells = [_separator(aligns[ci], widths[ci]) for ci in range(ncols)]
        else:
            cells = []
            for ci, cell in enumerate(row):
                pad = {"right": pad_left, "center": pad_center}.get(aligns[ci], pad_right)
                cells.append(pad(cell, widths[ci]))
        out.append(indent + "| " + " | ".join(cells) + " |")
    return out


def align_tables(lines: List[str]) -> List[str]:
    """Return ``lines`` with every pipe table aligned."""
    out                  = list(lines)
    fence: Optional[str] = None
    i                    = 0
    while i < len(out):
        m = _FENCE.match(out[i])
        if m:
            if fence is None:
                fence = m.group(1)
            elif m.group(1) == fence:
                fence = None
            i += 1
            continue
        if fence is None and _is_row(out[i]) and i + 1 < len(out) and _is_separator(out[i + 1]):
            end = i + 2
            while end < len(out) and _is_row(out[end]):
                end += 1
            out[i:end] = format_table(out[i:end])
            i          = end
            continue
        i += 1
    return out
