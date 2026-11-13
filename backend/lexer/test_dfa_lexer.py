"""Lexer tests for Pork CCig. Run from the project root:

    py -m unittest discover -s backend -v
"""

import random
import string
import unittest

from lexer.dfa_lexer import NO_TRANSITION, NOT_FINAL, PorkCCigLexer, token_type, tokenize, transition

WHITESPACE_TYPES = ("space", "tab", "newline")


def assert_full_coverage(source, tokens, errors):
    """Tokens and errors, sorted by position, must spell the normalized source
    exactly (no gaps, no overlaps), and each one must sit at its stated line/col."""
    text = source.replace("\r\n", "\n").replace("\r", "\n")
    pieces = sorted(list(tokens) + list(errors), key=lambda p: (p.line, p.column))
    line, col, rebuilt = 1, 1, ""
    for piece in pieces:
        assert (piece.line, piece.column) == (line, col), (source, piece, line, col)
        rebuilt += piece.lexeme
        for ch in piece.lexeme:
            line, col = (line + 1, 1) if ch == "\n" else (line, col + 1)
    assert rebuilt == text, (source, rebuilt)


def lex(source):
    tokens, errors = tokenize(source)
    assert_full_coverage(source, tokens, errors)
    return tokens, errors


def items(source):
    """Tokens (whitespace left out) and errors in source order:
    (type, lexeme, column) for a token, ("ERROR", lexeme, column) for an error."""
    tokens, errors = lex(source)
    rows = [(t.line, t.column, (t.type, t.lexeme, t.column)) for t in tokens if t.type not in WHITESPACE_TYPES]
    rows += [(e.line, e.column, ("ERROR", e.lexeme, e.column)) for e in errors]
    return [row[2] for row in sorted(rows, key=lambda r: (r[0], r[1]))]


def messages(source):
    return [e.message for e in lex(source)[1]]


# Character classes and delimiter sets

DIGITS = "0123456789"
ALPHA = string.ascii_letters
AI = ALPHA + "_"                  # alpha_id: no digits
AN = DIGITS + ALPHA + "_"         # alpha_num
OPS = "+-*/%<>=!&|"
WS = " \t\n"
PRINTABLE = [chr(c) for c in range(32, 127)] + ["\t", "\n"]

DELIM1 = ";" + WS
DELIM2 = ":" + WS
DELIM3 = "{" + WS
DELIM4 = "(" + WS
DELIM5 = ",({;" + WS
DELIM6 = OPS + "})]:;," + WS
DELIM7 = AN + "+-!{('\"" + WS
DELIM8 = AN + "+-!('\"" + WS
DELIM9 = AN + "-!('\"" + WS
DELIM10 = AI + "()],;" + WS
DELIM11 = AN + "+-!(" + WS
DELIM13 = AN + "+-!{(/'\"" + WS
DELIM14 = AI + "};," + WS
DELIM15 = AN + "-+!()'\"" + WS
DELIM16 = OPS + "{)[].,:;" + WS
DELIM17 = AN + "+-!(]'\"" + WS
DELIM18 = OPS + ")[],;" + WS
DELIM19 = AN + "{+-&'\"" + WS
DELIM20 = AN + "}+-" + WS
DELIM21 = OPS + "()[].,;" + WS
DELIM22 = OPS + ")]},:;" + WS
DELIM23 = OPS + "):]},;" + WS
DELIM25 = AN + OPS + "{}()[]:;,'\"" + WS

# (reserved word, the characters that may follow it)
RESERVED_WORDS = (
    ("meat", WS), ("sauce", WS), ("chop", WS), ("recipe", WS),
    ("cooked", WS), ("empty", WS), ("menu", WS), ("if", DELIM4),
    ("else", DELIM3), ("switch", DELIM4), ("case", DELIM2), ("default", DELIM2),
    ("for", DELIM4), ("while", DELIM4), ("do", DELIM3), ("stop", DELIM1),
    ("again", DELIM1), ("serveback", WS), ("pork", DELIM5), ("serve", DELIM4),
    ("taste", DELIM4), ("yummy", DELIM6), ("yuck", DELIM6), ("fixed", WS),
)
WORDS = [word for word, _ in RESERVED_WORDS]

# (reserved symbol, the characters that may follow it)
RESERVED_SYMBOLS = (
    ("=", DELIM7), ("==", DELIM8), ("+", DELIM9), ("++", DELIM10),
    ("+=", DELIM11), ("-", DELIM11), ("--", DELIM10), ("-=", DELIM11),
    ("*", DELIM11), ("*=", DELIM11), ("/", DELIM11), ("/=", DELIM11),
    ("%", DELIM11), ("%=", DELIM11), (">", DELIM8), (">=", DELIM8),
    ("<", DELIM8), ("<=", DELIM8), ("!", DELIM8), ("!=", DELIM8),
    ("&", DELIM8), ("&&", DELIM8), ("||", DELIM8), ("{", DELIM13),
    ("}", DELIM14), ("(", DELIM15), (")", DELIM16), ("[", DELIM17),
    ("]", DELIM18), (".", AI), (",", DELIM19), (":", WS),
    (";", DELIM20),
)
SYMBOLS = [symbol for symbol, _ in RESERVED_SYMBOLS]


class FirstPieceMixin:
    def check_followed_by(self, lexeme, token_type, delimiter, ch):
        """`lexeme` then `ch`: a token when ch is in the delimiter set, else an error."""
        first = items(lexeme + ch)[0]
        if ch in delimiter:
            self.assertEqual(first, (token_type, lexeme, 1), repr(lexeme + ch))
        else:
            self.assertEqual(first, ("ERROR", lexeme, 1), repr(lexeme + ch))


# Reserved words and identifiers


class ReservedWordTests(FirstPieceMixin, unittest.TestCase):
    def test_there_are_24_reserved_words(self):
        self.assertEqual(len(RESERVED_WORDS), 24)

    def test_every_reserved_word_with_every_following_character(self):
        for word, delimiter in RESERVED_WORDS:
            for ch in PRINTABLE:
                if ch in AN:
                    continue  # the word goes on: an identifier (or serve -> serveback)
                self.check_followed_by(word, word, delimiter, ch)

    def test_reserved_word_at_end_of_input(self):
        for word in WORDS:
            self.assertEqual(items(word), [(word, word, 1)])

    def test_longer_and_shorter_words_are_identifiers(self):
        for word in WORDS:
            for other in (word + "x", word + "_", word + "1", word[:-1], "x" + word, word.upper()):
                if other in WORDS:
                    continue  # "d" + "o": do[:-1] is not a word, but serveback[:-4] is
                self.assertEqual(items(other), [("id", other, 1)], other)

    def test_shared_prefixes_branch_correctly(self):
        self.assertEqual(items("meat menu mea men me m"), [
            ("meat", "meat", 1), ("menu", "menu", 6), ("id", "mea", 11), ("id", "men", 15),
            ("id", "me", 19), ("id", "m", 22),
        ])
        self.assertEqual(items("serve(serveback serveb"), [
            ("serve", "serve", 1), ("(", "(", 6), ("serveback", "serveback", 7), ("id", "serveb", 17),
        ])
        self.assertEqual(items("yummy;yuck;yum"), [
            ("yummy", "yummy", 1), (";", ";", 6), ("yuck", "yuck", 7), (";", ";", 11), ("id", "yum", 12),
        ])


class IdentifierTests(FirstPieceMixin, unittest.TestCase):
    def test_every_following_character(self):
        for name in ("x", "_", "a1", "_count", "studentName"):
            for ch in PRINTABLE:
                if ch not in AN:
                    self.check_followed_by(name, "id", DELIM21, ch)

    def test_length_limit(self):
        for n in (1, 19, 20):
            self.assertEqual(items("a" * n), [("id", "a" * n, 1)])
        self.assertEqual(items("a" * 21 + ";"), [("ERROR", "a" * 20, 1), ("id", "a", 21), (";", ";", 22)])
        self.assertEqual(messages("a" * 21), ["Identifier exceeds 20 characters"])

    def test_identifiers_are_case_sensitive_and_may_be_underscores(self):
        self.assertEqual(items("Meat MEAT ___"), [("id", "Meat", 1), ("id", "MEAT", 6), ("id", "___", 11)])


# Reserved symbols


class ReservedSymbolTests(FirstPieceMixin, unittest.TestCase):
    def test_every_symbol_with_every_following_character(self):
        for symbol, delimiter in RESERVED_SYMBOLS:
            for ch in PRINTABLE:
                if symbol + ch in SYMBOLS:
                    continue  # a longer symbol
                if symbol == "/" and ch in "/*":
                    continue  # a comment
                if symbol == "-" and ch in DIGITS:
                    continue  # a negative literal
                if symbol == "&" and ch == "&" or symbol == "|":
                    continue
                self.check_followed_by(symbol, symbol, delimiter, ch)

    def test_longest_match(self):
        self.assertEqual(items("a<=b"), [("id", "a", 1), ("<=", "<=", 2), ("id", "b", 4)])
        self.assertEqual(items("a== b"), [("id", "a", 1), ("==", "==", 2), ("id", "b", 5)])
        self.assertEqual(items("i++;"), [("id", "i", 1), ("++", "++", 2), (";", ";", 4)])

    def test_lone_pipe_is_an_error(self):
        self.assertEqual(items("a | b"), [("id", "a", 1), ("ERROR", "|", 3), ("id", "b", 5)])
        self.assertEqual(items("a || b"), [("id", "a", 1), ("||", "||", 3), ("id", "b", 6)])


# Whitespace


class WhitespaceTests(unittest.TestCase):
    def test_whitespace_tokens(self):
        tokens, errors = lex("a \tb\n")
        self.assertEqual([(t.type, t.lexeme, t.line, t.column) for t in tokens], [
            ("id", "a", 1, 1), ("space", " ", 1, 2), ("tab", "\t", 1, 3), ("id", "b", 1, 4), ("newline", "\n", 1, 5),
        ])
        self.assertEqual(errors, [])

    def test_whitespace_delimiter(self):
        for ws in WS:
            for ch in PRINTABLE:
                tokens, errors = lex("a" + ws + ch)
                if ch in DELIM25:
                    self.assertEqual(tokens[1].lexeme, ws, repr(ws + ch))
                else:
                    self.assertEqual(errors[0].lexeme, ws, repr(ws + ch))

    def test_line_endings_are_normalized(self):
        tokens, _ = lex("a\r\nb\rc")
        self.assertEqual([(t.lexeme, t.line, t.column) for t in tokens if t.type == "id"],
                         [("a", 1, 1), ("b", 2, 1), ("c", 3, 1)])


# Meat and sauce literals


class NumberTests(FirstPieceMixin, unittest.TestCase):
    def test_every_following_character(self):
        for ch in PRINTABLE:
            if ch not in DIGITS and ch != ".":
                self.check_followed_by("123", "meat_lit", DELIM22, ch)
            if ch not in DIGITS:
                self.check_followed_by("1.5", "sauce_lit", DELIM22, ch)

    def test_meat_digit_limit(self):
        for n in (1, 14, 15):
            self.assertEqual(items("9" * n), [("meat_lit", "9" * n, 1)])
        self.assertEqual(items("1234567890123456;"),
                         [("ERROR", "123456789012345", 1), ("meat_lit", "6", 16), (";", ";", 17)])
        self.assertEqual(messages("1234567890123456"), ["Meat value exceeds 15 digits"])

    def test_sauce_digit_limits(self):
        for source in ("0.0", "123456789012345.5", "1.1234567", "000001.10000"):
            self.assertEqual(items(source), [("sauce_lit", source, 1)])
        self.assertEqual(items("1.12345678"), [("ERROR", "1.1234567", 1), ("meat_lit", "8", 10)])
        self.assertEqual(messages("1.12345678"), ["Sauce decimal part exceeds 7 digits"])
        self.assertEqual(items("1234567890123456.5"), [("ERROR", "123456789012345", 1), ("sauce_lit", "6.5", 16)])

    def test_malformed_numbers(self):
        self.assertEqual(items("5.;"), [("ERROR", "5.", 1), (";", ";", 3)])
        self.assertEqual(messages("5.;"), ["Incomplete decimal value"])
        self.assertEqual(items("12abc;"), [("ERROR", "12", 1), ("id", "abc", 3), (";", ";", 6)])
        self.assertEqual(messages("12abc;"), ["Invalid numerical value"])
        self.assertEqual(items("1.2.3"), [("ERROR", "1.2", 1), ("ERROR", ".", 4), ("meat_lit", "3", 5)])
        self.assertEqual(messages("1.2.3")[0], "Multiple decimal points")
        self.assertEqual(items(".5"), [("ERROR", ".", 1), ("meat_lit", "5", 2)])

    def test_minus_rule(self):
        # "-" directly before a digit is always a negative literal.
        self.assertEqual(items("x-1"), [("id", "x", 1), ("meat_lit", "-1", 2)])
        self.assertEqual(items("x - 1"), [("id", "x", 1), ("-", "-", 3), ("meat_lit", "1", 5)])
        self.assertEqual(items("99-1"), [("meat_lit", "99", 1), ("meat_lit", "-1", 3)])
        self.assertEqual(items("a[0]-1"), [("id", "a", 1), ("[", "[", 2), ("meat_lit", "0", 3), ("]", "]", 4),
                                           ("meat_lit", "-1", 5)])
        self.assertEqual(items("x = -5;"), [("id", "x", 1), ("=", "=", 3), ("meat_lit", "-5", 5), (";", ";", 7)])
        self.assertEqual(items("99 - -1"), [("meat_lit", "99", 1), ("-", "-", 4), ("meat_lit", "-1", 6)])
        self.assertEqual(items("(-3.14)"), [("(", "(", 1), ("sauce_lit", "-3.14", 2), (")", ")", 7)])
        self.assertEqual(items("x /* note */ - 234"), [("id", "x", 1), ("Multi-Line Comment", "/* note */", 3),
                                                       ("-", "-", 14), ("meat_lit", "234", 16)])
        self.assertEqual(items("-x"), [("-", "-", 1), ("id", "x", 2)])
        self.assertEqual(items("-1234567890123456"), [("ERROR", "-123456789012345", 1), ("meat_lit", "6", 17)])
        self.assertEqual(items("serveback -5;"), [("serveback", "serveback", 1), ("meat_lit", "-5", 11), (";", ";", 13)])
        self.assertEqual(items("case -1:"), [("case", "case", 1), ("meat_lit", "-1", 6), (":", ":", 8)])
        self.assertEqual(items("'a'-1"), [("chop_lit", "'a'", 1), ("meat_lit", "-1", 4)])


# Chop and recipe literals


class ChopTests(FirstPieceMixin, unittest.TestCase):
    def test_valid_chops(self):
        for body in ["a", "A", " ", "#", '"', "$", "?", "@", "^", "\\n", "\\t", "\\'", '\\"', "\\\\", "\\0"]:
            source = "'" + body + "'"
            self.assertEqual(items(source), [("chop_lit", source, 1)], source)

    def test_every_following_character(self):
        for ch in PRINTABLE:
            self.check_followed_by("'a'", "chop_lit", DELIM22, ch)

    def test_invalid_chops(self):
        self.assertEqual(messages("''")[0], "Empty character value")
        self.assertEqual(messages("'ab'")[0], "Too many characters in chop value")
        self.assertEqual(messages("'a")[0], "Unclosed character value")
        self.assertEqual(messages("'\\q'")[0], "Invalid escape sequence")
        self.assertEqual(items("'\\q'")[0], ("ERROR", "'\\", 1))


class RecipeTests(FirstPieceMixin, unittest.TestCase):
    def test_valid_recipes(self):
        for source in ['""', '"recipe"', '"Hello World"', '"This is a; "', '"a \\t b\\n"', '"it\'s"', '"&d #d %d"',
                       '"How are you?"', '"a$b@c^d"',
                       '"\\\\ \\" \\\' \\0"']:
            self.assertEqual(items(source), [("recipe_lit", source, 1)], source)

    def test_every_following_character(self):
        for ch in PRINTABLE:
            self.check_followed_by('"s"', "recipe_lit", DELIM23, ch)

    def test_invalid_recipes(self):
        self.assertEqual(items('"Hello World'), [("ERROR", '"Hello World', 1)])
        self.assertEqual(messages('"Hello World'), ["Unclosed string value"])
        self.assertEqual(items('"Good M\\orning"')[0], ("ERROR", '"Good M\\', 1))
        self.assertEqual(messages('"Good M\\orning"')[0], "Invalid escape sequence")
        # A recipe cannot run past the end of its line.
        self.assertEqual(items('"abc\nx')[0], ("ERROR", '"abc', 1))


# Comments


class CommentTests(unittest.TestCase):
    def test_single_line_comment(self):
        self.assertEqual(items("// note\nx"), [("Single-Line Comment", "// note", 1), ("id", "x", 1)])
        self.assertEqual(items("x // a\tb"), [("id", "x", 1), ("Single-Line Comment", "// a\tb", 3)])
        self.assertEqual(items("//"), [("Single-Line Comment", "//", 1)])

    def test_multi_line_comment(self):
        source = "/* a\n * b **/ x"
        self.assertEqual(items(source), [("Multi-Line Comment", "/* a\n * b **/", 1), ("id", "x", 10)])
        self.assertEqual(items("/**/"), [("Multi-Line Comment", "/**/", 1)])

    def test_multi_line_comment_needs_whitespace_after_it(self):
        self.assertEqual(items("/* a */x"), [("ERROR", "/* a */", 1), ("id", "x", 8)])

    def test_unclosed_and_invalid_comments(self):
        self.assertEqual(messages("/* never closed\nstill"), ["Unclosed comment"])
        self.assertEqual(items("/* never closed\nstill"), [("ERROR", "/* never closed\nstill", 1)])
        self.assertEqual(items("// café")[:2], [("ERROR", "// caf", 1), ("ERROR", "é", 7)])
        self.assertEqual(messages("// café")[0], "Invalid character in comment")

    def test_unavailable_characters_are_allowed_in_comments(self):
        for source, kind in (("// what? $5 @home ^", "Single-Line Comment"),
                             ("/* what? $5 @home ^ */", "Multi-Line Comment")):
            self.assertEqual(items(source), [(kind, source, 1)])

    def test_comment_directly_after_a_token(self):
        # One character of lookahead cannot tell "/" from "//", so a comment may only
        # touch a token whose delimiter set has "/" (the operators).
        self.assertEqual(items("x//c"), [("id", "x", 1), ("Single-Line Comment", "//c", 2)])
        self.assertEqual(items(";//c"), [("ERROR", ";", 1), ("Single-Line Comment", "//c", 2)])


# Characters no diagram starts with


class InvalidCharacterTests(unittest.TestCase):
    def test_unavailable_characters(self):
        for bad in "$?@^":
            self.assertEqual(messages("a " + bad)[-1], "Unavailable character")

    def test_invalid_characters(self):
        for bad in ["#", "`", "~", "\\", "é", "\x01"]:
            tokens, errors = lex(bad)
            self.assertEqual([(e.lexeme, e.message) for e in errors], [(bad, "Invalid character")])


# Whole programs, positions and robustness

PROGRAM = """\
menu Student {
    meat id;
    recipe name;
};
fixed sauce RATE = 0.5;

meat add(meat a, meat b) {
    serveback a + b;
}

empty pork() {
    meat total = 0, scores[3] = {90, -85, 100};
    for (meat i = 0; i < 3; i++) {
        if (scores[i] >= 75 && !yuck) {
            total += scores[i];
        } else {
            again;
        }
    }
    switch (total) {
        case 1: stop;
        default: total = add(total, 1);
    }
    do {
        total--;
    } while(total > 0);
    taste("&d", &total);
    serve("Total: &d\\n", total);
}
"""


# Token types of PROGRAM (whitespace left out) as produced by the lexer this
# DFA replaced.
PROGRAM_TYPES = (
    "menu id { meat id ; recipe id ; } ; fixed sauce id = sauce_lit ; "
    "meat id ( meat id , meat id ) { serveback id + id ; } "
    "empty pork ( ) { meat id = meat_lit , id [ meat_lit ] = { meat_lit , meat_lit , meat_lit } ; "
    "for ( meat id = meat_lit ; id < meat_lit ; id ++ ) { "
    "if ( id [ id ] >= meat_lit && ! yuck ) { id += id [ id ] ; } else { again ; } } "
    "switch ( id ) { case meat_lit : stop ; default : id = id ( id , meat_lit ) ; } "
    "do { id -- ; } while ( id > meat_lit ) ; "
    "taste ( recipe_lit , & id ) ; serve ( recipe_lit , id ) ; }"
)


def trace(source):
    """States visited by the first lexeme of `source`."""
    lexer = PorkCCigLexer(source, debug=True)
    lexer.scan()
    return lexer.traces[0][1]


class DfaTableTests(unittest.TestCase):
    def test_states_are_0_to_299(self):
        inputs = PRINTABLE + [""]
        for state in range(300):
            targets = [transition(state, ch) for ch in inputs if transition(state, ch) != NO_TRANSITION]
            if token_type(state) == NOT_FINAL:
                self.assertTrue(targets, state)
            else:
                self.assertEqual(targets, [], state)
            for target in targets:
                self.assertTrue(0 < target < 300, (state, target))
        self.assertEqual(transition(300, "a"), NO_TRANSITION)
        self.assertEqual(token_type(300), NOT_FINAL)

    def test_alias_states(self):
        for alias, real in ((59, 55), (86, 81), (87, 82), (88, 83), (89, 84), (123, 118)):
            for ch in PRINTABLE + [""]:
                expected = transition(real, ch)
                if (alias, expected) in ((86, 82), (87, 83), (88, 84)):
                    expected += 5
                self.assertEqual(transition(alias, ch), expected, (alias, ch))

    def test_final_states(self):
        finals = [state for state in range(300) if token_type(state) != NOT_FINAL]
        self.assertEqual([s for s in finals if s < 127], [
            6, 11, 15, 21, 29, 31, 36, 41, 47, 50, 53, 58, 62, 67, 74, 80, 85, 94, 98, 104, 110, 116, 122, 126,
        ])
        self.assertEqual([s for s in finals if 127 <= s < 200], [
            128, 130, 132, 134, 136, 138, 140, 142, 144, 146, 148, 150, 152, 154, 156, 158, 160, 162, 164, 166,
            168, 170, 173, 175, 177, 179, 181, 183, 185, 187, 189, 191, 193, 195, 197, 199,
        ])
        self.assertEqual([s for s in finals if token_type(s) == "id"], list(range(201, 240, 2)))
        self.assertEqual([s for s in finals if token_type(s) == "meat_lit"], list(range(241, 270, 2)))
        self.assertEqual([s for s in finals if token_type(s) == "sauce_lit"], [272, 274, 276, 278, 280, 282, 284])
        self.assertEqual((token_type(289), token_type(293), token_type(295), token_type(299)),
                         ("chop_lit", "recipe_lit", "Single-Line Comment", "Multi-Line Comment"))
        self.assertEqual(sorted(token_type(s) for s in finals if s < 127), sorted(WORDS))

    def test_traces(self):
        self.assertEqual(trace("serveback "), [0, 75, 81, 82, 83, 84, 90, 91, 92, 93, 94])
        self.assertEqual(trace("serve("), [0, 75, 81, 82, 83, 84, 85])
        self.assertEqual(trace("menu "), [0, 54, 55, 60, 61, 62])
        self.assertEqual(trace("yuck;"), [0, 117, 118, 124, 125, 126])
        self.assertEqual(trace("agai;"), [0, 1, 2, 3, 4, 207])
        self.assertEqual(trace("ifx "), [0, 51, 52, 204, 205])
        self.assertEqual(trace("a" * 20)[-2:], [238, 239])
        self.assertEqual(trace("9" * 15)[-2:], [268, 269])
        self.assertEqual(trace("-5;"), [0, 137, 240, 241])
        self.assertEqual(trace("1.1234567")[-3:], [281, 283, 284])
        self.assertEqual(trace("'\\n'"), [0, 285, 286, 287, 288, 289])
        self.assertEqual(trace('"a\\tb"'), [0, 290, 290, 291, 290, 290, 292, 293])
        self.assertEqual(trace("//c\n"), [0, 147, 294, 294, 295])
        self.assertEqual(trace("/* a * b **/"), [0, 147, 296, 296, 296, 296, 297, 296, 296, 296, 297, 297, 298, 299])
        self.assertEqual(trace("|| b"), [0, 171, 172, 173])

    def test_keyword_delimiters_and_fallback(self):
        self.assertEqual(items("serveback;"), [("ERROR", "serveback", 1), (";", ";", 10)])
        self.assertEqual(items("(empty)"), [("(", "(", 1), ("ERROR", "empty", 2), (")", ")", 7)])
        self.assertEqual(messages("serveback;") + messages("(empty)"), ["Invalid delimiter"] * 2)
        self.assertEqual(items("agai;"), [("id", "agai", 1), (";", ";", 5)])
        self.assertEqual(items("serv "), [("id", "serv", 1)])
        self.assertEqual(items("ifx"), [("id", "ifx", 1)])
        self.assertEqual(items("mea{"), [("ERROR", "mea", 1), ("{", "{", 4)])

    def test_more_literals_and_comments(self):
        self.assertEqual(items("12."), [("ERROR", "12.", 1)])
        self.assertEqual(messages("12."), ["Incomplete decimal value"])
        self.assertEqual(items("1.1 1.1234567"), [("sauce_lit", "1.1", 1), ("sauce_lit", "1.1234567", 5)])
        self.assertEqual(items("/* a * b */"), [("Multi-Line Comment", "/* a * b */", 1)])
        self.assertEqual(items("meat x;\r\nmeat y;\r\n")[3:], [("meat", "meat", 1), ("id", "y", 6), (";", ";", 7)])

    def test_sample_program_matches_the_previous_lexer(self):
        tokens, errors = lex(PROGRAM)
        self.assertEqual(errors, [])
        self.assertEqual(" ".join(t.type for t in tokens if t.type not in WHITESPACE_TYPES), PROGRAM_TYPES)


class ProgramTests(unittest.TestCase):
    def test_valid_program_has_no_errors(self):
        tokens, errors = lex(PROGRAM)
        self.assertEqual(errors, [])
        self.assertEqual(sum(1 for t in tokens if t.type == "meat"), 6)

    def test_positions_across_lines(self):
        tokens, _ = lex("meat x;\n\tsauce y = 1.5;")
        self.assertEqual([(t.type, t.line, t.column) for t in tokens if t.type not in WHITESPACE_TYPES], [
            ("meat", 1, 1), ("id", 1, 6), (";", 1, 7),
            ("sauce", 2, 2), ("id", 2, 8), ("=", 2, 10), ("sauce_lit", 2, 12), (";", 2, 15),
        ])

    def test_error_recovery_restarts_at_the_offending_character(self):
        self.assertEqual(items("meat; x = 5;"), [
            ("ERROR", "meat", 1), (";", ";", 5), ("id", "x", 7), ("=", "=", 9), ("meat_lit", "5", 11), (";", ";", 12),
        ])

    def test_random_input_never_crashes_and_is_fully_covered(self):
        rng = random.Random(311)
        alphabet = string.printable + "$?@^" + "meatsauce" * 3 + "é"
        for _ in range(2000):
            source = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60)))
            lex(source)  # assert_full_coverage runs inside


if __name__ == "__main__":
    unittest.main()
