from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import handlers, telegram, config as app_config


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())

        try:
            update = json.loads(body)
            message = update.get("message") or update.get("edited_message")
            if not message:
                return

            # Handle foto (receipt scanning)
            if message.get("photo"):
                cycle = app_config.get_current_cycle()
                user_name = message.get("from", {}).get("first_name", "")
                reply_text = handlers.handle_receipt(message, cycle, user_name)
            else:
                reply_text = handlers.handle_message(message)

            telegram.reply(message, reply_text)

        except json.JSONDecodeError as e:
            print(f"[webhook] invalid JSON: {e}")
        except Exception as e:
            print(f"[webhook error] {e}")
            try:
                update = json.loads(body)
                message = update.get("message") or update.get("edited_message")
                if message:
                    telegram.reply(message, "Maaf, ada error. Coba lagi ya 🙏")
            except Exception:
                pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "webhook active"}).encode())
