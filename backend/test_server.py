"""Server tests for the Pork CCig lexer API. Run from the project root:

    py -m unittest discover -s backend -v
"""

import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from server import LexerRequestHandler, keyword_reference, lex_response

WORDS = [
    "again", "case", "chop", "cooked", "default", "do", "else", "empty", "fixed", "for", "if", "meat",
    "menu", "pork", "recipe", "sauce", "serve", "serveback", "stop", "switch", "taste", "while", "yummy", "yuck",
]


class ServerTests(unittest.TestCase):
    def test_identifiers_are_numbered_by_first_appearance(self):
        response = lex_response("a b a")
        self.assertEqual([(t["type"], t["lexeme"], t["line"], t["col"]) for t in response["tokens"] if t["type"] != "space"],
                         [("id1", "a", 1, 1), ("id2", "b", 1, 3), ("id1", "a", 1, 5)])
        self.assertEqual(response["symbols"], {"a": 1, "b": 2})

    def test_error_messages(self):
        cases = (
            ("meat;", "Line 1, Col 1: Invalid delimiter 'meat'", "Invalid"),
            ("$", "Line 1, Col 1: Unavailable character '$'", "Unavailable"),
            ("1.12345678", "Line 1, Col 1: Sauce decimal part exceeds 7 digits '1.1234567'", "Invalid"),
            ('"123456789012', "Line 1, Col 1: Unclosed string value '\"123456789...'", "Invalid"),
            ("x\n.", "Line 1, Col 2: Invalid delimiter '\\n'", "Invalid"),
        )
        for source, message, status in cases:
            error = lex_response(source)["errors"][0]
            self.assertEqual((error["message"], error["status"]), (message, status))

    def test_keyword_reference_matches_the_reserved_words(self):
        reference = keyword_reference()
        self.assertEqual(sorted(k["word"] for k in reference["keywords"]), sorted(WORDS))
        self.assertEqual([k["word"] for k in reference["keywords"] if k["group"] == "Data Types"],
                         ["meat", "sauce", "chop", "recipe", "cooked", "empty", "menu"])

    def test_http_endpoints(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), LexerRequestHandler)
        LexerRequestHandler.log_message = lambda *args: None
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urllib.request.urlopen(base + "/api/keywords") as response:
                self.assertEqual(len(json.load(response)["keywords"]), 24)
            request = urllib.request.Request(
                base + "/api/lex", data=json.dumps({"source": "meat x;"}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(request) as response:
                body = json.load(response)
            self.assertEqual([t["type"] for t in body["tokens"]], ["meat", "space", "id1", ";"])
            self.assertEqual(body["errors"], [])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
