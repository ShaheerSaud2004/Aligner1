import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from aligner.cli import EXIT_CHANGES, EXIT_ERROR, EXIT_OK, main


def run(args, stdin=None):
    out, err = io.StringIO(), io.StringIO()
    patches  = []
    if stdin is not None:
        fake        = io.StringIO(stdin)
        fake.isatty = lambda: False  # type: ignore[assignment]
        patches.append(mock.patch("sys.stdin", fake))
    for p in patches:
        p.start()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            code = main(args)
    finally:
        for p in patches:
            p.stop()
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return path

    def read(self, path):
        with open(path, encoding="utf-8", newline="") as fh:
            return fh.read()

    def test_check_reports_changes(self):
        path         = self.write("a.py", "a = 1\nbbbb = 2\n")
        code, _, err = run(["--check", path])
        self.assertEqual(code, EXIT_CHANGES)
        self.assertIn("would align", err)
        self.assertEqual(self.read(path), "a = 1\nbbbb = 2\n")

    def test_check_passes_when_aligned(self):
        path       = self.write("a.py", "a    = 1\nbbbb = 2\n")
        code, _, _ = run(["--check", path])
        self.assertEqual(code, EXIT_OK)

    def test_write_rewrites_file(self):
        path       = self.write("a.py", "a = 1\nbbbb = 2\n")
        code, _, _ = run(["--write", "--quiet", path])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(self.read(path), "a    = 1\nbbbb = 2\n")

    def test_default_prints_diff(self):
        path         = self.write("a.py", "a = 1\nbbbb = 2\n")
        code, out, _ = run([path])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("-a = 1", out)
        self.assertIn("+a    = 1", out)

    def test_directory_walk_skips_vendor_dirs_and_unknown_files(self):
        self.write("src/a.py", "a = 1\nbbbb = 2\n")
        self.write("node_modules/b.js", "let a = 1;\nlet bbbb = 2;\n")
        self.write("notes.xyz", "a = 1\nbbbb = 2\n")
        code, _, err = run(["--check", self.dir])
        self.assertEqual(code, EXIT_CHANGES)
        self.assertIn("a.py", err)
        self.assertNotIn("b.js", err)
        self.assertNotIn("notes.xyz", err)

    def test_unsupported_explicit_file_is_an_error(self):
        path         = self.write("notes.xyz", "a = 1\n")
        code, _, err = run(["--check", path])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("unsupported", err)

    def test_stdin_requires_lang(self):
        code, _, err = run(["-"], stdin="a = 1\n")
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("--lang", err)

    def test_stdin_round_trip(self):
        code, out, _ = run(["--lang", "python", "-"], stdin="a = 1\nbbbb = 2\n")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out, "a    = 1\nbbbb = 2\n")

    def test_kinds_override(self):
        path       = self.write("a.py", "a = 1  # x\nbbbb = 2  # y\n")
        code, _, _ = run(["--write", "--quiet", "--kinds", "comment", path])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(self.read(path), "a = 1     # x\nbbbb = 2  # y\n")

    def test_list_languages(self):
        code, out, _ = run(["--list-languages"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("python", out)
        self.assertIn("markdown", out)


if __name__ == "__main__":
    unittest.main()
