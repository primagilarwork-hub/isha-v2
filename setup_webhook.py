"""
Jalankan sekali untuk set webhook Telegram:
  python setup_webhook.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["TELEGRAM_TOKEN"]
VERCEL_URL = os.environ.get("VERCEL_URL", "https://isha-v2-r8po.vercel.app")

url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
res = requests.post(url, json={"url": f"{VERCEL_URL}/api/webhook"})
print(res.json())
