from supabase import create_client, Client
from lib.config import SUPABASE_URL, SUPABASE_KEY

_supabase_client: Client | None = None

def _client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client

# ── Expenses ───────────────────────────────────────────────
def add_expense(data: dict) -> dict:
    res = _client().table("expenses").insert(data).execute()
    return res.data[0] if res.data else {}

def delete_expense(expense_id: int) -> bool:
    res = _client().table("expenses").delete().eq("id", expense_id).execute()
    return bool(res.data)

def edit_expense(expense_id: int, data: dict) -> bool:
    res = _client().table("expenses").update(data).eq("id", expense_id).execute()
    return bool(res.data)

def get_recent_expenses(limit: int = 5) -> list:
    res = (
        _client().table("expenses")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []

def get_expenses(cycle_id: str, filters: dict = None) -> list:
    q = _client().table("expenses").select("*").eq("cycle_id", cycle_id)
    if filters:
        for k, v in filters.items():
            q = q.eq(k, v)
    res = q.order("expense_date", desc=True).execute()
    return res.data or []

def get_budget_status(cycle_id: str) -> dict:
    """Return total spent per budget_group untuk cycle ini."""
    res = (
        _client().table("expenses")
        .select("budget_group, amount")
        .eq("cycle_id", cycle_id)
        .execute()
    )
    rows = res.data or []
    totals: dict[str, float] = {}
    for row in rows:
        g = row["budget_group"]
        totals[g] = totals.get(g, 0.0) + float(row["amount"])
    return totals

def get_daily_summary(expense_date: str) -> dict:
    res = (
        _client().table("expenses")
        .select("amount, category, budget_group, description")
        .eq("expense_date", expense_date)
        .execute()
    )
    rows = res.data or []
    total = sum(float(r["amount"]) for r in rows)
    return {"total": total, "count": len(rows), "items": rows}

def get_cycle_summary(cycle_id: str) -> dict:
    rows = get_expenses(cycle_id)
    total = sum(float(r["amount"]) for r in rows)
    by_group = {}
    for r in rows:
        g = r["budget_group"]
        by_group[g] = by_group.get(g, 0) + float(r["amount"])
    return {"cycle_id": cycle_id, "total": total, "by_group": by_group, "items": rows}

# ── Income ─────────────────────────────────────────────────
def add_income(data: dict) -> dict:
    res = _client().table("income").insert(data).execute()
    return res.data[0] if res.data else {}

# ── Budget overrides ───────────────────────────────────────
def get_budget_override(cycle_id: str, budget_group: str) -> float | None:
    res = (
        _client().table("budget_overrides")
        .select("override_amount")
        .eq("cycle_id", cycle_id)
        .eq("budget_group", budget_group)
        .limit(1)
        .execute()
    )
    if res.data:
        return float(res.data[0]["override_amount"])
    return None

def save_budget_override(cycle_id: str, budget_group: str, original: float, override: float, reason: str = "") -> bool:
    # Hapus override lama untuk group ini dulu (upsert manual)
    _client().table("budget_overrides").delete().eq("cycle_id", cycle_id).eq("budget_group", budget_group).execute()
    res = _client().table("budget_overrides").insert({
        "cycle_id": cycle_id,
        "budget_group": budget_group,
        "original_amount": original,
        "override_amount": override,
        "reason": reason,
    }).execute()
    return bool(res.data)


# ── Pending actions (untuk konfirmasi hapus/edit) ──────────
def save_pending_action(chat_id: str, action_type: str, action_data: dict) -> bool:
    # Upsert: hapus lama + insert baru dalam satu operasi logis
    try:
        _client().table("pending_actions").delete().eq("chat_id", chat_id).execute()
        res = _client().table("pending_actions").insert({
            "chat_id": chat_id,
            "action_type": action_type,
            "action_data": action_data,
        }).execute()
        return bool(res.data)
    except Exception as e:
        print(f"[db] save_pending_action error: {e}")
        return False

def get_pending_action(chat_id: str) -> dict | None:
    # Hapus yang sudah lebih dari 5 menit
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    _client().table("pending_actions").delete().lt("created_at", cutoff).execute()

    res = (
        _client().table("pending_actions")
        .select("*")
        .eq("chat_id", chat_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None

def clear_pending_action(chat_id: str) -> None:
    _client().table("pending_actions").delete().eq("chat_id", chat_id).execute()

# ── Category overrides (T-704) ─────────────────────────────
def add_category_override(cycle_id: str, budget_group: str, category_name: str) -> bool:
    res = _client().table("category_overrides").insert({
        "cycle_id": cycle_id,
        "budget_group": budget_group,
        "action": "add",
        "category_name": category_name,
    }).execute()
    return bool(res.data)

def remove_category_override(cycle_id: str, budget_group: str, category_name: str) -> bool:
    res = _client().table("category_overrides").insert({
        "cycle_id": cycle_id,
        "budget_group": budget_group,
        "action": "remove",
        "category_name": category_name,
    }).execute()
    return bool(res.data)

def get_category_overrides(cycle_id: str) -> list:
    res = (
        _client().table("category_overrides")
        .select("*")
        .eq("cycle_id", cycle_id)
        .execute()
    )
    return res.data or []

# ── Custom budget groups (T-705) ───────────────────────────
def create_custom_group(cycle_id: str, name: str, amount: float, categories: list) -> bool:
    res = _client().table("custom_budget_groups").insert({
        "cycle_id": cycle_id,
        "name": name,
        "amount": amount,
        "categories": categories,
        "is_active": True,
    }).execute()
    return bool(res.data)

def get_custom_groups(cycle_id: str) -> list:
    res = (
        _client().table("custom_budget_groups")
        .select("*")
        .eq("cycle_id", cycle_id)
        .eq("is_active", True)
        .execute()
    )
    return res.data or []

def deactivate_custom_group(cycle_id: str, name: str) -> bool:
    res = (
        _client().table("custom_budget_groups")
        .update({"is_active": False})
        .eq("cycle_id", cycle_id)
        .eq("name", name)
        .execute()
    )
    return bool(res.data)

# ── Category mappings (T-706) ──────────────────────────────
def save_category_mapping(keyword: str, budget_group: str, category: str) -> bool:
    # Upsert berdasarkan keyword
    res = _client().table("category_mappings").upsert({
        "keyword": keyword.lower(),
        "budget_group": budget_group,
        "category": category,
    }, on_conflict="keyword").execute()
    return bool(res.data)

def get_category_mapping(keyword: str) -> dict | None:
    res = (
        _client().table("category_mappings")
        .select("*")
        .eq("keyword", keyword.lower())
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None

def get_all_mappings() -> list:
    res = _client().table("category_mappings").select("*").execute()
    return res.data or []

# ── Analytics helpers (T-707) ──────────────────────────────
def get_average_spending_by_group(num_cycles: int = 2) -> dict:
    """Ambil rata-rata pengeluaran per group dari N cycle terakhir."""
    from lib.config import get_current_cycle
    from datetime import date, timedelta
    cycle = get_current_cycle()

    # Kumpulkan cycle IDs sebelumnya
    cycle_ids = []
    ref_date = cycle["start"] - timedelta(days=1)
    for _ in range(num_cycles):
        from lib.config import _CONFIG
        start_day = _CONFIG["cycle"]["start_day"]
        if ref_date.day >= start_day:
            c_start = ref_date.replace(day=start_day)
        else:
            first = ref_date.replace(day=1)
            prev = first - timedelta(days=1)
            c_start = prev.replace(day=start_day)
        cycle_ids.append(c_start.strftime("%Y-%m-%d"))
        ref_date = c_start - timedelta(days=1)

    if not cycle_ids:
        return {}

    all_totals = {}
    for cid in cycle_ids:
        summary = get_cycle_summary(cid)
        for group, total in summary["by_group"].items():
            all_totals.setdefault(group, []).append(total)

    return {g: sum(v) / len(v) for g, v in all_totals.items()}

def count_expenses_by_category(cycle_id: str, category: str) -> int:
    res = (
        _client().table("expenses")
        .select("id", count="exact")
        .eq("cycle_id", cycle_id)
        .eq("category", category)
        .execute()
    )
    return res.count or 0

def delete_budget_override(cycle_id: str, budget_group: str | None = None) -> bool:
    q = _client().table("budget_overrides").delete().eq("cycle_id", cycle_id)
    if budget_group:
        q = q.eq("budget_group", budget_group)
    res = q.execute()
    return True

def get_budget_overrides(cycle_id: str) -> list:
    res = (
        _client().table("budget_overrides")
        .select("*")
        .eq("cycle_id", cycle_id)
        .execute()
    )
    return res.data or []
