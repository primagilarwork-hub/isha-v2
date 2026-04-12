"""Sheets sync handler."""
from lib import db, sheets_sync


def handle_sync_sheets(cycle: dict) -> str:
    try:
        expenses = db.get_expenses(cycle["id"])
        budget_status = db.get_budget_status(cycle["id"])
        result = sheets_sync.full_sync(cycle["id"], expenses)
        sheets_sync.update_dashboard(budget_status, cycle["id"])
        if result:
            return f"✅ Sync selesai! {len(expenses)} pengeluaran cycle ini sudah disinkronkan ke Sheets."
        return "❌ Sync gagal. Cek Vercel logs untuk detail error."
    except Exception as e:
        print(f"[sync_sheets error] {e}")
        return f"❌ Sync gagal: {str(e)}"
