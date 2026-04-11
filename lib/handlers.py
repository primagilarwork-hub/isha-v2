from datetime import date, timedelta
from lib import config, db, ai_engine, telegram, sheets_sync


def _format_budget_reply(budget_status: dict, cycle: dict) -> str:
    groups = config.get_budget_groups()
    lines = [f"📊 *Budget Cycle {cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b')}*\n"]
    for g in groups:
        spent = budget_status.get(g["name"], 0)
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
    active = config.get_active_budgets(cycle_id)
    budget_status = db.get_budget_status(cycle_id)
    for g in active:
        if g["name"] == budget_group:
            spent = budget_status.get(budget_group, 0)
            budgeted = g["amount"]
            pct = int(spent / budgeted * 100) if budgeted > 0 else 0
            remaining = budgeted - spent
            if pct >= 90:
                return f"🔴 *Budget {budget_group} hampir habis!* ({pct}% terpakai, sisa Rp {remaining:,.0f})"
            elif pct >= 70:
                return f"⚠️ *Budget {budget_group}* sudah {pct}% terpakai (sisa Rp {remaining:,.0f})"
    return None


def handle_expense(items: list, cycle: dict, user_name: str = "") -> str:
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
            "user_name": user_name,
        }
        saved_record = db.add_expense(record)
        record["id"] = saved_record.get("id", "")
        record["user_name"] = user_name
        record["created_at"] = saved_record.get("created_at", "")
        saved.append(record)

        # Sync ke Sheets (best effort)
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


def handle_edit(data: dict, cycle: dict) -> str:
    search = data.get("search", "")
    recent = db.get_recent_expenses(10)

    matches = [
        e for e in recent
        if search.lower() in (e.get("description") or "").lower()
        or search.lower() in (e.get("category") or "").lower()
    ]

    if not matches:
        return f"Tidak ketemu pengeluaran dengan kata kunci '{search}'."

    if len(matches) > 1:
        lines = [f"Ada {len(matches)} pengeluaran yang cocok, yang mana?\n"]
        for i, e in enumerate(matches[:5], 1):
            lines.append(f"{i}. {e['description']} — Rp {float(e['amount']):,.0f} ({e['expense_date']})")
        lines.append("\nBalas dengan nomor yang mau diedit.")
        return "\n".join(lines)

    e = matches[0]
    updates = {}

    new_amount = data.get("new_amount")
    if new_amount:
        updates["amount"] = float(new_amount)

    new_description = data.get("new_description")
    if new_description:
        updates["description"] = new_description

    new_category = data.get("new_category")
    if new_category:
        budget_info = config.get_budget_for_category(new_category)
        updates["category"] = new_category
        updates["budget_group"] = budget_info["group_name"]

    if not updates:
        return "Tidak ada yang diubah. Sebutkan yang mau diedit, misalnya 'edit bakso jadi 20rb'."

    db.edit_expense(e["id"], updates)

    # Sync ke Sheets — hapus baris lama, append yang baru
    try:
        updated = {**e, **updates}
        if not updated.get("user_name"):
            updated["user_name"] = e.get("user_name", "")
        # Coba sync_delete dengan ID sebagai string dan int
        sheets_sync.sync_delete(e["id"])
        sheets_sync.sync_expense(updated)
    except Exception as ex:
        print(f"[handle_edit sheets sync error] {ex}")
        # Fallback: full sync
        try:
            cycle_summary = db.get_expenses(cycle["id"])
            sheets_sync.full_sync(cycle["id"], cycle_summary)
        except Exception:
            pass

    # Compose reply
    old_amount = float(e["amount"])
    new_amt = updates.get("amount", old_amount)
    desc = updates.get("new_description", e.get("description", ""))
    return f"✏️ Diupdate!\n*{e['description']}* → Rp {new_amt:,.0f}\n_(sebelumnya Rp {old_amount:,.0f})_"


def handle_delete(data: dict, cycle: dict, chat_id: str = "") -> str:
    search = data.get("search", "")
    recent = db.get_recent_expenses(10)

    matches = [
        e for e in recent
        if search.lower() in (e.get("description") or "").lower()
        or search.lower() in (e.get("category") or "").lower()
    ]

    if not matches:
        return f"Tidak ketemu pengeluaran dengan kata kunci '{search}'."

    if len(matches) > 1:
        lines = [f"Ada {len(matches)} pengeluaran yang cocok, yang mana?\n"]
        for i, e in enumerate(matches[:5], 1):
            lines.append(f"{i}. {e['description']} — Rp {float(e['amount']):,.0f} ({e['expense_date']})")
        lines.append("\nBalas dengan nomor yang mau dihapus.")
        return "\n".join(lines)

    e = matches[0]

    # Simpan pending delete, minta konfirmasi
    if chat_id:
        db.save_pending_action(chat_id, "delete", {"expense_id": e["id"]})

    return (
        f"🗑️ Yakin mau hapus ini?\n"
        f"*{e['description']}* — Rp {float(e['amount']):,.0f} ({e['expense_date']})\n\n"
        f"Balas *ya* untuk hapus, *batal* untuk cancel."
    )


def confirm_delete(expense_id: int, chat_id: str) -> str:
    """Eksekusi hapus setelah user konfirmasi."""
    recent = db.get_recent_expenses(20)
    e = next((x for x in recent if x["id"] == expense_id), None)

    db.delete_expense(expense_id)
    db.clear_pending_action(chat_id)

    try:
        sheets_sync.sync_delete(expense_id)
    except Exception:
        pass

    if e:
        return f"✅ Dihapus: *{e['description']}* — Rp {float(e['amount']):,.0f}"
    return "✅ Pengeluaran berhasil dihapus."


def handle_receipt(message: dict, cycle: dict, user_name: str = "") -> str:
    """Handle foto struk dari user."""
    from lib import telegram as tg

    # Ambil foto resolusi tertinggi (last item = highest res)
    photos = message.get("photo", [])
    if not photos:
        return "Tidak ada foto yang diterima."

    file_id = photos[-1]["file_id"]
    photo_bytes = tg.get_file(file_id)
    if not photo_bytes:
        return "Gagal download foto. Coba kirim ulang ya."

    budget_status = db.get_budget_status(cycle["id"])

    try:
        result = ai_engine.scan_receipt(photo_bytes, budget_status)
    except Exception as e:
        print(f"[scan_receipt error] {e}")
        return "Maaf, gagal proses foto. Coba lagi ya 🙏"

    items = result.get("items", [])
    if not items:
        return result.get("reply", "Tidak bisa extract item dari struk ini.")

    # Set tanggal dari struk kalau ada, fallback ke hari ini
    receipt_date = result.get("date") or date.today().strftime("%Y-%m-%d")
    for item in items:
        item["expense_date"] = receipt_date

    # Catat semua items
    saved_reply = handle_expense(items, cycle, user_name)

    merchant = result.get("merchant", "")
    header = f"🧾 Struk *{merchant}* berhasil di-scan!\n\n" if merchant else "🧾 Struk berhasil di-scan!\n\n"
    return header + saved_reply


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
    user_name = message.get("from", {}).get("first_name", "")
    chat_id = str(message.get("chat", {}).get("id", ""))

    if not text:
        return "Maaf, aku belum bisa proses pesan ini. Coba kirim teks ya."

    # Ignore command Telegram (/start, /help, dll)
    if text.startswith("/"):
        if text.startswith("/start"):
            return "Halo! Aku Isha, financial advisor keluarga kamu 👋\n\nCukup chat natural aja, misalnya:\n• _makan siang 25rb_\n• _berapa sisa budget makan?_\n• _rangkum pengeluaran hari ini_"
        if text.startswith("/budget"):
            cycle = config.get_current_cycle()
            return handle_check_budget({}, cycle)
        return "Aku tidak pakai command. Cukup chat natural aja ya 😊"

    # Shortcut: sync sheets
    if any(kw in text.lower() for kw in ["sync sheets", "sinkron sheets", "sync spreadsheet"]):
        cycle = config.get_current_cycle()
        return handle_sync_sheets(cycle)

    # Shortcut: system review
    if any(kw in text.lower() for kw in ["review cycle", "review bulan", "ringkasan cycle", "system review"]):
        cycle = config.get_current_cycle()
        return generate_system_review(cycle["id"])

    # Shortcut: apply budget dari review
    if text.lower().startswith("apply"):
        return handle_apply_budget(text, chat_id)

    # Cek pending action
    if chat_id:
        pending = db.get_pending_action(chat_id)
        if pending:
            if text.lower() in ["ya", "yes", "iya", "ok", "hapus"]:
                if pending["action_type"] == "delete":
                    return confirm_delete(pending["action_data"]["expense_id"], chat_id)
                elif pending["action_type"] == "remove_category":
                    d = pending["action_data"]
                    db.remove_category_override(d["cycle_id"], d["group"], d["category"])
                    db.clear_pending_action(chat_id)
                    return f"✅ Kategori *{d['category']}* dihapus dari *{d['group']}*."
            elif text.lower() in ["ya hapus"]:
                if pending["action_type"] == "remove_budget_group":
                    d = pending["action_data"]
                    if d.get("is_custom"):
                        db.deactivate_custom_group(d["cycle_id"], d["group"])
                    else:
                        db.save_budget_override(d["cycle_id"], d["group"], 0, 0, "removed")
                    db.clear_pending_action(chat_id)
                    return f"✅ Budget *{d['group']}* dihapus."
            elif text.lower() in ["ya reset"]:
                if pending["action_type"] == "reset_all_budget":
                    db.delete_budget_override(pending["action_data"]["cycle_id"])
                    db.clear_pending_action(chat_id)
                    return "✅ Semua budget dikembalikan ke nilai default YAML."
            elif text.lower() in ["batal", "cancel", "tidak", "nggak", "gak"]:
                db.clear_pending_action(chat_id)
                return "Oke, dibatalkan 👍"
            # Handle pilihan unknown category (1/2/3)
            elif pending["action_type"] == "unknown_category" and text.strip().isdigit():
                d = pending["action_data"]
                idx = int(text.strip()) - 1
                suggestions = d.get("suggestions", [])
                if 0 <= idx < len(suggestions):
                    s = suggestions[idx]
                    # Tambah kategori ke group
                    db.add_category_override(d["cycle_id"], s["group"], s["category"])
                    # Simpan mapping untuk next time
                    db.save_category_mapping(d["description"].lower(), s["group"], s["category"])
                    db.clear_pending_action(chat_id)
                    # Catat expense
                    cycle = config.get_current_cycle()
                    items = [{"amount": d["amount"], "category": s["category"], "description": d["description"]}]
                    saved = handle_expense(items, cycle, user_name)
                    return f"✅ Kategori *{s['category']}* dibuat di *{s['group']}*.\n{saved}\n\n💡 Lain kali *{d['description']}* otomatis masuk ke {s['group']} > {s['category']}."
                else:
                    # Pilih Lain-lain
                    db.clear_pending_action(chat_id)
                    cycle = config.get_current_cycle()
                    items = [{"amount": d["amount"], "category": "misc", "description": d["description"]}]
                    return handle_expense(items, cycle, user_name)

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
        if intent == "RECORD_EXPENSE":
            items = data.get("items", [])
            # T-722: Cek unknown category
            for item in items:
                cat = item.get("category", "misc")
                found = config.find_category_by_keyword(cat, cycle["id"])
                if not found and cat not in config.get_all_categories():
                    return handle_unknown_category(item.get("description", cat), item.get("amount", 0), cycle, chat_id)
            reply = handle_expense(items, cycle, user_name)
        elif intent == "CHECK_BUDGET":
            reply = handle_check_budget(data, cycle)
        elif intent == "REPORT":
            reply = handle_report(data, cycle)
        elif intent == "DELETE_EXPENSE":
            reply = handle_delete(data, cycle, chat_id)
        elif intent == "EDIT_EXPENSE":
            reply = handle_edit(data, cycle)
        elif intent == "RECORD_INCOME":
            reply = handle_income(data, cycle)
        elif intent == "VIEW_BUDGETS":
            reply = handle_view_budgets(cycle)
        elif intent == "EDIT_BUDGET":
            reply = handle_edit_budget(data, cycle, chat_id)
        elif intent == "ADD_CATEGORY":
            reply = handle_add_category(data, cycle)
        elif intent == "REMOVE_CATEGORY":
            reply = handle_remove_category(data, cycle, chat_id)
        elif intent == "CREATE_BUDGET_GROUP":
            reply = handle_create_budget_group(data, cycle, chat_id)
        elif intent == "REMOVE_BUDGET_GROUP":
            reply = handle_remove_budget_group(data, cycle, chat_id)
        elif intent == "RESET_BUDGET":
            reply = handle_reset_budget(data, cycle, chat_id)
        elif intent == "SETUP_BUDGET_HELP":
            reply = handle_setup_budget_help(data, cycle, chat_id)
    except Exception as e:
        print(f"[handler error] intent={intent} error={e}")
        return "Maaf, ada error saat proses permintaanmu. Coba lagi ya 🙏"

    if advice:
        reply += f"\n\n💡 {advice}"

    return reply


def handle_apply_budget(text: str, chat_id: str) -> str:
    """Apply saran budget dari System Review."""
    # Ambil saran yang tersimpan
    pending = db.get_pending_action("review_suggestions")
    if not pending or pending["action_type"] != "budget_suggestions":
        return "Tidak ada saran budget aktif. Ketik *review cycle* dulu ya."

    suggestions = pending["action_data"]["suggestions"]
    cycle_id = pending["action_data"]["cycle_id"]

    # Parse nomor yang mau di-apply: "apply 1 2" atau "apply 1 dan 2" atau "apply semua"
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
            db.save_budget_override(
                cycle_id=cycle_id,
                budget_group=s["group"],
                original=s["current"],
                override=s["suggested"],
                reason=s["reason"],
            )
            arrow = "⬆️" if s["suggested"] > s["current"] else "⬇️"
            applied.append(f"{arrow} *{s['group']}*: Rp {s['current']:,.0f} → Rp {s['suggested']:,.0f}")

    if not applied:
        return "Nomor saran tidak ditemukan. Cek lagi nomor yang tersedia di System Review."

    lines = ["✅ *Budget berhasil diupdate!*\n"] + applied
    lines.append("\nBerlaku mulai cycle berikutnya 🚀")
    return "\n".join(lines)


def handle_sync_sheets(cycle: dict) -> str:
    """Full sync Sheets dari Supabase."""
    try:
        expenses = db.get_expenses(cycle["id"])
        budget_status = db.get_budget_status(cycle["id"])
        sheets_sync.full_sync(cycle["id"], expenses)
        sheets_sync.update_dashboard(budget_status, cycle["id"])
        return f"✅ Sync selesai! {len(expenses)} pengeluaran cycle ini sudah disinkronkan ke Sheets."
    except Exception as e:
        print(f"[sync_sheets error] {e}")
        return "❌ Sync gagal. Coba lagi ya."


def generate_new_cycle_message() -> str:
    """Pesan sambutan cycle baru, dikirim di hari pertama cycle."""
    cycle = config.get_current_cycle()
    groups = config.get_budget_groups()

    # Hitung cycle sebelumnya
    from datetime import timedelta
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

    # Rekap cycle lalu kalau ada data
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

    # Budget cycle ini (cek override)
    lines.append(f"💰 *Budget cycle ini:*")
    has_override = False
    for g in groups:
        override = db.get_budget_override(cycle["id"], g["name"])
        budgeted = override if override else g["amount"]
        if override:
            has_override = True
            lines.append(f"• {g['name']}: Rp {budgeted:,.0f} _(diupdate)_")
        else:
            lines.append(f"• {g['name']}: Rp {budgeted:,.0f}")

    lines.append(f"\nTotal budget: Rp {total_budget:,.0f}")
    lines.append("\nSemangat! Catat pengeluaran pertama cycle ini ya 💪")
    return "\n".join(lines)


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
        if pct >= 80:
            lines.append(f"⚠️ Budget *{g['name']}* sudah {pct}% terpakai")

    if cycle["days_remaining"] <= 3:
        lines.append(f"\n📅 Cycle hampir selesai! Sisa {cycle['days_remaining']} hari.")

    return "\n".join(lines)


def generate_weekly_summary() -> str:
    today = date.today()
    # Minggu lalu: Senin - Minggu
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)

    cycle = config.get_current_cycle()
    expenses = db.get_expenses(cycle["id"])

    # Filter ke minggu lalu
    weekly = [
        e for e in expenses
        if last_monday.strftime("%Y-%m-%d") <= e["expense_date"] <= last_sunday.strftime("%Y-%m-%d")
    ]

    if not weekly:
        return f"📅 *Ringkasan Minggu Lalu* ({last_monday.strftime('%d %b')} - {last_sunday.strftime('%d %b')})\n\nTidak ada pengeluaran minggu lalu."

    total = sum(float(e["amount"]) for e in weekly)
    by_group = {}
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
    suggestions = []  # [(group_name, current, suggested, reason)]

    for g in groups:
        spent = summary["by_group"].get(g["name"], 0)
        pct = int(spent / g["amount"] * 100) if g["amount"] > 0 else 0
        remaining = g["amount"] - spent
        if pct >= 90:
            icon = "🔴"
            # Saran naik 10-20%
            suggested = round(g["amount"] * 1.15 / 50000) * 50000
            suggestions.append((g["name"], g["amount"], suggested, f"over {pct}% terpakai"))
        elif pct < 50 and spent > 0:
            icon = "✅"
            # Saran turun
            suggested = round(spent * 1.2 / 50000) * 50000
            if suggested < g["amount"]:
                suggestions.append((g["name"], g["amount"], suggested, f"selalu sisa Rp {remaining:,.0f}"))
        elif pct >= 70:
            icon = "⚠️"
        else:
            icon = "✅"
        lines.append(f"{icon} {g['name']}: Rp {spent:,.0f} / {g['amount']:,.0f} ({pct}%)")

    # Saran rebalancing dengan nomor
    if suggestions:
        lines.append("\n🔄 *SARAN BUDGET CYCLE BERIKUTNYA*")
        for i, (name, current, suggested, reason) in enumerate(suggestions, 1):
            arrow = "⬆️" if suggested > current else "⬇️"
            lines.append(f"{i}. {arrow} *{name}*: Rp {current:,.0f} → Rp {suggested:,.0f} _{reason}_")

        lines.append(f"\nKetik *apply [nomor]* untuk terapkan, contoh: _apply 1_ atau _apply 1 2_")

        # Simpan saran ke pending action (pakai chat_id kosong = global)
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


# ── Budget Management Handlers (T-713~725) ─────────────────

def check_total_budget_vs_income(cycle_id: str, active_budgets: list = None) -> dict:
    """T-723: Cek total budget vs income."""
    if active_budgets is None:
        active_budgets = config.get_active_budgets(cycle_id)
    total_budget = sum(g["amount"] for g in active_budgets)
    income = config._CONFIG.get("income", {}).get("monthly", 0)
    over = total_budget - income
    return {
        "total_budget": total_budget,
        "income": income,
        "over_amount": over,
        "is_over": over > 0,
    }


def suggest_budget_reallocation(cycle_id: str, need_amount: float) -> str:
    """T-724: Saran realokasi budget berdasarkan pola pengeluaran."""
    avg = db.get_average_spending_by_group(num_cycles=2)
    active = config.get_active_budgets(cycle_id)
    suggestions = []

    for g in active:
        avg_spent = avg.get(g["name"], g["amount"])
        slack = g["amount"] - avg_spent
        if slack > 50000:  # Ada sisa minimal 50rb
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


def handle_view_budgets(cycle: dict) -> str:
    """T-713: Tampilkan semua budget aktif."""
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
    """T-714: Edit amount single budget."""
    group_name = data.get("group", "")
    new_amount = float(data.get("new_amount", 0))

    if not group_name or new_amount <= 0:
        return "Sebutkan nama budget dan jumlah barunya, contoh: _ubah budget makan jadi 3.5jt_"

    # Cari group yang cocok (fuzzy)
    active = config.get_active_budgets(cycle["id"])
    matched = next((g for g in active if group_name.lower() in g["name"].lower()), None)
    if not matched:
        return f"Budget group '{group_name}' tidak ditemukan."

    old_amount = matched["amount"]
    db.save_budget_override(cycle["id"], matched["name"], old_amount, new_amount, "manual edit")

    # Update dashboard di Sheets
    try:
        budget_status = db.get_budget_status(cycle["id"])
        sheets_sync.update_dashboard(budget_status, cycle["id"])
    except Exception:
        pass

    # Cek total vs income
    check = check_total_budget_vs_income(cycle["id"])
    new_total = check["total_budget"] - old_amount + new_amount
    income = check["income"]

    reply = f"✅ *{matched['name']}* diubah: Rp {old_amount:,.0f} → Rp {new_amount:,.0f}"
    if new_total > income:
        over = new_total - income
        reply += f"\n\n⚠️ Total budget sekarang Rp {new_total:,.0f} — over Rp {over:,.0f} dari income.\nMau kurangi budget lain?"
    return reply


def handle_add_category(data: dict, cycle: dict) -> str:
    """T-715: Tambah kategori ke group existing."""
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
    """T-716: Hapus kategori dari group."""
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

    # Cek expense history
    count = db.count_expenses_by_category(cycle["id"], cat_name)
    warning = f"⚠️ Kategori *{cat_name}* punya *{count} expense* di cycle ini." if count > 0 else ""

    if chat_id:
        db.save_pending_action(chat_id, "remove_category", {
            "cycle_id": cycle["id"],
            "group": matched_group["name"],
            "category": cat_name,
        })

    lines = []
    if warning:
        lines.append(warning)
        lines.append("Kalau dihapus, expense lama tetap ada di history.\n")
    lines.append(f"Yakin hapus kategori *{cat_name}* dari *{matched_group['name']}*?")
    lines.append("Balas *ya* untuk hapus, *batal* untuk cancel.")
    return "\n".join(lines)


def handle_create_budget_group(data: dict, cycle: dict, chat_id: str = "") -> str:
    """T-717: Bikin budget group baru."""
    name = data.get("name", "").strip()
    amount = float(data.get("amount", 0))
    categories = data.get("categories", [])

    if not name or amount <= 0:
        return "Sebutkan nama budget dan jumlahnya, contoh: _bikin budget Kebutuhan Anak 1.5jt_"

    # Cek duplikat
    active = config.get_active_budgets(cycle["id"])
    if any(g["name"].lower() == name.lower() for g in active):
        return f"Budget group '{name}' sudah ada."

    db.create_custom_group(cycle["id"], name, amount, categories)

    # Cek total vs income
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
    """T-718: Hapus budget group."""
    group_name = data.get("group", "")
    active = config.get_active_budgets(cycle["id"])
    matched = next((g for g in active if group_name.lower() in g["name"].lower()), None)

    if not matched:
        return f"Budget group '{group_name}' tidak ditemukan."

    spent = db.get_budget_status(cycle["id"]).get(matched["name"], 0)

    if chat_id:
        db.save_pending_action(chat_id, "remove_budget_group", {
            "cycle_id": cycle["id"],
            "group": matched["name"],
            "is_custom": matched.get("is_custom", False),
        })

    lines = [f"⚠️ Budget *{matched['name']}* akan dihapus."]
    if spent > 0:
        lines.append(f"Ada Rp {spent:,.0f} terpakai di cycle ini.")
    lines.append("Expense history tetap ada.\n")
    lines.append("Ketik *ya hapus* untuk konfirmasi.")
    return "\n".join(lines)


def handle_reset_budget(data: dict, cycle: dict, chat_id: str = "") -> str:
    """T-719: Reset budget ke YAML default."""
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

    # Reset single group
    active = config.get_active_budgets(cycle["id"])
    matched = next((g for g in active if group.lower() in g["name"].lower()), None)
    if not matched:
        return f"Budget group '{group}' tidak ditemukan."

    if not matched.get("is_overridden"):
        return f"Budget *{matched['name']}* sudah di nilai default."

    # Ambil original amount dari YAML
    yaml_groups = config.get_budget_groups()
    yaml_group = next((g for g in yaml_groups if g["name"] == matched["name"]), None)
    original = yaml_group["amount"] if yaml_group else matched["amount"]

    db.delete_budget_override(cycle["id"], matched["name"])
    return f"✅ *{matched['name']}* dikembalikan ke default: Rp {original:,.0f}\n_(Dari override Rp {matched['amount']:,.0f})_"


def handle_setup_budget_help(data: dict, cycle: dict, chat_id: str = "") -> str:
    """T-720: Multi-step guided budget setup."""
    step = data.get("step", "start")
    income = data.get("income")

    if step == "start" or not income:
        if chat_id:
            db.save_pending_action(chat_id, "setup_budget", {"step": "ask_income"})
        return "Tentu! Berapa pemasukan bulanan kamu? (contoh: _10 juta_ atau _8500000_)"

    return "Oke, aku bantu setup budget. Ketik *setup budget* untuk mulai dari awal."


def handle_unknown_category(description: str, amount: float, cycle: dict, chat_id: str = "") -> str:
    """T-721: Handle expense dengan kategori unknown."""
    active = config.get_active_budgets(cycle["id"])

    # Saran: masuk ke group mana
    suggestions = []
    # Cek keyword umum
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
        # Default suggestions
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
