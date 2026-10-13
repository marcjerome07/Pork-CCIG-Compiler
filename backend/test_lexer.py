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

from pork_lexer import KEYWORDS, UNAVAILABLE, is_token_type, tokenize
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


def base_type(token_type):
    """id1, id2, ... -> id, so position tests don't depend on the numbering."""
    return "id" if token_type.startswith("id") and token_type[2:].isdigit() else token_type


def lex(source):
    result = tokenize(source)
    assert_full_coverage(source, result)
    for token in result.tokens:
        assert is_token_type(token.type), token
    return result


def items(result):
    """Non-space tokens as (type, lexeme, line, col) and errors as (code, ...).
    Numbered identifiers are written as plain "id"."""
    out = [(base_type(t.type), t.lexeme, t.line, t.col) for t in result.tokens if t.type != "space"]
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

# Characters that cannot start any token (LEX-901, or LEX-902 for $ ? @ ^).
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
            ("id1", "a", 1, 1), ("space", " ", 1, 2), ("tab", "\t", 1, 3),
            ("id2", "b", 1, 4), ("newline", "\n", 1, 5), ("id3", "c", 2, 1),
        ])

    def test_line_and_col_after_lf_and_crlf(self):
        for source in ("meat x;\r\n  sauce y;\n\tz", "meat x;\r  sauce y;\n\tz"):
            result = lex(source)
            self.assertEqual(result.errors, [])
            self.assertEqual([(t.type, t.line, t.col) for t in result.tokens], [
                ("meat", 1, 1), ("space", 1, 5), ("id1", 1, 6), (";", 1, 7), ("newline", 1, 8),
                ("space", 2, 1), ("space", 2, 2), ("sauce", 2, 3), ("space", 2, 8),
                ("id2", 2, 9), (";", 2, 10), ("newline", 2, 11), ("tab", 3, 1), ("id3", 3, 2),
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
        self.assertEqual(codes(result), ["LEX-902"])

    def test_comment_may_follow_any_token(self):
        # Group decision: "//" or "/*" right after a token is always allowed.
        self.assertEqual(items(lex("x=5;//No spaces anywhere")), [
            ("id", "x", 1, 1), ("=", "=", 1, 2), ("meat_lit", "5", 1, 3), (";", ";", 1, 4),
            ("Single-Line Comment", "//No spaces anywhere", 1, 5),
        ])
        for source in ("meat x;/* note */", "stop;//done", "serve(x)//out", "x++//inc", "'a'//c"):
            self.assertEqual(lex(source).errors, [], source)
        # A lone "/" still follows the delimiter table: ";/" is not allowed.
        self.assertEqual(codes(lex("x;/2")), ["LEX-602"])


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
            at = [(base_type(t.type), t.lexeme) for t in result.tokens if (t.line, t.col) == (1, col)]
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
        # A character that starts no token is reported once (LEX-901/902), so the
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
        # Sauce rule 8 (October 16, 2026 version): up to 15 whole digits.
        for n in (13, 14, 15):
            source = "9" * n + ".5"
            self.assertEqual(items(lex(source)), [("sauce_lit", source, 1, 1)], source)
        # A 16th whole digit is LEX-102 (professor's restart rule).
        self.assertEqual(items(lex("9" * 16 + ".5")), [
            ("LEX-102", "9" * 15, 1, 1), ("sauce_lit", "9.5", 1, 16),
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
# Error messages: Line <n>, Col <n>: <Error message> '<lexeme>'
# ---------------------------------------------------------------------------


class ErrorMessageTests(unittest.TestCase):
    CASES = (
        # MEAT
        ("12a", "Line 1, Col 1: Invalid numerical value '12a'"),
        ("1234567890123456", "Line 1, Col 1: Meat value exceeds 15 digits '123456789012345'"),
        # SAUCE
        ("12.", "Line 1, Col 1: Incomplete decimal value '12.'"),
        (".5", "Line 1, Col 1: Incomplete decimal value '.5'"),
        ("1.2.3", "Line 1, Col 1: Multiple decimal points '1.2.3'"),
        ("1..2", "Line 1, Col 1: Multiple decimal points '1..2'"),
        ("1234567890123456.5", "Line 1, Col 1: Sauce whole part exceeds 15 digits '123456789012345'"),
        ("1.12345678", "Line 1, Col 1: Sauce decimal part exceeds 7 digits '1.1234567'"),
        # CHOP
        ("''", "Line 1, Col 1: Empty character value ''''"),
        ("'a", "Line 1, Col 1: Unclosed character value ''a'"),
        ("'ab'", "Line 1, Col 1: Too many characters in chop value ''ab''"),
        ("'\\q'", "Line 1, Col 1: Invalid escape sequence ''\\q''"),
        # RECIPE
        ('"Hello', "Line 1, Col 1: Unclosed string value '\"Hello'"),
        ('"Good M\\orning"', "Line 1, Col 1: Invalid escape sequence '\"Good M\\orning\"'"),
        # COOKED
        ("yummy(1)", "Line 1, Col 1: Invalid boolean value 'yummy'"),
        ("yuck{", "Line 1, Col 1: Invalid boolean value 'yuck'"),
        # IDENTIFIER
        ("a" * 21, "Line 1, Col 1: Identifier exceeds 20 characters '" + "a" * 20 + "'"),
        ("a$b", "Line 1, Col 1: Invalid identifier 'a$b'"),
        ("x#1y", "Line 1, Col 1: Invalid identifier 'x#1y'"),
        # GENERAL
        ("@", "Line 1, Col 1: Unavailable character '@'"),
        ("meat x;\n  $", "Line 2, Col 3: Unavailable character '$'"),
        ("chop c = '?';", "Line 1, Col 11: Unavailable character '?'"),
        ("#", "Line 1, Col 1: Invalid character '#'"),
        ("|", "Line 1, Col 1: Invalid character '|'"),
        ("// café", "Line 1, Col 7: Invalid character 'é'"),
        ("'a'x", "Line 1, Col 1: Invalid delimiter ''a''"),
        ('"s"x', "Line 1, Col 1: Invalid delimiter '\"s\"'"),
        ("5{", "Line 1, Col 1: Invalid delimiter '5'"),
        ("meat;", "Line 1, Col 1: Invalid delimiter 'meat'"),
        ("a{", "Line 1, Col 1: Invalid delimiter 'a'"),
        (";;", "Line 1, Col 1: Invalid delimiter ';'"),
        ("x .", "Line 1, Col 2: Invalid delimiter ' '"),
        ("/* a */x", "Line 1, Col 1: Invalid delimiter '/* a */'"),
        # Comments (not in the list): unclosed multi-line comment
        ("/* a", "Line 1, Col 1: Unclosed comment '/* a'"),
    )

    def test_messages(self):
        for source, message in self.CASES:
            with self.subTest(source=source):
                errors = lex(source).errors
                self.assertEqual(len(errors), 1, [e.message for e in errors])
                self.assertEqual(errors[0].message, message)

    def test_status_counts_unavailable_separately(self):
        for source, _ in self.CASES:
            error = lex(source).errors[0]
            expected = "Unavailable" if error.code == "LEX-902" else "Invalid"
            self.assertEqual(error.status, expected, source)

    def test_unterminated_literals_and_comments_are_shortened(self):
        # The first 10 characters of the lexeme, then "..."; 10 or fewer stay whole.
        self.assertEqual(lex('"Hello there, friend').errors[0].message,
                         "Line 1, Col 1: Unclosed string value '\"Hello the...'")
        self.assertEqual(lex("'abcdefghijklmn").errors[0].message,
                         "Line 1, Col 1: Unclosed character value ''abcdefghi...'")
        self.assertEqual(lex("/* never closed\nstill").errors[0].message,
                         "Line 1, Col 1: Unclosed comment '/* never c...'")
        self.assertEqual(lex('"123456789').errors[0].message,
                         "Line 1, Col 1: Unclosed string value '\"123456789'")

    def test_newline_and_tab_are_written_as_escapes(self):
        self.assertEqual(lex("x\n.").errors[0].message, "Line 1, Col 2: Invalid delimiter '\\n'")
        self.assertEqual(lex("x\t.").errors[0].message, "Line 1, Col 2: Invalid delimiter '\\t'")

    def test_format(self):
        for source, _ in self.CASES:
            message = lex(source).errors[0].message
            self.assertRegex(message, r"^Line \d+, Col \d+: [A-Z][a-z0-9 ]+ '.*'$")


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
         [("LEX-102", "123456789000000", 11), ("LEX-103", "00.1234567", 26), ("meat_lit", "890000", 36)],
         ["LEX-102", "LEX-103"]),
        ("sauce a = 1234567890000.1", [("sauce_lit", "1234567890000.1", 11)], []),
        ("sauce a = 123456789000.12345678",
         [("LEX-103", "123456789000.1234567", 11), ("meat_lit", "8", 31)], ["LEX-103"]),
        ("sauce a = 5.;", [("LEX-104", "5.", 11), (";", ";", 13)], ["LEX-104"]),
        ("sauce a = 1.5.2;",
         [("LEX-106", "1.5.2", 11), (";", ";", 16)], ["LEX-106"]),
        ("meat x = 1234567890123456;",
         [("LEX-101", "123456789012345", 10), ("meat_lit", "6", 25), (";", ";", 26)], ["LEX-101"]),
        ("meat x = 123456789012345;", [("meat_lit", "123456789012345", 10), (";", ";", 25)], []),
        ("meat x = -123456789012345;", [("meat_lit", "-123456789012345", 10), (";", ";", 26)], []),
        ("-1234567890123456;",
         [("LEX-101", "-123456789012345", 1), ("meat_lit", "6", 17), (";", ";", 18)], ["LEX-101"]),
        ("meat x = 12abc;", [("LEX-107", "12abc", 10), (";", ";", 15)], ["LEX-107"]),
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
        ("chop c = ' ';", [("chop_lit", "' '", 10), (";", ";", 13)], []),
        ('recipe s = "hello;', [("LEX-301", '"hello;', 12)], ["LEX-301"]),
        ('recipe s = "Good M\\orning";', [("LEX-302", '"Good M\\orning"', 12), (";", ";", 27)], ["LEX-302"]),
        ("a | b", [("id", "a", 1), ("LEX-601", "|", 3), ("id", "b", 5)], ["LEX-601"]),
        ("meat x = 5 @ 3;", [("LEX-902", "@", 12), ("meat_lit", "3", 14), (";", ";", 15)], ["LEX-902"]),
        ("/* comment", [("LEX-701", "/* comment", 1)], ["LEX-701"]),
        ("cooked ok = true;", [("id", "true", 13)], []),
        ("meat price = 150; // note", [("Single-Line Comment", "// note", 19)], []),
        ("x++5", [("id", "x", 1), ("LEX-602", "++", 2), ("meat_lit", "5", 4)], ["LEX-602"]),
        (".5", [("LEX-105", ".5", 1)], ["LEX-105"]),
    )

    def test_required_cases(self):
        self.assertEqual(len(self.CASES), 32)
        for source, expected, expected_codes in self.CASES:
            result = lex(source)
            found = [(kind, lexeme, col) for kind, lexeme, _, col in items(result)]
            for item in expected:
                self.assertIn(item, found, source)
            self.assertEqual(codes(result), expected_codes, source)


# ---------------------------------------------------------------------------
# H. Space chop, numbered identifiers and unavailable characters ($ ? @ ^)
# ---------------------------------------------------------------------------


def raw(result):
    """Non-space tokens as (type, lexeme, col) with the real idN types, and
    errors as (code, message)."""
    return ([(t.type, t.lexeme, t.col) for t in result.tokens if t.type != "space"],
            [(e.code, e.message) for e in result.errors])


class SpaceChopTests(unittest.TestCase):
    def test_valid_chop_literals(self):
        for chop in ("' '", "'a'", "'A'", "'#'", "'\\t'", "'\\n'", "'\\''", "'\\\"'", "'\\\\'", "'\\0'"):
            self.assertEqual(items(lex(chop)), [("chop_lit", chop, 1, 1)], chop)

    def test_space_chop_in_a_declaration(self):
        self.assertEqual(raw(lex("chop c = ' ';")), (
            [("chop", "chop", 1), ("id1", "c", 6), ("=", "=", 8), ("chop_lit", "' '", 10), (";", ";", 13)], [],
        ))

    def test_chop_errors_stay_errors(self):
        for source, code in (("''", "LEX-202"), ("'ab'", "LEX-203"), ("'\\'", "LEX-201"),
                             ("'a", "LEX-201"), ("'a'x", "LEX-205")):
            self.assertEqual(codes(lex(source)), [code], source)

    def test_recipe_spaces_unchanged(self):
        self.assertEqual(items(lex('" a b "')), [("recipe_lit", '" a b "', 1, 1)])


class IdentifierNumberTests(unittest.TestCase):
    def test_repeat_keeps_its_number(self):
        result = lex("meat x = y + x;")
        self.assertEqual(raw(result)[0], [
            ("meat", "meat", 1), ("id1", "x", 6), ("=", "=", 8), ("id2", "y", 10),
            ("+", "+", 12), ("id1", "x", 14), (";", ";", 15),
        ])
        self.assertEqual(result.symbols, {"x": 1, "y": 2})

    def test_case_sensitive(self):
        self.assertEqual(lex("meat Age = age;").symbols, {"Age": 1, "age": 2})

    def test_reserved_words_get_no_number(self):
        result = lex("meat porky = 1; meatball = yummy;")
        self.assertEqual([t.type for t in result.tokens if t.type.startswith("id")], ["id1", "id2"])
        self.assertEqual(result.symbols, {"porky": 1, "meatball": 2})

    def test_underscore_names(self):
        self.assertEqual(raw(lex("meat ___ = 2;"))[0][1], ("id1", "___", 6))

    def test_errors_use_no_number(self):
        result = lex("meat abcdefghijklmnopqrstu = 1; a$b; c;")
        self.assertEqual(result.symbols, {"u": 1, "c": 2})

    def test_reset_for_each_input(self):
        lex("meat a; meat b;")
        self.assertEqual(lex("meat b;").symbols, {"b": 1})

    def test_symbols_in_api_output(self):
        self.assertEqual(lex("x = y + x;").to_dict()["symbols"], {"x": 1, "y": 2})


class UnavailableCharacterTests(unittest.TestCase):
    def test_removed_from_every_ascii_set(self):
        from pork_lexer import _is_ascii1, _is_ascii2, _is_ascii3, _is_ascii4
        self.assertEqual(UNAVAILABLE, frozenset("$?@^"))
        for check in (_is_ascii1, _is_ascii2, _is_ascii3, _is_ascii4):
            for ch in UNAVAILABLE:
                self.assertFalse(check(ch), (check.__name__, ch))
            self.assertTrue(check("#"), check.__name__)

    def test_inside_literals_and_comments(self):
        cases = (
            ("chop c = '$';", "'$'", "Line 1, Col 11: Unavailable character '$'"),
            ("chop c = '?';", "'?'", "Line 1, Col 11: Unavailable character '?'"),
            ('recipe s = "Hi @ there";', '"Hi @ there"', "Line 1, Col 16: Unavailable character '@'"),
            ('recipe s = "2^3";', '"2^3"', "Line 1, Col 14: Unavailable character '^'"),
            ("// is this valid?", "// is this valid?", "Line 1, Col 17: Unavailable character '?'"),
            ("/* price in $ */", "/* price in $ */", "Line 1, Col 13: Unavailable character '$'"),
            ("/* line one\n  cost $5 */", "/* line one\n  cost $5 */",
             "Line 2, Col 8: Unavailable character '$'"),
        )
        for source, lexeme, message in cases:
            with self.subTest(source=source):
                errors = lex(source).errors
                self.assertEqual([(e.code, e.status, e.lexeme, e.message) for e in errors],
                                 [("LEX-902", "Unavailable", lexeme, message)])

    def test_scanning_continues_after_the_literal(self):
        self.assertEqual(items(lex("chop c = '$';"))[-1], (";", ";", 1, 13))

    def test_from_state_zero(self):
        self.assertEqual(raw(lex("?"))[1], [("LEX-902", "Line 1, Col 1: Unavailable character '?'")])
        result = lex("meat x;\n?\nx = 1;")
        self.assertEqual(raw(result)[1], [("LEX-902", "Line 2, Col 1: Unavailable character '?'")])

    def test_identifier_followed_by_unavailable(self):
        self.assertEqual(raw(lex("meat a$b = 1;")), (
            [("meat", "meat", 1), ("=", "=", 10), ("meat_lit", "1", 12), (";", ";", 13)],
            [("LEX-503", "Line 1, Col 6: Invalid identifier 'a$b'")],
        ))

    def test_hash_still_valid(self):
        self.assertEqual(lex("chop c = '#';").errors, [])


if __name__ == "__main__":
    unittest.main()
