import unittest

from aligner import align_text
from aligner.markdown import split_row


class SplitRowTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(split_row("| a | b |"), ["a", "b"])

    def test_escaped_pipe(self):
        self.assertEqual(split_row(r"| a \| b | c |"), [r"a \| b", "c"])

    def test_pipe_in_code_span(self):
        self.assertEqual(split_row("| `a | b` | c |"), ["`a | b`", "c"])


class TableTests(unittest.TestCase):
    def test_alignment_markers(self):
        src = "| Name | Score | Note |\n|:--|--:|:-:|\n| Ana | 9 | hi |\n| Bartholomew | 10 | ok |\n"
        self.assertEqual(
            align_text(src, "markdown"),
            "| Name        | Score | Note |\n"
            "| :---------- | ----: | :--: |\n"
            "| Ana         |     9 |  hi  |\n"
            "| Bartholomew |    10 |  ok  |\n",
        )

    def test_short_rows_are_padded(self):
        src = "| a | b |\n|---|---|\n| only |\n"
        self.assertEqual(
            align_text(src, "markdown"),
            "| a    | b   |\n| ---- | --- |\n| only |     |\n",
        )

    def test_fenced_code_is_untouched(self):
        src = "```\n| a | b |\n|---|---|\n```\n"
        self.assertEqual(align_text(src, "markdown"), src)

    def test_rows_without_separator_are_not_a_table(self):
        src = "| just | pipes |\n| more | text |\n"
        self.assertEqual(align_text(src, "markdown"), src)

    def test_indented_table_keeps_indent(self):
        src = "  | a | bb |\n  |---|---|\n  | ccc | d |\n"
        self.assertEqual(
            align_text(src, "markdown"),
            "  | a   | bb  |\n  | --- | --- |\n  | ccc | d   |\n",
        )


if __name__ == "__main__":
    unittest.main()
