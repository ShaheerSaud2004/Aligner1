"""Alignment rules.

Each rule has a *matcher* that decides whether a single line takes part in that
kind of alignment, and a *formatter* that rewrites a block of matched lines so
their columns line up. A block is a run of two or more consecutive matching
lines (with the same indentation, for code rules).
"""

from typing import Callable, Iterator, List, Optional, Tuple, TypeVar

from .scanner import LineInfo
from .width import display_width, pad_left, pad_right

T = TypeVar("T")

ASSIGN_OPS = frozenset(
    {
        "=", ":=", "+=", "-=", "*=", "/=", "//=", "%=", "**=", "@=",
        "|=", "&=", "^=", "<<=", ">>=", ">>>=", "??=", "||=", "&&=",
    }
)
_OP_CHARS = frozenset("+-*/%|&^<>:!?=@")


def blocks(
    infos: List[LineInfo],
    match: Callable[[LineInfo], Optional[T]],
    same_indent: bool = True,
) -> Iterator[List[Tuple[int, T]]]:
    """Yield runs of 2+ consecutive lines that ``match``."""
    current: List[Tuple[int, T]] = []
    for idx, info in enumerate(infos):
        found = None if info.opaque else match(info)
        if found is not None and current and same_indent:
            if infos[current[-1][0]].indent != info.indent:
                if len(current) > 1:
                    yield current
                current = []
        if found is None:
            if len(current) > 1:
                yield current
            current = []
            continue
        current.append((idx, found))
    if len(current) > 1:
        yield current


# --- assignment -------------------------------------------------------------

Assign = Tuple[str, str, str]  # (left incl. indent, operator, right incl. comment)


def match_assign(info: LineInfo) -> Optional[Assign]:
    """Match ``left <op> right`` where <op> is an assignment operator.

    The operator must already be surrounded by whitespace. That keeps keyword
    arguments (``f(a=1)`` split across lines) and other deliberately tight code
    out of alignment.
    """
    t = info.text
    for i in sorted(info.top):
        if t[i] != "=":
            continue
        nxt = t[i + 1] if i + 1 < len(t) else ""
        if nxt in ("=", ">", "~"):
            continue  # ==, =>, =~
        j = i
        while j > 0 and t[j - 1] in _OP_CHARS and (j - 1) in info.top:
            j -= 1
        op = t[j : i + 1]
        if op not in ASSIGN_OPS:
            continue  # comparison such as <=, !=, ===
        if j == 0 or not t[j - 1].isspace():
            return None
        if nxt and not nxt.isspace():
            return None
        left = t[:j].rstrip()
        if not left.strip():
            return None
        return left, op, t[i + 1 :].strip()
    return None


def format_assign(items: List[Assign]) -> List[str]:
    left_w = max(display_width(left) for left, _, _ in items)
    op_w   = max(len(op) for _, op, _ in items)
    return [
        (pad_right(left, left_w) + " " + pad_left(op, op_w) + " " + right).rstrip()
        for left, op, right in items
    ]


# --- key: value -------------------------------------------------------------

Colon = Tuple[str, str]  # (key incl. indent, value incl. comment)


def match_colon(info: LineInfo) -> Optional[Colon]:
    """Match ``key: value`` pairs (object literals, YAML, JSON, type fields)."""
    if match_assign(info) is not None:
        return None
    t = info.text
    for i in sorted(info.top):
        if t[i] != ":":
            continue
        prev = t[i - 1] if i > 0 else ""
        nxt  = t[i + 1] if i + 1 < len(t) else ""
        if prev == ":" or nxt == ":":
            continue  # C++ / Rust paths
        if not prev or prev.isspace():
            return None  # ternary ``a ? b : c`` or a bare colon
        if not nxt.isspace():
            return None  # ``key:`` opening a nested block, or ``12:30``
        if not t[i + 1 : info.code_end].strip():
            return None
        if not t[:i].strip():
            return None
        return t[:i], t[i + 1 :].strip()
    return None


def format_colon(items: List[Colon]) -> List[str]:
    key_w = max(display_width(key) for key, _ in items) + 1
    return [(pad_right(key + ":", key_w) + " " + value).rstrip() for key, value in items]


# --- trailing comments ------------------------------------------------------

Comment = Tuple[str, str]  # (code, comment)


def match_comment(info: LineInfo) -> Optional[Comment]:
    if info.comment_start is None:
        return None
    code = info.text[: info.comment_start].rstrip()
    if not code.strip():
        return None
    return code, info.text[info.comment_start :].rstrip()


def make_comment_formatter(gap: int) -> Callable[[List[Comment]], List[str]]:
    def format_comment(items: List[Comment]) -> List[str]:
        column = max(display_width(code) for code, _ in items) + gap
        return [pad_right(code, column) + comment for code, comment in items]

    return format_comment
