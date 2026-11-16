"""Command-line interface: ``aligner [paths...] [--write | --check | --diff]``."""

import argparse
import difflib
import os
import sys
from typing import Iterator, List, Optional, Sequence, Tuple

from . import __version__
from .core import align_text
from .languages import LANGUAGES, Language, get_language, language_for_path

SKIP_DIRS = frozenset(
    {
        ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "env", "__pycache__",
        ".mypy_cache", ".pytest_cache", ".tox", "dist", "build", "target", ".next",
    }
)

EXIT_OK      = 0
EXIT_CHANGES = 1
EXIT_ERROR   = 2


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aligner",
        description="Vertically align assignments, key/value pairs, trailing comments "
        "and Markdown tables.",
        epilog="With no mode flag, aligner prints a diff for files and the aligned text for stdin.",
    )
    p.add_argument("paths", nargs="*", help="files or directories to align; '-' reads stdin")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("-w", "--write", action="store_true", help="rewrite files in place")
    mode.add_argument(
        "-c", "--check", action="store_true", help="exit 1 if any file would change (for CI)"
    )
    mode.add_argument("-d", "--diff", action="store_true", help="print a unified diff (default)")
    p.add_argument(
        "-k",
        "--kinds",
        help="comma-separated kinds to run instead of the language default: "
        "assign, colon, comment, table",
    )
    p.add_argument("-l", "--lang", help="force a language (required when reading stdin)")
    p.add_argument("-q", "--quiet", action="store_true", help="only report errors")
    p.add_argument("--list-languages", action="store_true", help="show supported languages and exit")
    p.add_argument("--version", action="version", version=f"aligner {__version__}")
    return p


def _iter_files(paths: Sequence[str], forced: Optional[Language]) -> Iterator[Tuple[str, Optional[Language]]]:
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for name in sorted(files):
                    full = os.path.join(root, name)
                    lang = forced or language_for_path(full)
                    if lang is not None:
                        yield full, lang
        else:
            yield path, forced or language_for_path(path)


def _list_languages() -> None:
    for lang in LANGUAGES:
        exts = " ".join(lang.extensions)
        print(f"{lang.name:<11} {','.join(lang.kinds):<22} {exts}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args   = parser.parse_args(argv)

    if args.list_languages:
        _list_languages()
        return EXIT_OK

    try:
        forced = get_language(args.lang) if args.lang else None
        kinds  = [k.strip() for k in args.kinds.split(",") if k.strip()] if args.kinds else None
    except ValueError as exc:
        parser.error(str(exc))

    paths = args.paths
    if not paths:
        if sys.stdin.isatty():
            parser.print_help(sys.stderr)
            return EXIT_ERROR
        paths = ["-"]

    status  = EXIT_OK
    changed = 0
    for path, lang in _iter_files(paths, forced):
        if path == "-":
            if lang is None:
                print("aligner: --lang is required when reading stdin", file=sys.stderr)
                return EXIT_ERROR
            source = sys.stdin.read()
            try:
                result = align_text(source, lang, kinds)
            except ValueError as exc:
                parser.error(str(exc))
            if args.check:
                if result != source:
                    changed += 1
                    status   = EXIT_CHANGES
            else:
                sys.stdout.write(result)
            continue

        if lang is None:
            print(f"aligner: {path}: unsupported file type (use --lang)", file=sys.stderr)
            status = max(status, EXIT_ERROR)
            continue
        try:
            with open(path, encoding="utf-8", newline="") as fh:
                source = fh.read()
        except (OSError, UnicodeDecodeError) as exc:
            print(f"aligner: {path}: {exc}", file=sys.stderr)
            status = max(status, EXIT_ERROR)
            continue

        try:
            result = align_text(source, lang, kinds)
        except ValueError as exc:
            parser.error(str(exc))
        if result == source:
            continue
        changed += 1

        if args.write:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(result)
            if not args.quiet:
                print(f"aligned {path}", file=sys.stderr)
        elif args.check:
            if not args.quiet:
                print(f"would align {path}", file=sys.stderr)
            status = max(status, EXIT_CHANGES)
        else:
            sys.stdout.writelines(
                difflib.unified_diff(
                    source.splitlines(keepends=True),
                    result.splitlines(keepends=True),
                    fromfile=f"a/{path}",
                    tofile=f"b/{path}",
                )
            )

    if args.check and not args.quiet and status == EXIT_OK:
        print("all files aligned", file=sys.stderr)
    return status


if __name__ == "__main__":
    sys.exit(main())
