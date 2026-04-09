from supabase import create_client
from lib.config import SUPABASE_URL, SUPABASE_KEY

def _client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

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
    res = (
        _client().table("expenses")
        .select("budget_group, amount")
        .eq("cycle_id", cycle_id)
        .execute()
    )
    rows = res.data or []
    totals = {}
    for row in rows:
        g = row["budget_group"]
        totals[g] = totals.get(g, 0) + float(row["amount"])
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
    # Hapus pending lama untuk chat ini dulu
    _client().table("pending_actions").delete().eq("chat_id", chat_id).execute()
    res = _client().table("pending_actions").insert({
        "chat_id": chat_id,
        "action_type": action_type,
        "action_data": action_data,
    }).execute()
    return bool(res.data)

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
