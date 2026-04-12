"""Report handlers — daily, weekly, cycle summaries, system review."""
from datetime import date, timedelta
from lib import config, db
from lib.constants import BUDGET_ALERT_CRITICAL, BUDGET_ALERT_WARNING


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

    from lib.handlers.budget import handle_check_budget
    return handle_check_budget(data, cycle)


def generate_weekly_summary() -> str:
    today = date.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    cycle = config.get_current_cycle()
    expenses = db.get_expenses(cycle["id"])
    weekly = [
        e for e in expenses
        if last_monday.strftime("%Y-%m-%d") <= e["expense_date"] <= last_sunday.strftime("%Y-%m-%d")
    ]
    if not weekly:
        return f"📅 *Ringkasan Minggu Lalu* ({last_monday.strftime('%d %b')} - {last_sunday.strftime('%d %b')})\n\nTidak ada pengeluaran minggu lalu."
    total = sum(float(e["amount"]) for e in weekly)
    by_group: dict[str, float] = {}
    for e in weekly:
        g = e["budget_group"]
        by_group[g] = by_group.get(g, 0) + float(e["amount"])
    lines = [
        f"📅 *Ringkasan Minggu Lalu* ({last_monday.strftime('%d %b')} - {last_sunday.strftime('%d %b')})",
        f"Total: Rp {total:,.0f} ({len(weekly)} transaksi)\n",
    ]
    for group, amt in sorted(by_group.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"• {group}: Rp {amt:,.0f}")
    return "\n".join(lines)


def generate_system_review(cycle_id: str) -> str:
    summary = db.get_cycle_summary(cycle_id)
    cycle = config.get_current_cycle()
    groups = config.get_budget_groups()
    total = summary["total"]
    total_budget = sum(g["amount"] for g in groups)
    surplus = total_budget - total
    saving_rate = int(surplus / total_budget * 100) if total_budget > 0 else 0

    lines = [f"📋 *SYSTEM REVIEW — Cycle {cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b %Y')}*\n"]
    lines.append(f"📊 *RINGKASAN CYCLE*")
    lines.append(f"Total pengeluaran: Rp {total:,.0f} / {total_budget:,.0f}")
    lines.append(f"Surplus: Rp {surplus:,.0f} | Saving rate: {saving_rate}%\n")
    lines.append("💰 *STATUS PER BUDGET*")
    suggestions = []

    for g in groups:
        spent = summary["by_group"].get(g["name"], 0)
        pct = int(spent / g["amount"] * 100) if g["amount"] > 0 else 0
        remaining = g["amount"] - spent
        if pct >= BUDGET_ALERT_CRITICAL:
            icon = "🔴"
            suggested = round(g["amount"] * 1.15 / 50000) * 50000
            suggestions.append((g["name"], g["amount"], suggested, f"over {pct}% terpakai"))
        elif pct < 50 and spent > 0:
            icon = "✅"
            suggested = round(spent * 1.2 / 50000) * 50000
            if suggested < g["amount"]:
                suggestions.append((g["name"], g["amount"], suggested, f"selalu sisa Rp {remaining:,.0f}"))
        elif pct >= BUDGET_ALERT_WARNING:
            icon = "⚠️"
        else:
            icon = "✅"
        lines.append(f"{icon} {g['name']}: Rp {spent:,.0f} / {g['amount']:,.0f} ({pct}%)")

    if suggestions:
        lines.append("\n🔄 *SARAN BUDGET CYCLE BERIKUTNYA*")
        for i, (name, current, suggested, reason) in enumerate(suggestions, 1):
            arrow = "⬆️" if suggested > current else "⬇️"
            lines.append(f"{i}. {arrow} *{name}*: Rp {current:,.0f} → Rp {suggested:,.0f} _{reason}_")
        lines.append(f"\nKetik *apply [nomor]* untuk terapkan, contoh: _apply 1_ atau _apply 1 2_")
        db.save_pending_action("review_suggestions", "budget_suggestions", {
            "suggestions": [
                {"index": i, "group": s[0], "current": s[1], "suggested": s[2], "reason": s[3]}
                for i, s in enumerate(suggestions, 1)
            ],
            "cycle_id": cycle["id"],
        })

    if saving_rate > 0:
        lines.append(f"\n🎯 *PENCAPAIAN*")
        lines.append(f"Saving rate cycle ini: {saving_rate}% 🎉")
        if saving_rate >= 10:
            lines.append("Luar biasa! Konsisten ya di cycle berikutnya 💪")

    lines.append("\nSemangat cycle baru! 🚀")
    return "\n".join(lines)
