"""Lexer tests for Pork CCig. Run from the project root:

    py -m unittest discover -s backend -v

The SNIPPETS are the same copyable lexer tests listed for manual testing in
the UI. They test tokens only and are not meant to be complete programs.
"""

import unittest

from pork_lexer import KEYWORDS, keyword_reference, tokenize

SNIPPETS = {
    "keywords": (
        "meat sauce chop recipe cooked empty menu\n"
        "if else switch case default\n"
        "for while do\n"
        "stop again serveback\n"
        "pork serve taste yummy yuck fixed"
    ),
    # "_count" comes first: delim25 (after whitespace) has no underscore.
    "identifiers": (
        "_count age studentName student_name score1 "
        "meatball format iffy Meat yummy2 abcdefghijklmnopqrst"
    ),
    "literals": (
        "meat count = -15;\n"
        "sauce price = 150.50;\n"
        "chop grade = 'A';\n"
        r"chop tab = '\t';" "\n"
        "chop hash = '#';\n"
        r'recipe dish = "Sisig\n";' "\n"
        'recipe none = "";\n'
        "cooked done = yummy ;"
    ),
    "symbols": (
        "+ - * / % ++ -- = += -= *= /= %=\n"
        "< > == != <= >= ! && || &\n"
        "( ) [ ] { } ; , :\n"
        "a.b"
    ),
    "longest_match": "x<=y a==b c!=d e&&f g||h i+=j k--",
    "comments": (
        "// single-line comment\n"
        "meat x ; /* multi-line\n"
        "   comment */\n"
        "x = 5 ;"
    ),
    "errors": (
        "meat price = 5 $ 2;\n"
        'recipe msg = "unterminated\n'
        "chop c = 'ab';\n"
        "chop e = '';\n"
        r'recipe bad = "Good M\orning";' "\n"
        "abcdefghijklmnopqrstu = 1;\n"
        "meat big = 1234567890123456;\n"
        "sauce s = 1234567890123.5;\n"
        "sauce t = 1.12345678;\n"
        "sauce u = 1.2.3;\n"
        "sauce v = 12.;\n"
        "meat n = 123abc;\n"
        "cooked ok = yummy{\n"
        "x = y | z;\n"
        "chop q = 'x\n"
        "/* never closed"
    ),
}

HIDDEN = {"space", "newline", "tab"}


def visible(result):
    return [(t.type, t.lexeme, t.line, t.col) for t in result.tokens if t.type not in HIDDEN]


class KeywordTests(unittest.TestCase):
    def test_every_keyword_recognized(self):
        result = tokenize(SNIPPETS["keywords"])
        self.assertEqual(result.errors, [])
        found = [t.type for t in result.tokens if t.type not in HIDDEN]
        self.assertEqual(found, [
            "meat", "sauce", "chop", "recipe", "cooked", "empty", "menu",
            "if", "else", "switch", "case", "default",
            "for", "while", "do",
            "stop", "again", "serveback",
            "pork", "serve", "taste", "yummy", "yuck", "fixed",
        ])

    def test_keyword_list_matches_spec(self):
        self.assertEqual(len(KEYWORDS), 24)
        words = [k["word"] for k in keyword_reference()["keywords"]]
        self.assertEqual(sorted(words), sorted(k.word for k in KEYWORDS))

    def test_positions(self):
        tokens = visible(tokenize(SNIPPETS["keywords"]))
        self.assertEqual(tokens[0], ("meat", "meat", 1, 1))
        self.assertEqual(tokens[7], ("if", "if", 2, 1))
        self.assertEqual(tokens[-1], ("fixed", "fixed", 5, 29))

    def test_keywords_are_lowercase_only(self):
        self.assertEqual(visible(tokenize("Meat IF")), [("id", "Meat", 1, 1), ("id", "IF", 1, 6)])

    def test_keyword_delimiters_follow_diagram(self):
        self.assertEqual(visible(tokenize("if(x")), [("if", "if", 1, 1), ("(", "(", 1, 3), ("id", "x", 1, 4)])
        self.assertEqual(visible(tokenize("stop;")), [("stop", "stop", 1, 1), (";", ";", 1, 5)])
        self.assertEqual(visible(tokenize("pork()")), [("pork", "pork", 1, 1), ("(", "(", 1, 5), (")", ")", 1, 6)])
        result = tokenize("while(x)")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("after reserved word 'while'", result.errors[0].message)

    def test_boolean_delimiter_is_delim6(self):
        for source in ("yummy ", "yuck;", "yummy)", "yuck,", "yummy}", "yuck]", "yummy:",
                       "yuck==", "yummy!=", "yuck&&", "yummy||", "yuck+"):
            self.assertEqual(tokenize(source).errors, [], source)
        for source in ("yummy{", "yuck(", "yummy'a'"):
            result = tokenize(source)
            self.assertEqual(len(result.errors), 1, source)
            self.assertIn("(delim6)", result.errors[0].message)


class IdentifierTests(unittest.TestCase):
    def test_identifiers_including_keyword_text(self):
        result = tokenize(SNIPPETS["identifiers"])
        self.assertEqual(result.errors, [])
        tokens = visible(result)
        self.assertTrue(all(t[0] == "id" for t in tokens))
        self.assertEqual([t[1] for t in tokens], [
            "_count", "age", "studentName", "student_name", "score1",
            "meatball", "format", "iffy", "Meat", "yummy2", "abcdefghijklmnopqrst",
        ])

    def test_identifier_delimiter_follows_diagram(self):
        for source in ("add(a)", "scores[2]", "b4.title", "x;"):
            self.assertEqual(tokenize(source).errors, [], source)
        result = tokenize("{a}")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("after identifier 'a'", result.errors[0].message)


class DelimiterTableTests(unittest.TestCase):
    """Delimiter sets and diagram labels from the updated spec (pp. 73-82)."""

    def test_valid_after_symbols_and_literals(self):
        for source in ("x = {1, 2}", "i++;", "i--;", "x*2", "x+=1", "a == +b", "s = 1.5:",
                       "case 1:", "case 'A':", 'case "Play":', "if (!done) {",
                       "taste(\"&d\", &servings);", "scores[2] = 5;", "b4.title"):
            self.assertEqual(tokenize(source).errors, [], source)

    def test_symbol_and_whitespace_delimiters(self):
        # Each case is rejected by the delimiter drawn for the symbol before it.
        for source, delimiter in (("x;;", "delim20"), ("{}", "delim13"), ("a. b", "alpha_id"),
                                  ("f(_x)", "delim15"), ("a[_i]", "delim17"), ("f(a,_b)", "delim19"),
                                  ("default:x", "whitespace"), ("meat _count;", "delim25")):
            result = tokenize(source)
            self.assertEqual(len(result.errors), 1, source)
            self.assertIn(f"({delimiter})", result.errors[0].message)


class LiteralTests(unittest.TestCase):
    def test_literals(self):
        result = tokenize(SNIPPETS["literals"])
        self.assertEqual(result.errors, [])
        literals = [(t[0], t[1]) for t in visible(result) if t[0].endswith("_lit") or t[0] == "yummy"]
        self.assertEqual(literals, [
            ("meat_lit", "-15"),
            ("sauce_lit", "150.50"),
            ("chop_lit", "'A'"),
            ("chop_lit", r"'\t'"),
            ("chop_lit", "'#'"),
            ("recipe_lit", r'"Sisig\n"'),
            ("recipe_lit", '""'),
            ("yummy", "yummy"),
        ])

    def test_chop_space_is_error(self):
        result = tokenize("chop c = ' ';")
        self.assertEqual([(e.line, e.col) for e in result.errors], [(1, 10)])
        self.assertIn("cannot be a space", result.errors[0].message)
        self.assertIn((";", ";", 1, 13), visible(result))

    def test_numeric_limits(self):
        self.assertEqual(visible(tokenize("999999999999999")), [("meat_lit", "999999999999999", 1, 1)])
        self.assertEqual(visible(tokenize("999999999999.9999999")), [("sauce_lit", "999999999999.9999999", 1, 1)])

    def test_sauce_needs_digit_before_point(self):
        result = tokenize(".12345;")
        self.assertEqual([(e.line, e.col) for e in result.errors], [(1, 1)])
        self.assertIn("digit is required before the decimal point", result.errors[0].message)
        self.assertIn((";", ";", 1, 7), visible(result))
        self.assertEqual(tokenize("b4.title").errors, [])

    def test_minus_before_digit_is_part_of_literal(self):
        self.assertEqual(visible(tokenize("x-1")), [("id", "x", 1, 1), ("meat_lit", "-1", 1, 2)])
        self.assertEqual(visible(tokenize("x - 1")), [("id", "x", 1, 1), ("-", "-", 1, 3), ("meat_lit", "1", 1, 5)])


class SymbolTests(unittest.TestCase):
    def test_all_symbols(self):
        result = tokenize(SNIPPETS["symbols"])
        self.assertEqual(result.errors, [])
        self.assertEqual([t[0] for t in visible(result)], [
            "+", "-", "*", "/", "%", "++", "--", "=", "+=", "-=", "*=", "/=", "%=",
            "<", ">", "==", "!=", "<=", ">=", "!", "&&", "||", "&",
            "(", ")", "[", "]", "{", "}", ";", ",", ":",
            "id", ".", "id",
        ])

    def test_longest_match(self):
        result = tokenize(SNIPPETS["longest_match"])
        self.assertEqual(result.errors, [])
        self.assertEqual([t[1] for t in visible(result)], [
            "x", "<=", "y", "a", "==", "b", "c", "!=", "d",
            "e", "&&", "f", "g", "||", "h", "i", "+=", "j", "k", "--",
        ])


class WhitespaceAndCommentTests(unittest.TestCase):
    def test_comments_and_lines(self):
        result = tokenize(SNIPPETS["comments"])
        self.assertEqual(result.errors, [])
        self.assertEqual(visible(result), [
            ("Single-Line Comment", "// single-line comment", 1, 1),
            ("meat", "meat", 2, 1),
            ("id", "x", 2, 6),
            (";", ";", 2, 8),
            ("Multi-Line Comment", "/* multi-line\n   comment */", 2, 10),
            ("id", "x", 4, 1),
            ("=", "=", 4, 3),
            ("meat_lit", "5", 4, 5),
            (";", ";", 4, 7),
        ])

    def test_whitespace_tokens(self):
        tokens = [(t.type, t.lexeme, t.line, t.col) for t in tokenize("a \tb\nc").tokens]
        self.assertEqual(tokens, [
            ("id", "a", 1, 1), ("space", " ", 1, 2), ("tab", "\t", 1, 3),
            ("id", "b", 1, 4), ("newline", "\n", 1, 5), ("id", "c", 2, 1),
        ])

    def test_crlf_line_endings(self):
        self.assertEqual(visible(tokenize("a\r\nb")), [("id", "a", 1, 1), ("id", "b", 2, 1)])

    def test_empty_input(self):
        result = tokenize("")
        self.assertEqual((result.tokens, result.errors), ([], []))


class ErrorTests(unittest.TestCase):
    def test_errors_and_recovery(self):
        result = tokenize(SNIPPETS["errors"])
        errors = [(e.line, e.col) for e in result.errors]
        self.assertEqual(errors, [
            (1, 15), (1, 16), (2, 14), (3, 10), (4, 10), (5, 21), (6, 1), (7, 12), (8, 11),
            (9, 11), (10, 11), (11, 11), (12, 10), (13, 13), (14, 7), (15, 10), (16, 1),
        ])
        expected = [
            "Invalid delimiter '$' after space",  # delim25 has no '$'
            "Invalid character '$'",
            "Unterminated recipe literal",
            "exactly one",
            "Empty chop literal",
            r"Invalid escape '\o'",
            "limit is 20",
            "limit is 15",
            "limit is 12",
            "limit is 7",
            "multiple decimal points",
            "digit is required after the decimal point",
            "Invalid token '123abc'",
            "after reserved word 'yummy'",
            "Invalid character '|'",
            "Unterminated chop literal",
            "Unterminated multi-line comment",
        ]
        for text, error in zip(expected, result.errors):
            self.assertIn(text, error.message)
        # Recovery: tokens after each error are still produced.
        tokens = visible(result)
        self.assertIn(("meat_lit", "2", 1, 18), tokens)
        self.assertIn(("chop", "chop", 3, 1), tokens)
        self.assertIn(("id", "z", 14, 9), tokens)


if __name__ == "__main__":
    unittest.main()
