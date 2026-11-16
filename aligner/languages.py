"""Language definitions.

A language tells the scanner how to recognise comments and string literals so
that an ``=`` inside a string or a comment is never mistaken for code, and it
sets which alignment kinds run by default for that file type.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

ALL_KINDS = ("assign", "colon", "comment", "table")


@dataclass(frozen=True)
class Delimiter:
    """A pair of tokens that open and close an opaque region (string or block comment)."""

    open: str
    close: str
    multiline: bool = False
    escapes: bool   = True


@dataclass(frozen=True)
class Language:
    name: str
    extensions: Tuple[str, ...]
    line_comments: Tuple[str, ...]    = ()
    delimiters: Tuple[Delimiter, ...] = ()
    kinds: Tuple[str, ...]            = ("assign", "comment")
    comment_gap: int                  = 1
    aliases: Tuple[str, ...]          = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # Longest opener first so '"""' wins over '"'.
        ordered = tuple(sorted(self.delimiters, key=lambda d: -len(d.open)))
        object.__setattr__(self, "delimiters", ordered)


def _quotes(*chars: str) -> Tuple[Delimiter, ...]:
    return tuple(Delimiter(c, c) for c in chars)


_C_BLOCK = Delimiter("/*", "*/", multiline=True, escapes=False)

LANGUAGES: Tuple[Language, ...] = (
    Language(
        "python",
        (".py", ".pyi"),
        line_comments=("#",),
        delimiters=(
            Delimiter('"""', '"""', multiline=True),
            Delimiter("'''", "'''", multiline=True),
        )
        + _quotes('"', "'"),
        comment_gap=2,
        aliases=("py",),
    ),
    Language(
        "javascript",
        (".js", ".mjs", ".cjs", ".jsx"),
        line_comments=("//",),
        delimiters=(Delimiter("`", "`", multiline=True), _C_BLOCK) + _quotes('"', "'"),
        kinds=("assign", "colon", "comment"),
        aliases=("js",),
    ),
    Language(
        "typescript",
        (".ts", ".tsx", ".mts", ".cts"),
        line_comments=("//",),
        delimiters=(Delimiter("`", "`", multiline=True), _C_BLOCK) + _quotes('"', "'"),
        kinds=("assign", "colon", "comment"),
        aliases=("ts",),
    ),
    Language(
        "go",
        (".go",),
        line_comments=("//",),
        delimiters=(Delimiter("`", "`", multiline=True, escapes=False), _C_BLOCK)
        + _quotes('"', "'"),
    ),
    Language(
        "rust",
        (".rs",),
        line_comments=("//",),
        # Single quotes are lifetimes as often as char literals, so only '"' is a string.
        delimiters=(_C_BLOCK,) + _quotes('"'),
        aliases=("rs",),
    ),
    Language(
        "c-family",
        (".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".java", ".kt", ".kts", ".cs", ".swift", ".dart", ".scala"),
        line_comments=("//",),
        delimiters=(_C_BLOCK,) + _quotes('"', "'"),
        aliases=("c", "cpp", "java", "kotlin", "csharp", "swift"),
    ),
    Language(
        "php",
        (".php",),
        line_comments=("//", "#"),
        delimiters=(_C_BLOCK,) + _quotes('"', "'"),
    ),
    Language(
        "shell",
        (".sh", ".bash", ".zsh"),
        line_comments=("#",),
        delimiters=_quotes('"', "'"),
        kinds=("comment",),
        aliases=("sh", "bash", "zsh"),
    ),
    Language(
        "ruby",
        (".rb",),
        line_comments=("#",),
        delimiters=_quotes('"', "'"),
        aliases=("rb",),
    ),
    Language(
        "lua",
        (".lua",),
        line_comments=("--",),
        delimiters=_quotes('"', "'"),
    ),
    Language(
        "sql",
        (".sql",),
        line_comments=("--",),
        delimiters=(_C_BLOCK,) + _quotes("'", '"'),
        kinds=("comment",),
    ),
    Language(
        "yaml",
        (".yml", ".yaml"),
        line_comments=("#",),
        delimiters=_quotes('"', "'"),
        kinds=("colon", "comment"),
        aliases=("yml",),
    ),
    Language(
        "toml",
        (".toml",),
        line_comments=("#",),
        delimiters=(
            Delimiter('"""', '"""', multiline=True),
            Delimiter("'''", "'''", multiline=True, escapes=False),
        )
        + _quotes('"', "'"),
    ),
    Language(
        "ini",
        (".ini", ".cfg", ".conf"),
        line_comments=(";", "#"),
        delimiters=_quotes('"'),
    ),
    Language(
        "json",
        (".json",),
        delimiters=_quotes('"'),
        kinds=("colon",),
    ),
    Language(
        "markdown",
        (".md", ".markdown"),
        kinds=("table",),
        aliases=("md",),
    ),
)

_BY_NAME: Dict[str, Language] = {}
_BY_EXT: Dict[str, Language]  = {}
for _lang in LANGUAGES:
    _BY_NAME[_lang.name] = _lang
    for _alias in _lang.aliases:
        _BY_NAME[_alias] = _lang
    for _ext in _lang.extensions:
        _BY_EXT[_ext] = _lang


def get_language(name: str) -> Language:
    """Look up a language by name or alias (case-insensitive)."""
    try:
        return _BY_NAME[name.lower()]
    except KeyError:
        known = ", ".join(sorted(lang.name for lang in LANGUAGES))
        raise ValueError(f"unknown language {name!r} (known: {known})") from None


def language_for_path(path: str) -> Optional[Language]:
    """Guess the language from a file name, or return None if unsupported."""
    lower = path.lower()
    dot   = lower.rfind(".")
    if dot == -1:
        return None
    return _BY_EXT.get(lower[dot:])
