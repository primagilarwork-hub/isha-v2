"""Reminder handlers — daily, weekly, new cycle."""
from datetime import date, timedelta
from lib import config, db
from lib.constants import BUDGET_ALERT_REMINDER


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
    groups = config.get_budget_groups()
    for g in groups:
        spent = budget_status.get(g["name"], 0)
        pct = int(spent / g["amount"] * 100) if g["amount"] > 0 else 0
        if pct >= BUDGET_ALERT_REMINDER:
            lines.append(f"⚠️ Budget *{g['name']}* sudah {pct}% terpakai")
    if cycle["days_remaining"] <= 3:
        lines.append(f"\n📅 Cycle hampir selesai! Sisa {cycle['days_remaining']} hari.")
    return "\n".join(lines)


def generate_new_cycle_message() -> str:
    cycle = config.get_current_cycle()
    groups = config.get_budget_groups()
    prev_cycle_end = cycle["start"] - timedelta(days=1)
    prev_cycle_start_day = config._CONFIG["cycle"]["start_day"]
    if prev_cycle_end.day >= prev_cycle_start_day:
        prev_cycle_start = prev_cycle_end.replace(day=prev_cycle_start_day)
    else:
        first = prev_cycle_end.replace(day=1)
        prev_month = first - timedelta(days=1)
        prev_cycle_start = prev_month.replace(day=prev_cycle_start_day)
    prev_cycle_id = prev_cycle_start.strftime("%Y-%m-%d")
    prev_summary = db.get_cycle_summary(prev_cycle_id)
    total_budget = sum(g["amount"] for g in groups)
    lines = [
        f"🗓️ *Cycle baru dimulai!*",
        f"_{cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b %Y')}_\n",
    ]
    if prev_summary["total"] > 0:
        prev_total = prev_summary["total"]
        prev_surplus = total_budget - prev_total
        prev_saving = int(prev_surplus / total_budget * 100) if total_budget > 0 else 0
        lines.append(f"📊 *Rekap cycle lalu:*")
        lines.append(f"Total pengeluaran: Rp {prev_total:,.0f} / {total_budget:,.0f}")
        if prev_surplus > 0:
            lines.append(f"Surplus: Rp {prev_surplus:,.0f} | Saving rate: {prev_saving}% 🎉")
        else:
            lines.append(f"Over budget: Rp {abs(prev_surplus):,.0f} 😅")
        lines.append("")
    lines.append(f"💰 *Budget cycle ini:*")
    for g in groups:
        override = db.get_budget_override(cycle["id"], g["name"])
        budgeted = override if override else g["amount"]
        tag = " _(diupdate)_" if override else ""
        lines.append(f"• {g['name']}: Rp {budgeted:,.0f}{tag}")
    lines.append(f"\nTotal budget: Rp {total_budget:,.0f}")
    lines.append("\nSemangat! Catat pengeluaran pertama cycle ini ya 💪")
    return "\n".join(lines)
