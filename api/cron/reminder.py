from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lib import handlers, telegram, config
from lib.config import CRON_SECRET


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        if CRON_SECRET and auth != f"Bearer {CRON_SECRET}":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

        try:
            cycle = config.get_current_cycle()
            today = date.today()

            # Hari pertama cycle baru → kirim notifikasi awal cycle
            if today == cycle["start"]:
                msg = handlers.generate_new_cycle_message()
                telegram.broadcast(msg)
                self.wfile.write(json.dumps({"status": "ok", "event": "new_cycle"}).encode())
                return

            # Hari terakhir cycle → kirim System Review
            if today == cycle["end"]:
                review = handlers.generate_system_review(cycle["id"])
                telegram.broadcast(review)

            # Hari Senin → kirim weekly summary
            if today.weekday() == 0:
                weekly = handlers.generate_weekly_summary()
                telegram.broadcast(weekly)

            # Reminder harian
            reminder = handlers.generate_reminder_message()
            telegram.broadcast(reminder)

            self.wfile.write(json.dumps({"status": "ok", "sent": True}).encode())

        except Exception as e:
            print(f"[cron error] {e}")
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
