import textwrap
import unittest

from aligner import align_text


def dedent(s: str) -> str:
    return textwrap.dedent(s).lstrip("\n")


class AssignTests(unittest.TestCase):
    def test_simple_block(self):
        src = dedent(
            """
            x = 1
            foo_bar = 2
            """
        )
        self.assertEqual(
            align_text(src, "python"),
            dedent(
                """
                x       = 1
                foo_bar = 2
                """
            ),
        )

    def test_compound_operators_line_up_on_equals(self):
        src = "total = 0\ncount += 1\nmask |= 4\n"
        self.assertEqual(
            align_text(src, "python"),
            "total  = 0\ncount += 1\nmask  |= 4\n",
        )

    def test_comparisons_are_not_assignments(self):
        src = "ok = a == b\nfine = a <= b\n"
        self.assertEqual(align_text(src, "python"), "ok   = a == b\nfine = a <= b\n")

    def test_equals_inside_strings_is_ignored(self):
        src = 'a = "x = y"\nlonger = "z"\n'
        self.assertEqual(align_text(src, "python"), 'a      = "x = y"\nlonger = "z"\n')

    def test_keyword_arguments_are_left_alone(self):
        src = "call(\n    a=1,\n    bbb=2,\n)\n"
        self.assertEqual(align_text(src, "python"), src)

    def test_nested_brackets_are_ignored(self):
        src = "f(a = 1)\nlonger = 2\n"
        self.assertEqual(align_text(src, "python"), src)

    def test_indentation_change_breaks_block(self):
        src = "a = 1\n    bbbb = 2\n"
        self.assertEqual(align_text(src, "python"), src)

    def test_blank_line_breaks_block(self):
        src = "a = 1\n\nbbbb = 2\n"
        self.assertEqual(align_text(src, "python"), src)

    def test_single_line_is_untouched(self):
        self.assertEqual(align_text("x   = 1\n", "python"), "x   = 1\n")

    def test_arrow_functions_are_not_assignments(self):
        src = "const f = (x) => x;\nconst longer = 2;\n"
        self.assertEqual(
            align_text(src, "js"),
            "const f      = (x) => x;\nconst longer = 2;\n",
        )

    def test_go_short_declaration(self):
        src = "x := 1\nname := \"go\"\n"
        self.assertEqual(align_text(src, "go"), 'x    := 1\nname := "go"\n')


class ColonTests(unittest.TestCase):
    def test_object_literal(self):
        src = dedent(
            """
            const o = {
              a: 1,
              long_key: "v",
            };
            """
        )
        self.assertEqual(
            align_text(src, "js"),
            dedent(
                """
                const o = {
                  a:        1,
                  long_key: "v",
                };
                """
            ),
        )

    def test_yaml_skips_nested_block_keys(self):
        src = dedent(
            """
            name: aligner
            version: 1
            deps:
              a: 1
              bbb: 2
            """
        )
        self.assertEqual(
            align_text(src, "yaml"),
            dedent(
                """
                name:    aligner
                version: 1
                deps:
                  a:   1
                  bbb: 2
                """
            ),
        )

    def test_ternary_is_not_a_key(self):
        src = "const a = b ? c : d;\nconst x = y ? z : w;\n"
        self.assertEqual(align_text(src, "js", kinds=["colon"]), src)

    def test_time_values_do_not_split(self):
        src = "start: 12:30\nend_time: 13:45\n"
        self.assertEqual(align_text(src, "yaml"), "start:    12:30\nend_time: 13:45\n")

    def test_json(self):
        src = '{\n  "a": 1,\n  "bbb": [1, 2]\n}\n'
        self.assertEqual(align_text(src, "json"), '{\n  "a":   1,\n  "bbb": [1, 2]\n}\n')


class CommentTests(unittest.TestCase):
    def test_python_uses_two_space_gap(self):
        src = "a = 1 # one\nlonger_line() # two\n"
        self.assertEqual(
            align_text(src, "python", kinds=["comment"]),
            "a = 1          # one\nlonger_line()  # two\n",
        )

    def test_comment_block_ignores_indentation(self):
        src = "if x:  // a\n    y();  // b\n"
        self.assertEqual(align_text(src, "c"), "if x:    // a\n    y(); // b\n")

    def test_hash_inside_string_is_not_comment(self):
        src = 'a = "#1"\nb = 2\n'
        self.assertEqual(align_text(src, "python"), src)

    def test_full_line_comments_break_blocks(self):
        src = "a = 1  # x\n# heading\nbbbbbb = 2  # y\n"
        self.assertEqual(align_text(src, "python"), src)

    def test_sql_comments(self):
        src = "SELECT a, -- first\n       bbbb -- second\n"
        self.assertEqual(
            align_text(src, "sql"),
            "SELECT a,   -- first\n       bbbb -- second\n",
        )


class SafetyTests(unittest.TestCase):
    def test_multiline_strings_are_opaque(self):
        src = 's = """\nc = 1\ndddd = 2\n"""\n'
        self.assertEqual(align_text(src, "python"), src)

    def test_block_comments_are_opaque(self):
        src = "/*\n * a = 1\n * bbbb = 2\n */\n"
        self.assertEqual(align_text(src, "c"), src)

    def test_template_literals_are_opaque(self):
        src = "const t = `\na = 1\nbbbb = 2\n`;\n"
        self.assertEqual(align_text(src, "ts"), src)

    def test_off_directive(self):
        src = "# aligner: off\na = 1\nbbbb = 2\n# aligner: on\nc = 3\ndddd = 4\n"
        self.assertEqual(
            align_text(src, "python"),
            "# aligner: off\na = 1\nbbbb = 2\n# aligner: on\nc    = 3\ndddd = 4\n",
        )

    def test_crlf_is_preserved(self):
        src = "a = 1\r\nbbbb = 2\r\n"
        self.assertEqual(align_text(src, "python"), "a    = 1\r\nbbbb = 2\r\n")

    def test_missing_trailing_newline_is_preserved(self):
        self.assertEqual(align_text("a = 1\nbb = 2", "python"), "a  = 1\nbb = 2")

    def test_wide_characters(self):
        src = "名前 = 1\nab = 2\n"
        self.assertEqual(align_text(src, "python"), "名前 = 1\nab   = 2\n")

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            align_text("a = 1\n", "python", kinds=["nope"])

    def test_unknown_language_raises(self):
        with self.assertRaises(ValueError):
            align_text("a = 1\n", "cobol")


class IdempotenceTests(unittest.TestCase):
    SAMPLES = {
        "python": "x = 1\nfoo_bar = 2  # c\nbaz += 3 # d\n\ndef f():\n    a = 1\n    bb = 2\n",
        "js": "const o = {\n  a: 1, // x\n  bbb: 2, // y\n};\nlet q = 1;\nlet qqq = 2;\n",
        "yaml": "a: 1\nbbb: 2 # c\ncc: 3 # dd\n",
        "markdown": "| a | bb |\n|---|:-:|\n| ccc | d |\n",
    }

    def test_second_run_is_a_no_op(self):
        for lang, src in self.SAMPLES.items():
            with self.subTest(lang=lang):
                once = align_text(src, lang)
                self.assertEqual(align_text(once, lang), once)


if __name__ == "__main__":
    unittest.main()
