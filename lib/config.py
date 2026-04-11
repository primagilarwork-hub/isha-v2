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

# ── Active budgets (T-709) — merged YAML + overrides + custom ──
def get_active_budgets(cycle_id: str = None) -> list:
    """
    Return budget gabungan dari:
    1. budget.yaml (base)
    2. budget_overrides (amount changes)
    3. custom_budget_groups (new groups)
    4. category_overrides (add/remove categories)
    """
    # Import di sini untuk avoid circular import
    from lib import db as _db

    if not cycle_id:
        cycle_id = get_current_cycle()["id"]

    base_groups = get_budget_groups()
    overrides = {o["budget_group"]: float(o["override_amount"]) for o in _db.get_budget_overrides(cycle_id)}
    cat_overrides = _db.get_category_overrides(cycle_id)
    custom_groups = _db.get_custom_groups(cycle_id)

    # Build added/removed categories per group
    added = {}
    removed = {}
    for co in cat_overrides:
        g = co["budget_group"]
        if co["action"] == "add":
            added.setdefault(g, []).append(co["category_name"])
        else:
            removed.setdefault(g, []).append(co["category_name"])

    result = []
    for g in base_groups:
        cats = list(g["categories"])
        # Apply add/remove
        for c in added.get(g["name"], []):
            if c not in cats:
                cats.append(c)
        cats = [c for c in cats if c not in removed.get(g["name"], [])]

        result.append({
            "name": g["name"],
            "amount": overrides.get(g["name"], g["amount"]),
            "categories": cats,
            "is_custom": False,
            "is_overridden": g["name"] in overrides,
        })

    # Tambah custom groups
    for cg in custom_groups:
        result.append({
            "name": cg["name"],
            "amount": float(cg["amount"]),
            "categories": cg["categories"] if isinstance(cg["categories"], list) else [],
            "is_custom": True,
            "is_overridden": False,
        })

    return result


def get_budget_for_category_active(category: str, cycle_id: str = None) -> dict:
    """
    T-708: Cek kategori dengan urutan:
    1. category_overrides (kalau di-remove, return Lain-lain)
    2. custom_budget_groups
    3. budget.yaml (default)
    """
    if not cycle_id:
        cycle_id = get_current_cycle()["id"]

    active = get_active_budgets(cycle_id)
    for g in active:
        if category in g["categories"]:
            return {"group_name": g["name"], "amount": g["amount"]}
    return {"group_name": "Lain-lain", "amount": 1000000}


def find_category_by_keyword(keyword: str, cycle_id: str = None) -> dict | None:
    """
    T-710: Cari kategori berdasarkan keyword.
    1. Exact match di active categories
    2. category_mappings (learned)
    3. Fuzzy match (substring)
    4. Return None kalau tidak ketemu
    """
    from lib import db as _db

    if not cycle_id:
        cycle_id = get_current_cycle()["id"]

    kw = keyword.lower().strip()
    active = get_active_budgets(cycle_id)

    # 1. Exact match
    for g in active:
        if kw in [c.lower() for c in g["categories"]]:
            return {"group_name": g["name"], "category": kw}

    # 2. Learned mapping
    mapping = _db.get_category_mapping(kw)
    if mapping:
        return {"group_name": mapping["budget_group"], "category": mapping["category"]}

    # 3. Fuzzy match (keyword ada di nama kategori atau sebaliknya)
    for g in active:
        for cat in g["categories"]:
            if kw in cat.lower() or cat.lower() in kw:
                return {"group_name": g["name"], "category": cat}

    return None
