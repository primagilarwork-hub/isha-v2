"""Setup budget help and unknown category handlers."""
from lib import config, db


def handle_setup_budget_help(data: dict, cycle: dict, chat_id: str = "") -> str:
    step = data.get("step", "start")
    income = data.get("income")
    if step == "start" or not income:
        if chat_id:
            db.save_pending_action(chat_id, "setup_budget", {"step": "ask_income"})
        return "Tentu! Berapa pemasukan bulanan kamu? (contoh: _10 juta_ atau _8500000_)"
    return "Oke, aku bantu setup budget. Ketik *setup budget* untuk mulai dari awal."


def handle_unknown_category(description: str, amount: float, cycle: dict, chat_id: str = "") -> str:
    active = config.get_active_budgets(cycle["id"])
    suggestions = []
    kw_map = {
        "netflix": ("Tagihan", "langganan"),
        "spotify": ("Tagihan", "langganan"),
        "youtube": ("Tagihan", "langganan"),
        "grab": ("Transport", "ojol"),
        "gojek": ("Transport", "ojol"),
        "tokopedia": ("Lain-lain", "belanja-online"),
        "shopee": ("Lain-lain", "belanja-online"),
    }
    desc_lower = description.lower()
    for kw, (group, cat) in kw_map.items():
        if kw in desc_lower:
            suggestions.append((group, f"kategori baru '{cat}'", cat))
            break
    if not suggestions:
        suggestions = [
            ("Tagihan", "kategori baru 'langganan'", "langganan"),
            ("Lain-lain", "kategori baru 'misc'", "misc"),
        ]
    if chat_id:
        db.save_pending_action(chat_id, "unknown_category", {
            "description": description,
            "amount": amount,
            "suggestions": [{"group": s[0], "label": s[1], "category": s[2]} for s in suggestions],
            "cycle_id": cycle["id"],
        })
    lines = [f"🤔 *{description}* belum ada di kategori manapun.\n"]
    lines.append("Saran aku, masukkan ke:")
    for i, (group, label, cat) in enumerate(suggestions[:3], 1):
        lines.append(f"{i}. {group} > {label}")
    lines.append(f"{len(suggestions)+1}. Lain-lain (default)")
    lines.append("\nBalas dengan nomor pilihanmu.")
    return "\n".join(lines)
