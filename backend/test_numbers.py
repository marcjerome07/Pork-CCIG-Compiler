"""Number literal tests (meat_lit / sauce_lit). Run from the project root:

    py -m unittest discover -s backend -v

Names in the spec map to the lexer's token types: INT_LIT = meat_lit,
FLOAT_LIT = sauce_lit, IDENTIFIER = id, MINUS = "-", PLUS = "+",
SEMICOLON = ";", LPAREN = "(", RPAREN = ")". INVALID numbers are not tokens:
they are errors (code + whole lexeme), as the group decided (Q2).
"""

import unittest

from pork_lexer import tokenize
from test_lexer import assert_full_coverage

# (source, expected items in column order). Tokens are (type, lexeme, col);
# errors are (code, lexeme, col). All on line 1; whitespace tokens omitted.
CASES = (
    # Valid numbers.
    ("3.14", [("sauce_lit", "3.14", 1)]),
    ("42", [("meat_lit", "42", 1)]),
    ("0.5", [("sauce_lit", "0.5", 1)]),
    ("-3.14", [("sauce_lit", "-3.14", 1)]),
    ("x-3.14", [("id", "x", 1), ("-", "-", 2), ("sauce_lit", "3.14", 3)]),
    ("3.14;", [("sauce_lit", "3.14", 1), (";", ";", 5)]),
    ("(2.5)", [("(", "(", 1), ("sauce_lit", "2.5", 2), (")", ")", 5)]),
    ("1.5+2.5", [("sauce_lit", "1.5", 1), ("+", "+", 4), ("sauce_lit", "2.5", 5)]),
    ("007", [("meat_lit", "007", 1)]),                   # leading zeros allowed (meat rule 8)
    ("000000.1", [("sauce_lit", "000000.1", 1)]),         # 6 whole digits: valid (doc table is wrong)
    # Malformed numbers: the whole chunk up to a delim22 character is ONE error.
    ("12.3.4", [("LEX-106", "12.3.4", 1)]),
    ("12.3.4;", [("LEX-106", "12.3.4", 1), (";", ";", 7)]),
    ("5.", [("LEX-104", "5.", 1)]),
    ("5.;", [("LEX-104", "5.", 1), (";", ";", 3)]),
    ("3.14abc", [("LEX-107", "3.14abc", 1)]),
    ("12abc", [("LEX-107", "12abc", 1)]),
    ("1..2", [("LEX-104", "1..2", 1)]),
    (".5", [("LEX-105", ".5", 1)]),                       # sauce rule 7
    (".5;", [("LEX-105", ".5", 1), (";", ";", 3)]),
    ("-12abc;", [("LEX-107", "-12abc", 1), (";", ";", 7)]),
    ("x = 12.3.4 + 1;", [("id", "x", 1), ("=", "=", 3), ("LEX-106", "12.3.4", 5),
                         ("+", "+", 12), ("meat_lit", "1", 14), (";", ";", 15)]),
    # Digit limits keep the professor's restart rule; leading zeros count.
    ("1234567890123456", [("LEX-101", "123456789012345", 1), ("meat_lit", "6", 16)]),
    ("1234567890000.1", [("LEX-102", "1234567890000", 1), ("LEX-105", ".1", 14)]),
    ("0000000000000.1", [("LEX-102", "0000000000000", 1), ("LEX-105", ".1", 14)]),
    ("12345678.87654321", [("LEX-103", "12345678.8765432", 1), ("meat_lit", "1", 17)]),
    # "-" then ".": the document's delim11 has no ".", so the "-" is also an error.
    ("-.5", [("LEX-602", "-", 1), ("LEX-105", ".5", 2)]),
)


def items(result):
    found = [(t.type, t.lexeme, t.col) for t in result.tokens
             if t.type not in ("space", "tab", "newline")]
    found += [(e.code, e.lexeme, e.col) for e in result.errors]
    return sorted(found, key=lambda item: item[2])


class NumberLiteralTests(unittest.TestCase):
    def test_cases(self):
        for source, expected in CASES:
            with self.subTest(source=source):
                result = tokenize(source)
                assert_full_coverage(source, result)
                self.assertEqual(items(result), expected)

    def test_chunk_never_includes_the_delimiter(self):
        for source, delimiter in (("12.3.4;", ";"), ("12abc)", ")"), ("5.,", ","), ("1..2 x", " ")):
            with self.subTest(source=source):
                result = tokenize(source)
                self.assertNotIn(delimiter, result.errors[0].lexeme)

    def test_errors_are_not_tokens(self):
        result = tokenize("12.3.4;")
        self.assertEqual([t.type for t in result.tokens], [";"])
        self.assertEqual(result.errors[0].message, "LEX-106 (Ln 1, Col 1): Invalid '12.3.4'")


if __name__ == "__main__":
    unittest.main()
