"""Base handler untuk Mini App API endpoints."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from http.server import BaseHTTPRequestHandler
from api.miniapp.auth import authenticate


def json_response(data: dict, status: int = 200) -> bytes:
    return json.dumps({"success": status < 400, **data}).encode()


class MiniAppBaseHandler(BaseHTTPRequestHandler):
    """Base class untuk semua Mini App API handlers."""

    def _auth(self) -> dict | None:
        """Authenticate request. Returns user dict or sends 401/403 and returns None."""
        user, status = authenticate(dict(self.headers))
        if status != 200:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            msg = "Unauthorized" if status == 401 else "Forbidden"
            self.wfile.write(json_response({"error": msg}, status))
            return None
        return user

    def _send(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json_response(data, status))

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Telegram-Init-Data")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress default access logs
