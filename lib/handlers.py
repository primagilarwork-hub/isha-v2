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
    groups = config.get_budget_groups()
    budget_status = db.get_budget_status(cycle_id)
    for g in groups:
        if g["name"] == budget_group:
            spent = budget_status.get(budget_group, 0)
            override = db.get_budget_override(cycle_id, budget_group)
            budgeted = override if override else g["amount"]
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
        # Pertahankan user_name dari record asli di Supabase
        if not updated.get("user_name"):
            updated["user_name"] = e.get("user_name", "")
        sheets_sync.sync_delete(e["id"])
        sheets_sync.sync_expense(updated)
    except Exception:
        pass

    # Compose reply
    old_amount = float(e["amount"])
    new_amt = updates.get("amount", old_amount)
    desc = updates.get("new_description", e.get("description", ""))
    return f"✏️ Diupdate!\n*{e['description']}* → Rp {new_amt:,.0f}\n_(sebelumnya Rp {old_amount:,.0f})_"


def handle_delete(data: dict, cycle: dict) -> str:
    search = data.get("search", "")
    recent = db.get_recent_expenses(10)

    matches = [
        e for e in recent
        if search.lower() in (e.get("description") or "").lower()
        or search.lower() in (e.get("category") or "").lower()
    ]

    if not matches:
        return f"Tidak ketemu pengeluaran dengan kata kunci '{search}'."

    if len(matches) == 1:
        e = matches[0]
        db.delete_expense(e["id"])
        try:
            sheets_sync.sync_delete(e["id"])
        except Exception:
            pass
        return f"🗑️ Dihapus: *{e['description']}* — Rp {float(e['amount']):,.0f} ({e['expense_date']})"

    lines = [f"Ada {len(matches)} pengeluaran yang cocok, yang mana?\n"]
    for i, e in enumerate(matches[:5], 1):
        lines.append(f"{i}. {e['description']} — Rp {float(e['amount']):,.0f} ({e['expense_date']})")
    lines.append("\nBalas dengan nomor yang mau dihapus.")
    return "\n".join(lines)


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
            reply = handle_expense(items, cycle, user_name)
        elif intent == "CHECK_BUDGET":
            reply = handle_check_budget(data, cycle)
        elif intent == "REPORT":
            reply = handle_report(data, cycle)
        elif intent == "DELETE_EXPENSE":
            reply = handle_delete(data, cycle)
        elif intent == "EDIT_EXPENSE":
            reply = handle_edit(data, cycle)
        elif intent == "RECORD_INCOME":
            reply = handle_income(data, cycle)
    except Exception as e:
        print(f"[handler error] intent={intent} error={e}")
        return "Maaf, ada error saat proses permintaanmu. Coba lagi ya 🙏"

    if advice:
        reply += f"\n\n💡 {advice}"

    return reply


def handle_sync_sheets(cycle: dict) -> str:
    """Full sync Sheets dari Supabase."""
    try:
        expenses = db.get_expenses(cycle["id"])
        budget_status = db.get_budget_status(cycle["id"])
        sheets_sync.full_sync(cycle["id"], expenses)
        sheets_sync.update_dashboard(budget_status)
        return f"✅ Sync selesai! {len(expenses)} pengeluaran cycle ini sudah disinkronkan ke Sheets."
    except Exception as e:
        print(f"[sync_sheets error] {e}")
        return "❌ Sync gagal. Coba lagi ya."


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

    lines = [f"📋 *SYSTEM REVIEW — Cycle {cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b %Y')}*\n"]

    total = summary["total"]
    total_budget = sum(g["amount"] for g in groups)
    surplus = total_budget - total
    saving_rate = int(surplus / total_budget * 100) if total_budget > 0 else 0

    lines.append(f"📊 *RINGKASAN CYCLE*")
    lines.append(f"Total pengeluaran: Rp {total:,.0f} / {total_budget:,.0f}")
    lines.append(f"Surplus: Rp {surplus:,.0f} | Saving rate: {saving_rate}%\n")

    lines.append("💰 *STATUS PER BUDGET*")
    for g in groups:
        spent = summary["by_group"].get(g["name"], 0)
        pct = int(spent / g["amount"] * 100) if g["amount"] > 0 else 0
        if pct >= 90:
            icon = "🔴"
        elif pct >= 70:
            icon = "⚠️"
        else:
            icon = "✅"
        lines.append(f"{icon} {g['name']}: Rp {spent:,.0f} / {g['amount']:,.0f} ({pct}%)")

    lines.append("\nSemangat cycle baru! 🚀")
    return "\n".join(lines)
