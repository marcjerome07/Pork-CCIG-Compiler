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
    "-": "delim11", "--": "delim10", "-=": "delim11",
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

# Tokens ignored when deciding whether "-" before a digit is a sign or an operator.
TRIVIA = frozenset([SPACE, NEWLINE, TAB, SINGLE_LINE_COMMENT, MULTI_LINE_COMMENT])

# A "-" right after one of these is subtraction, not the sign of a literal.
OPERAND_END = frozenset([
    ID, MEAT_LIT, SAUCE_LIT, CHOP_LIT, RECIPE_LIT, "yummy", "yuck", ")", "]", "++", "--",
])

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

# code -> (status, title). "Incomplete": a token was started but a required part
# is missing. "Invalid": a formed token breaks a rule.
ERROR_CATALOG = {
    "LEX-101": ("Invalid", "Invalid numerical value"),
    "LEX-102": ("Invalid", "Invalid decimal value"),
    "LEX-103": ("Invalid", "Invalid decimal value"),
    "LEX-104": ("Incomplete", "Incomplete decimal"),
    "LEX-105": ("Incomplete", "Incomplete decimal"),
    "LEX-106": ("Invalid", "Invalid decimal value"),
    "LEX-107": ("Invalid", "Invalid identifier"),
    "LEX-108": ("Invalid", "Invalid delimiter"),
    "LEX-201": ("Incomplete", "Incomplete character literal"),
    "LEX-202": ("Invalid", "Invalid character literal"),
    "LEX-203": ("Invalid", "Invalid character literal"),
    "LEX-204": ("Invalid", "Invalid escape sequence"),
    "LEX-205": ("Invalid", "Invalid delimiter"),
    "LEX-206": ("Invalid", "Invalid character literal"),
    "LEX-301": ("Incomplete", "Incomplete string literal"),
    "LEX-302": ("Invalid", "Invalid escape sequence"),
    "LEX-303": ("Invalid", "Invalid delimiter"),
    "LEX-401": ("Invalid", "Invalid delimiter"),
    "LEX-501": ("Invalid", "Invalid identifier"),
    "LEX-502": ("Invalid", "Invalid delimiter"),
    "LEX-601": ("Incomplete", "Incomplete operator"),
    "LEX-602": ("Invalid", "Invalid delimiter"),
    "LEX-701": ("Incomplete", "Incomplete comment"),
    "LEX-702": ("Invalid", "Invalid comment character"),
    "LEX-703": ("Invalid", "Invalid delimiter"),
    "LEX-901": ("Invalid", "Invalid character"),
}


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


def _show(ch):
    """A character as it appears in messages: space, tab, newline, end of input,
    or the character in quotes."""
    if ch is None:
        return "end of input"
    if ch in WHITESPACE_TOKENS:
        return WHITESPACE_TOKENS[ch]
    if 32 <= ord(ch) <= 126:
        return f"'{ch}'"
    return f"U+{ord(ch):04X}"


class _Lexer:
    def __init__(self, source):
        # Normalize Windows and old Mac line endings so columns stay correct.
        self.src = source.replace("\r\n", "\n").replace("\r", "\n")
        self.n = len(self.src)
        self.i = 0
        self.line = 1
        self.col = 1
        self.prev = None  # type of the last emitted non-trivia token
        self.result = LexResult()

    # -- helpers -------------------------------------------------------------

    def char_at(self, index):
        return self.src[index] if index < self.n else None

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
        if token_type not in TRIVIA:
            self.prev = token_type
        self.advance_to(end)

    def fail(self, code, message, end):
        """Report an error covering src[i:end] and resume scanning at `end`."""
        status, title = ERROR_CATALOG[code]
        self.result.errors.append(
            LexError(code, status, title, self.line, self.col, self.src[self.i:end], message)
        )
        self.advance_to(end)

    def delimiter_ok(self, end, delimiter):
        # End of input is accepted as a delimiter for every token.
        nxt = self.char_at(end)
        return nxt is None or nxt in DELIMITERS[delimiter]

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
        while self.i < self.n:
            ch = self.src[self.i]
            nxt = self.char_at(self.i + 1)
            nxt_is_digit = nxt is not None and nxt in DIGITS
            if ch in WHITESPACE_TOKENS:
                self.lex_whitespace()
            elif ch in ALPHA_ID:
                self.lex_word()
            elif ch in DIGITS:
                self.lex_number()
            elif ch == "-" and nxt_is_digit and self.prev not in OPERAND_END:
                self.lex_number()  # negative literal, e.g. "x = -5" or "(-1)"
            elif ch == "." and nxt_is_digit:
                self.fail(
                    "LEX-105",
                    "A decimal value must have at least one digit before the decimal point.",
                    self.i + 1,
                )
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

    # -- whitespace ------------------------------------------------------------

    def lex_whitespace(self):
        end = self.i + 1
        nxt = self.char_at(end)
        # A character that starts no token is reported once, as LEX-901, rather
        # than also as a bad delimiter after the whitespace before it.
        if self.delimiter_ok(end, WHITESPACE_DELIMITER) or nxt not in TOKEN_START:
            self.emit(WHITESPACE_TOKENS[self.src[self.i]], end)
        else:
            self.fail("LEX-602", f"{_show(nxt)} cannot follow {_show(self.src[self.i])}.", end)

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
                self.fail(
                    "LEX-401",
                    f"{_show(self.char_at(end))} cannot follow the reserved word '{word}'.",
                    end,
                )
            return

        if len(word) > MAX_IDENTIFIER_LENGTH:
            cut = self.i + MAX_IDENTIFIER_LENGTH
            self.fail(
                "LEX-501",
                f"'{self.src[self.i:cut]}' exceeds the {MAX_IDENTIFIER_LENGTH}-character "
                "identifier limit.",
                cut,
            )
        elif not self.delimiter_ok(end, ID_DELIMITER):
            self.fail(
                "LEX-502",
                f"{_show(self.char_at(end))} cannot follow the identifier '{word}'.",
                end,
            )
        else:
            self.emit(ID, end)

    # -- meat and sauce literals -----------------------------------------------

    def lex_number(self):
        """One character of lookahead: the part read so far becomes the error
        lexeme and scanning restarts at the failing character."""
        start = self.i
        j = start + 1 if self.src[start] == "-" else start
        int_start = j
        while j < self.n and self.src[j] in DIGITS and j - int_start < MAX_MEAT_DIGITS:
            j += 1
        int_count = j - int_start
        nxt = self.char_at(j)

        if nxt is not None and nxt in DIGITS:
            self.fail(
                "LEX-101",
                f"'{self.src[start:j]}' exceeds the {MAX_MEAT_DIGITS}-digit integer limit.",
                j,
            )
            return

        token_type = MEAT_LIT
        if nxt == ".":
            if int_count > MAX_SAUCE_WHOLE_DIGITS:
                self.fail(
                    "LEX-102",
                    f"The whole-number part of '{self.src[start:j]}' exceeds the "
                    f"{MAX_SAUCE_WHOLE_DIGITS}-digit limit for decimal values.",
                    j,
                )
                return
            j += 1  # the "."
            nxt = self.char_at(j)
            if nxt is None or nxt not in DIGITS:
                self.fail(
                    "LEX-104",
                    f"'{self.src[start:j]}' must have at least one digit after the decimal point.",
                    j,
                )
                return
            frac_start = j
            while j < self.n and self.src[j] in DIGITS and j - frac_start < MAX_SAUCE_DECIMAL_DIGITS:
                j += 1
            nxt = self.char_at(j)
            if nxt is not None and nxt in DIGITS:
                self.fail(
                    "LEX-103",
                    f"The fractional part of '{self.src[start:j]}' exceeds the "
                    f"{MAX_SAUCE_DECIMAL_DIGITS}-digit limit.",
                    j,
                )
                return
            if nxt == ".":
                self.fail(
                    "LEX-106",
                    f"'{self.src[start:j]}' cannot contain more than one decimal point.",
                    j,
                )
                return
            token_type = SAUCE_LIT

        lexeme = self.src[start:j]
        if nxt is not None and nxt in ALPHA_ID:
            self.fail(
                "LEX-107",
                f"'{lexeme}' is followed by '{nxt}'; identifiers cannot begin with a digit.",
                j,
            )
        elif not self.delimiter_ok(j, NUMBER_DELIMITER):
            self.fail("LEX-108", f"{_show(nxt)} cannot follow the numeric literal '{lexeme}'.", j)
        else:
            self.emit(token_type, j)

    # -- chop and recipe literals ----------------------------------------------

    @staticmethod
    def literal_body_problem(body, is_valid_char):
        """Return (char_count, problem). problem is None, ("escape", "\\q") or
        ("char", c) for a character outside the allowed ASCII range."""
        count = 0
        k = 0
        while k < len(body):
            ch = body[k]
            if ch == "\\":
                esc = body[k + 1] if k + 1 < len(body) else ""
                if esc == "" or esc not in ESCAPE_SEQ:
                    return count, ("escape", "\\" + esc)
                k += 2
            elif is_valid_char(ch):
                k += 1
            else:
                return count, ("char", ch)
            count += 1
        return count, None

    def lex_chop(self):
        close = self.find_closing_quote(self.i + 1, "'")
        if close is None:
            self.fail("LEX-201", "Missing closing single quote (').", self.end_of_line(self.i))
            return
        end = close + 1
        lexeme = self.src[self.i:end]
        body = self.src[self.i + 1:close]
        if body == "":
            self.fail("LEX-202", "A character literal cannot be empty.", end)
            return
        if body == " ":
            self.fail("LEX-206", "A chop value cannot be a space.", end)
            return
        count, problem = self.literal_body_problem(body, _is_ascii1)
        if problem and problem[0] == "escape":
            self.fail("LEX-204", f"'{problem[1]}' is not a valid escape sequence.", end)
        elif problem:
            self.fail(
                "LEX-204",
                f"{_show(problem[1])} is not a printable ASCII character; it is not allowed "
                "in a character literal.",
                end,
            )
        elif count != 1:
            self.fail(
                "LEX-203",
                f"{lexeme} contains more than one character; use a recipe (string) instead.",
                end,
            )
        elif not self.delimiter_ok(end, CHOP_DELIMITER):
            self.fail(
                "LEX-205",
                f"{_show(self.char_at(end))} cannot follow the character literal {lexeme}.",
                end,
            )
        else:
            self.emit(CHOP_LIT, end)

    def lex_recipe(self):
        close = self.find_closing_quote(self.i + 1, '"')
        if close is None:
            self.fail("LEX-301", 'Missing closing double quote (").', self.end_of_line(self.i))
            return
        end = close + 1
        lexeme = self.src[self.i:end]
        _, problem = self.literal_body_problem(self.src[self.i + 1:close], _is_ascii2)
        if problem and problem[0] == "escape":
            self.fail("LEX-302", f"'{problem[1]}' is not a valid escape sequence in {lexeme}.", end)
        elif problem:
            self.fail(
                "LEX-302",
                f"{_show(problem[1])} is not a printable ASCII character; it is not allowed "
                f"in {lexeme}.",
                end,
            )
        elif not self.delimiter_ok(end, RECIPE_DELIMITER):
            self.fail(
                "LEX-303",
                f"{_show(self.char_at(end))} cannot follow the string literal {lexeme}.",
                end,
            )
        else:
            self.emit(RECIPE_LIT, end)

    # -- comments ----------------------------------------------------------------

    def lex_single_line_comment(self):
        # Runs to the end of the line; the newline itself becomes its own token.
        end = self.end_of_line(self.i)
        for k in range(self.i + 2, end):
            ch = self.src[k]
            if not (_is_ascii3(ch) or ch == "\t"):
                self.fail("LEX-702", f"{_show(ch)} is not allowed inside a comment.", end)
                return
        self.emit(SINGLE_LINE_COMMENT, end)

    def lex_multi_line_comment(self):
        close = self.src.find("*/", self.i + 2)
        if close == -1:
            self.fail("LEX-701", "Multi-line comment is missing its closing '*/'.", self.n)
            return
        end = close + 2
        for k in range(self.i + 2, close):
            ch = self.src[k]
            if not (_is_ascii4(ch) or ch in WHITESPACE):
                self.fail("LEX-702", f"{_show(ch)} is not allowed inside a comment.", end)
                return
        if self.delimiter_ok(end, MULTI_LINE_COMMENT_DELIMITER):
            self.emit(MULTI_LINE_COMMENT, end)
        else:
            self.fail(
                "LEX-703",
                f"{_show(self.char_at(end))} cannot follow a multi-line comment.",
                end,
            )

    # -- reserved symbols ----------------------------------------------------------

    def lex_symbol(self):
        for symbol in SYMBOLS_LONGEST_FIRST:
            if self.src.startswith(symbol, self.i):
                end = self.i + len(symbol)
                if self.delimiter_ok(end, DIAGRAM_SYMBOLS[symbol]):
                    self.emit(symbol, end)
                else:
                    self.fail(
                        "LEX-602",
                        f"{_show(self.char_at(end))} cannot follow '{symbol}'.",
                        end,
                    )
                return
        ch = self.src[self.i]
        if ch == "|":
            self.fail(
                "LEX-601",
                "'|' must be followed by '|' to form the logical OR operator (||).",
                self.i + 1,
            )
        else:
            self.fail("LEX-901", f"{_show(ch)} is not a valid character.", self.i + 1)
