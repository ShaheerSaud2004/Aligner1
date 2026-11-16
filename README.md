# Aligner

**Aligner** is a small, zero-dependency command-line tool that lines things up in source code and docs:

- assignments (`=`, `+=`, `:=`, …)
- `key: value` pairs in object literals, YAML and JSON
- trailing comments
- Markdown tables

It's for developers who like column-aligned code but don't want to hand-pad it, or redo the padding every time a variable gets renamed. It works across a dozen languages, never touches anything inside strings or comments, and running it twice gives the same result. That makes it safe for pre-commit hooks and CI.

```diff
-timeout = 30
-max_retries = 5  # per request
-backoff += 1 # seconds
+timeout      = 30
+max_retries  = 5  # per request
+backoff     += 1  # seconds
```

```diff
-| Name | Score |
-|:--|--:|
-| Ana | 9 |
-| Bartholomew | 10 |
+| Name        | Score |
+| :---------- | ----: |
+| Ana         |     9 |
+| Bartholomew |    10 |
```

## Built with

- Python 3.9+ standard library only. There are no runtime dependencies.
- A small line scanner (`aligner/scanner.py`) that tracks strings, block comments and bracket depth. Rules only consider *top-level* code, so `f(a=1)`, `"x = y"` and `# a = b` are never treated as assignments.
- Tests use the standard library's `unittest`. GitHub Actions runs them on Python 3.10–3.13 (3.9 is supported but no longer available on GitHub's runners).

## Install

From a clone:

```bash
python3 -m pip install .
```

Or run it without installing:

```bash
python3 -m aligner --help
```

## Usage

```bash
aligner src/                 # show a diff of what would change (default)
aligner --write src/ docs/   # rewrite files in place
aligner --check .            # exit 1 if anything is unaligned (CI)
cat config.yml | aligner --lang yaml -   # filter stdin to stdout
aligner --kinds comment app.py           # only align trailing comments
aligner --list-languages
```

When you pass a directory, Aligner walks it, picks up files with known extensions and skips `.git`, `node_modules`, virtualenvs and build folders.

### What gets aligned

| Kind      | Matches                                                                  | Example                       |
| --------- | ------------------------------------------------------------------------ | ----------------------------- |
| `assign`  | consecutive lines with an assignment operator surrounded by spaces       | `x    = 1` / `name = "a"`     |
| `colon`   | `key: value` lines (no space before the colon, a value after it)         | `a:        1` / `long_key: 2` |
| `comment` | consecutive lines that end in a trailing comment                         | `x = 1  # a` / `yy = 2 # b`   |
| `table`   | Markdown pipe tables with a separator row, honouring `:--`, `:-:`, `--:` |                               |

A block is two or more consecutive lines that match the same kind and have the same indentation. A blank line, an indentation change or a line that doesn't match ends the block. Compound operators line up on their `=`. Aligner only touches lines where the operator already has spaces around it, so tight code like keyword arguments (`a=1`) is left alone.

### Languages

| Language   | Extensions                                      | Default kinds          |
| ---------- | ----------------------------------------------- | ---------------------- |
| python     | `.py .pyi`                                      | assign, comment        |
| javascript | `.js .mjs .cjs .jsx`                            | assign, colon, comment |
| typescript | `.ts .tsx .mts .cts`                            | assign, colon, comment |
| go         | `.go`                                           | assign, comment        |
| rust       | `.rs`                                           | assign, comment        |
| c-family   | `.c .h .cpp .hpp .cc .java .kt .cs .swift` etc. | assign, comment        |
| php        | `.php`                                          | assign, comment        |
| shell      | `.sh .bash .zsh`                                | comment                |
| ruby       | `.rb`                                           | assign, comment        |
| lua        | `.lua`                                          | assign, comment        |
| sql        | `.sql`                                          | comment                |
| yaml       | `.yml .yaml`                                    | colon, comment         |
| toml       | `.toml`                                         | assign, comment        |
| ini        | `.ini .cfg .conf`                               | assign, comment        |
| json       | `.json`                                         | colon                  |
| markdown   | `.md .markdown`                                 | table                  |

### Turning it off for a region

```python
# aligner: off
MATRIX = [1, 0,
          0, 1]
x = 1
# aligner: on
```

Lines inside multi-line strings, template literals and `/* block comments */` are never changed either.

### Pre-commit

```yaml
repos:
  - repo: https://github.com/ShaheerSaud2004/Aligner1
    rev: v0.1.0
    hooks:
      - id: aligner        # or aligner-check to fail without rewriting
```

### As a library

```python
from aligner import align_text

print(align_text("a = 1\nlonger = 2\n", "python"))
```

## Development

```bash
python3 -m unittest discover -s tests -v   # run the tests
python3 -m aligner --check aligner tests   # Aligner keeps its own source aligned
```

The project layout:

```text
aligner/
  scanner.py    # finds top-level code positions, comments, opaque lines
  rules.py      # matchers + formatters for assign / colon / comment
  markdown.py   # pipe-table parsing and formatting
  languages.py  # comment/string syntax and default kinds per language
  width.py      # display-width aware padding (CJK, combining marks)
  core.py       # align_text(): runs the passes in order
  cli.py        # argparse front end
tests/
```

## Roadmap

See [ROADMAP.md](ROADMAP.md). Next up: configuration via `pyproject.toml`, a max-padding limit, `=>` alignment, and editor integrations.

## License

[MIT](LICENSE)
