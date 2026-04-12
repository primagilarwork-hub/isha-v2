from api.miniapp._base import MiniAppBaseHandler
from lib import config, db


class handler(MiniAppBaseHandler):
    def do_GET(self):
        user = self._auth()
        if not user:
            return
        cycle = config.get_current_cycle()
        active = config.get_active_budgets(cycle["id"])
        budget_status = db.get_budget_status(cycle["id"])
        income = config._CONFIG.get("income", {}).get("monthly", 0)
        total = sum(g["amount"] for g in active)
        budgets = []
        for g in active:
            spent = budget_status.get(g["name"], 0)
            budgets.append({
                "name": g["name"],
                "amount": g["amount"],
                "spent": spent,
                "remaining": g["amount"] - spent,
                "percentage": int(spent / g["amount"] * 100) if g["amount"] > 0 else 0,
                "categories": g["categories"],
                "is_custom": g.get("is_custom", False),
                "is_overridden": g.get("is_overridden", False),
            })
        self._send({"data": {"budgets": budgets, "income": income, "total_allocated": total}})

    def do_POST(self):
        user = self._auth()
        if not user:
            return
        body = self._body()
        name = body.get("name", "").strip()
        amount = float(body.get("amount", 0))
        categories = body.get("categories", [])
        if not name or amount <= 0:
            self._send({"error": {"code": "VALIDATION_ERROR", "message": "Name dan amount wajib diisi"}}, 400)
            return
        cycle = config.get_current_cycle()
        db.create_custom_group(cycle["id"], name, amount, categories)
        self._send({"data": {"created": True, "name": name}}, 201)

    def do_PUT(self):
        user = self._auth()
        if not user:
            return
        parts = self.path.split("/")
        group = parts[-1] if parts[-1] else None
        if not group:
            self._send({"error": {"code": "NOT_FOUND", "message": "Budget group required"}}, 404)
            return
        body = self._body()
        new_amount = float(body.get("amount", 0))
        if new_amount <= 0:
            self._send({"error": {"code": "VALIDATION_ERROR", "message": "Amount harus lebih dari 0"}}, 400)
            return
        cycle = config.get_current_cycle()
        active = config.get_active_budgets(cycle["id"])
        matched = next((g for g in active if g["name"].lower() == group.lower()), None)
        if not matched:
            self._send({"error": {"code": "NOT_FOUND", "message": f"Budget group '{group}' tidak ditemukan"}}, 404)
            return
        db.save_budget_override(cycle["id"], matched["name"], matched["amount"], new_amount, "miniapp edit")
        self._send({"data": {"updated": True, "new_amount": new_amount}})

    def do_DELETE(self):
        user = self._auth()
        if not user:
            return
        parts = self.path.split("/")
        group = parts[-1] if parts[-1] else None
        if not group:
            self._send({"error": {"code": "NOT_FOUND", "message": "Budget group required"}}, 404)
            return
        cycle = config.get_current_cycle()
        active = config.get_active_budgets(cycle["id"])
        matched = next((g for g in active if g["name"].lower() == group.lower()), None)
        if not matched:
            self._send({"error": {"code": "NOT_FOUND", "message": f"Budget group '{group}' tidak ditemukan"}}, 404)
            return
        if matched.get("is_custom"):
            db.deactivate_custom_group(cycle["id"], matched["name"])
        else:
            db.save_budget_override(cycle["id"], matched["name"], matched["amount"], 0, "removed")
        self._send({"data": {"deleted": True}})
