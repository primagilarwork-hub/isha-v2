import os
import json
import gspread
from google.oauth2.service_account import Credentials
from lib.config import get_budget_groups, get_current_cycle, get_all_categories

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "")
_CREDS_JSON = os.environ.get("GOOGLE_SHEETS_CREDS", "")

TAB_EXPENSES = "Pengeluaran"
TAB_DASHBOARD = "Dashboard"
TAB_REKAP = "Rekap Bulanan"
TAB_CONFIG = "Config"


def _client():
    if not _CREDS_JSON:
        raise ValueError("GOOGLE_SHEETS_CREDS not set")
    creds_dict = json.loads(_CREDS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_sheet(tab_name: str):
    gc = _client()
    sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        return sh.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=tab_name, rows=1000, cols=20)


def setup_spreadsheet():
    """Inisialisasi 4 tab dengan header. Jalankan sekali saat setup."""
    gc = _client()
    sh = gc.open_by_key(SPREADSHEET_ID)

    # Tab 1: Pengeluaran
    try:
        ws = sh.worksheet(TAB_EXPENSES)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=TAB_EXPENSES, rows=1000, cols=10)
    ws.update("A1:I1", [["ID", "Tanggal", "Kategori", "Budget Group", "Deskripsi", "Jumlah", "Dicatat Oleh", "Cycle", "Dibuat"]])

    # Tab 2: Dashboard
    try:
        sh.worksheet(TAB_DASHBOARD)
    except gspread.WorksheetNotFound:
        ws2 = sh.add_worksheet(title=TAB_DASHBOARD, rows=50, cols=7)
        ws2.update("A1:F1", [["Budget Group", "Budget", "Terpakai", "Sisa", "%", "Status"]])

    # Tab 3: Rekap Bulanan
    try:
        sh.worksheet(TAB_REKAP)
    except gspread.WorksheetNotFound:
        ws3 = sh.add_worksheet(title=TAB_REKAP, rows=50, cols=10)
        ws3.update("A1:A1", [["Budget Group"]])

    # Tab 4: Config
    try:
        ws4 = sh.worksheet(TAB_CONFIG)
    except gspread.WorksheetNotFound:
        ws4 = sh.add_worksheet(title=TAB_CONFIG, rows=50, cols=3)
        ws4.update("A1:C1", [["Budget Group", "Sub-Kategori", "Budget / Cycle"]])
        groups = get_budget_groups()
        rows = []
        for g in groups:
            rows.append([g["name"], ", ".join(g["categories"]), g["amount"]])
        if rows:
            ws4.append_rows(rows)

    return True


def sync_expense(expense: dict) -> bool:
    """Append satu baris expense ke tab Pengeluaran."""
    try:
        ws = _get_sheet(TAB_EXPENSES)
        cycle = get_current_cycle()
        row = [
            expense.get("id", ""),
            expense.get("expense_date", ""),
            expense.get("category", ""),
            expense.get("budget_group", ""),
            expense.get("description", ""),
            expense.get("amount", 0),
            expense.get("user_name", ""),
            f"{cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b %Y')}",
            expense.get("created_at", ""),
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        print(f"[sheets_sync] sync_expense error: {e}")
        return False


def sync_delete(expense_id: int) -> bool:
    """Hapus baris dengan ID tertentu dari tab Pengeluaran."""
    try:
        ws = _get_sheet(TAB_EXPENSES)
        cell = ws.find(str(expense_id), in_column=1)
        if cell:
            ws.delete_rows(cell.row)
        return True
    except Exception as e:
        print(f"[sheets_sync] sync_delete error: {e}")
        return False


def update_dashboard(budget_status: dict) -> bool:
    """Update tab Dashboard dengan status budget cycle aktif."""
    try:
        ws = _get_sheet(TAB_DASHBOARD)
        cycle = get_current_cycle()
        groups = get_budget_groups()

        rows = []
        for g in groups:
            spent = budget_status.get(g["name"], 0)
            budgeted = g["amount"]
            remaining = budgeted - spent
            pct = int(spent / budgeted * 100) if budgeted > 0 else 0
            if pct >= 90:
                status = "🔴"
            elif pct >= 70:
                status = "⚠️"
            else:
                status = "✅"
            rows.append([g["name"], budgeted, spent, remaining, f"{pct}%", status])

        # Clear dan tulis ulang (skip header row 1)
        ws.batch_clear(["A2:F50"])
        if rows:
            ws.update(f"A2:F{1+len(rows)}", rows)
        return True
    except Exception as e:
        print(f"[sheets_sync] update_dashboard error: {e}")
        return False
