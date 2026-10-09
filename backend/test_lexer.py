"""Lexer tests for Pork CCig. Run from the project root:

    py -m unittest discover -s backend -v

Every expected value here is written by hand from the documentation
(regular definitions p. 72, delimiter table p. 73, transition diagrams
pp. 74-82). Nothing is computed from the lexer's own tables.
Every input goes through lex(), which also checks the coverage invariant.
"""

import json
import random
import string
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from pork_lexer import KEYWORDS, TOKEN_TYPES, tokenize
from server import LexerRequestHandler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def assert_full_coverage(source, result):
    """Tokens and errors, sorted by position, must spell the normalized source
    exactly (no gaps, no overlaps), and each one must sit at its stated line/col."""
    text = source.replace("\r\n", "\n").replace("\r", "\n")
    items = sorted(list(result.tokens) + list(result.errors), key=lambda x: (x.line, x.col))
    offset, line, col = 0, 1, 1
    for item in items:
        if (item.line, item.col) != (line, col):
            raise AssertionError(f"{source!r}: expected an item at {line}:{col}, found {item}")
        if not item.lexeme or text[offset:offset + len(item.lexeme)] != item.lexeme:
            raise AssertionError(f"{source!r}: {item} does not match the source at offset {offset}")
        for ch in item.lexeme:
            line, col = (line + 1, 1) if ch == "\n" else (line, col + 1)
        offset += len(item.lexeme)
    if offset != len(text):
        raise AssertionError(f"{source!r}: characters after offset {offset} are not covered")


def lex(source):
    result = tokenize(source)
    assert_full_coverage(source, result)
    for token in result.tokens:
        assert token.type in TOKEN_TYPES, token
    return result


def items(result):
    """Non-space tokens as (type, lexeme, line, col) and errors as (code, ...)."""
    out = [(t.type, t.lexeme, t.line, t.col) for t in result.tokens if t.type != "space"]
    out += [(e.code, e.lexeme, e.line, e.col) for e in result.errors]
    return sorted(out, key=lambda x: (x[2], x[3]))


def codes(result):
    return [e.code for e in result.errors]


# ---------------------------------------------------------------------------
# Hand-written character classes and delimiter sets (spec pp. 72-73)
# ---------------------------------------------------------------------------

DIGITS = "0123456789"
ALPHA = string.ascii_letters
AI = ALPHA + "_"                  # alpha_id: no digits
AN = DIGITS + ALPHA + "_"         # alpha_numeric: includes underscore
OPS = "+-*/%<>=!&|"
WS = " \t\n"

DELIM = {
    "whitespace": WS,
    "delim1": ";" + WS,
    "delim2": ":" + WS,
    "delim3": "{" + WS,
    "delim4": "(" + WS,
    "delim5": ",({;" + WS,
    "delim6": OPS + "})]:;," + WS,
    "delim7": AN + "+-!{('\"" + WS,
    "delim8": AN + "+-!('\"" + WS,
    "delim9": AN + "-!('\"" + WS,
    "delim10": AI + "()],;" + WS,
    "delim11": AN + "+-!(" + WS,
    "delim13": AN + "+-!{(/'\"" + WS,
    "delim14": ALPHA + "_};," + WS,
    "delim15": AN + "-+!()'\"" + WS,
    "delim16": OPS + "{)[].,:;" + WS,
    "delim17": AN + "+-!(]'\"" + WS,
    "delim18": OPS + ")[],;" + WS,
    "delim19": AN + "{+-&'\"" + WS,
    "delim20": AN + "}+-" + WS,
    "delim21": OPS + "()[].,;" + WS,
    "delim22": OPS + ")]},:;" + WS,
    "delim23": OPS + "):]},;" + WS,
    "delim25": AN + OPS + "{}()[]:;,'\"" + WS,
    "alpha_id": AI,
}

KEYWORD_DELIM = {
    "meat": "whitespace", "sauce": "whitespace", "chop": "whitespace",
    "recipe": "whitespace", "cooked": "whitespace", "empty": "whitespace",
    "menu": "whitespace", "if": "delim4", "else": "delim3", "switch": "delim4",
    "case": "delim2", "default": "delim2", "for": "delim4", "while": "whitespace",
    "do": "delim3", "stop": "delim1", "again": "delim1", "serveback": "whitespace",
    "pork": "delim5", "serve": "delim4", "taste": "delim4", "yummy": "delim6",
    "yuck": "delim6", "fixed": "whitespace",
}

SYMBOL_DELIM = {
    "=": "delim7", "==": "delim8", "+": "delim9", "++": "delim10", "+=": "delim11",
    "-": "delim11", "--": "delim10", "-=": "delim11", "*": "delim11", "*=": "delim11",
    "/": "delim11", "/=": "delim11", "%": "delim11", "%=": "delim11",
    ">": "delim8", ">=": "delim8", "<": "delim8", "<=": "delim8",
    "!": "delim8", "!=": "delim8", "&": "delim8", "&&": "delim8", "||": "delim8",
    "{": "delim13", "}": "delim14", "(": "delim15", ")": "delim16",
    "[": "delim17", "]": "delim18", ".": "alpha_id", ",": "delim19",
    ":": "whitespace", ";": "delim20",
}

# Next characters that turn a symbol into a longer token (maximal munch), so
# the symbol itself never ends there.
SYMBOL_MUNCH = {
    "=": "=", "+": "+=", "-": "-=", "*": "=", "/": "=/*", "%": "=",
    ">": "=", "<": "=", "!": "=", "&": "&",
}

# Characters that cannot start any token (they are LEX-901).
NO_TOKEN_START = "@$#`~?^\\"

NEXT_CHARS = [chr(c) for c in range(32, 127)] + ["\t", "\n"]

# ---------------------------------------------------------------------------
# A. Every token kind with type, lexeme, line and col
# ---------------------------------------------------------------------------


class TokenRecognitionTests(unittest.TestCase):
    def test_each_reserved_word(self):
        self.assertEqual(len(KEYWORD_DELIM), 24)
        self.assertEqual(sorted(k.word for k in KEYWORDS), sorted(KEYWORD_DELIM))
        for word in KEYWORD_DELIM:
            self.assertEqual(items(lex(word)), [(word, word, 1, 1)], word)

    def test_reserved_words_are_lowercase_and_whole(self):
        self.assertEqual(items(lex("Meat IF true meatball")), [
            ("id", "Meat", 1, 1), ("id", "IF", 1, 6), ("id", "true", 1, 9), ("id", "meatball", 1, 14),
        ])

    def test_each_symbol(self):
        self.assertEqual(len(SYMBOL_DELIM), 33)
        for symbol in SYMBOL_DELIM:
            self.assertEqual(items(lex(symbol)), [(symbol, symbol, 1, 1)], symbol)

    def test_longest_match(self):
        self.assertEqual([t[0] for t in items(lex("x<=y a==b c!=d e&&f g||h i+=j k--"))], [
            "id", "<=", "id", "id", "==", "id", "id", "!=", "id", "id", "&&", "id",
            "id", "||", "id", "id", "+=", "id", "id", "--",
        ])

    def test_whitespace_tokens(self):
        result = lex("a \tb\nc")
        self.assertEqual([(t.type, t.lexeme, t.line, t.col) for t in result.tokens], [
            ("id", "a", 1, 1), ("space", " ", 1, 2), ("tab", "\t", 1, 3),
            ("id", "b", 1, 4), ("newline", "\n", 1, 5), ("id", "c", 2, 1),
        ])

    def test_line_and_col_after_lf_and_crlf(self):
        for source in ("meat x;\r\n  sauce y;\n\tz", "meat x;\r  sauce y;\n\tz"):
            result = lex(source)
            self.assertEqual(result.errors, [])
            self.assertEqual([(t.type, t.line, t.col) for t in result.tokens], [
                ("meat", 1, 1), ("space", 1, 5), ("id", 1, 6), (";", 1, 7), ("newline", 1, 8),
                ("space", 2, 1), ("space", 2, 2), ("sauce", 2, 3), ("space", 2, 8),
                ("id", 2, 9), (";", 2, 10), ("newline", 2, 11), ("tab", 3, 1), ("id", 3, 2),
            ], repr(source))

    def test_literal_kinds(self):
        result = lex("x = -15;\ny = 150.50;\nc = 'A';\nd = '\\t';\ns = \"Sisig\\n\";\ne = \"\";\nb = yummy;")
        self.assertEqual(result.errors, [])
        literals = [t for t in items(result) if t[0].endswith("_lit") or t[0] == "yummy"]
        self.assertEqual(literals, [
            ("meat_lit", "-15", 1, 5),
            ("sauce_lit", "150.50", 2, 5),
            ("chop_lit", "'A'", 3, 5),
            ("chop_lit", "'\\t'", 4, 5),
            ("recipe_lit", '"Sisig\\n"', 5, 5),
            ("recipe_lit", '""', 6, 5),
            ("yummy", "yummy", 7, 5),
        ])

    def test_comments(self):
        result = lex("// single-line comment\nmeat x ; /* multi-line\n   comment */\nx = 5 ;")
        self.assertEqual(result.errors, [])
        self.assertEqual(items(result), [
            ("Single-Line Comment", "// single-line comment", 1, 1),
            ("newline", "\n", 1, 23),
            ("meat", "meat", 2, 1), ("id", "x", 2, 6), (";", ";", 2, 8),
            ("Multi-Line Comment", "/* multi-line\n   comment */", 2, 10),
            ("newline", "\n", 3, 14),
            ("id", "x", 4, 1), ("=", "=", 4, 3), ("meat_lit", "5", 4, 5), (";", ";", 4, 7),
        ])

    def test_empty_input(self):
        result = lex("")
        self.assertEqual((result.tokens, result.errors), ([], []))

    def test_errors_are_never_tokens(self):
        result = lex("meat x = 5 @ 3;")
        self.assertNotIn("@", [t.lexeme for t in result.tokens])
        self.assertEqual(codes(result), ["LEX-901"])


# ---------------------------------------------------------------------------
# B. Delimiter matrix: every token kind against every possible next character
# ---------------------------------------------------------------------------


class DelimiterMatrixTests(unittest.TestCase):
    def check(self, prefix, text, token_type, allowed, never=""):
        """`text` after `prefix`, then each next char. The token must be emitted
        exactly when the next char is allowed (and does not extend the token)."""
        col = len(prefix) + 1
        for c in NEXT_CHARS:
            result = lex(prefix + text + c)
            at = [(t.type, t.lexeme) for t in result.tokens if (t.line, t.col) == (1, col)]
            accepted = at == [(token_type, text)]
            expected = c in allowed and c not in never
            self.assertEqual(accepted, expected, f"{prefix + text!r} followed by {c!r}")

    def test_keywords(self):
        for word, delim in KEYWORD_DELIM.items():
            self.check("", word, word, DELIM[delim], never=AN)

    def test_symbols(self):
        for symbol, delim in SYMBOL_DELIM.items():
            self.check("x ", symbol, symbol, DELIM[delim], never=SYMBOL_MUNCH.get(symbol, ""))

    def test_identifier(self):
        self.check("", "x", "id", DELIM["delim21"], never=AN)

    def test_numbers(self):
        self.check("", "5", "meat_lit", DELIM["delim22"], never=DIGITS)
        self.check("", "1.5", "sauce_lit", DELIM["delim22"], never=DIGITS)

    def test_chop_and_recipe(self):
        self.check("", "'a'", "chop_lit", DELIM["delim22"])
        self.check("", '"s"', "recipe_lit", DELIM["delim23"])

    def test_space(self):
        # A character that starts no token is reported once as LEX-901, so the
        # space before it is still a valid token.
        self.check("x", " ", "space", DELIM["delim25"] + NO_TOKEN_START)

    def test_underscore_and_digit_consequences(self):
        for source in ("meat _count;", "f(_x)", "a[_i]", "f(a,_b)", "x = _y", "a.b"):
            self.assertEqual(lex(source).errors, [], source)
        self.assertEqual(items(lex("x++5")), [
            ("id", "x", 1, 1), ("LEX-602", "++", 1, 2), ("meat_lit", "5", 1, 4),
        ])
        self.assertEqual(codes(lex("a.5")), ["LEX-105"])


# ---------------------------------------------------------------------------
# C. Boundaries
# ---------------------------------------------------------------------------


class BoundaryTests(unittest.TestCase):
    def test_meat_digits(self):
        for sign in ("", "-"):
            for n in (14, 15):
                source = sign + "9" * n
                self.assertEqual(items(lex(source)), [("meat_lit", source, 1, 1)], source)
            source = sign + "9" * 16
            self.assertEqual(items(lex(source)), [
                ("LEX-101", sign + "9" * 15, 1, 1), ("meat_lit", "9", 1, 16 + len(sign)),
            ], source)

    def test_sauce_whole_part(self):
        for n in (11, 12):
            source = "9" * n + ".5"
            self.assertEqual(items(lex(source)), [("sauce_lit", source, 1, 1)], source)
        self.assertEqual(items(lex("9" * 13 + ".5")), [
            ("LEX-102", "9" * 13, 1, 1), ("LEX-105", ".", 1, 14), ("meat_lit", "5", 1, 15),
        ])

    def test_sauce_fraction(self):
        for n in (6, 7):
            source = "1." + "9" * n
            self.assertEqual(items(lex(source)), [("sauce_lit", source, 1, 1)], source)
        self.assertEqual(items(lex("1." + "9" * 8)), [
            ("LEX-103", "1.9999999", 1, 1), ("meat_lit", "9", 1, 10),
        ])

    def test_identifier_length(self):
        for n in (19, 20):
            source = "a" * n
            self.assertEqual(items(lex(source)), [("id", source, 1, 1)], source)
        self.assertEqual(items(lex("a" * 21)), [
            ("LEX-501", "a" * 20, 1, 1), ("id", "a", 1, 21),
        ])

    def test_every_escape(self):
        for esc in ("n", "t", "'", '"', "\\", "0"):
            chop = "'\\" + esc + "'"
            self.assertEqual(items(lex(chop)), [("chop_lit", chop, 1, 1)], chop)
            recipe = '"a\\' + esc + 'b"'
            self.assertEqual(items(lex(recipe)), [("recipe_lit", recipe, 1, 1)], recipe)
        self.assertEqual(codes(lex("'\\q'")), ["LEX-204"])
        self.assertEqual(codes(lex('"\\q"')), ["LEX-302"])

    def test_leading_and_trailing_zeros_count(self):
        self.assertEqual(codes(lex("0" * 16)), ["LEX-101"])
        self.assertEqual(codes(lex("1." + "0" * 8)), ["LEX-103"])


# ---------------------------------------------------------------------------
# Error catalog: code, status, title and exact message
# ---------------------------------------------------------------------------


class ErrorCatalogTests(unittest.TestCase):
    CASES = (
        ("1234567890123456", "LEX-101", "Invalid", "Invalid numerical value",
         "'123456789012345' exceeds the 15-digit integer limit."),
        ("1234567890123.5", "LEX-102", "Invalid", "Invalid decimal value",
         "The whole-number part of '1234567890123' exceeds the 12-digit limit for decimal values."),
        ("1.12345678", "LEX-103", "Invalid", "Invalid decimal value",
         "The fractional part of '1.1234567' exceeds the 7-digit limit."),
        ("5.", "LEX-104", "Incomplete", "Incomplete decimal",
         "'5.' must have at least one digit after the decimal point."),
        (".5", "LEX-105", "Incomplete", "Incomplete decimal",
         "A decimal value must have at least one digit before the decimal point."),
        ("1.5.2", "LEX-106", "Invalid", "Invalid decimal value",
         "'1.5' cannot contain more than one decimal point."),
        ("12abc", "LEX-107", "Invalid", "Invalid identifier",
         "'12' is followed by 'a'; identifiers cannot begin with a digit."),
        ("5{", "LEX-108", "Invalid", "Invalid delimiter",
         "'{' cannot follow the numeric literal '5'."),
        ("'a", "LEX-201", "Incomplete", "Incomplete character literal",
         "Missing closing single quote (')."),
        ("''", "LEX-202", "Invalid", "Invalid character literal",
         "A character literal cannot be empty."),
        ("'ab'", "LEX-203", "Invalid", "Invalid character literal",
         "'ab' contains more than one character; use a recipe (string) instead."),
        ("'\\q'", "LEX-204", "Invalid", "Invalid escape sequence",
         "'\\q' is not a valid escape sequence."),
        ("'a'x", "LEX-205", "Invalid", "Invalid delimiter",
         "'x' cannot follow the character literal 'a'."),
        ("' '", "LEX-206", "Invalid", "Invalid character literal",
         "A chop value cannot be a space."),
        ('"ab', "LEX-301", "Incomplete", "Incomplete string literal",
         'Missing closing double quote (").'),
        ('"a\\qb"', "LEX-302", "Invalid", "Invalid escape sequence",
         "'\\q' is not a valid escape sequence in \"a\\qb\"."),
        ('"s"x', "LEX-303", "Invalid", "Invalid delimiter",
         "'x' cannot follow the string literal \"s\"."),
        ("meat;", "LEX-401", "Invalid", "Invalid delimiter",
         "';' cannot follow the reserved word 'meat'."),
        ("a" * 21, "LEX-501", "Invalid", "Invalid identifier",
         "'" + "a" * 20 + "' exceeds the 20-character identifier limit."),
        ("a{", "LEX-502", "Invalid", "Invalid delimiter",
         "'{' cannot follow the identifier 'a'."),
        ("|", "LEX-601", "Incomplete", "Incomplete operator",
         "'|' must be followed by '|' to form the logical OR operator (||)."),
        (";;", "LEX-602", "Invalid", "Invalid delimiter",
         "';' cannot follow ';'."),
        ("x .", "LEX-602", "Invalid", "Invalid delimiter",
         "'.' cannot follow space."),
        ("/* a", "LEX-701", "Incomplete", "Incomplete comment",
         "Multi-line comment is missing its closing '*/'."),
        ("// caf\u00e9", "LEX-702", "Invalid", "Invalid comment character",
         "U+00E9 is not allowed inside a comment."),
        ("/* a */x", "LEX-703", "Invalid", "Invalid delimiter",
         "'x' cannot follow a multi-line comment."),
        ("@", "LEX-901", "Invalid", "Invalid character",
         "'@' is not a valid character."),
    )

    def test_catalog(self):
        for source, code, status, title, message in self.CASES:
            error = lex(source).errors[0]
            self.assertEqual((error.code, error.status, error.title, error.message),
                             (code, status, title, message), source)

    def test_readable_characters(self):
        self.assertEqual(lex("a.\n").errors[0].message, "newline cannot follow '.'.")
        self.assertEqual(lex("a.\t").errors[0].message, "tab cannot follow '.'.")


# ---------------------------------------------------------------------------
# D/E. Fuzz: tokenize never raises and coverage always holds
# ---------------------------------------------------------------------------


class FuzzTests(unittest.TestCase):
    FRAGMENTS = ["meat", "sauce", "x", "_a", "123", "-", "9" * 16, ".", "'", '"', "\\", ";",
                 "/*", "*/", "//", "|", "@", " ", "\n", "\t", "==", "1.5", "yummy", "(", "]",
                 "++", "-5", "abcdefghijklmnopqrstuv"]

    def test_fuzz(self):
        rng = random.Random(42)
        for _ in range(5000):
            source = "".join(rng.choice(self.FRAGMENTS) for _ in range(rng.randint(1, 12)))
            lex(source)  # raises on any exception or coverage failure


# ---------------------------------------------------------------------------
# F. The HTTP endpoint returns exactly what tokenize() returns
# ---------------------------------------------------------------------------


class _QuietHandler(LexerRequestHandler):
    def log_message(self, *args):
        pass


class EndpointTests(unittest.TestCase):
    def test_api_lex_matches_tokenize(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _QuietHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            source = "meat x = 12abc;\r\nchop c = ' ';\nsauce s = 1.5; // ok"
            request = urllib.request.Request(
                f"http://127.0.0.1:{server.server_address[1]}/api/lex",
                data=json.dumps({"source": source}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                body = json.loads(response.read())
            self.assertEqual(body, lex(source).to_dict())
            self.assertEqual(set(body["errors"][0]),
                             {"code", "status", "title", "line", "col", "lexeme", "message"})
        finally:
            server.shutdown()
            server.server_close()


# ---------------------------------------------------------------------------
# G. Required cases (positions are line 1). Each listed item must appear, and
#    the error codes must be exactly the listed ones, in order.
# ---------------------------------------------------------------------------


class RequiredCaseTests(unittest.TestCase):
    CASES = (
        ("sauce a = 123456789000.1234567", [("sauce_lit", "123456789000.1234567", 11)], []),
        ("sauce a = 12345678900000000.1234567890000",
         [("LEX-101", "123456789000000", 11), ("LEX-103", "00.1234567", 26), ("meat_lit", "890000", 36)],
         ["LEX-101", "LEX-103"]),
        ("sauce a = 1234567890000.1",
         [("LEX-102", "1234567890000", 11), ("LEX-105", ".", 24), ("meat_lit", "1", 25)],
         ["LEX-102", "LEX-105"]),
        ("sauce a = 123456789000.12345678",
         [("LEX-103", "123456789000.1234567", 11), ("meat_lit", "8", 31)], ["LEX-103"]),
        ("sauce a = 5.;", [("LEX-104", "5.", 11), (";", ";", 13)], ["LEX-104"]),
        ("sauce a = 1.5.2;",
         [("LEX-106", "1.5", 11), ("LEX-105", ".", 14), ("meat_lit", "2", 15), (";", ";", 16)],
         ["LEX-106", "LEX-105"]),
        ("meat x = 1234567890123456;",
         [("LEX-101", "123456789012345", 10), ("meat_lit", "6", 25), (";", ";", 26)], ["LEX-101"]),
        ("meat x = 123456789012345;", [("meat_lit", "123456789012345", 10), (";", ";", 25)], []),
        ("meat x = -123456789012345;", [("meat_lit", "-123456789012345", 10), (";", ";", 26)], []),
        ("-1234567890123456;",
         [("LEX-101", "-123456789012345", 1), ("meat_lit", "6", 17), (";", ";", 18)], ["LEX-101"]),
        ("meat x = 12abc;", [("LEX-107", "12", 10), ("id", "abc", 12), (";", ";", 15)], ["LEX-107"]),
        ("99-1", [("meat_lit", "99", 1), ("-", "-", 3), ("meat_lit", "1", 4)], []),
        ("99 - -1", [("meat_lit", "99", 1), ("-", "-", 4), ("meat_lit", "-1", 6)], []),
        ("meat x = -5;", [("meat_lit", "-5", 10), (";", ";", 12)], []),
        ("x-1", [("id", "x", 1), ("-", "-", 2), ("meat_lit", "1", 3)], []),
        ("(-1)", [("(", "(", 1), ("meat_lit", "-1", 2), (")", ")", 4)], []),
        ("meat;;", [("LEX-401", "meat", 1), ("LEX-602", ";", 5), (";", ";", 6)], ["LEX-401", "LEX-602"]),
        ("meat a = 5;meat b = 2;", [(";", ";", 11), ("meat", "meat", 12), (";", ";", 22)], []),
        ("meat _count;", [("id", "_count", 6)], []),
        ("meat abcdefghijklmnopqrstu = 1;",
         [("LEX-501", "abcdefghijklmnopqrst", 6), ("id", "u", 26), ("=", "=", 28),
          ("meat_lit", "1", 30), (";", ";", 31)], ["LEX-501"]),
        ("chop c = 'ab';", [("LEX-203", "'ab'", 10), (";", ";", 14)], ["LEX-203"]),
        ("chop c = '';", [("LEX-202", "''", 10), (";", ";", 12)], ["LEX-202"]),
        ("chop c = ' ';", [("LEX-206", "' '", 10), (";", ";", 13)], ["LEX-206"]),
        ('recipe s = "hello;', [("LEX-301", '"hello;', 12)], ["LEX-301"]),
        ('recipe s = "Good M\\orning";', [("LEX-302", '"Good M\\orning"', 12), (";", ";", 27)], ["LEX-302"]),
        ("a | b", [("id", "a", 1), ("LEX-601", "|", 3), ("id", "b", 5)], ["LEX-601"]),
        ("meat x = 5 @ 3;", [("LEX-901", "@", 12), ("meat_lit", "3", 14), (";", ";", 15)], ["LEX-901"]),
        ("/* comment", [("LEX-701", "/* comment", 1)], ["LEX-701"]),
        ("cooked ok = true;", [("id", "true", 13)], []),
        ("meat price = 150; // note", [("Single-Line Comment", "// note", 19)], []),
        ("x++5", [("id", "x", 1), ("LEX-602", "++", 2), ("meat_lit", "5", 4)], ["LEX-602"]),
        (".5", [("LEX-105", ".", 1), ("meat_lit", "5", 2)], ["LEX-105"]),
    )

    def test_required_cases(self):
        self.assertEqual(len(self.CASES), 32)
        for source, expected, expected_codes in self.CASES:
            result = lex(source)
            found = [(kind, lexeme, col) for kind, lexeme, _, col in items(result)]
            for item in expected:
                self.assertIn(item, found, source)
            self.assertEqual(codes(result), expected_codes, source)


if __name__ == "__main__":
    unittest.main()
