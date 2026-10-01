"""Local HTTP server that exposes the Pork CCig lexer to the React UI.

Standard library only. Run from the project root:

    py backend/server.py

Endpoints:
    GET  /api/keywords   keyword reference (same table the lexer uses)
    POST /api/lex        body {"source": "..."} -> {"tokens": [...], "errors": [...]}
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pork_lexer import keyword_reference, tokenize

HOST = "127.0.0.1"
PORT = 8000
MAX_BODY_BYTES = 2_000_000


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

        self.send_json(200, tokenize(source).to_dict())

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
