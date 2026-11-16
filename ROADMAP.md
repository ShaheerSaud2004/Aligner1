# Roadmap

Planned work for Aligner, roughly in priority order. Each item becomes a GitHub issue when work starts.

## 0.2: configuration

- [ ] Read settings from `[tool.aligner]` in `pyproject.toml` and from a standalone `.aligner.toml` (kinds per language, comment gap, excluded paths).
- [ ] `--exclude` / `--include` glob options for directory runs.
- [ ] A `max-padding` limit, so one very long line doesn't push a whole block far to the right. Lines over the limit should break the block instead.
- [ ] `--stdin-filename` so editors can pipe a buffer and still get language detection.

## 0.3: more alignment rules

- [ ] `=>` alignment for PHP arrays, Ruby hashes and Elixir/Scala match arms.
- [ ] Go struct field types and tags (the columns after the field name).
- [ ] C/C++ `#define NAME value` columns.
- [ ] Align function-call arguments across consecutive similar calls (table-like test data).
- [ ] Markdown tables without leading pipes, and tables inside block quotes.
- [ ] Align code inside fenced Markdown blocks using the fence's language tag.

## 0.4: editor and tooling integrations

- [ ] Publish to PyPI as `aligner-cli`.
- [ ] VS Code extension: "Align selection" and format-on-save.
- [ ] Neovim plugin / `formatprg` recipe.
- [ ] `--range START:END` to align only part of a file (for editor selections).
- [ ] Git-aware mode: only touch lines changed since a base ref.

## Quality

- [ ] Property-based tests (idempotence, never changes non-whitespace characters).
- [ ] Benchmark on large repos and optimise the scanner.
- [ ] Rust raw strings (`r#"..."#`), Python f-string nesting, heredocs in shell.
- [ ] Docs site with before/after examples for every language.
