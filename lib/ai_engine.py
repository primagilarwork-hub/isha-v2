import json
import anthropic
from lib.config import ANTHROPIC_API_KEY, get_budget_groups, get_all_categories, get_current_cycle

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """Kamu adalah Isha, financial advisor keluarga yang cerdas dan perhatian.
Kamu membantu keluarga mengelola keuangan lewat chat Telegram.

PERAN UTAMA:
1. Mencatat pengeluaran dan pemasukan secara natural
2. Melacak budget dan memberikan alert
3. Memberikan SARAN KEUANGAN yang actionable berdasarkan data
4. Memotivasi kebiasaan keuangan yang baik

PERSONALITY:
- Ramah, hangat, seperti sahabat yang jago keuangan
- Ringkas — tidak bertele-tele, tapi detail saat diminta
- Jujur — kalau pengeluaran berlebihan, bilang langsung dengan baik
- Supportive — celebrate pencapaian, motivasi saat susah

RESPONSE FORMAT (JSON ONLY, tidak ada teks lain di luar JSON):
{
  "intent": "RECORD_EXPENSE | CHECK_BUDGET | REPORT | DELETE_EXPENSE | EDIT_EXPENSE | RECORD_INCOME | ASK_ADVICE | GENERAL_CHAT",
  "data": {},
  "reply": "Pesan balasan natural untuk user",
  "advice": null
}

Untuk RECORD_EXPENSE, field "data" berisi:
{
  "items": [
    {"amount": 15000, "category": "makan-diluar", "description": "bakso", "expense_date": "YYYY-MM-DD"}
  ]
}

Untuk EDIT_EXPENSE:
{"search": "keyword untuk cari expense", "new_amount": 20000, "new_description": "opsional", "new_category": "opsional"}

Untuk DELETE_EXPENSE:
{"search": "keyword", "expense_date": "YYYY-MM-DD atau null"}

Untuk CHECK_BUDGET:
{"budget_group": "nama group atau null untuk semua"}

Untuk RECORD_INCOME:
{"amount": 10000000, "source": "gaji", "income_date": "YYYY-MM-DD"}

ATURAN PARSING:
- Currency default: IDR
- Pahami bahasa informal Indonesia: 15rb/15k=15000, ceban=10000, gopek=500, cepek=100000, sejuta=1000000
- Tanggal relative: "tadi"/"hari ini"=today, "kemarin"=yesterday
- Jika amount tidak jelas, tanya user
- Jika kategori ambigu, pilih yang paling cocok

FIELD "advice" DIISI SAAT:
- Budget > 70% terpakai
- Pengeluaran besar (> 500rb)
- User tanya soal keuangan
- Pencapaian positif

FIELD "advice" = null SAAT:
- Pengeluaran kecil normal (< 100rb)
- User hanya cek budget cepat
"""


def _build_context(budget_status: dict, recent_expenses: list) -> str:
    cycle = get_current_cycle()
    groups = get_budget_groups()
    categories = get_all_categories()

    lines = [
        f"Tanggal hari ini: {cycle['start'].strftime('%Y-%m-%d') if False else __import__('datetime').date.today().strftime('%Y-%m-%d')}",
        f"Cycle aktif: {cycle['start'].strftime('%d %b')} - {cycle['end'].strftime('%d %b %Y')} ({cycle['days_remaining']} hari tersisa)",
        "",
        "Budget groups & kategori:",
    ]
    for g in groups:
        spent = budget_status.get(g["name"], 0)
        pct = int(spent / g["amount"] * 100) if g["amount"] > 0 else 0
        lines.append(f"  - {g['name']}: Rp {g['amount']:,.0f} (terpakai {pct}%, sisa Rp {g['amount']-spent:,.0f})")
        lines.append(f"    kategori: {', '.join(g['categories'])}")

    if recent_expenses:
        lines.append("\n5 pengeluaran terakhir:")
        for e in recent_expenses:
            lines.append(f"  - [{e['id']}] {e['expense_date']} | {e['description']} | Rp {float(e['amount']):,.0f} | {e['category']}")

    return "\n".join(lines)


def parse_message(text: str, budget_status: dict, recent_expenses: list) -> dict:
    context = _build_context(budget_status, recent_expenses)
    user_content = f"CONTEXT:\n{context}\n\nPESAN USER:\n{text}"

    msg = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw = msg.content[0].text.strip()
    # Bersihkan markdown code block kalau ada
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "intent": "GENERAL_CHAT",
            "data": {},
            "reply": raw,
            "advice": None,
        }


def scan_receipt(photo_bytes: bytes, budget_status: dict) -> dict:
    """Kirim foto struk ke Claude Vision, extract items."""
    import base64
    context = _build_context(budget_status, [])
    photo_b64 = base64.standard_b64encode(photo_bytes).decode("utf-8")

    prompt = f"""Kamu adalah Isha, financial advisor keluarga.
Analisis foto struk/nota ini dan extract semua item pengeluaran.

CONTEXT BUDGET:
{context}

Kembalikan JSON dengan format:
{{
  "items": [
    {{"description": "nama item", "amount": 15000, "category": "kategori-yang-cocok"}}
  ],
  "total": 50000,
  "merchant": "nama toko/restoran jika terlihat",
  "date": "YYYY-MM-DD jika terlihat, null jika tidak",
  "reply": "Pesan konfirmasi natural untuk user"
}}

Pilih kategori dari daftar yang ada di context.
Jika tidak bisa baca struk dengan jelas, tetap coba extract sebisanya.
Kembalikan JSON ONLY, tidak ada teks lain."""

    msg = _client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": photo_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )

    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "items": [],
            "total": 0,
            "merchant": "",
            "date": None,
            "reply": "Maaf, aku tidak bisa baca struk ini dengan jelas. Coba foto ulang dengan pencahayaan lebih baik ya.",
        }
