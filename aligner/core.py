"""The public alignment entry point."""

from typing import Iterable, List, Optional, Union

from . import rules
from .languages import ALL_KINDS, Language, get_language
from .markdown import align_tables
from .scanner import analyze


def _apply(lines: List[str], lang: Language, match, fmt, same_indent: bool) -> List[str]:
    infos = analyze(lines, lang)
    out   = list(lines)
    for block in rules.blocks(infos, match, same_indent=same_indent):
        indices = [idx for idx, _ in block]
        for idx, new in zip(indices, fmt([found for _, found in block])):
            out[idx] = new
    return out


def resolve_kinds(lang: Language, kinds: Optional[Iterable[str]]) -> List[str]:
    chosen  = list(lang.kinds if kinds is None else kinds)
    unknown = [k for k in chosen if k not in ALL_KINDS]
    if unknown:
        raise ValueError(f"unknown kind(s): {', '.join(unknown)} (known: {', '.join(ALL_KINDS)})")
    # Always run in a fixed order: assignments and keys first, comments last,
    # because aligning code changes where trailing comments land.
    return [k for k in ALL_KINDS if k in chosen]


def align_text(
    text: str,
    language: Union[str, Language] = "python",
    kinds: Optional[Iterable[str]] = None,
) -> str:
    """Align ``text`` and return the result.

    ``language`` is a :class:`Language` or a name such as ``"python"``.
    ``kinds`` overrides the language's default alignment kinds; choose from
    ``assign``, ``colon``, ``comment`` and ``table``.
    """
    lang    = get_language(language) if isinstance(language, str) else language
    newline = "\r\n" if "\r\n" in text else "\n"
    lines   = text.split(newline)

    for kind in resolve_kinds(lang, kinds):
        if kind == "assign":
            lines = _apply(lines, lang, rules.match_assign, rules.format_assign, True)
        elif kind == "colon":
            lines = _apply(lines, lang, rules.match_colon, rules.format_colon, True)
        elif kind == "comment":
            fmt   = rules.make_comment_formatter(lang.comment_gap)
            lines = _apply(lines, lang, rules.match_comment, fmt, False)
        elif kind == "table":
            lines = align_tables(lines)

    return newline.join(lines)
