# Isha v2 — AI Family Financial Advisor

Bot Telegram untuk manajemen keuangan keluarga, ditenagai Claude AI.
Chat natural bahasa Indonesia untuk catat pengeluaran, cek budget, dan lihat laporan.

## Stack
- **Platform**: Vercel Serverless (Hobby, gratis)
- **Database**: Supabase PostgreSQL
- **AI**: Claude Sonnet (Anthropic API)
- **Spreadsheet**: Google Sheets (family view)

## Cara Pakai
Cukup chat natural ke bot:
- `makan siang nasi padang 25rb` → catat pengeluaran
- `tadi bensin 80rb, parkir 5rb` → catat multi-item
- `berapa sisa budget makan?` → cek budget
- `rangkum pengeluaran hari ini` → laporan harian
- `hapus yang bakso tadi` → hapus pengeluaran
- `gaji masuk 10jt` → catat pemasukan

## Setup

### 1. Clone & install
```bash
git clone https://github.com/primagilarwork-hub/isha-v2.git
cd isha-v2
pip3 install -r requirements.txt
pip3 install python-dotenv
```

### 2. Environment variables
```bash
cp .env.example .env
# Isi semua nilai di .env
```

### 3. Supabase schema
Jalankan `schema.sql` di Supabase SQL Editor.

### 4. Google Sheets
```bash
python3 setup_sheets.py
```

### 5. Deploy ke Vercel
```bash
git push  # Vercel auto-deploy
```

### 6. Set Telegram webhook (1x saja)
```
https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://isha-v2-r8po.vercel.app/api/webhook
```

## File Structure
```
isha-v2/
├── api/
│   ├── webhook.py          # Telegram webhook entry point
│   ├── cron/reminder.py    # Daily reminder (21:00 WIB)
│   └── health.py           # Health check
├── lib/
│   ├── handlers.py         # Business logic
│   ├── ai_engine.py        # Claude API wrapper
│   ├── db.py               # Supabase operations
│   ├── telegram.py         # Telegram API helper
│   ├── sheets_sync.py      # Google Sheets sync
│   └── config.py           # Config & cycle logic
├── budget.yaml             # Budget configuration
└── schema.sql              # Database schema
```

## Konfigurasi Budget
Edit `budget.yaml` untuk sesuaikan budget dan tanggal gajian:
```yaml
cycle:
  start_day: 25  # Gaji masuk tanggal 25

income:
  monthly: 10000000
```
