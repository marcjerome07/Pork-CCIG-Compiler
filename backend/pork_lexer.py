"""Lexical analyzer for the Pork CCig language.

Implements only the lexical phase of the Pork CCig Compiler specification:
reserved words, reserved symbols, identifiers, literals, comments and
whitespace. It never parses, type-checks or executes the source.

How the specification is applied:
  * Regular definitions and delimiter sets come from spec pp. 72-73; the
    transition diagrams (pp. 74-82) say which delimiter follows each token.
  * The scanner looks at most one character ahead. When the next character
    has no transition or is not an allowed delimiter, the characters read so
    far become an error and scanning restarts at that character.
  * Every token in the regular-expression table (pp. 69-72) is reported,
    including space, newline, tab and both comment kinds. Errors are never
    tokens.
"""

from dataclasses import asdict, dataclass, field

# ---------------------------------------------------------------------------
# Regular definitions (spec p. 72)
# ---------------------------------------------------------------------------

DIGITS = frozenset("0123456789")
ALPHA = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
UNDERSCORE = frozenset("_")
ALPHA_ID = ALPHA | UNDERSCORE              # alpha_id: letters and _, no digits
ALPHA_NUMERIC = DIGITS | ALPHA_ID          # alpha_numeric: digits, letters and _
OPERATORS = frozenset("+-*/%<>=!&|")
WHITESPACE = frozenset(" \t\n")
ESCAPE_SEQ = frozenset("nt'\"\\0")


def _is_ascii1(ch):  # printable ASCII except \ and '   (chop literal text)
    return 32 <= ord(ch) <= 126 and ch not in "\\'"


def _is_ascii2(ch):  # printable ASCII except \ and "   (recipe literal text)
    return 32 <= ord(ch) <= 126 and ch not in '\\"'


def _is_ascii3(ch):  # printable ASCII                  (single-line comment text)
    return 32 <= ord(ch) <= 126


def _is_ascii4(ch):  # printable ASCII except space     (multi-line comment text)
    return 33 <= ord(ch) <= 126


# ---------------------------------------------------------------------------
# Delimiter sets (spec p. 73)
# ---------------------------------------------------------------------------

AN, AI, OPS, WS = ALPHA_NUMERIC, ALPHA_ID, OPERATORS, WHITESPACE

DELIMITERS = {
    "whitespace": WS,
    "delim1": frozenset(";") | WS,
    "delim2": frozenset(":") | WS,
    "delim3": frozenset("{") | WS,
    "delim4": frozenset("(") | WS,
    "delim5": frozenset(",({;") | WS,
    "delim6": OPS | frozenset("})]:;,") | WS,
    "delim7": AN | frozenset("+-!{('\"") | WS,
    "delim8": AN | frozenset("+-!('\"") | WS,
    "delim9": AN | frozenset("-!('\"") | WS,
    "delim10": AI | frozenset("()],;") | WS,
    # Group decision (deviates from p. 73): "--" may also be followed by a digit
    # or "-", so "--234" (decrement, then 234) and "---234" (decrement, then -234)
    # are lexically valid. "++" keeps delim10, so "x++5" is still an error.
    "delim10_decrement": AI | DIGITS | frozenset("-()],;") | WS,
    "delim11": AN | frozenset("+-!(") | WS,
    "delim13": AN | frozenset("+-!{(/'\"") | WS,
    "delim14": ALPHA | UNDERSCORE | frozenset("};,") | WS,
    "delim15": AN | frozenset("-+!()'\"") | WS,
    "delim16": OPS | frozenset("{)[].,:;") | WS,
    "delim17": AN | frozenset("+-!(]'\"") | WS,
    "delim18": OPS | frozenset(")[],;") | WS,
    "delim19": AN | frozenset("{+-&'\"") | WS,
    "delim20": AN | frozenset("}+-") | WS,
    "delim21": OPS | frozenset("()[].,;") | WS,
    "delim22": OPS | frozenset(")]},:;") | WS,
    "delim23": OPS | frozenset("):]},;") | WS,
    "delim25": AN | OPS | frozenset("{}()[]:;,'\"") | WS,
    "alpha_id": AI,
}

ID_DELIMITER = "delim21"
NUMBER_DELIMITER = "delim22"
CHOP_DELIMITER = "delim22"
RECIPE_DELIMITER = "delim23"
WHITESPACE_DELIMITER = "delim25"
MULTI_LINE_COMMENT_DELIMITER = "whitespace"

# ---------------------------------------------------------------------------
# Reserved words (spec pp. 5-6 for meaning, p. 74 for the delimiter after each)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Keyword:
    word: str
    group: str
    c_counterpart: str
    description: str
    delimiter: str


KEYWORD_GROUPS = (
    "Data Types",
    "Conditional Statements",
    "Iterative Statements",
    "Jump Statements",
    "Others",
)

KEYWORDS = (
    Keyword("meat", "Data Types", "int", "A data type used for storing whole numbers.", "whitespace"),
    Keyword("sauce", "Data Types", "float", "A data type used for numbers that contain decimal values.", "whitespace"),
    Keyword("chop", "Data Types", "char", "A data type that holds a single character.", "whitespace"),
    Keyword("recipe", "Data Types", "char[]", "Used to store a series of characters or a string.", "whitespace"),
    Keyword("cooked", "Data Types", "bool", "A data type that holds either a true or false value.", "whitespace"),
    Keyword("empty", "Data Types", "void", "A type used when no value is returned.", "whitespace"),
    Keyword("menu", "Data Types", "struct", "A user-defined type that combines related variables.", "whitespace"),
    Keyword("if", "Conditional Statements", "if", "Executes a statement when the given condition is true.", "delim4"),
    Keyword("else", "Conditional Statements", "else", "Executes a block of code when the if condition is false.", "delim3"),
    Keyword("switch", "Conditional Statements", "switch", "Allows the program to choose between several possible blocks of code.", "delim4"),
    Keyword("case", "Conditional Statements", "case", "Represents one possible choice within a switch statement.", "delim2"),
    Keyword("default", "Conditional Statements", "default", "Executes when none of the cases match.", "delim2"),
    Keyword("for", "Iterative Statements", "for", "A loop commonly used to repeat code a specific number of times.", "delim4"),
    Keyword("while", "Iterative Statements", "while", "Repeats a block of code as long as its condition remains true.", "whitespace"),
    Keyword("do", "Iterative Statements", "do", "Runs the loop body first and checks the condition afterward.", "delim3"),
    Keyword("stop", "Jump Statements", "break", "Ends the execution of a loop or switch statement.", "delim1"),
    Keyword("again", "Jump Statements", "continue", "Skips the current loop cycle and proceeds to the next one.", "delim1"),
    Keyword("serveback", "Jump Statements", "return", "Ends a function and may send a value back to the caller.", "whitespace"),
    Keyword("pork", "Others", "main", "The function where the execution of the program begins.", "delim5"),
    Keyword("serve", "Others", "printf", "A function used to show text or other output on the screen.", "delim4"),
    Keyword("taste", "Others", "scanf", "A function used to receive data entered by the user.", "delim4"),
    Keyword("yummy", "Others", "true", "A boolean value used to indicate a correct or active condition.", "delim6"),
    Keyword("yuck", "Others", "false", "A boolean value used to indicate an incorrect or inactive condition.", "delim6"),
    Keyword("fixed", "Others", "const", "A keyword used to keep a variable's value from being changed.", "whitespace"),
)

KEYWORD_DELIMITER = {kw.word: kw.delimiter for kw in KEYWORDS}

# ---------------------------------------------------------------------------
# Reserved symbols (spec pp. 75-77): symbol -> delimiter that must follow it.
# A lone "|" has no final state.
# ---------------------------------------------------------------------------

DIAGRAM_SYMBOLS = {
    "=": "delim7", "==": "delim8",
    "+": "delim9", "++": "delim10", "+=": "delim11",
    "-": "delim11", "--": "delim10_decrement", "-=": "delim11",
    "*": "delim11", "*=": "delim11",
    "/": "delim11", "/=": "delim11",
    "%": "delim11", "%=": "delim11",
    ">": "delim8", ">=": "delim8",
    "<": "delim8", "<=": "delim8",
    "!": "delim8", "!=": "delim8",
    "&": "delim8", "&&": "delim8", "||": "delim8",
    "{": "delim13", "}": "delim14",
    "(": "delim15", ")": "delim16",
    "[": "delim17", "]": "delim18",
    ".": "alpha_id", ",": "delim19",
    ":": "whitespace", ";": "delim20",
}

# Longer symbols are tried first so "<=" wins over "<".
SYMBOLS_LONGEST_FIRST = sorted(DIAGRAM_SYMBOLS, key=len, reverse=True)

# ---------------------------------------------------------------------------
# Token types: the "Token" column of the regular-expression table (pp. 69-72)
# ---------------------------------------------------------------------------

SPACE, NEWLINE, TAB = "space", "newline", "tab"
WHITESPACE_TOKENS = {" ": SPACE, "\n": NEWLINE, "\t": TAB}

ID = "id"
MEAT_LIT = "meat_lit"
SAUCE_LIT = "sauce_lit"
CHOP_LIT = "chop_lit"
RECIPE_LIT = "recipe_lit"
SINGLE_LINE_COMMENT = "Single-Line Comment"
MULTI_LINE_COMMENT = "Multi-Line Comment"
OTHER_TOKEN_TYPES = (
    ID, MEAT_LIT, SAUCE_LIT, CHOP_LIT, RECIPE_LIT, SINGLE_LINE_COMMENT, MULTI_LINE_COMMENT,
)

TOKEN_TYPES = frozenset(
    [kw.word for kw in KEYWORDS]
    + list(DIAGRAM_SYMBOLS)
    + list(WHITESPACE_TOKENS.values())
    + list(OTHER_TOKEN_TYPES)
)

# Whitespace and comments are skipped by the lookback pointer.
TRIVIA = frozenset([SPACE, NEWLINE, TAB, SINGLE_LINE_COMMENT, MULTI_LINE_COMMENT])

# Minus rule: a "-" whose lookback character ends an operand is subtraction;
# otherwise a "-" followed by a digit starts a negative literal.
OPERAND_END_CHARS = ALPHA_NUMERIC | frozenset(")]")

# Characters that can begin some token. Anything else is LEX-901.
TOKEN_START = (
    ALPHA_NUMERIC | WHITESPACE | frozenset("'\".|")
    | frozenset(symbol[0] for symbol in DIAGRAM_SYMBOLS)
)

# ---------------------------------------------------------------------------
# Literal and identifier limits (written rules, spec pp. 8-10)
# ---------------------------------------------------------------------------

MAX_IDENTIFIER_LENGTH = 20
MAX_MEAT_DIGITS = 15
MAX_SAUCE_WHOLE_DIGITS = 12
MAX_SAUCE_DECIMAL_DIGITS = 7

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

# Every lexer message uses one of four status words:
#   Valid        the lexeme was accepted as a token (token lines in the UI)
#   Invalid      allowed characters, but malformed or in the wrong place
#   Unavailable  the character does not exist in the PORK CCIG character set
#   Available    reserved for later use; no lexical error uses it
STATUS = {
    "LEX-101": "Invalid",      # integer longer than 15 digits
    "LEX-102": "Invalid",      # decimal whole part longer than 12 digits
    "LEX-103": "Invalid",      # decimal fraction longer than 7 digits
    "LEX-104": "Invalid",      # no digit after the decimal point
    "LEX-105": "Invalid",      # no digit before the decimal point
    "LEX-106": "Invalid",      # second decimal point
    "LEX-107": "Invalid",      # number followed by a letter (e.g. 2cups)
    "LEX-108": "Invalid",      # bad delimiter after a number
    "LEX-201": "Invalid",      # unterminated chop literal
    "LEX-202": "Invalid",      # empty chop literal ''
    "LEX-203": "Invalid",      # chop literal with more than one character
    "LEX-204": "Invalid",      # bad escape in a chop literal
    "LEX-205": "Invalid",      # bad delimiter after a chop literal
    "LEX-206": "Invalid",      # chop literal ' ' (a space)
    "LEX-301": "Invalid",      # unterminated recipe literal
    "LEX-302": "Invalid",      # bad escape in a recipe literal
    "LEX-303": "Invalid",      # bad delimiter after a recipe literal
    "LEX-401": "Invalid",      # bad delimiter after a reserved word
    "LEX-501": "Invalid",      # identifier longer than 20 characters
    "LEX-502": "Invalid",      # bad delimiter after an identifier
    "LEX-601": "Invalid",      # lone "|"
    "LEX-602": "Invalid",      # bad delimiter after a symbol or whitespace
    "LEX-701": "Invalid",      # unterminated multi-line comment
    "LEX-702": "Unavailable",  # character outside the comment character set
    "LEX-703": "Invalid",      # bad delimiter after a multi-line comment
    "LEX-901": "Unavailable",  # character not in the PORK CCIG character set (@ $ # ...)
}

# Short titles for each code (sent to the UI as data; not part of the message).
TITLES = {
    "LEX-101": "Numerical value", "LEX-102": "Decimal value", "LEX-103": "Decimal value",
    "LEX-104": "Decimal value", "LEX-105": "Decimal value", "LEX-106": "Decimal value",
    "LEX-107": "Identifier", "LEX-108": "Delimiter",
    "LEX-201": "Character literal", "LEX-202": "Character literal", "LEX-203": "Character literal",
    "LEX-204": "Escape sequence", "LEX-205": "Delimiter", "LEX-206": "Character literal",
    "LEX-301": "String literal", "LEX-302": "Escape sequence", "LEX-303": "Delimiter",
    "LEX-401": "Delimiter", "LEX-501": "Identifier", "LEX-502": "Delimiter",
    "LEX-601": "Operator", "LEX-602": "Delimiter",
    "LEX-701": "Comment", "LEX-702": "Comment character", "LEX-703": "Delimiter",
    "LEX-901": "Character",
}

# Unterminated literals and comments quote only their first 10 characters.
SHORTENED_CODES = frozenset(["LEX-201", "LEX-301", "LEX-701"])
SHORTENED_LENGTH = 10


def show_lexeme(lexeme, code=None):
    """The lexeme as quoted in a message. Newline and tab are written as \\n and
    \\t; unterminated literals and comments are cut to 10 characters plus "..."."""
    if code in SHORTENED_CODES and len(lexeme) > SHORTENED_LENGTH:
        lexeme = lexeme[:SHORTENED_LENGTH] + "..."
    return lexeme.replace("\n", "\\n").replace("\t", "\\t")


def format_message(code, line, col, lexeme):
    """The one place lexer messages are built: <CODE> (Ln <l>, Col <c>): <STATUS> '<lexeme>'"""
    return f"{code} (Ln {line}, Col {col}): {STATUS[code]} '{show_lexeme(lexeme, code)}'"


@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    col: int


@dataclass
class LexError:
    code: str
    status: str
    title: str
    line: int
    col: int
    lexeme: str
    message: str


@dataclass
class LexResult:
    tokens: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def to_dict(self):
        return {
            "tokens": [asdict(t) for t in self.tokens],
            "errors": [asdict(e) for e in self.errors],
        }


def keyword_reference():
    """Keyword list for the UI, generated from the same table the lexer uses."""
    return {
        "groups": list(KEYWORD_GROUPS),
        "keywords": [
            {
                "word": kw.word,
                "group": kw.group,
                "cCounterpart": kw.c_counterpart,
                "description": kw.description,
            }
            for kw in KEYWORDS
        ],
    }


def tokenize(source):
    """Run lexical analysis on Pork CCig source text and return a LexResult."""
    return _Lexer(source).run()


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


class _Lexer:
    def __init__(self, source):
        # Normalize Windows and old Mac line endings so columns stay correct.
        self.src = source.replace("\r\n", "\n").replace("\r", "\n")
        self.n = len(self.src)
        self.i = 0
        self.line = 1
        self.col = 1
        # Index of the last character of the last token or error that was not
        # whitespace or a comment; -1 at the start of input. Feeds lookback().
        self.last_index = -1
        self.result = LexResult()

    # -- helpers -------------------------------------------------------------

    def char_at(self, index):
        return self.src[index] if 0 <= index < self.n else None

    # The three pointers: current is src[i]; lookahead peeks src[i + 1] without
    # consuming it; lookback is the previous non-whitespace character. Both
    # helpers return '' past either end of the input instead of raising.
    def current(self):
        return self.src[self.i] if self.i < self.n else ""

    def lookahead(self):
        return self.src[self.i + 1] if self.i + 1 < self.n else ""

    def lookback(self):
        # Spaces, tabs, newlines and comments are skipped, so "x - 234" and
        # "x /* note */ - 234" both look back to "x".
        return self.src[self.last_index] if self.last_index >= 0 else ""

    def remember(self, end, is_trivia):
        if not is_trivia and end > self.i:
            self.last_index = end - 1

    def advance_to(self, end):
        """Consume characters up to (not including) index `end`."""
        while self.i < end:
            if self.src[self.i] == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.i += 1

    def emit(self, token_type, end):
        if token_type not in TOKEN_TYPES:
            raise AssertionError(f"Unknown token type {token_type!r}; it is not in TOKEN_TYPES.")
        self.result.tokens.append(Token(token_type, self.src[self.i:end], self.line, self.col))
        self.remember(end, token_type in TRIVIA)
        self.advance_to(end)

    def fail(self, code, end):
        """Report an error covering src[i:end] and resume scanning at `end`."""
        lexeme = self.src[self.i:end]
        message = format_message(code, self.line, self.col, lexeme)
        self.result.errors.append(
            LexError(code, STATUS[code], TITLES[code], self.line, self.col, lexeme, message)
        )
        is_trivia = lexeme.isspace() or lexeme.startswith(("//", "/*"))
        self.remember(end, is_trivia)
        self.advance_to(end)

    def delimiter_ok(self, end, delimiter):
        # End of input is accepted as a delimiter for every token.
        nxt = self.char_at(end)
        if nxt is None:
            return True
        # Group decision: a comment may follow any token directly (comment rule 6,
        # p. 65), e.g. "x=5;//note", even though most delimiter sets on p. 73 have
        # no "/". A lone "/" still has to be in the token's delimiter set.
        if nxt == "/" and self.char_at(end + 1) in ("/", "*"):
            return True
        return nxt in DELIMITERS[delimiter]

    def find_closing_quote(self, start, quote):
        """Index of the closing quote on the same line, or None. A backslash
        skips the next character unless that character is a newline."""
        j = start
        while j < self.n:
            ch = self.src[j]
            if ch == "\n":
                return None
            if ch == "\\" and j + 1 < self.n and self.src[j + 1] != "\n":
                j += 2
                continue
            if ch == quote:
                return j
            j += 1
        return None

    def end_of_line(self, start):
        j = self.src.find("\n", start)
        return self.n if j == -1 else j

    # -- main loop -------------------------------------------------------------

    def run(self):
        # Each pass reads the pointers fresh: i only moves forward inside emit()
        # and fail() (via advance_to), and both of those also update lookback.
        while self.i < self.n:
            ch = self.current()
            nxt = self.lookahead()
            nxt_is_digit = nxt != "" and nxt in DIGITS
            if ch in WHITESPACE_TOKENS:
                self.lex_whitespace()
            elif ch in ALPHA_ID:
                self.lex_word()
            elif ch in DIGITS:
                self.lex_number()
            elif ch == "-":
                self.lex_minus(nxt, nxt_is_digit)
            elif ch == "." and nxt_is_digit:
                # ".5": sauce rule 7 needs a digit before the point. One error
                # for the whole malformed number, e.g. Invalid '.5'.
                self.fail("LEX-105", self.number_chunk_end(self.i + 1))
            elif ch == "'":
                self.lex_chop()
            elif ch == '"':
                self.lex_recipe()
            elif ch == "/" and nxt == "/":
                self.lex_single_line_comment()
            elif ch == "/" and nxt == "*":
                self.lex_multi_line_comment()
            else:
                self.lex_symbol()
        return self.result

    # -- minus: decrement, subtraction or negative literal --------------------

    def lex_minus(self, lookahead, lookahead_is_digit):
        # 1. "--" or "-=" (longest match): checked first, so "--234" is a
        #    decrement followed by 234, never "-" and "-234".
        if lookahead in ("-", "="):
            self.lex_symbol()
        # 2. "-" + digit where the lookback character does not end an operand
        #    (start of input, an operator, "(", ",", "=", ";", "{", ...):
        #    a negative literal such as "-234" or "-3.14"; its column is the "-".
        elif lookahead_is_digit and self.lookback() not in OPERAND_END_CHARS:
            self.lex_number()
        # 3. Otherwise plain subtraction or unary minus, e.g. "x-1" or "-x".
        else:
            self.lex_symbol()

    # -- whitespace ------------------------------------------------------------

    def lex_whitespace(self):
        end = self.i + 1
        nxt = self.char_at(end)
        # A character that starts no token is reported once, as LEX-901, rather
        # than also as a bad delimiter after the whitespace before it.
        if self.delimiter_ok(end, WHITESPACE_DELIMITER) or nxt not in TOKEN_START:
            self.emit(WHITESPACE_TOKENS[self.src[self.i]], end)
        else:
            self.fail("LEX-602", end)

    # -- reserved words and identifiers --------------------------------------

    def lex_word(self):
        end = self.i
        while end < self.n and self.src[end] in ALPHA_NUMERIC:
            end += 1
        word = self.src[self.i:end]

        # A reserved word only matches as the complete run: "meatball" is an id.
        if word in KEYWORD_DELIMITER:
            if self.delimiter_ok(end, KEYWORD_DELIMITER[word]):
                self.emit(word, end)
            else:
                self.fail("LEX-401", end)
            return

        if len(word) > MAX_IDENTIFIER_LENGTH:
            cut = self.i + MAX_IDENTIFIER_LENGTH
            self.fail("LEX-501", cut)
        elif not self.delimiter_ok(end, ID_DELIMITER):
            self.fail("LEX-502", end)
        else:
            self.emit(ID, end)

    # -- meat and sauce literals -----------------------------------------------

    def number_chunk_end(self, j):
        """Index of the first delim22 character (or end of input) from j on.
        "." is not in delim22, so extra decimal points stay inside the chunk."""
        while j < self.n and self.src[j] not in DELIMITERS[NUMBER_DELIMITER]:
            j += 1
        return j

    def lex_number(self):
        """State machine for meat/sauce literals, one character of lookahead.

        Two kinds of error recovery:
          * Digit limits (LEX-101/102/103), the professor's rule: the part read
            so far is the error and scanning restarts at the next character.
          * Malformed numbers (LEX-104/106/107): the whole chunk up to the next
            delim22 character is ONE error, e.g. Invalid '12.3.4'. The
            delimiter itself is never consumed.
        """
        start = self.i
        j = start + 1 if self.src[start] == "-" else start
        int_start = j
        while j < self.n and self.src[j] in DIGITS and j - int_start < MAX_MEAT_DIGITS:
            j += 1
        int_count = j - int_start
        nxt = self.char_at(j)

        if nxt is not None and nxt in DIGITS:
            self.fail("LEX-101", j)
            return

        token_type = MEAT_LIT
        if nxt == ".":
            if int_count > MAX_SAUCE_WHOLE_DIGITS:
                self.fail("LEX-102", j)
                return
            j += 1  # the "."
            nxt = self.char_at(j)
            if nxt is None or nxt not in DIGITS:
                self.fail("LEX-104", self.number_chunk_end(j))  # "5.", "1..2"
                return
            frac_start = j
            while j < self.n and self.src[j] in DIGITS and j - frac_start < MAX_SAUCE_DECIMAL_DIGITS:
                j += 1
            nxt = self.char_at(j)
            if nxt is not None and nxt in DIGITS:
                self.fail("LEX-103", j)
                return
            if nxt == ".":
                self.fail("LEX-106", self.number_chunk_end(j))  # "12.3.4"
                return
            token_type = SAUCE_LIT

        if nxt is not None and nxt in ALPHA_ID:
            self.fail("LEX-107", self.number_chunk_end(j))  # "12abc", "3.14abc"
        elif not self.delimiter_ok(j, NUMBER_DELIMITER):
            self.fail("LEX-108", j)
        else:
            self.emit(token_type, j)

    # -- chop and recipe literals ----------------------------------------------

    @staticmethod
    def literal_body(body, is_valid_char):
        """Return (char_count, ok). ok is False on a bad escape (a backslash not
        followed by n t ' " \\ 0) or a character outside the allowed ASCII range."""
        count = 0
        k = 0
        while k < len(body):
            ch = body[k]
            if ch == "\\":
                esc = body[k + 1] if k + 1 < len(body) else ""
                if esc == "" or esc not in ESCAPE_SEQ:
                    return count, False
                k += 2
            elif is_valid_char(ch):
                k += 1
            else:
                return count, False
            count += 1
        return count, True

    def lex_chop(self):
        close = self.find_closing_quote(self.i + 1, "'")
        if close is None:
            self.fail("LEX-201", self.end_of_line(self.i))
            return
        end = close + 1
        body = self.src[self.i + 1:close]
        if body == "":
            self.fail("LEX-202", end)
            return
        if body == " ":
            self.fail("LEX-206", end)
            return
        count, ok = self.literal_body(body, _is_ascii1)
        if not ok:
            self.fail("LEX-204", end)
        elif count != 1:
            self.fail("LEX-203", end)
        elif not self.delimiter_ok(end, CHOP_DELIMITER):
            self.fail("LEX-205", end)
        else:
            self.emit(CHOP_LIT, end)

    def lex_recipe(self):
        close = self.find_closing_quote(self.i + 1, '"')
        if close is None:
            self.fail("LEX-301", self.end_of_line(self.i))
            return
        end = close + 1
        _, ok = self.literal_body(self.src[self.i + 1:close], _is_ascii2)
        if not ok:
            self.fail("LEX-302", end)
        elif not self.delimiter_ok(end, RECIPE_DELIMITER):
            self.fail("LEX-303", end)
        else:
            self.emit(RECIPE_LIT, end)

    # -- comments ----------------------------------------------------------------

    def lex_single_line_comment(self):
        # Runs to the end of the line; the newline itself becomes its own token.
        end = self.end_of_line(self.i)
        for k in range(self.i + 2, end):
            ch = self.src[k]
            if not (_is_ascii3(ch) or ch == "\t"):
                self.fail("LEX-702", end)
                return
        self.emit(SINGLE_LINE_COMMENT, end)

    def lex_multi_line_comment(self):
        close = self.src.find("*/", self.i + 2)
        if close == -1:
            self.fail("LEX-701", self.n)
            return
        end = close + 2
        for k in range(self.i + 2, close):
            ch = self.src[k]
            if not (_is_ascii4(ch) or ch in WHITESPACE):
                self.fail("LEX-702", end)
                return
        if self.delimiter_ok(end, MULTI_LINE_COMMENT_DELIMITER):
            self.emit(MULTI_LINE_COMMENT, end)
        else:
            self.fail("LEX-703", end)

    # -- reserved symbols ----------------------------------------------------------

    def lex_symbol(self):
        for symbol in SYMBOLS_LONGEST_FIRST:
            if self.src.startswith(symbol, self.i):
                end = self.i + len(symbol)
                if self.delimiter_ok(end, DIAGRAM_SYMBOLS[symbol]):
                    self.emit(symbol, end)
                else:
                    self.fail("LEX-602", end)
                return
        ch = self.src[self.i]
        if ch == "|":
            self.fail("LEX-601", self.i + 1)
        else:
            self.fail("LEX-901", self.i + 1)
