"""Budget handlers — view, edit, create, remove."""
from lib import config, db, sheets_sync
from lib.constants import BUDGET_ALERT_CRITICAL, BUDGET_ALERT_WARNING
from lib.handlers.expense import check_budget_alert


def check_total_budget_vs_income(cycle_id: str, active_budgets: list = None) -> dict:
    if active_budgets is None:
        active_budgets = config.get_active_budgets(cycle_id)
    total_budget = sum(g["amount"] for g in active_budgets)
    income = config._CONFIG.get("income", {}).get("monthly", 0)
    over = total_budget - income
    return {"total_budget": total_budget, "income": income, "over_amount": over, "is_over": over > 0}


def suggest_budget_reallocation(cycle_id: str, need_amount: float) -> str:
    avg = db.get_average_spending_by_group(num_cycles=2)
    active = config.get_active_budgets(cycle_id)
    suggestions = []
    for g in active:
        avg_spent = avg.get(g["name"], g["amount"])
        slack = g["amount"] - avg_spent
        if slack > 50000:
            suggestions.append((g["name"], g["amount"], slack))
    suggestions.sort(key=lambda x: x[2], reverse=True)
    if not suggestions:
        return "Tidak ada budget yang bisa dikurangi berdasarkan pola pengeluaran kamu."
    lines = ["Saran berdasarkan pola pengeluaran kamu:"]
    total_slack = 0
    for name, current, slack in suggestions[:3]:
        suggested = round((current - slack * 0.8) / 50000) * 50000
        lines.append(f"• {name} ({current:,.0f}) → {suggested:,.0f} (hemat ~{slack*0.8:,.0f})")
        total_slack += slack * 0.8
    if total_slack >= need_amount:
        lines.append(f"\nTotal bisa dihemat: Rp {total_slack:,.0f} ✅")
    else:
        lines.append(f"\nTotal bisa dihemat: Rp {total_slack:,.0f} (masih kurang Rp {need_amount-total_slack:,.0f})")
    return "\n".join(lines)


def _format_budget_reply(budget_status: dict, cycle: dict) -> str:
    active = config.get_active_budgets(cycle["id"])
    lines = [f"📊 *Budget Cycle {cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b')}*\n"]
    for g in active:
        spent = budget_status.get(g["name"], 0)
        budgeted = g["amount"]
        pct = int(spent / budgeted * 100) if budgeted > 0 else 0
        icon = "🔴" if pct >= BUDGET_ALERT_CRITICAL else "⚠️" if pct >= BUDGET_ALERT_WARNING else "✅"
        tag = " _(diubah)_" if g.get("is_overridden") else ""
        lines.append(f"{icon} *{g['name']}*: Rp {spent:,.0f} / {budgeted:,.0f} ({pct}%){tag}")
    lines.append(f"\n_{cycle['days_remaining']} hari tersisa di cycle ini_")
    return "\n".join(lines)


def handle_check_budget(data: dict, cycle: dict) -> str:
    budget_status = db.get_budget_status(cycle["id"])
    return _format_budget_reply(budget_status, cycle)


def handle_view_budgets(cycle: dict) -> str:
    active = config.get_active_budgets(cycle["id"])
    income = config._CONFIG.get("income", {}).get("monthly", 0)
    total = sum(g["amount"] for g in active)
    lines = [f"💰 *Budget aktif cycle {cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b')}:*\n"]
    for g in active:
        pct = int(g["amount"] / income * 100) if income > 0 else 0
        tag = " _(custom)_" if g.get("is_custom") else ""
        tag += " _(diubah)_" if g.get("is_overridden") else ""
        cats = ", ".join(g["categories"][:4])
        if len(g["categories"]) > 4:
            cats += f" +{len(g['categories'])-4} lagi"
        lines.append(f"• *{g['name']}*: Rp {g['amount']:,.0f} ({pct}%){tag}")
        if g["categories"]:
            lines.append(f"  └ {cats}")
    status = "✅" if total <= income else "⚠️ over income"
    lines.append(f"\nTotal: Rp {total:,.0f} / Rp {income:,.0f} {status}")
    return "\n".join(lines)


def handle_edit_budget(data: dict, cycle: dict, chat_id: str = "") -> str:
    group_name = data.get("group", "")
    new_amount = float(data.get("new_amount", 0))
    if not group_name or new_amount <= 0:
        return "Sebutkan nama budget dan jumlah barunya, contoh: _ubah budget makan jadi 3.5jt_"
    active = config.get_active_budgets(cycle["id"])
    matched = next((g for g in active if group_name.lower() in g["name"].lower()), None)
    if not matched:
        return f"Budget group '{group_name}' tidak ditemukan."
    old_amount = matched["amount"]
    db.save_budget_override(cycle["id"], matched["name"], old_amount, new_amount, "manual edit")
    try:
        budget_status = db.get_budget_status(cycle["id"])
        sheets_sync.update_dashboard(budget_status, cycle["id"])
    except Exception:
        pass
    check = check_total_budget_vs_income(cycle["id"])
    new_total = check["total_budget"] - old_amount + new_amount
    income = check["income"]
    reply = f"✅ *{matched['name']}* diubah: Rp {old_amount:,.0f} → Rp {new_amount:,.0f}"
    if new_total > income:
        over = new_total - income
        reply += f"\n\n⚠️ Total budget sekarang Rp {new_total:,.0f} — over Rp {over:,.0f} dari income.\nMau kurangi budget lain?"
    return reply


def handle_add_category(data: dict, cycle: dict) -> str:
    group_name = data.get("group", "")
    cat_name = data.get("category_name", "").lower().strip()
    if not group_name or not cat_name:
        return "Sebutkan nama group dan kategori, contoh: _tambah kategori langganan ke Tagihan_"
    active = config.get_active_budgets(cycle["id"])
    matched = next((g for g in active if group_name.lower() in g["name"].lower()), None)
    if not matched:
        return f"Budget group '{group_name}' tidak ditemukan."
    if cat_name in [c.lower() for c in matched["categories"]]:
        return f"Kategori '{cat_name}' sudah ada di {matched['name']}."
    db.add_category_override(cycle["id"], matched["name"], cat_name)
    updated_cats = matched["categories"] + [cat_name]
    lines = [f"✅ Kategori *{cat_name}* ditambahkan ke *{matched['name']}*.\n"]
    lines.append(f"Sekarang {matched['name']} punya {len(updated_cats)} kategori:")
    for c in updated_cats:
        marker = " (baru)" if c == cat_name else ""
        lines.append(f"• {c}{marker}")
    return "\n".join(lines)


def handle_remove_category(data: dict, cycle: dict, chat_id: str = "") -> str:
    cat_name = data.get("category_name", "").lower().strip()
    group_name = data.get("group", "")
    if not cat_name:
        return "Sebutkan nama kategori yang mau dihapus."
    active = config.get_active_budgets(cycle["id"])
    matched_group = None
    for g in active:
        if cat_name in [c.lower() for c in g["categories"]]:
            if not group_name or group_name.lower() in g["name"].lower():
                matched_group = g
                break
    if not matched_group:
        return f"Kategori '{cat_name}' tidak ditemukan."
    count = db.count_expenses_by_category(cycle["id"], cat_name)
    if chat_id:
        db.save_pending_action(chat_id, "remove_category", {
            "cycle_id": cycle["id"], "group": matched_group["name"], "category": cat_name,
        })
    lines = []
    if count > 0:
        lines.append(f"⚠️ Kategori *{cat_name}* punya *{count} expense* di cycle ini.")
        lines.append("Kalau dihapus, expense lama tetap ada di history.\n")
    lines.append(f"Yakin hapus kategori *{cat_name}* dari *{matched_group['name']}*?")
    lines.append("Balas *ya* untuk hapus, *batal* untuk cancel.")
    return "\n".join(lines)


def handle_create_budget_group(data: dict, cycle: dict, chat_id: str = "") -> str:
    name = data.get("name", "").strip()
    amount = float(data.get("amount", 0))
    categories = data.get("categories", [])
    if not name or amount <= 0:
        return "Sebutkan nama budget dan jumlahnya, contoh: _bikin budget Kebutuhan Anak 1.5jt_"
    active = config.get_active_budgets(cycle["id"])
    if any(g["name"].lower() == name.lower() for g in active):
        return f"Budget group '{name}' sudah ada."
    db.create_custom_group(cycle["id"], name, amount, categories)
    total_new = sum(g["amount"] for g in active) + amount
    income = config._CONFIG.get("income", {}).get("monthly", 0)
    cats_str = f"\nKategori: {', '.join(categories)}" if categories else ""
    reply = f"✅ Budget *{name}* dibuat dengan Rp {amount:,.0f}{cats_str}"
    if total_new > income:
        over = total_new - income
        reply += f"\n\n⚠️ Total budget jadi Rp {total_new:,.0f} — over Rp {over:,.0f} dari income Rp {income:,.0f}."
        reply += f"\n\n{suggest_budget_reallocation(cycle['id'], over)}"
        reply += "\n\nMau aku bantu alokasi ulang? Atau tetap lanjut?"
    return reply


def handle_remove_budget_group(data: dict, cycle: dict, chat_id: str = "") -> str:
    group_name = data.get("group", "")
    active = config.get_active_budgets(cycle["id"])
    matched = next((g for g in active if group_name.lower() in g["name"].lower()), None)
    if not matched:
        return f"Budget group '{group_name}' tidak ditemukan."
    spent = db.get_budget_status(cycle["id"]).get(matched["name"], 0)
    if chat_id:
        db.save_pending_action(chat_id, "remove_budget_group", {
            "cycle_id": cycle["id"], "group": matched["name"], "is_custom": matched.get("is_custom", False),
        })
    lines = [f"⚠️ Budget *{matched['name']}* akan dihapus."]
    if spent > 0:
        lines.append(f"Ada Rp {spent:,.0f} terpakai di cycle ini.")
    lines.append("Expense history tetap ada.\n")
    lines.append("Ketik *ya hapus* untuk konfirmasi.")
    return "\n".join(lines)


def handle_reset_budget(data: dict, cycle: dict, chat_id: str = "") -> str:
    group = data.get("group", "")
    if group == "all" or "semua" in group.lower():
        overrides = db.get_budget_overrides(cycle["id"])
        if not overrides:
            return "Tidak ada override aktif. Budget sudah sesuai default."
        if chat_id:
            db.save_pending_action(chat_id, "reset_all_budget", {"cycle_id": cycle["id"]})
        lines = ["⚠️ Ini akan kembalikan SEMUA budget ke nilai default YAML."]
        lines.append("Perubahan yang akan di-revert:")
        for o in overrides:
            lines.append(f"• {o['budget_group']}: Rp {float(o['override_amount']):,.0f} → Rp {float(o['original_amount']):,.0f}")
        lines.append("\nKetik *ya reset* untuk konfirmasi.")
        return "\n".join(lines)
    active = config.get_active_budgets(cycle["id"])
    matched = next((g for g in active if group.lower() in g["name"].lower()), None)
    if not matched:
        return f"Budget group '{group}' tidak ditemukan."
    if not matched.get("is_overridden"):
        return f"Budget *{matched['name']}* sudah di nilai default."
    yaml_groups = config.get_budget_groups()
    yaml_group = next((g for g in yaml_groups if g["name"] == matched["name"]), None)
    original = yaml_group["amount"] if yaml_group else matched["amount"]
    db.delete_budget_override(cycle["id"], matched["name"])
    return f"✅ *{matched['name']}* dikembalikan ke default: Rp {original:,.0f}\n_(Dari override Rp {matched['amount']:,.0f})_"


def handle_apply_budget(text: str, chat_id: str) -> str:
    pending = db.get_pending_action("review_suggestions")
    if not pending or pending["action_type"] != "budget_suggestions":
        return "Tidak ada saran budget aktif. Ketik *review cycle* dulu ya."
    suggestions = pending["action_data"]["suggestions"]
    cycle_id = pending["action_data"]["cycle_id"]
    text_lower = text.lower().replace("dan", " ").replace(",", " ")
    if "semua" in text_lower or "all" in text_lower:
        selected = [s["index"] for s in suggestions]
    else:
        import re
        selected = [int(n) for n in re.findall(r'\d+', text_lower)]
    if not selected:
        return "Sebutkan nomor sarannya, contoh: _apply 1_ atau _apply 1 2_ atau _apply semua_"
    applied = []
    for s in suggestions:
        if s["index"] in selected:
            db.save_budget_override(cycle_id=cycle_id, budget_group=s["group"],
                                    original=s["current"], override=s["suggested"], reason=s["reason"])
            arrow = "⬆️" if s["suggested"] > s["current"] else "⬇️"
            applied.append(f"{arrow} *{s['group']}*: Rp {s['current']:,.0f} → Rp {s['suggested']:,.0f}")
    if not applied:
        return "Nomor saran tidak ditemukan. Cek lagi nomor yang tersedia di System Review."
    lines = ["✅ *Budget berhasil diupdate!*\n"] + applied
    lines.append("\nBerlaku mulai cycle berikutnya 🚀")
    return "\n".join(lines)
