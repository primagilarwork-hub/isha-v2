import os
import yaml
from datetime import date, timedelta

# Load budget.yaml
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_BASE_DIR, "budget.yaml"), "r") as f:
    _CONFIG = yaml.safe_load(f)

# ── Env vars ──────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_IDS = list(filter(None, [
    os.environ.get("TELEGRAM_CHAT_ID", ""),
    os.environ.get("TELEGRAM_CHAT_ID_2", ""),
]))
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
CRON_SECRET = os.environ.get("CRON_SECRET", "")

# ── Budget helpers ─────────────────────────────────────────
def get_budget_groups():
    return _CONFIG.get("budgets", [])

def get_all_categories():
    cats = []
    for group in get_budget_groups():
        cats.extend(group.get("categories", []))
    return cats

def get_budget_for_category(category):
    for group in get_budget_groups():
        if category in group.get("categories", []):
            return {"group_name": group["name"], "amount": group["amount"]}
    return {"group_name": "Lain-lain", "amount": 1000000}

# ── Cycle helpers ──────────────────────────────────────────
def get_current_cycle():
    start_day = _CONFIG["cycle"]["start_day"]
    today = date.today()

    if today.day >= start_day:
        cycle_start = today.replace(day=start_day)
    else:
        # Bulan sebelumnya
        first_of_month = today.replace(day=1)
        prev_month_end = first_of_month - timedelta(days=1)
        cycle_start = prev_month_end.replace(day=start_day)

    # Cycle end = satu hari sebelum start_day bulan berikutnya
    if cycle_start.month == 12:
        next_start = cycle_start.replace(year=cycle_start.year + 1, month=1)
    else:
        next_start = cycle_start.replace(month=cycle_start.month + 1)
    cycle_end = next_start - timedelta(days=1)

    days_remaining = (cycle_end - today).days + 1
    cycle_id = cycle_start.strftime("%Y-%m-%d")

    return {
        "start": cycle_start,
        "end": cycle_end,
        "id": cycle_id,
        "days_remaining": days_remaining,
    }
