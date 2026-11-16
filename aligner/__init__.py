"""Aligner: line up assignments, keys, trailing comments and Markdown tables."""

from .core import align_text
from .languages import LANGUAGES, Language, get_language, language_for_path

__version__ = "0.1.0"

__all__ = [
    "LANGUAGES",
    "Language",
    "__version__",
    "align_text",
    "get_language",
    "language_for_path",
]
