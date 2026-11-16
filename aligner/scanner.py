"""Line scanner.

The scanner walks a document once and records, for every line, which character
positions are *top-level code*: outside string literals, outside comments, and
not nested inside brackets. Alignment rules only ever look at those positions,
which is what keeps ``x = "a = b"`` or ``f(a=1)`` from being touched.

Lines that start or end inside a multi-line string or block comment, and lines
inside an ``aligner: off`` region, are marked *opaque* and never modified.
"""

from dataclasses import dataclass
from typing import FrozenSet, List, Optional

from .languages import Delimiter, Language

OFF_DIRECTIVE = "aligner: off"
ON_DIRECTIVE  = "aligner: on"


@dataclass(frozen=True)
class LineInfo:
    text: str
    indent: str
    opaque: bool
    comment_start: Optional[int]
    top: FrozenSet[int]

    @property
    def code_end(self) -> int:
        """Index where code stops (start of trailing comment, or end of line)."""
        return len(self.text) if self.comment_start is None else self.comment_start


def _leading_ws(text: str) -> str:
    return text[: len(text) - len(text.lstrip())]


def analyze(lines: List[str], lang: Language) -> List[LineInfo]:
    """Scan ``lines`` and return one :class:`LineInfo` per line."""
    infos: List[LineInfo]      = []
    state: Optional[Delimiter] = None
    disabled                   = False

    for line in lines:
        starts_inside          = state is not None
        top                    = set()
        comment: Optional[int] = None
        depth                  = 0
        i                      = 0
        n                      = len(line)

        while i < n:
            if state is not None:
                if state.escapes and line[i] == "\\":
                    i += 2
                    continue
                if line.startswith(state.close, i):
                    i     += len(state.close)
                    state  = None
                    continue
                i += 1
                continue

            if any(line.startswith(c, i) for c in lang.line_comments):
                comment = i
                break

            opened = next((d for d in lang.delimiters if line.startswith(d.open, i)), None)
            if opened is not None:
                state  = opened
                i     += len(opened.open)
                continue

            ch = line[i]
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth = max(0, depth - 1)
            elif depth == 0:
                top.add(i)
            i += 1

        ends_inside = state is not None
        if state is not None and not state.multiline:
            # An unterminated single-line string: be safe, leave the line alone.
            state = None

        directive = False
        if comment is not None:
            comment_text = line[comment:]
            if OFF_DIRECTIVE in comment_text:
                disabled, directive = True, True
            elif ON_DIRECTIVE in comment_text:
                disabled, directive = False, True

        infos.append(
            LineInfo(
                text=line,
                indent=_leading_ws(line),
                opaque=starts_inside or ends_inside or disabled or directive,
                comment_start=comment,
                top=frozenset(top),
            )
        )
    return infos
