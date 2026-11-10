"""Vercel serverless entry point for the Pork CCig lexer.

Vercel's Python runtime serves the BaseHTTPRequestHandler subclass named
`handler`. vercel.json rewrites every /api/* request here, and the request keeps
its original path, so backend/server.py routes it exactly as it does locally.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from server import LexerRequestHandler  # noqa: E402


class handler(LexerRequestHandler):
    pass
