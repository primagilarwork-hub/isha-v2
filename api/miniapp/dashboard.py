from api.miniapp._base import MiniAppBaseHandler
from lib import config, db
from lib.constants import BUDGET_ALERT_CRITICAL, BUDGET_ALERT_WARNING
from datetime import date


class handler(MiniAppBaseHandler):
    def do_GET(self):
        user = self._auth()
        if not user:
            return

        cycle = config.get_current_cycle()
        budget_status = db.get_budget_status(cycle["id"])
        active_budgets = config.get_active_budgets(cycle["id"])
        today_summary = db.get_daily_summary(date.today().strftime("%Y-%m-%d"))

        total_budget = sum(g["amount"] for g in active_budgets)
        total_spent = sum(budget_status.values())
        pct = int(total_spent / total_budget * 100) if total_budget > 0 else 0

        budgets_summary = []
        for g in active_budgets:
            spent = budget_status.get(g["name"], 0)
            budgeted = g["amount"]
            g_pct = int(spent / budgeted * 100) if budgeted > 0 else 0
            status = "danger" if g_pct >= BUDGET_ALERT_CRITICAL else "warning" if g_pct >= BUDGET_ALERT_WARNING else "ok"
            budgets_summary.append({
                "name": g["name"],
                "amount": budgeted,
                "spent": spent,
                "remaining": budgeted - spent,
                "percentage": g_pct,
                "status": status,
                "categories": g["categories"],
                "is_custom": g.get("is_custom", False),
                "is_overridden": g.get("is_overridden", False),
            })

        self._send({
            "data": {
                "cycle": {
                    "id": cycle["id"],
                    "start": cycle["start"].strftime("%Y-%m-%d"),
                    "end": cycle["end"].strftime("%Y-%m-%d"),
                    "days_remaining": cycle["days_remaining"],
                    "label": f"{cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b %Y')}",
                },
                "summary": {
                    "total_budget": total_budget,
                    "total_spent": total_spent,
                    "total_remaining": total_budget - total_spent,
                    "percentage": pct,
                },
                "budgets": budgets_summary,
                "today": {
                    "total": today_summary["total"],
                    "count": today_summary["count"],
                },
            }
        })
