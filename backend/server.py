"""Local HTTP server that exposes the Pork CCig lexer to the React UI.

Standard library only. Run from the project root:

    py backend/server.py

Endpoints:
    GET  /api/keywords   keyword reference for the UI
    POST /api/lex        body {"source": "..."} -> {"tokens": [...], "errors": [...]}
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pork_lexer import IDENTIFIER, tokenize

HOST = "127.0.0.1"
PORT = 8000
MAX_BODY_BYTES = 2_000_000

# Keyword reference shown by the UI. Display data only: the lexer recognizes
# reserved words with its own transition table.

KEYWORD_GROUPS = (
    "Data Types",
    "Conditional Statements",
    "Iterative Statements",
    "Jump Statements",
    "Others",
)

# (word, group, C counterpart, description)
KEYWORDS = (
    ("meat", "Data Types", "int", "A data type used for storing whole numbers."),
    ("sauce", "Data Types", "float", "A data type used for numbers that contain decimal values."),
    ("chop", "Data Types", "char", "A data type that holds a single character."),
    ("recipe", "Data Types", "char[]", "Used to store a series of characters or a string."),
    ("cooked", "Data Types", "bool", "A data type that holds either a true or false value."),
    ("empty", "Data Types", "void", "A type used when no value is returned."),
    ("menu", "Data Types", "struct", "A user-defined type that combines related variables."),
    ("if", "Conditional Statements", "if", "Executes a statement when the given condition is true."),
    ("else", "Conditional Statements", "else", "Executes a block of code when the if condition is false."),
    ("switch", "Conditional Statements", "switch", "Allows the program to choose between several possible blocks of code."),
    ("case", "Conditional Statements", "case", "Represents one possible choice within a switch statement."),
    ("default", "Conditional Statements", "default", "Executes when none of the cases match."),
    ("for", "Iterative Statements", "for", "A loop commonly used to repeat code a specific number of times."),
    ("while", "Iterative Statements", "while", "Repeats a block of code as long as its condition remains true."),
    ("do", "Iterative Statements", "do", "Runs the loop body first and checks the condition afterward."),
    ("stop", "Jump Statements", "break", "Ends the execution of a loop or switch statement."),
    ("again", "Jump Statements", "continue", "Skips the current loop cycle and proceeds to the next one."),
    ("serveback", "Jump Statements", "return", "Ends a function and may send a value back to the caller."),
    ("pork", "Others", "main", "The function where the execution of the program begins."),
    ("serve", "Others", "printf", "A function used to show text or other output on the screen."),
    ("taste", "Others", "scanf", "A function used to receive data entered by the user."),
    ("yummy", "Others", "true", "A boolean value used to indicate a correct or active condition."),
    ("yuck", "Others", "false", "A boolean value used to indicate an incorrect or inactive condition."),
    ("fixed", "Others", "const", "A keyword used to keep a variable's value from being changed."),
)


def keyword_reference():
    return {
        "groups": list(KEYWORD_GROUPS),
        "keywords": [
            {"word": word, "group": group, "cCounterpart": c_counterpart, "description": description}
            for word, group, c_counterpart, description in KEYWORDS
        ],
    }


# /api/lex response: the lexer's (tokens, errors) in the shape the UI reads.

# Unterminated literals and comments can run to the end of the file, so their
# lexeme is cut to 10 characters plus "..." in the message.
SHORTENED_LENGTH = 10


def format_message(error):
    """Every error message reads:  Line <n>, Col <n>: <Error message> '<lexeme>'"""
    lexeme = error.lexeme
    if error.message.startswith("Unclosed") and len(lexeme) > SHORTENED_LENGTH:
        lexeme = lexeme[:SHORTENED_LENGTH] + "..."
    lexeme = lexeme.replace("\n", "\\n").replace("\t", "\\t")
    return f"Line {error.line}, Col {error.column}: {error.message} '{lexeme}'"


def lex_response(source):
    tokens, errors = tokenize(source)
    # Symbol table: identifier lexeme -> number, in order of first appearance.
    # Identifiers are shown as id1, id2, ... in the Lexer Table.
    symbols = {}
    token_rows = []
    for token in tokens:
        token_type = token.type
        if token_type == IDENTIFIER:
            number = symbols.setdefault(token.lexeme, len(symbols) + 1)
            token_type = f"{IDENTIFIER}{number}"
        token_rows.append({"type": token_type, "lexeme": token.lexeme, "line": token.line, "col": token.column})
    error_rows = [
        {
            "status": "Unavailable" if error.message == "Unavailable character" else "Invalid",
            "title": error.message,
            "line": error.line,
            "col": error.column,
            "lexeme": error.lexeme,
            "message": format_message(error),
        }
        for error in errors
    ]
    return {"tokens": token_rows, "errors": error_rows, "symbols": symbols}


class LexerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/keywords":
            self.send_json(200, keyword_reference())
        elif self.path == "/api/health":
            self.send_json(200, {"status": "ok"})
        else:
            self.send_json(404, {"error": "Not found."})

    def do_POST(self):
        if self.path != "/api/lex":
            self.send_json(404, {"error": "Not found."})
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY_BYTES:
            self.send_json(413, {"error": "Source code is too large."})
            return

        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "Request body must be JSON."})
            return

        source = payload.get("source") if isinstance(payload, dict) else None
        if not isinstance(source, str):
            self.send_json(400, {"error": 'Expected {"source": "<text>"}.'})
            return

        self.send_json(200, lex_response(source))

    def send_json(self, status, body):
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    server = ThreadingHTTPServer((HOST, PORT), LexerRequestHandler)
    print(f"Pork CCig lexer server running at http://{HOST}:{PORT}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
