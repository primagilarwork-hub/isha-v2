from http.server import BaseHTTPRequestHandler
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "MINIAPP_DEV_MODE": os.environ.get("MINIAPP_DEV_MODE", "NOT SET"),
            "ALLOWED_USER_IDS": os.environ.get("ALLOWED_USER_IDS", "NOT SET"),
        }).encode())

    def log_message(self, *args):
        pass
