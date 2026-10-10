"""Minus rule tests: decrement "--", minus "-" and negative literals.
Run from the project root:

    py -m unittest discover -s backend -v

The prompt's names map to the lexer's token types like this:
INT_LIT = meat_lit, FLOAT_LIT = sauce_lit, IDENTIFIER = id, DECREMENT = "--",
MINUS = "-", ASSIGN = "=", LPAREN = "(", RPAREN = ")", LBRACKET = "[", RBRACKET = "]".
"""

import unittest

from pork_lexer import tokenize
from test_lexer import assert_full_coverage

# (source, expected non-whitespace tokens as (type, lexeme, col)), all on line 1.
CASES = (
    ("-234", [("meat_lit", "-234", 1)]),
    ("--234", [("--", "--", 1), ("meat_lit", "234", 3)]),
    ("---234", [("--", "--", 1), ("meat_lit", "-234", 3)]),
    ("x-234", [("id", "x", 1), ("-", "-", 2), ("meat_lit", "234", 3)]),
    ("x - 234", [("id", "x", 1), ("-", "-", 3), ("meat_lit", "234", 5)]),
    ("x = -234", [("id", "x", 1), ("=", "=", 3), ("meat_lit", "-234", 5)]),
    ("(-234)", [("(", "(", 1), ("meat_lit", "-234", 2), (")", ")", 6)]),
    ("a[i]-5", [("id", "a", 1), ("[", "[", 2), ("id", "i", 3), ("]", "]", 4),
                ("-", "-", 5), ("meat_lit", "5", 6)]),
    ("x--", [("id", "x", 1), ("--", "--", 2)]),
    ("5 - -3", [("meat_lit", "5", 1), ("-", "-", 3), ("meat_lit", "-3", 5)]),
    ("-3.14", [("sauce_lit", "-3.14", 1)]),
    ("-x", [("-", "-", 1), ("id", "x", 2)]),
)


def visible(result):
    return [(t.type, t.lexeme, t.col) for t in result.tokens
            if t.type not in ("space", "tab", "newline")]


class MinusRuleTests(unittest.TestCase):
    def test_cases(self):
        for source, expected in CASES:
            with self.subTest(source=source):
                result = tokenize(source)
                assert_full_coverage(source, result)
                self.assertEqual(result.errors, [])
                self.assertEqual(visible(result), expected)

    def test_lookback_skips_whitespace_and_comments(self):
        for source in ("x\n\t - 5", "x /* note */ - 5", "x // note\n- 5"):
            with self.subTest(source=source):
                self.assertEqual([t[0] for t in visible(tokenize(source)) if "Comment" not in t[0]],
                                 ["id", "-", "meat_lit"])

    def test_negative_literal_column_and_line(self):
        token = [t for t in tokenize("meat a;\n  x = -42;").tokens if t.type == "meat_lit"][0]
        self.assertEqual((token.lexeme, token.line, token.col), ("-42", 2, 7))

    def test_minus_assign_is_longest_match(self):
        self.assertEqual(visible(tokenize("x-=1")), [("id", "x", 1), ("-=", "-=", 2), ("meat_lit", "1", 4)])

    def test_increment_keeps_doc_delimiter(self):
        # Only "--" got the exception; "++" still follows delim10 (p. 73).
        self.assertEqual([e.code for e in tokenize("x++5").errors], ["LEX-602"])


if __name__ == "__main__":
    unittest.main()
