"""Income handler."""
from datetime import date
from lib import db


def handle_income(data: dict, cycle: dict) -> str:
    amount = float(data.get("amount", 0))
    if amount <= 0:
        return "Jumlah pemasukan tidak valid."
    source = data.get("source", "lainnya")
    income_date = data.get("income_date") or date.today().strftime("%Y-%m-%d")
    db.add_income({"amount": amount, "source": source, "income_date": income_date, "cycle_id": cycle["id"]})
    return f"💰 Pemasukan tercatat!\n*{source}* — Rp {amount:,.0f}"
