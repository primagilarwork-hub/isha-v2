"""Receipt scanning handler."""
from datetime import date
from lib import db, ai_engine


def handle_receipt(message: dict, cycle: dict, user_name: str = "") -> str:
    from lib import telegram as tg
    from lib.handlers.expense import handle_expense

    photos = message.get("photo", [])
    if not photos:
        return "Tidak ada foto yang diterima."

    file_id = photos[-1]["file_id"]
    photo_bytes = tg.get_file(file_id)
    if not photo_bytes:
        return "Gagal download foto. Coba kirim ulang ya."

    budget_status = db.get_budget_status(cycle["id"])
    try:
        result = ai_engine.scan_receipt(photo_bytes, budget_status)
    except Exception as e:
        print(f"[scan_receipt error] {e}")
        return "Maaf, gagal proses foto. Coba lagi ya 🙏"

    items = result.get("items", [])
    if not items:
        return result.get("reply", "Tidak bisa extract item dari struk ini.")

    receipt_date = result.get("date") or date.today().strftime("%Y-%m-%d")
    for item in items:
        item["expense_date"] = receipt_date

    saved_reply = handle_expense(items, cycle, user_name)
    merchant = result.get("merchant", "")
    header = f"🧾 Struk *{merchant}* berhasil di-scan!\n\n" if merchant else "🧾 Struk berhasil di-scan!\n\n"
    return header + saved_reply
