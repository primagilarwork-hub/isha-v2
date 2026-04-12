from api.miniapp._base import MiniAppBaseHandler
from lib import config, db
from urllib.parse import urlparse, parse_qs


class handler(MiniAppBaseHandler):
    def do_GET(self):
        user = self._auth()
        if not user:
            return
        params = parse_qs(urlparse(self.path).query)
        report_type = params.get("type", ["pie"])[0]
        cycle = config.get_current_cycle()
        cycle_id = params.get("cycle_id", [cycle["id"]])[0]

        if report_type == "pie":
            self._send({"data": self._pie(cycle_id)})
        elif report_type == "trend":
            self._send({"data": self._trend(cycle_id)})
        elif report_type == "top":
            limit = int(params.get("limit", [5])[0])
            self._send({"data": self._top_categories(cycle_id, limit)})
        else:
            self._send({"error": {"code": "NOT_FOUND", "message": f"Report type '{report_type}' tidak dikenal"}}, 404)

    def _pie(self, cycle_id: str) -> dict:
        summary = db.get_cycle_summary(cycle_id)
        colors = ["#378ADD", "#1D9E75", "#EF9F27", "#E24B4A", "#8B5CF6", "#6B7280"]
        labels = list(summary["by_group"].keys())
        data = list(summary["by_group"].values())
        return {
            "labels": labels,
            "data": data,
            "colors": colors[:len(labels)],
            "total": summary["total"],
        }

    def _trend(self, cycle_id: str) -> dict:
        expenses = db.get_expenses(cycle_id)
        by_date: dict[str, float] = {}
        for e in expenses:
            d = e["expense_date"]
            by_date[d] = by_date.get(d, 0) + float(e["amount"])
        sorted_dates = sorted(by_date.keys())
        return {
            "dates": sorted_dates,
            "amounts": [by_date[d] for d in sorted_dates],
        }

    def _top_categories(self, cycle_id: str, limit: int) -> dict:
        expenses = db.get_expenses(cycle_id)
        by_cat: dict[str, float] = {}
        for e in expenses:
            c = e["category"]
            by_cat[c] = by_cat.get(c, 0) + float(e["amount"])
        sorted_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:limit]
        return {
            "categories": [{"name": c, "total": t} for c, t in sorted_cats]
        }
