from api.miniapp._base import MiniAppBaseHandler
from lib import config, db
from lib.constants import DEFAULT_PAGE_SIZE
from datetime import date


class handler(MiniAppBaseHandler):
    def do_GET(self):
        user = self._auth()
        if not user:
            return
        from urllib.parse import urlparse, parse_qs
        params = parse_qs(urlparse(self.path).query)
        limit = int(params.get("limit", [DEFAULT_PAGE_SIZE])[0])
        offset = int(params.get("offset", [0])[0])
        cycle = config.get_current_cycle()
        expenses = db.get_expenses(cycle["id"])
        # Sort by date desc, id desc
        expenses = sorted(expenses, key=lambda e: (e.get("expense_date", ""), e.get("id", 0)), reverse=True)
        total = len(expenses)
        page = expenses[offset:offset + limit]
        self._send({
            "data": {
                "items": page,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
            }
        })

    def do_POST(self):
        user = self._auth()
        if not user:
            return
        body = self._body()
        amount = float(body.get("amount", 0))
        if amount <= 0:
            self._send({"error": {"code": "VALIDATION_ERROR", "message": "Amount harus lebih dari 0"}}, 400)
            return
        category = body.get("category", "misc")
        budget_info = config.get_budget_for_category(category)
        cycle = config.get_current_cycle()
        record = {
            "amount": amount,
            "category": category,
            "budget_group": budget_info["group_name"],
            "description": body.get("description", ""),
            "expense_date": body.get("expense_date") or date.today().strftime("%Y-%m-%d"),
            "cycle_id": cycle["id"],
            "user_name": user.get("first_name", ""),
        }
        saved = db.add_expense(record)
        record["id"] = saved.get("id")
        record["created_at"] = saved.get("created_at")
        try:
            from lib import sheets_sync
            sheets_sync.sync_expense(record)
        except Exception:
            pass
        self._send({"data": {"expense": record}}, 201)

    def do_PUT(self):
        user = self._auth()
        if not user:
            return
        # Extract ID from path: /api/miniapp/expenses/123
        parts = self.path.split("/")
        expense_id = int(parts[-1]) if parts[-1].isdigit() else None
        if not expense_id:
            self._send({"error": {"code": "NOT_FOUND", "message": "Expense ID required"}}, 404)
            return
        body = self._body()
        updates = {}
        if "amount" in body:
            updates["amount"] = float(body["amount"])
        if "description" in body:
            updates["description"] = body["description"]
        if "category" in body:
            budget_info = config.get_budget_for_category(body["category"])
            updates["category"] = body["category"]
            updates["budget_group"] = budget_info["group_name"]
        if not updates:
            self._send({"error": {"code": "VALIDATION_ERROR", "message": "Tidak ada field yang diupdate"}}, 400)
            return
        db.edit_expense(expense_id, updates)
        self._send({"data": {"updated": True}})

    def do_DELETE(self):
        user = self._auth()
        if not user:
            return
        parts = self.path.split("/")
        expense_id = int(parts[-1]) if parts[-1].isdigit() else None
        if not expense_id:
            self._send({"error": {"code": "NOT_FOUND", "message": "Expense ID required"}}, 404)
            return
        db.delete_expense(expense_id)
        try:
            from lib import sheets_sync
            sheets_sync.sync_delete(expense_id)
        except Exception:
            pass
        self._send({"data": {"deleted": True}})
