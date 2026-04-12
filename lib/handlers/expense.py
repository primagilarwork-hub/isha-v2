"""Expense handlers — add, edit, delete."""
from datetime import date
from lib import config, db, sheets_sync
from lib.constants import RECENT_EXPENSES_LIMIT
from lib.utils.validators import validate_amount


def check_budget_alert(budget_group: str, cycle_id: str, budget_status: dict = None, active_budgets: list = None) -> str | None:
    """Cek alert budget. Pass budget_status dan active_budgets untuk hindari N+1 query."""
    from lib.constants import BUDGET_ALERT_CRITICAL, BUDGET_ALERT_WARNING
    if active_budgets is None:
        active_budgets = config.get_active_budgets(cycle_id)
    if budget_status is None:
        budget_status = db.get_budget_status(cycle_id)
    for g in active_budgets:
        if g["name"] == budget_group:
            spent = budget_status.get(budget_group, 0)
            budgeted = g["amount"]
            if budgeted <= 0:
                return None
            pct = int(spent / budgeted * 100)
            remaining = budgeted - spent
            if pct >= BUDGET_ALERT_CRITICAL:
                return f"🔴 *Budget {budget_group} hampir habis!* ({pct}% terpakai, sisa Rp {remaining:,.0f})"
            elif pct >= BUDGET_ALERT_WARNING:
                return f"⚠️ *Budget {budget_group}* sudah {pct}% terpakai (sisa Rp {remaining:,.0f})"
    return None


def handle_expense(items: list, cycle: dict, user_name: str = "") -> str:
    if not items:
        return "Maaf, aku tidak bisa parse pengeluarannya. Coba ulangi ya."

    saved = []
    alerts = []
    active_budgets = config.get_active_budgets(cycle["id"])

    for item in items:
        amount = float(item.get("amount", 0))
        valid, err = validate_amount(amount)
        if not valid:
            return err

        category = item.get("category", "misc")
        budget_info = config.get_budget_for_category(category)
        expense_date = item.get("expense_date") or date.today().strftime("%Y-%m-%d")

        record = {
            "amount": amount,
            "category": category,
            "budget_group": budget_info["group_name"],
            "description": item.get("description", ""),
            "expense_date": expense_date,
            "cycle_id": cycle["id"],
            "user_name": user_name,
        }
        saved_record = db.add_expense(record)
        record["id"] = saved_record.get("id", "")
        record["created_at"] = saved_record.get("created_at", "")
        saved.append(record)

        try:
            sheets_sync.sync_expense(record)
        except Exception:
            pass

    if not saved:
        return "Tidak ada pengeluaran yang berhasil dicatat."

    budget_status = db.get_budget_status(cycle["id"])
    seen_groups = set()
    for r in saved:
        g = r["budget_group"]
        if g not in seen_groups:
            seen_groups.add(g)
            alert = check_budget_alert(g, cycle["id"], budget_status, active_budgets)
            if alert:
                alerts.append(alert)

    if len(saved) == 1:
        r = saved[0]
        reply = f"✅ Tercatat!\n*{r['description']}* — Rp {r['amount']:,.0f}\nKategori: {r['category']}"
    else:
        lines = [f"✅ *{len(saved)} pengeluaran tercatat!*"]
        total = sum(r['amount'] for r in saved)
        for r in saved:
            lines.append(f"• {r['description']} — Rp {r['amount']:,.0f}")
        lines.append(f"Total: Rp {total:,.0f}")
        reply = "\n".join(lines)

    if alerts:
        reply += "\n\n" + "\n".join(alerts)
    return reply


def handle_edit(data: dict, cycle: dict) -> str:
    search = data.get("search", "")
    recent = db.get_recent_expenses(RECENT_EXPENSES_LIMIT)
    matches = [
        e for e in recent
        if search.lower() in (e.get("description") or "").lower()
        or search.lower() in (e.get("category") or "").lower()
    ]

    if not matches:
        return f"Tidak ketemu pengeluaran dengan kata kunci '{search}'."

    if len(matches) > 1:
        lines = [f"Ada {len(matches)} pengeluaran yang cocok, yang mana?\n"]
        for i, e in enumerate(matches[:5], 1):
            lines.append(f"{i}. {e['description']} — Rp {float(e['amount']):,.0f} ({e['expense_date']})")
        lines.append("\nBalas dengan nomor yang mau diedit.")
        return "\n".join(lines)

    e = matches[0]
    updates = {}
    if data.get("new_amount"):
        updates["amount"] = float(data["new_amount"])
    if data.get("new_description"):
        updates["description"] = data["new_description"]
    if data.get("new_category"):
        budget_info = config.get_budget_for_category(data["new_category"])
        updates["category"] = data["new_category"]
        updates["budget_group"] = budget_info["group_name"]

    if not updates:
        return "Tidak ada yang diubah. Sebutkan yang mau diedit, misalnya 'edit bakso jadi 20rb'."

    db.edit_expense(e["id"], updates)

    try:
        updated = {**e, **updates}
        if not updated.get("user_name"):
            updated["user_name"] = e.get("user_name", "")
        sheets_sync.sync_delete(e["id"])
        sheets_sync.sync_expense(updated)
    except Exception as ex:
        print(f"[handle_edit sheets sync error] {ex}")
        try:
            sheets_sync.full_sync(cycle["id"], db.get_expenses(cycle["id"]))
        except Exception:
            pass

    old_amount = float(e["amount"])
    new_amt = updates.get("amount", old_amount)
    return f"✏️ Diupdate!\n*{e['description']}* → Rp {new_amt:,.0f}\n_(sebelumnya Rp {old_amount:,.0f})_"


def handle_delete(data: dict, cycle: dict, chat_id: str = "") -> str:
    search = data.get("search", "")
    recent = db.get_recent_expenses(RECENT_EXPENSES_LIMIT)
    matches = [
        e for e in recent
        if search.lower() in (e.get("description") or "").lower()
        or search.lower() in (e.get("category") or "").lower()
    ]

    if not matches:
        return f"Tidak ketemu pengeluaran dengan kata kunci '{search}'."

    if len(matches) > 1:
        lines = [f"Ada {len(matches)} pengeluaran yang cocok, yang mana?\n"]
        for i, e in enumerate(matches[:5], 1):
            lines.append(f"{i}. {e['description']} — Rp {float(e['amount']):,.0f} ({e['expense_date']})")
        lines.append("\nBalas dengan nomor yang mau dihapus.")
        return "\n".join(lines)

    e = matches[0]
    if chat_id:
        db.save_pending_action(chat_id, "delete", {"expense_id": e["id"]})

    return (
        f"🗑️ Yakin mau hapus ini?\n"
        f"*{e['description']}* — Rp {float(e['amount']):,.0f} ({e['expense_date']})\n\n"
        f"Balas *ya* untuk hapus, *batal* untuk cancel."
    )


def confirm_delete(expense_id: int, chat_id: str) -> str:
    recent = db.get_recent_expenses(20)
    e = next((x for x in recent if x["id"] == expense_id), None)
    db.delete_expense(expense_id)
    db.clear_pending_action(chat_id)
    try:
        sheets_sync.sync_delete(expense_id)
    except Exception:
        pass
    if e:
        return f"✅ Dihapus: *{e['description']}* — Rp {float(e['amount']):,.0f}"
    return "✅ Pengeluaran berhasil dihapus."
