import requests
from lib.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_IDS

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def send_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> bool:
    res = requests.post(f"{BASE_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }, timeout=10)
    return res.ok

def broadcast(text: str, parse_mode: str = "Markdown") -> None:
    """Kirim ke semua chat ID yang terdaftar."""
    for chat_id in TELEGRAM_CHAT_IDS:
        send_message(chat_id, text, parse_mode)

def get_file(file_id: str) -> bytes | None:
    res = requests.get(f"{BASE_URL}/getFile", params={"file_id": file_id}, timeout=10)
    if not res.ok:
        return None
    file_path = res.json()["result"]["file_path"]
    dl = requests.get(f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}", timeout=30)
    return dl.content if dl.ok else None

def set_webhook(url: str) -> bool:
    res = requests.post(f"{BASE_URL}/setWebhook", json={"url": url}, timeout=10)
    return res.ok

def reply(message: dict, text: str, parse_mode: str = "Markdown") -> bool:
    chat_id = message.get("chat", {}).get("id")
    return send_message(str(chat_id), text, parse_mode)
