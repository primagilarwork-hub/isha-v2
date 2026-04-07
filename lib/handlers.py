from datetime import date
from lib import config, db, ai_engine, telegram, sheets_sync


def _format_budget_reply(budget_status: dict, cycle: dict) -> str:
    groups = config.get_budget_groups()
    lines = [f"📊 *Budget Cycle {cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b')}*\n"]
    for g in groups:
        spent = budget_status.get(g["name"], 0)
        # Cek override
        override = db.get_budget_override(cycle["id"], g["name"])
        budgeted = override if override else g["amount"]
        remaining = budgeted - spent
        pct = int(spent / budgeted * 100) if budgeted > 0 else 0
        if pct >= 90:
            icon = "🔴"
        elif pct >= 70:
            icon = "⚠️"
        else:
            icon = "✅"
        lines.append(f"{icon} *{g['name']}*: Rp {spent:,.0f} / {budgeted:,.0f} ({pct}%)")
    lines.append(f"\n_{cycle['days_remaining']} hari tersisa di cycle ini_")
    return "\n".join(lines)


def check_budget_alert(budget_group: str, cycle_id: str) -> str | None:
    groups = config.get_budget_groups()
    budget_status = db.get_budget_status(cycle_id)
    for g in groups:
        if g["name"] == budget_group:
            spent = budget_status.get(budget_group, 0)
            override = db.get_budget_override(cycle_id, budget_group)
            budgeted = override if override else g["amount"]
            pct = int(spent / budgeted * 100) if budgeted > 0 else 0
            remaining = budgeted - spent
            if pct >= 90:
                return f"🔴 *Budget {budget_group} hampir habis!* ({pct}% terpakai, sisa Rp {remaining:,.0f})"
            elif pct >= 70:
                return f"⚠️ *Budget {budget_group}* sudah {pct}% terpakai (sisa Rp {remaining:,.0f})"
    return None


def handle_expense(items: list, cycle: dict) -> str:
    if not items:
        return "Maaf, aku tidak bisa parse pengeluarannya. Coba ulangi ya."

    saved = []
    alerts = []

    for item in items:
        amount = float(item.get("amount", 0))
        if amount <= 0:
            continue

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
        }
        db.add_expense(record)
        saved.append(record)

        # Sync ke Sheets (best effort, tidak blocking)
        try:
            sheets_sync.sync_expense(record)
        except Exception:
            pass

        alert = check_budget_alert(budget_info["group_name"], cycle["id"])
        if alert and alert not in alerts:
            alerts.append(alert)

    if not saved:
        return "Tidak ada pengeluaran yang berhasil dicatat."

    if len(saved) == 1:
        r = saved[0]
        reply = f"✅ Tercatat!\n*{r['description']}* — Rp {r['amount']:,.0f}\nKategori: {r['category']}"
    else:
        lines = [f"✅ *{len(saved)} pengeluaran tercatat!*"]
        total = 0
        for r in saved:
            lines.append(f"• {r['description']} — Rp {r['amount']:,.0f}")
            total += r['amount']
        lines.append(f"Total: Rp {total:,.0f}")
        reply = "\n".join(lines)

    if alerts:
        reply += "\n\n" + "\n".join(alerts)

    return reply


def handle_check_budget(data: dict, cycle: dict) -> str:
    budget_status = db.get_budget_status(cycle["id"])
    return _format_budget_reply(budget_status, cycle)


def handle_report(data: dict, cycle: dict) -> str:
    period = data.get("period", "today")
    today = date.today().strftime("%Y-%m-%d")

    if period == "today":
        summary = db.get_daily_summary(today)
        if summary["count"] == 0:
            return "Belum ada pengeluaran hari ini."
        lines = [f"📋 *Pengeluaran hari ini* — Total Rp {summary['total']:,.0f}\n"]
        for item in summary["items"]:
            lines.append(f"• {item['description']} ({item['category']}) — Rp {float(item['amount']):,.0f}")
        return "\n".join(lines)

    elif period == "this_cycle":
        summary = db.get_cycle_summary(cycle["id"])
        if not summary["items"]:
            return "Belum ada pengeluaran di cycle ini."
        lines = [f"📊 *Ringkasan Cycle {cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b')}*",
                 f"Total: Rp {summary['total']:,.0f}\n"]
        for group, total in summary["by_group"].items():
            lines.append(f"• {group}: Rp {total:,.0f}")
        return "\n".join(lines)

    return handle_check_budget(data, cycle)


def handle_delete(data: dict, cycle: dict) -> str:
    search = data.get("search", "")
    recent = db.get_recent_expenses(10)

    matches = [
        e for e in recent
        if search.lower() in (e.get("description") or "").lower()
        or search.lower() in (e.get("category") or "").lower()
    ]

    if not matches:
        return f"Tidak ketemu pengeluaran dengan kata kunci '{search}'."

    if len(matches) == 1:
        e = matches[0]
        db.delete_expense(e["id"])
        try:
            sheets_sync.sync_delete(e["id"])
        except Exception:
            pass
        return f"🗑️ Dihapus: *{e['description']}* — Rp {float(e['amount']):,.0f} ({e['expense_date']})"

    lines = [f"Ada {len(matches)} pengeluaran yang cocok, yang mana?\n"]
    for i, e in enumerate(matches[:5], 1):
        lines.append(f"{i}. {e['description']} — Rp {float(e['amount']):,.0f} ({e['expense_date']})")
    lines.append("\nBalas dengan nomor yang mau dihapus.")
    return "\n".join(lines)


def handle_income(data: dict, cycle: dict) -> str:
    amount = float(data.get("amount", 0))
    if amount <= 0:
        return "Jumlah pemasukan tidak valid."
    source = data.get("source", "lainnya")
    income_date = data.get("income_date") or date.today().strftime("%Y-%m-%d")
    db.add_income({
        "amount": amount,
        "source": source,
        "income_date": income_date,
        "cycle_id": cycle["id"],
    })
    return f"💰 Pemasukan tercatat!\n*{source}* — Rp {amount:,.0f}"


def handle_message(message: dict) -> str:
    text = message.get("text", "")
    if not text:
        return "Maaf, aku belum bisa proses pesan ini."

    cycle = config.get_current_cycle()
    budget_status = db.get_budget_status(cycle["id"])
    recent = db.get_recent_expenses(5)

    parsed = ai_engine.parse_message(text, budget_status, recent)
    intent = parsed.get("intent", "GENERAL_CHAT")
    data = parsed.get("data", {})
    reply = parsed.get("reply", "")
    advice = parsed.get("advice")

    if intent == "RECORD_EXPENSE":
        items = data.get("items", [])
        reply = handle_expense(items, cycle)
    elif intent == "CHECK_BUDGET":
        reply = handle_check_budget(data, cycle)
    elif intent == "REPORT":
        reply = handle_report(data, cycle)
    elif intent == "DELETE_EXPENSE":
        reply = handle_delete(data, cycle)
    elif intent == "RECORD_INCOME":
        reply = handle_income(data, cycle)
    # GENERAL_CHAT, ASK_ADVICE, EDIT_EXPENSE → pakai reply dari Claude langsung

    if advice:
        reply += f"\n\n💡 {advice}"

    return reply


def generate_reminder_message() -> str:
    cycle = config.get_current_cycle()
    today = date.today().strftime("%Y-%m-%d")
    summary = db.get_daily_summary(today)
    budget_status = db.get_budget_status(cycle["id"])

    lines = ["🌙 *Reminder Malam*\n"]

    if summary["count"] > 0:
        lines.append(f"Hari ini kamu catat *{summary['count']} pengeluaran*, total Rp {summary['total']:,.0f}")
    else:
        lines.append("Hari ini belum ada pengeluaran yang dicatat. Ada yang ketinggalan?")

    # Budget alerts
    groups = config.get_budget_groups()
    for g in groups:
        spent = budget_status.get(g["name"], 0)
        pct = int(spent / g["amount"] * 100) if g["amount"] > 0 else 0
        if pct >= 80:
            lines.append(f"⚠️ Budget *{g['name']}* sudah {pct}% terpakai")

    if cycle["days_remaining"] <= 3:
        lines.append(f"\n📅 Cycle hampir selesai! Sisa {cycle['days_remaining']} hari.")

    return "\n".join(lines)
