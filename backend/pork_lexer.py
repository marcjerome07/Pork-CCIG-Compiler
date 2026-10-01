"""Lexical analyzer for the Pork CCig language.

Implements only the lexical phase of the Pork CCig Compiler specification:
reserved words, reserved symbols, identifiers, literals, comments and
whitespace. It never parses, type-checks or executes the source.

How the specification is applied (decided by the project group):
  * Transition diagrams (spec pp. 76-85) define the token paths and the
    delimiter that must follow each token.
  * Where a diagram contradicts the written rules or regular definitions,
    the written rules win (e.g. escapes start with a backslash, identifiers
    may contain underscores and have up to 20 characters).
  * Symbols that have no transition diagram are recognized without a
    delimiter check.
  * Every token listed in the regular-expression table (spec pp. 70-73) is
    reported, including space, newline, tab and comments.
"""

from dataclasses import asdict, dataclass, field

# ---------------------------------------------------------------------------
# Regular definitions (spec pp. 73-74)
# ---------------------------------------------------------------------------

DIGITS = frozenset("0123456789")
LOWERCASE = frozenset("abcdefghijklmnopqrstuvwxyz")
UPPERCASE = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ALPHA = LOWERCASE | UPPERCASE
ALPHA_NUM = DIGITS | ALPHA  # the spec also writes this as "alpha_numeric"
UNDERSCORE = frozenset("_")
ALPHA_ID = ALPHA_NUM | UNDERSCORE
WHITESPACE = frozenset(" \t\n")
OPERATORS = frozenset("+-*/%<>=!&|")
ESCAPE_SEQ = frozenset("nt'\"\\0")

# ascii1: printable ASCII except \ and '   (chop literal characters)
# ascii2: printable ASCII except \ and "   (recipe literal characters)
# ascii3: printable ASCII                  (single-line comment text, plus tab)
# ascii4: printable ASCII except space     (multi-line comment text, plus whitespace)
def _is_ascii1(ch):
    return 32 <= ord(ch) <= 126 and ch not in "\\'"


def _is_ascii2(ch):
    return 32 <= ord(ch) <= 126 and ch not in '\\"'


def _is_ascii3(ch):
    return 32 <= ord(ch) <= 126


def _is_ascii4(ch):
    return 33 <= ord(ch) <= 126


# Delimiter sets: name -> (characters, readable description). Only the sets
# used by the transition diagrams are listed.
DELIMITERS = {
    "whitespace": (WHITESPACE, "whitespace"),
    "delim1": (frozenset(";") | WHITESPACE, "; or whitespace"),
    "delim2": (frozenset(":") | WHITESPACE, ": or whitespace"),
    "delim3": (frozenset("{") | WHITESPACE, "{ or whitespace"),
    "delim4": (frozenset("(") | WHITESPACE, "( or whitespace"),
    "delim5": (frozenset(",({;") | WHITESPACE, ", ( { ; or whitespace"),
    "delim7": (ALPHA_NUM | frozenset("+-!('\"") | WHITESPACE,
               "letter, digit, + - ! ( ' \" or whitespace"),
    "delim8": (ALPHA_NUM | frozenset("-!('\"") | WHITESPACE,
               "letter, digit, - ! ( ' \" or whitespace"),
    "delim9": (ALPHA_ID | frozenset("()],;") | WHITESPACE,
               "letter, digit, _, ( ) ] , ; or whitespace"),
    "delim10": (ALPHA_NUM | UNDERSCORE | frozenset("+-!(") | WHITESPACE,
                "letter, digit, _, + - ! ( or whitespace"),
    "delim11": (ALPHA | UNDERSCORE | frozenset("+!('") | WHITESPACE,
                "letter, _, + ! ( ' or whitespace"),
    "delim21": (OPERATORS | frozenset(")]},:;") | WHITESPACE,
                "operator, ) ] } , : ; or whitespace"),
    "delim22": (OPERATORS | frozenset(")]},;") | WHITESPACE,
                "operator, ) ] } , ; or whitespace"),
    "delim23": (frozenset("+><=!&|})],;") | WHITESPACE,
                "+ > < = ! & | } ) ] , ; or whitespace"),
}

# ---------------------------------------------------------------------------
# Reserved words (spec p. 5-6 for meaning, pp. 70-71 for groups,
# pp. 76-77 for the delimiter that must follow each word)
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
    Keyword("yummy", "Others", "true", "A boolean value used to indicate a correct or active condition.", "whitespace"),
    Keyword("yuck", "Others", "false", "A boolean value used to indicate an incorrect or inactive condition.", "whitespace"),
    Keyword("fixed", "Others", "const", "A keyword used to keep a variable's value from being changed.", "whitespace"),
)

KEYWORD_DELIMITER = {kw.word: kw.delimiter for kw in KEYWORDS}

# ---------------------------------------------------------------------------
# Reserved symbols (spec pp. 7-8 and 71-73)
# ---------------------------------------------------------------------------

# Symbols drawn in the reserved-symbol transition diagram (spec p. 78),
# with the delimiter that must follow each one.
DIAGRAM_SYMBOLS = {
    "=": "delim7", "==": "delim8",
    "+": "delim9", "++": "delim10", "+=": "delim11",
    "-": "delim11", "--": "delim9", "-=": "delim11",
    "*": "delim11", "*=": "delim11",
    "/": "delim11", "/=": "delim11",
    "%": "delim11", "%=": "delim11",
    ">": "delim8", ">=": "delim8",
    "<": "delim8", "<=": "delim8",
}

# Symbols in the reserved-symbol table that have no transition diagram:
# recognized without a delimiter check.
UNCHECKED_SYMBOLS = frozenset({
    "!=", "&&", "||", "!", "&",
    "(", ")", "[", "]", "{", "}",
    ";", ",", ".", ":",
})

# Longer symbols are tried first so "<=" wins over "<".
SYMBOLS_LONGEST_FIRST = sorted(
    set(DIAGRAM_SYMBOLS) | UNCHECKED_SYMBOLS, key=len, reverse=True
)

# ---------------------------------------------------------------------------
# Literal and identifier limits (written rules, spec pp. 8-11)
# ---------------------------------------------------------------------------

MAX_IDENTIFIER_LENGTH = 20
MAX_MEAT_DIGITS = 15
MAX_SAUCE_WHOLE_DIGITS = 12
MAX_SAUCE_DECIMAL_DIGITS = 7

WHITESPACE_TOKENS = {" ": "space", "\n": "newline", "\t": "tab"}
ESCAPE_HELP = "valid escapes are \\n \\t \\\\ \\' \\\" \\0"

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    col: int


@dataclass
class LexError:
    line: int
    col: int
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
    if ch is None:
        return "end of input"
    if ch in WHITESPACE_TOKENS:
        return WHITESPACE_TOKENS[ch]
    return f"'{ch}'"


class _Lexer:
    def __init__(self, source):
        # Normalize Windows and old Mac line endings so columns stay correct.
        self.src = source.replace("\r\n", "\n").replace("\r", "\n")
        self.n = len(self.src)
        self.i = 0
        self.line = 1
        self.col = 1
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
        self.result.tokens.append(
            Token(token_type, self.src[self.i:end], self.line, self.col)
        )
        self.advance_to(end)

    def error(self, message, line=None, col=None):
        self.result.errors.append(
            LexError(line or self.line, col or self.col, message)
        )

    def fail(self, message, end):
        """Report an error at the current token start and skip to `end`."""
        self.error(message)
        self.advance_to(end)

    def delimiter_ok(self, end, delimiter):
        nxt = self.char_at(end)
        # End of input is accepted as a delimiter (the diagrams do not cover it).
        return nxt is None or nxt in DELIMITERS[delimiter][0]

    def delimiter_error(self, what, end, delimiter):
        lexeme = self.src[self.i:end]
        allowed = DELIMITERS[delimiter][1]
        self.fail(
            f"Invalid delimiter {_show(self.char_at(end))} after {what} "
            f"'{lexeme}'. Allowed: {allowed} ({delimiter}).",
            end,
        )

    def find_closing_quote(self, start, quote):
        """Index of the closing quote on the same line, skipping escapes."""
        j = start
        while j < self.n:
            ch = self.src[j]
            if ch == "\n":
                return None
            if ch == "\\":
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
            if ch in WHITESPACE_TOKENS:
                self.emit(WHITESPACE_TOKENS[ch], self.i + 1)
            elif ch in ALPHA or ch == "_":
                self.lex_word()
            elif ch in DIGITS or (ch == "-" and nxt is not None and nxt in DIGITS):
                self.lex_number()
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

    # -- reserved words and identifiers --------------------------------------

    def lex_word(self):
        end = self.i
        while end < self.n and self.src[end] in ALPHA_ID:
            end += 1
        word = self.src[self.i:end]

        # A reserved word only matches as a complete word: "meatball" keeps
        # reading letters and becomes an identifier.
        if word in KEYWORD_DELIMITER:
            delimiter = KEYWORD_DELIMITER[word]
            if self.delimiter_ok(end, delimiter):
                self.emit(word, end)
            else:
                self.delimiter_error("reserved word", end, delimiter)
            return

        if len(word) > MAX_IDENTIFIER_LENGTH:
            self.fail(
                f"Identifier '{word}' has {len(word)} characters; the limit "
                f"is {MAX_IDENTIFIER_LENGTH}.",
                end,
            )
        elif not self.delimiter_ok(end, "delim21"):
            self.delimiter_error("identifier", end, "delim21")
        else:
            self.emit("id", end)

    # -- meat and sauce literals -----------------------------------------------

    def lex_number(self):
        j = self.i + 1 if self.src[self.i] == "-" else self.i
        whole_start = j
        while j < self.n and self.src[j] in DIGITS:
            j += 1
        whole_digits = j - whole_start
        decimal_digits = None

        if self.char_at(j) == ".":
            if self.char_at(j + 1) is not None and self.src[j + 1] in DIGITS:
                frac_start = j + 1
                j = frac_start
                while j < self.n and self.src[j] in DIGITS:
                    j += 1
                decimal_digits = j - frac_start
            else:
                self.fail(
                    f"Malformed sauce literal '{self.src[self.i:j + 1]}': a "
                    "digit is required after the decimal point.",
                    j + 1,
                )
                return

        # Letters, underscores or extra decimal points glued to the number.
        if self.char_at(j) is not None and (
            self.src[j] in ALPHA_ID or (decimal_digits is not None and self.src[j] == ".")
        ):
            end = j
            while end < self.n and (self.src[end] in ALPHA_ID or self.src[end] == "."):
                end += 1
            bad = self.src[self.i:end]
            body = bad.lstrip("-")
            if all(c in DIGITS or c == "." for c in body):
                self.fail(f"Malformed sauce literal '{bad}': multiple decimal points.", end)
            else:
                self.fail(
                    f"Invalid token '{bad}': identifiers cannot start with a "
                    "digit and numbers cannot contain letters.",
                    end,
                )
            return

        lexeme = self.src[self.i:j]
        if decimal_digits is None:
            if whole_digits > MAX_MEAT_DIGITS:
                self.fail(
                    f"meat literal '{lexeme}' has {whole_digits} digits; the "
                    f"limit is {MAX_MEAT_DIGITS}.",
                    j,
                )
            elif not self.delimiter_ok(j, "delim21"):
                self.delimiter_error("meat literal", j, "delim21")
            else:
                self.emit("meat_lit", j)
            return

        if whole_digits > MAX_SAUCE_WHOLE_DIGITS:
            self.fail(
                f"sauce literal '{lexeme}' has {whole_digits} whole-number "
                f"digits; the limit is {MAX_SAUCE_WHOLE_DIGITS}.",
                j,
            )
        elif decimal_digits > MAX_SAUCE_DECIMAL_DIGITS:
            self.fail(
                f"sauce literal '{lexeme}' has {decimal_digits} decimal "
                f"digits; the limit is {MAX_SAUCE_DECIMAL_DIGITS}.",
                j,
            )
        elif not self.delimiter_ok(j, "delim22"):
            self.delimiter_error("sauce literal", j, "delim22")
        else:
            self.emit("sauce_lit", j)

    # -- chop and recipe literals ----------------------------------------------

    def check_literal_body(self, body, body_col, is_valid_char, kind):
        """Validate characters and escapes. Returns (char_count, ok)."""
        count = 0
        k = 0
        while k < len(body):
            ch = body[k]
            if ch == "\\":
                esc = body[k + 1] if k + 1 < len(body) else None
                if esc is None or esc not in ESCAPE_SEQ:
                    shown = "\\" + esc if esc else "\\"
                    self.error(
                        f"Invalid escape '{shown}' in {kind} literal; a single "
                        f"backslash is not allowed ({ESCAPE_HELP}).",
                        self.line,
                        body_col + k,
                    )
                    return count, False
                k += 2
            elif is_valid_char(ch):
                k += 1
            else:
                self.error(
                    f"Invalid character {_show(ch)} in {kind} literal; only "
                    "printable ASCII characters are allowed.",
                    self.line,
                    body_col + k,
                )
                return count, False
            count += 1
        return count, True

    def lex_chop(self):
        close = self.find_closing_quote(self.i + 1, "'")
        if close is None:
            self.fail("Unterminated chop literal: missing closing '.", self.end_of_line(self.i))
            return
        end = close + 1
        body = self.src[self.i + 1:close]
        if body == "":
            self.fail("Empty chop literal ''; a chop literal must contain one character.", end)
            return
        start_i = self.i
        count, ok = self.check_literal_body(body, self.col + 1, _is_ascii1, "chop")
        if not ok:
            self.advance_to(end)
            return
        if count != 1:
            self.fail(
                f"chop literal {self.src[start_i:end]} has {count} characters; "
                "it must contain exactly one.",
                end,
            )
        elif not self.delimiter_ok(end, "delim21"):
            self.delimiter_error("chop literal", end, "delim21")
        else:
            self.emit("chop_lit", end)

    def lex_recipe(self):
        close = self.find_closing_quote(self.i + 1, '"')
        if close is None:
            self.fail('Unterminated recipe literal: missing closing ".', self.end_of_line(self.i))
            return
        end = close + 1
        body = self.src[self.i + 1:close]
        _, ok = self.check_literal_body(body, self.col + 1, _is_ascii2, "recipe")
        if not ok:
            self.advance_to(end)
        elif not self.delimiter_ok(end, "delim23"):
            self.delimiter_error("recipe literal", end, "delim23")
        else:
            self.emit("recipe_lit", end)

    # -- comments ----------------------------------------------------------------

    def lex_single_line_comment(self):
        # Runs to the end of the line; the newline itself becomes its own token.
        end = self.end_of_line(self.i)
        for k in range(self.i + 2, end):
            ch = self.src[k]
            if not (_is_ascii3(ch) or ch == "\t"):
                self.error(
                    f"Invalid character {_show(ch)} in single-line comment.",
                    self.line,
                    self.col + (k - self.i),
                )
                self.advance_to(end)
                return
        self.emit("Single-Line Comment", end)

    def lex_multi_line_comment(self):
        close = self.src.find("*/", self.i + 2)
        if close == -1:
            self.fail("Unterminated multi-line comment: missing closing */.", self.n)
            return
        end = close + 2
        line, col = self.line, self.col + 2  # position just after "/*"
        for k in range(self.i + 2, close):
            ch = self.src[k]
            if not (_is_ascii4(ch) or ch in WHITESPACE):
                self.error(f"Invalid character {_show(ch)} in multi-line comment.", line, col)
                self.advance_to(end)
                return
            if ch == "\n":
                line, col = line + 1, 1
            else:
                col += 1
        # Spec p. 85: a multi-line comment must be followed by whitespace.
        if not self.delimiter_ok(end, "whitespace"):
            self.delimiter_error("multi-line comment", end, "whitespace")
        else:
            self.emit("Multi-Line Comment", end)

    # -- reserved symbols ----------------------------------------------------------

    def lex_symbol(self):
        for symbol in SYMBOLS_LONGEST_FIRST:
            if self.src.startswith(symbol, self.i):
                end = self.i + len(symbol)
                delimiter = DIAGRAM_SYMBOLS.get(symbol)
                if delimiter and not self.delimiter_ok(end, delimiter):
                    self.delimiter_error("symbol", end, delimiter)
                else:
                    self.emit(symbol, end)
                return
        self.fail(f"Invalid character {_show(self.src[self.i])}.", self.i + 1)
