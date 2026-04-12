"""Main message router — entry point untuk semua pesan Telegram."""
from lib import config, db, ai_engine
from lib.handlers.expense import handle_expense, handle_edit, handle_delete, confirm_delete
from lib.handlers.budget import (
    handle_check_budget, handle_view_budgets, handle_edit_budget,
    handle_add_category, handle_remove_category, handle_create_budget_group,
    handle_remove_budget_group, handle_reset_budget, handle_apply_budget,
)
from lib.handlers.report import handle_report, generate_system_review
from lib.handlers.income import handle_income
from lib.handlers.setup import handle_setup_budget_help, handle_unknown_category
from lib.handlers.sync import handle_sync_sheets


def handle_message(message: dict) -> str:
    text = message.get("text", "")
    user_name = message.get("from", {}).get("first_name", "")
    chat_id = str(message.get("chat", {}).get("id", ""))

    if not text:
        return "Maaf, aku belum bisa proses pesan ini. Coba kirim teks ya."

    # ── Telegram commands ──────────────────────────────────
    if text.startswith("/"):
        if text.startswith("/start"):
            return (
                "Halo! Aku Isha, financial advisor keluarga kamu 👋\n\n"
                "Cukup chat natural aja, misalnya:\n"
                "• _makan siang 25rb_\n"
                "• _berapa sisa budget makan?_\n"
                "• _rangkum pengeluaran hari ini_"
            )
        if text.startswith("/budget"):
            cycle = config.get_current_cycle()
            return handle_check_budget({}, cycle)
        return "Aku tidak pakai command. Cukup chat natural aja ya 😊"

    # ── Shortcuts (no AI needed) ───────────────────────────
    text_lower = text.lower()

    if any(kw in text_lower for kw in ["sync sheets", "sinkron sheets", "sync spreadsheet"]):
        return handle_sync_sheets(config.get_current_cycle())

    if any(kw in text_lower for kw in ["review cycle", "review bulan", "ringkasan cycle", "system review"]):
        cycle = config.get_current_cycle()
        return generate_system_review(cycle["id"])

    if text_lower.startswith("apply"):
        return handle_apply_budget(text, chat_id)

    # ── Pending action (konfirmasi) ────────────────────────
    if chat_id:
        pending = db.get_pending_action(chat_id)
        if pending:
            result = _handle_pending(pending, text, text_lower, chat_id, user_name)
            if result is not None:
                return result

    # ── AI routing ─────────────────────────────────────────
    cycle = config.get_current_cycle()
    budget_status = db.get_budget_status(cycle["id"])
    recent = db.get_recent_expenses(5)

    try:
        parsed = ai_engine.parse_message(text, budget_status, recent)
    except Exception as e:
        print(f"[ai_engine error] {e}")
        return "Maaf, aku lagi gangguan koneksi ke AI. Coba lagi dalam beberapa detik ya 🙏"

    intent = parsed.get("intent", "GENERAL_CHAT")
    data = parsed.get("data", {})
    reply = parsed.get("reply", "")
    advice = parsed.get("advice")

    try:
        reply = _route_intent(intent, data, cycle, chat_id, user_name, reply)
    except Exception as e:
        print(f"[handler error] intent={intent} error={e}")
        return "Maaf, ada error saat proses permintaanmu. Coba lagi ya 🙏"

    if advice:
        reply += f"\n\n💡 {advice}"
    return reply


def _handle_pending(pending: dict, text: str, text_lower: str, chat_id: str, user_name: str) -> str | None:
    """Handle pending action responses. Returns None kalau tidak ada match."""
    action_type = pending["action_type"]

    if text_lower in ["ya", "yes", "iya", "ok", "hapus"]:
        if action_type == "delete":
            return confirm_delete(pending["action_data"]["expense_id"], chat_id)
        elif action_type == "remove_category":
            d = pending["action_data"]
            db.remove_category_override(d["cycle_id"], d["group"], d["category"])
            db.clear_pending_action(chat_id)
            return f"✅ Kategori *{d['category']}* dihapus dari *{d['group']}*."

    elif text_lower == "ya hapus":
        if action_type == "remove_budget_group":
            d = pending["action_data"]
            if d.get("is_custom"):
                db.deactivate_custom_group(d["cycle_id"], d["group"])
            else:
                db.save_budget_override(d["cycle_id"], d["group"], 0, 0, "removed")
            db.clear_pending_action(chat_id)
            return f"✅ Budget *{d['group']}* dihapus."

    elif text_lower == "ya reset":
        if action_type == "reset_all_budget":
            db.delete_budget_override(pending["action_data"]["cycle_id"])
            db.clear_pending_action(chat_id)
            return "✅ Semua budget dikembalikan ke nilai default YAML."

    elif text_lower in ["batal", "cancel", "tidak", "nggak", "gak"]:
        db.clear_pending_action(chat_id)
        return "Oke, dibatalkan 👍"

    elif action_type == "unknown_category" and text.strip().isdigit():
        d = pending["action_data"]
        idx = int(text.strip()) - 1
        suggestions = d.get("suggestions", [])
        if 0 <= idx < len(suggestions):
            s = suggestions[idx]
            db.add_category_override(d["cycle_id"], s["group"], s["category"])
            db.save_category_mapping(d["description"].lower(), s["group"], s["category"])
            db.clear_pending_action(chat_id)
            cycle = config.get_current_cycle()
            items = [{"amount": d["amount"], "category": s["category"], "description": d["description"]}]
            saved = handle_expense(items, cycle, user_name)
            return (f"✅ Kategori *{s['category']}* dibuat di *{s['group']}*.\n{saved}\n\n"
                    f"💡 Lain kali *{d['description']}* otomatis masuk ke {s['group']} > {s['category']}.")
        else:
            db.clear_pending_action(chat_id)
            cycle = config.get_current_cycle()
            items = [{"amount": d["amount"], "category": "misc", "description": d["description"]}]
            return handle_expense(items, cycle, user_name)

    return None


def _route_intent(intent: str, data: dict, cycle: dict, chat_id: str, user_name: str, default_reply: str) -> str:
    """Route parsed intent ke handler yang tepat."""
    if intent == "RECORD_EXPENSE":
        items = data.get("items", [])
        for item in items:
            cat = item.get("category", "misc")
            found = config.find_category_by_keyword(cat, cycle["id"])
            if not found and cat not in config.get_all_categories():
                return handle_unknown_category(item.get("description", cat), item.get("amount", 0), cycle, chat_id)
        return handle_expense(items, cycle, user_name)
    elif intent == "CHECK_BUDGET":
        return handle_check_budget(data, cycle)
    elif intent == "REPORT":
        return handle_report(data, cycle)
    elif intent == "DELETE_EXPENSE":
        return handle_delete(data, cycle, chat_id)
    elif intent == "EDIT_EXPENSE":
        return handle_edit(data, cycle)
    elif intent == "RECORD_INCOME":
        return handle_income(data, cycle)
    elif intent == "VIEW_BUDGETS":
        return handle_view_budgets(cycle)
    elif intent == "EDIT_BUDGET":
        return handle_edit_budget(data, cycle, chat_id)
    elif intent == "ADD_CATEGORY":
        return handle_add_category(data, cycle)
    elif intent == "REMOVE_CATEGORY":
        return handle_remove_category(data, cycle, chat_id)
    elif intent == "CREATE_BUDGET_GROUP":
        return handle_create_budget_group(data, cycle, chat_id)
    elif intent == "REMOVE_BUDGET_GROUP":
        return handle_remove_budget_group(data, cycle, chat_id)
    elif intent == "RESET_BUDGET":
        return handle_reset_budget(data, cycle, chat_id)
    elif intent == "SETUP_BUDGET_HELP":
        return handle_setup_budget_help(data, cycle, chat_id)
    return default_reply
