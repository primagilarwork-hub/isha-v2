# ISHA v2 — Blueprint & Architecture
## AI Family Financial Advisor (Telegram Bot)
### Vercel + Supabase Edition

---

## 1. Ringkasan Project

**Isha** adalah bot Telegram untuk manajemen keuangan keluarga, ditenagai oleh Claude AI. User cukup chat natural (bahasa Indonesia) untuk mencatat pengeluaran, cek budget, dan melihat laporan.

### Masalah di v1:
| Masalah | Solusi v2 |
|---------|-----------|
| Harus pakai command | 100% natural language |
| Sering lupa catat | Reminder otomatis tiap malam |
| Budget reset awal bulan, gaji akhir bulan | Siklus budget fleksibel dari tanggal gajian |
| Kategori & budget tidak sinkron | Hierarchical categories (induk → sub) |
| Arsitektur 15 file, susah maintain | Arsitektur simpel (~8 file) |
| Railway mahal | Vercel free tier |
| Google Sheets berantakan | Spreadsheet baru, 4 tab terstruktur |

### Key Decisions:
- **Stack**: Python (vibe coding dengan Claude Code)
- **Platform**: Vercel Serverless (Hobby plan, gratis)
- **Database**: Supabase PostgreSQL (free tier, 500MB)
- **AI Engine**: Claude Sonnet (Anthropic API)
- **Spreadsheet**: Google Sheets (sync/backup + family view)
- **Bot Mode**: Webhook (bukan polling)
- **Development**: Claude Code di VS Code

---

## 2. Tech Stack Detail

| Komponen | Pilihan | Free Tier |
|----------|---------|-----------|
| Hosting | **Vercel** (Hobby) | 150K invocations/bln, 100GB bandwidth |
| Database | **Supabase** | 500MB, 50K rows, unlimited API requests |
| AI | **Claude Sonnet** (Anthropic API) | Bayar per token (~murah untuk personal) |
| Telegram | **Telegram Bot API** (via webhook) | Gratis |
| Sheets | **Google Sheets API** (gspread) | Gratis |
| Cron | **Vercel Cron** | 2 cron jobs, 1x/hari |
| OCR | **Claude Vision API** | Bayar per request |

### Kenapa Supabase?
- Free tier 500MB cukup untuk bertahun-tahun data keuangan keluarga
- PostgreSQL = powerful query untuk laporan & aggregasi
- REST API built-in = mudah akses dari Vercel serverless
- Real-time subscriptions (bisa dipakai nanti untuk dashboard)
- Python client library (`supabase-py`) tersedia

---

## 3. Arsitektur Vercel

### Perbedaan utama dari arsitektur VPS:

| Aspek | VPS (blueprint lama) | Vercel (blueprint baru) |
|-------|---------------------|------------------------|
| Bot mode | Polling (bot jalan terus) | Webhook (function bangun saat ada pesan) |
| Database | SQLite (file lokal) | Supabase PostgreSQL (cloud) |
| Scheduler | APScheduler (in-process) | Vercel Cron + event-driven |
| File structure | Bebas | Harus ikuti `/api/` convention |
| Deploy | Manual / script | Git push → auto deploy |

### Cara Kerja Webhook:

```
User kirim pesan di Telegram
        │
        ▼
Telegram kirim POST request ke:
https://isha-v2.vercel.app/api/webhook
        │
        ▼
Vercel bangunkan function /api/webhook.py
        │
        ▼
Function proses pesan → panggil Claude → simpan ke Supabase → balas user
        │
        ▼
Function selesai, mati (hemat resource)
```

---

## 4. Architecture Principles (Scalability & Migration-Ready)

### 4.1 Prinsip Utama

Arsitektur Isha v2 didesain dengan prinsip berikut agar scalable dan mudah migrasi:

```
1. SEPARATION OF CONCERNS
   Setiap file punya 1 tanggung jawab jelas.
   Tidak ada business logic di api/webhook.py — dia hanya routing.

2. ABSTRACTION LAYER
   lib/ berisi semua logic. api/ hanya entry point.
   Kalau pindah dari Vercel ke Railway/VPS, yang berubah hanya api/ layer.
   lib/ tetap sama 100%.

3. DATABASE ABSTRACTION
   lib/db.py adalah satu-satunya file yang bicara ke database.
   Kalau mau ganti dari Supabase ke SQLite/MySQL, cukup ubah db.py saja.
   Semua file lain panggil db.py, bukan langsung ke database.

4. PLATFORM AGNOSTIC CORE
   lib/ai_engine.py, lib/config.py, lib/sheets_sync.py
   tidak tahu dan tidak peduli apakah jalan di Vercel, Railway, atau VPS.

5. HANDLER PATTERN
   Semua intent (RECORD_EXPENSE, CHECK_BUDGET, dll) diproses oleh
   lib/handlers.py — satu file yang berisi semua business logic.
   Entry point (webhook/polling) hanya panggil handler.

6. CONFIG-DRIVEN
   Budget, kategori, cycle — semua di budget.yaml.
   Tidak ada hardcode di dalam code.
```

### 4.2 Layer Architecture

```
┌─────────────────────────────────────────────┐
│           ENTRY POINT LAYER                 │
│  (Platform-specific, GANTI saat migrasi)    │
│                                             │
│  Vercel:   api/webhook.py                   │
│  Railway:  main.py (polling mode)           │
│  VPS:      main.py (polling mode)           │
└──────────────────┬──────────────────────────┘
                   │ panggil
                   ▼
┌─────────────────────────────────────────────┐
│           HANDLER LAYER                     │
│  (Business logic, TIDAK BERUBAH)            │
│                                             │
│  lib/handlers.py                            │
│  → route intent ke fungsi yang tepat        │
│  → compose reply message                   │
│  → trigger side effects (sheets, alert)     │
└──────────────────┬──────────────────────────┘
                   │ panggil
                   ▼
┌─────────────────────────────────────────────┐
│           SERVICE LAYER                     │
│  (Integrations, TIDAK BERUBAH)              │
│                                             │
│  lib/ai_engine.py  → Claude API             │
│  lib/db.py         → Database (abstracted)  │
│  lib/telegram.py   → Telegram API           │
│  lib/sheets_sync.py→ Google Sheets          │
│  lib/config.py     → Budget config          │
└─────────────────────────────────────────────┘
```

### 4.3 Migration Path

```
SEKARANG: Vercel (free)
   │
   │  Kalau butuh lebih:
   │  - Reminder lebih sering dari 1x/hari
   │  - Background jobs yang kompleks
   │  - Persistent connection / websocket
   │  - Budget bertambah
   │
   ▼
NANTI: Railway / VPS ($5-7/bulan)
   Yang berubah:
   ├── Hapus api/webhook.py → Ganti main.py (polling mode)
   ├── Hapus vercel.json → Ganti Procfile atau docker-compose
   ├── Tambah APScheduler di main.py (reminder fleksibel)
   └── Opsional: ganti Supabase → SQLite (hemat, lokal)

   Yang TIDAK berubah:
   ├── lib/handlers.py (100% sama)
   ├── lib/ai_engine.py (100% sama)
   ├── lib/db.py (sama, atau minor update kalau ganti DB)
   ├── lib/telegram.py (100% sama)
   ├── lib/sheets_sync.py (100% sama)
   ├── lib/config.py (100% sama)
   └── budget.yaml (100% sama)

   Estimasi effort migrasi: 1-2 jam dengan Claude Code
```

---

## 5. File Structure

```
isha-v2/
├── api/                        # ← ENTRY POINT (Vercel-specific)
│   ├── webhook.py              #   Main handler: terima POST dari Telegram
│   ├── cron/
│   │   └── reminder.py         #   Cron job: reminder harian
│   └── health.py               #   Health check endpoint
│
├── lib/                        # ← CORE LOGIC (platform-agnostic)
│   ├── handlers.py             #   Business logic: route intent → action
│   ├── ai_engine.py            #   Claude API wrapper (chat + vision)
│   ├── db.py                   #   Database abstraction (Supabase)
│   ├── telegram.py             #   Telegram API helper
│   ├── sheets_sync.py          #   Google Sheets sync
│   └── config.py               #   Load config & budget definitions
│
├── budget.yaml                 # Budget configuration (config-driven)
├── vercel.json                 # Vercel config (routes, cron)
├── requirements.txt            # Python dependencies
├── .env                        # API keys (lokal dev)
├── .env.example                # Template env vars (untuk dokumentasi)
└── README.md                   # Setup & usage guide
```

**Total: ~11 file** — tapi yang penting: semua logic ada di `lib/`, jadi migrasi hanya sentuh `api/` folder.

**File baru vs blueprint sebelumnya: `lib/handlers.py`**
File ini jadi "otak" Isha — menerima intent dari AI engine dan menjalankan aksi yang tepat. Ini memisahkan business logic dari entry point, sehingga kalau pindah platform, handlers tetap sama.

---

## 5. Core Concepts

### 5.1 Budget Cycle Fleksibel

```yaml
# budget.yaml
cycle:
  start_day: 25          # Gaji masuk tanggal 25
  # Cycle: 25 Jan → 24 Feb = 1 periode

income:
  monthly: 10000000      # Total pemasukan per cycle

budgets:
  - name: "Makan & Minum"
    amount: 3000000
    categories:
      - makan-diluar
      - groceries
      - kopi
      - jajan

  - name: "Transport"
    amount: 1500000
    categories:
      - bensin
      - parkir
      - tol
      - ojol

  - name: "Tagihan"
    amount: 2000000
    categories:
      - listrik
      - internet
      - pulsa
      - air

  - name: "Kebutuhan Rumah"
    amount: 1500000
    categories:
      - peralatan
      - perbaikan
      - kebersihan

  - name: "Tabungan & Investasi"
    amount: 1000000
    categories:
      - emas
      - tabungan
      - darurat

  - name: "Lain-lain"
    amount: 1000000
    categories:
      - hiburan
      - kesehatan
      - gift
      - misc
```

**Cara kerja cycle:**
- `start_day: 25` artinya periode budget dimulai tanggal 25
- Tanggal 25 Januari → 24 Februari = 1 cycle
- Budget TIDAK reset tanggal 1, tapi tanggal 25
- Semua laporan mengikuti cycle ini

### 5.2 Hierarchical Categories

```
Budget "Makan & Minum" (Rp 3.000.000)
├── makan-diluar    → Rp 1.200.000 spent
├── groceries       → Rp 800.000 spent
├── kopi            → Rp 300.000 spent
└── jajan           → Rp 400.000 spent
                      ─────────────────
                      Rp 2.700.000 / 3.000.000 (sisa Rp 300.000)
```

- Budget di-set di **level induk** (grup)
- Pengeluaran dicatat di **level sub-kategori**
- Laporan bisa detail per sub-kategori atau ringkas per grup

### 5.3 Full Natural Language (No Commands)

Semua interaksi lewat chat biasa. Claude yang parse intent dan extract data.

**Contoh input yang harus dipahami:**

```
User: "tadi makan bakso 15rb"
→ Intent: RECORD_EXPENSE
→ Data: { amount: 15000, category: "makan-diluar", description: "bakso" }

User: "kemarin isi bensin 80ribu di shell"
→ Intent: RECORD_EXPENSE
→ Data: { amount: 80000, category: "bensin", description: "isi bensin shell", date: yesterday }

User: "berapa sisa budget makan bulan ini?"
→ Intent: CHECK_BUDGET
→ Data: { budget_group: "Makan & Minum" }

User: "rangkum pengeluaran minggu ini"
→ Intent: REPORT
→ Data: { period: "this_week" }

User: "hapus yang bakso tadi"
→ Intent: DELETE_EXPENSE
→ Data: { search: "bakso", date: today }

User: [kirim foto struk]
→ Intent: SCAN_RECEIPT
→ Data: extracted from image via Claude Vision
```

### 5.4 Isha AI Personality & Advisor Behavior

Isha bukan sekadar pencatat — dia adalah **financial advisor keluarga** yang pintar,
proaktif, dan supportive.

**Prinsip Advisor:**
```
1. PROAKTIF TAPI TIDAK ANNOYING
   - Kasih saran saat relevan, bukan setiap saat
   - Saat catat expense biasa (bakso 15rb) → cukup konfirmasi singkat
   - Saat ada pola menarik atau concern → tambahkan insight
   - Jangan ceramah setiap kali user buka chat

2. TONE ADAPTIF
   - Pengeluaran normal → friendly & ringkas
   - Budget hampir habis → tegas tapi supportive
   - User tanya saran → detail & thoughtful
   - User curhat soal keuangan → empati & motivasi
   - Pencapaian (hemat, di bawah budget) → celebration & dorongan positif

3. DATA-DRIVEN
   - Saran berdasarkan data nyata dari history pengeluaran
   - Bukan saran generik, tapi spesifik ke pola user
   - "Kamu sudah ngopi 12x bulan ini, rata-rata Rp 25rb"
     bukan "Sebaiknya kurangi jajan"

4. KONTEKSTUAL
   - Tahu hari keberapa di cycle (awal bulan lebih santai, akhir bulan lebih hati-hati)
   - Tahu pattern: "Biasanya di minggu ke-3 budget transport mulai tipis"
   - Tahu situasi: kalau budget mepet, jangan suggest pengeluaran baru
```

**Kapan Isha proaktif kasih saran:**
```
SELALU kasih insight saat:
- Budget > 80% terpakai
- Pengeluaran hari ini unusually tinggi vs rata-rata
- Ada pengeluaran besar (> Rp 500rb)
- Kategori tertentu naik signifikan vs cycle lalu
- User belum catat tabungan/investasi padahal sudah pertengahan cycle
- Pencapaian positif (budget masih aman, hemat vs bulan lalu)

JANGAN kasih saran saat:
- Pengeluaran kecil yang normal (makan siang, parkir)
- User baru saja dapat saran (jangan spam)
- User cuma mau cek saldo/budget cepat
```

### 5.5 System Prompt untuk Claude AI Engine

```
Kamu adalah Isha, financial advisor keluarga yang cerdas dan perhatian.
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
- Adaptive — tone sesuai situasi:
  → Catat expense biasa: friendly & singkat
  → Budget mepet: tegas & perhatian
  → User tanya saran: thoughtful & detail
  → Pencapaian: excited & encouraging

RESPONSE FORMAT (JSON):
{
  "intent": "RECORD_EXPENSE | CHECK_BUDGET | REPORT | DELETE_EXPENSE | EDIT_EXPENSE | RECORD_INCOME | ASK_ADVICE | GENERAL_CHAT",
  "data": { ... sesuai intent ... },
  "reply": "Pesan balasan natural untuk user",
  "advice": "Saran keuangan (opsional, null jika tidak relevan)"
}

FIELD "advice" DIISI SAAT:
- Budget > 70% terpakai → saran cara hemat sisa cycle
- Pengeluaran besar (> 500rb) → pertanyaan/konfirmasi halus
- Pola menarik terdeteksi → insight berbasis data
- User tanya soal keuangan → saran detail & actionable
- Pencapaian positif → pujian & motivasi
- Akhir cycle mendekat → ringkasan & saran untuk cycle berikutnya

FIELD "advice" = null SAAT:
- Pengeluaran kecil normal (< 100rb, kategori biasa)
- User hanya mau cek budget cepat
- Baru saja kasih saran di pesan sebelumnya

ATURAN PARSING:
- Currency default: IDR
- Pahami bahasa informal Indonesia:
  - 15rb / 15k = 15.000
  - ceban = 10.000
  - gopek = 500
  - cepek = 100.000
  - sejuta = 1.000.000
- Tanggal relative: "tadi" = hari ini, "kemarin" = yesterday
- Jika amount tidak jelas, TANYA
- Jika kategori ambigu, pilih yang paling cocok dan konfirmasi

JENIS SARAN YANG BISA DIBERIKAN:
1. Tips hemat berdasarkan pola pengeluaran
   → "Kopi rata-rata 25rb x 12 = 300rb/bulan. Kalau kurangi jadi 2x/minggu, hemat ~150rb"
2. Saran alokasi budget
   → "Budget Makan selalu over, Transport selalu sisa. Mau coba geser 200rb?"
3. Peringatan pengeluaran tidak wajar
   → "Pengeluaran hari ini 850rb, 3x lipat dari rata-rata harianmu (280rb)"
4. Insight & pattern
   → "Minggu ke-3 biasanya budget Transport mulai tipis. Mungkin bisa hemat parkir?"
5. Motivasi & dorongan
   → "Budget Makan masih 45%! Lebih baik dari bulan lalu (60% di titik yang sama) 🎉"
6. Saran tabungan/investasi sederhana
   → "Sisa budget bulan ini Rp 800rb. Mau alokasikan sebagian ke tabungan darurat?"
```

---

## 6. Database Schema (Supabase PostgreSQL)

```sql
-- Tabel pengeluaran
CREATE TABLE expenses (
    id BIGSERIAL PRIMARY KEY,
    amount DECIMAL(12,2) NOT NULL,
    category TEXT NOT NULL,              -- sub-kategori (e.g., "makan-diluar")
    budget_group TEXT NOT NULL,          -- grup induk (e.g., "Makan & Minum")
    description TEXT,
    expense_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    user_id TEXT,                        -- Telegram user ID
    user_name TEXT,                      -- Display name
    receipt_photo_url TEXT,              -- URL foto struk (optional)
    cycle_id TEXT NOT NULL               -- Format: "2025-01-25" (cycle start date)
);

-- Tabel income (pemasukan)
CREATE TABLE income (
    id BIGSERIAL PRIMARY KEY,
    amount DECIMAL(12,2) NOT NULL,
    source TEXT,                         -- "gaji", "freelance", "bonus"
    income_date DATE NOT NULL,
    cycle_id TEXT NOT NULL,
    user_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index untuk query cepat
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_cycle ON expenses(cycle_id);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_expenses_budget_group ON expenses(budget_group);

-- View: ringkasan budget per cycle
CREATE VIEW budget_summary AS
SELECT
    cycle_id,
    budget_group,
    SUM(amount) as total_spent,
    COUNT(*) as transaction_count
FROM expenses
GROUP BY cycle_id, budget_group;

-- Tabel cycle reviews (System Review dari Isha)
CREATE TABLE cycle_reviews (
    id BIGSERIAL PRIMARY KEY,
    cycle_id TEXT NOT NULL,              -- Cycle yang di-review
    review_text TEXT NOT NULL,           -- Full review message
    budget_suggestions JSONB,           -- Saran budget: [{ group, current, suggested, reason }]
    category_suggestions JSONB,         -- Saran kategori: [{ action, category, reason }]
    insights JSONB,                     -- Pattern & insight yang ditemukan
    applied_changes JSONB,              -- Perubahan yang di-apply user
    saving_rate DECIMAL(5,2),           -- Saving rate cycle ini (%)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel budget overrides (jika user apply saran perubahan budget)
CREATE TABLE budget_overrides (
    id BIGSERIAL PRIMARY KEY,
    cycle_id TEXT NOT NULL,              -- Berlaku mulai cycle ini
    budget_group TEXT NOT NULL,
    original_amount DECIMAL(12,2),       -- Budget asal dari YAML
    override_amount DECIMAL(12,2),       -- Budget baru yang di-apply
    reason TEXT,                         -- Alasan perubahan
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 7. Flow Diagrams

### 7.1 Message Flow (Webhook)

```
User kirim pesan di Telegram
        │
        ▼
POST https://isha-v2.vercel.app/api/webhook
        │
        ▼
  api/webhook.py
  (parse update dari Telegram)
        │
        ├─ Text message?
        │   └─ lib/ai_engine.py → Claude Chat API
        │       └─ Return: { intent, data, reply }
        │
        ├─ Photo message?
        │   └─ Download foto dari Telegram
        │       └─ lib/ai_engine.py → Claude Vision API
        │           └─ Return: { intent, data, reply }
        │
        ▼
  Route berdasarkan intent:
        │
        ├─ RECORD_EXPENSE
        │   └─ lib/db.py → Supabase INSERT
        │   └─ Cek budget alert (> 80%?)
        │   └─ lib/sheets_sync.py → Google Sheets (async-ish)
        │   └─ lib/telegram.py → Balas user
        │
        ├─ CHECK_BUDGET
        │   └─ lib/db.py → Supabase SELECT + aggregate
        │   └─ lib/telegram.py → Balas user dengan ringkasan
        │
        ├─ REPORT
        │   └─ lib/db.py → Supabase aggregate query
        │   └─ lib/telegram.py → Balas user dengan laporan
        │
        ├─ DELETE_EXPENSE / EDIT_EXPENSE
        │   └─ lib/db.py → Supabase UPDATE/DELETE
        │   └─ lib/sheets_sync.py → Sync Sheets
        │   └─ lib/telegram.py → Balas user
        │
        └─ GENERAL_CHAT
            └─ lib/telegram.py → Balas langsung dari reply Claude
```

### 7.2 Reminder Flow (Cron)

```
Vercel Cron (1x/hari, malam ~21:00 WIB)
        │
        ▼
  api/cron/reminder.py
        │
        ├─ Cek: ada expense hari ini?
        │   ├─ Ya → "Hari ini kamu sudah catat X pengeluaran, total Rp Y"
        │   └─ Tidak → "Hai! Hari ini ada pengeluaran yang belum dicatat?"
        │
        ├─ Cek: budget ada yang > 80%?
        │   └─ Ya → "⚠️ Budget [nama] sudah X% terpakai"
        │
        ├─ Cek: hari Senin?
        │   └─ Ya → Kirim ringkasan minggu lalu
        │
        ├─ Cek: 3 hari sebelum cycle berakhir?
        │   └─ Ya → "Cycle hampir selesai. Mau lihat ringkasan?"
        │
        └─ lib/telegram.py → Kirim reminder ke chat

Catatan: Vercel Hobby cron bisa geser ±59 menit dari waktu yang diset.
Jadi set jam 21:00 bisa trigger antara 21:00-21:59. Ini acceptable untuk reminder.
```

### 7.3 Budget Alert (Event-Driven)

```
Setiap kali expense baru dicatat (di webhook.py):
        │
        ▼
  Hitung total spent untuk budget_group di cycle ini
        │
        ▼
  Bandingkan dengan budget amount dari config
        │
        ├─ < 70% → Aman, tidak ada alert
        ├─ 70-90% → ⚠️ "Budget [X] sudah Y% terpakai"
        └─ > 90% → 🔴 "Budget [X] hampir habis! Sisa Rp Z"
        │
        ▼
  Sertakan alert di reply message
```

### 7.4 Cycle-End System Review (Isha Advisor)

Di akhir setiap cycle, Isha menganalisis semua data cycle yang baru selesai
dan memberikan **System Review** — rekomendasi untuk improve budget, kategori,
dan workflow untuk cycle berikutnya.

```
Trigger: Cron harian mendeteksi hari ini = hari terakhir cycle
         ATAU user minta "review cycle"
        │
        ▼
  handlers.generate_system_review(cycle_id)
        │
        ▼
  Kumpulkan data analisis:
        │
        ├─ Per budget group:
        │   ├─ Actual vs budgeted (over/under/on track)
        │   ├─ Trend 3 cycle terakhir (naik/turun/stabil)
        │   └─ Rata-rata utilization %
        │
        ├─ Per kategori:
        │   ├─ Frekuensi penggunaan (berapa kali dipakai)
        │   ├─ Kategori yang tidak pernah dipakai
        │   └─ Kategori yang sering dipakai tapi belum ada
        │
        ├─ Pattern analysis:
        │   ├─ Pengeluaran per minggu (minggu mana paling boros?)
        │   ├─ Hari-hari dengan spending tertinggi
        │   └─ Expense terbesar yang recurring
        │
        └─ Overall:
            ├─ Total income vs total expense
            ├─ Saving rate (%)
            └─ Perbandingan vs cycle sebelumnya
        │
        ▼
  Kirim semua data ke Claude AI dengan prompt khusus:
  "Analisis data ini dan berikan System Review"
        │
        ▼
  Claude generate rekomendasi:
        │
        ├─ BUDGET REBALANCING
        │   "Budget Tagihan over 3 bulan berturut. Saran: naikkan Rp 200rb,
        │    ambil dari Transport yang selalu sisa."
        │
        ├─ KATEGORI OPTIMIZATION
        │   "Kategori 'hiburan' tidak pernah dipakai 2 cycle terakhir.
        │    Hapus atau rename jadi 'subscription'?"
        │   "Kamu sering catat 'langganan spotify', 'netflix'.
        │    Mau bikin kategori 'subscription' baru?"
        │   "Kategori 'jajan' dan 'kopi' bisa digabung?"
        │
        ├─ SPENDING INSIGHT
        │   "Pengeluaran minggu ke-3 selalu tertinggi (rata-rata Rp 2.8jt).
        │    Mungkin karena ada tagihan bulanan di minggu ini."
        │   "Hari Sabtu rata-rata spend 2x lipat hari biasa."
        │
        ├─ ACHIEVEMENT & MOTIVASI
        │   "Saving rate bulan ini 8% — naik dari 5% bulan lalu! 🎉"
        │   "Kamu konsisten nabung 5 cycle berturut-turut 💪"
        │
        └─ ACTION ITEMS
            "Mau aku update budget untuk cycle berikutnya?
             1. Tagihan: 2.000.000 → 2.200.000
             2. Transport: 1.500.000 → 1.300.000
             3. Tambah kategori 'subscription' di Tagihan
             Ketik 'ok' untuk apply atau kasih tau mau ubah yang mana."
        │
        ▼
  Kirim System Review ke chat
  + Simpan review di Supabase (tabel cycle_reviews)
  + Update Google Sheets tab Rekap Bulanan
```

**Contoh System Review:**

```
🤖: 📋 SYSTEM REVIEW — Cycle 25 Feb - 24 Mar

    📊 RINGKASAN CYCLE
    Total pengeluaran: Rp 9.200.000 / 10.000.000
    Surplus: Rp 800.000 | Saving rate: 8%
    vs cycle lalu: pengeluaran turun 3% ✅

    🔄 SARAN BUDGET
    1. ⬆️ Tagihan: 2.0jt → 2.2jt (over 3 bulan berturut)
    2. ⬇️ Transport: 1.5jt → 1.3jt (selalu sisa ~200rb)
    3. ➡️ Makan & Minum: tetap 3.0jt (pas)

    📁 SARAN KATEGORI
    4. ➕ Tambah "subscription" di Tagihan
       (Netflix, Spotify, YouTube = Rp 150rb/bulan tapi masuk "lain-lain")
    5. 🗑️ "Hiburan" belum pernah dipakai — hapus atau rename?
    6. 🔀 "Jajan" dan "kopi" overlap — gabung jadi "snack & kopi"?

    💡 INSIGHT
    • Minggu ke-3 selalu paling boros (Rp 2.8jt rata-rata)
    • Hari Sabtu spending 2x lipat hari biasa
    • Kopi 14x bulan ini — turun dari 18x bulan lalu 👏

    🎯 PENCAPAIAN
    • Saving rate naik dari 5% → 8% 📈
    • Budget Transport makin efisien tiap bulan
    • 5 cycle berturut konsisten nabung 🏆

    Mau aku apply saran budget #1-#3 untuk cycle berikutnya?
    Atau mau adjust sendiri? Ketik nomor yang mau di-apply.

👤: apply 1 dan 2 aja, kategori nanti deh
🤖: ✅ Done! Budget cycle 25 Mar - 24 Apr:
    • Tagihan: Rp 2.200.000 (naik 200rb)
    • Transport: Rp 1.300.000 (turun 200rb)
    Sisanya tetap sama. Semangat cycle baru! 🚀
```

---

## 8. File-by-File Specification

### 8.1 `api/webhook.py` (Entry Point — Vercel-specific)

```
FUNGSI: Terima webhook POST dari Telegram, delegasi ke handlers.py.
INI FILE YANG BERUBAH SAAT MIGRASI. Isinya minimal.

FLOW:
1. Parse JSON body dari Telegram
2. Extract message (text atau photo)
3. Panggil handlers.handle_message(message)
4. Return 200 OK ke Telegram

PENTING:
- File ini TIDAK berisi business logic
- Hanya parsing input + panggil handler + return response
- Saat migrasi ke Railway, file ini diganti main.py (polling mode)

ERROR HANDLING:
- Try/catch semua, always return 200 ke Telegram
- Error detail dikirim ke user via handlers
```

### 8.2 `lib/handlers.py` (Business Logic — Platform-agnostic) ⭐

```
FUNGSI: Otak Isha. Semua business logic ada di sini.
FILE INI TIDAK BERUBAH SAAT MIGRASI PLATFORM.

FUNCTIONS:
- handle_message(message) → str (reply text)
  Main router. Terima message, return reply.
  1. Cek apakah text atau photo
  2. Kirim ke ai_engine untuk parse intent
  3. Route ke handler spesifik berdasarkan intent
  4. Return reply text

- handle_expense(data) → str
  1. Validasi data (amount > 0, category valid)
  2. Determine budget_group dari category
  3. db.add_expense(data)
  4. Cek budget alert
  5. sheets_sync.sync_expense(data) (best effort)
  6. Compose reply dengan sisa budget

- handle_check_budget(data) → str
  1. db.get_budget_status(cycle_id)
  2. Format reply dengan tabel budget

- handle_report(data) → str
  1. Determine period (hari ini / minggu / cycle)
  2. db.get_summary(...)
  3. Format reply dengan ringkasan

- handle_delete(data) → str
  1. db.get_recent_expenses() untuk cari match
  2. Konfirmasi ke user kalau ambigu
  3. db.delete_expense(id)
  4. sheets_sync.sync_delete(id)

- handle_receipt(photo) → str
  1. telegram.get_file(file_id) → download foto
  2. ai_engine.scan_receipt(photo_bytes)
  3. Konfirmasi items ke user
  4. handle_expense() untuk setiap item

- check_budget_alert(budget_group, cycle_id) → str or None
  1. db.get_budget_status() untuk group ini
  2. < 70% → None (no alert)
  3. 70-90% → "⚠️ Budget X sudah Y%"
  4. > 90% → "🔴 Budget X hampir habis!"

- generate_reminder_message() → str
  Compose daily reminder message.
  Dipanggil oleh api/cron/reminder.py DAN bisa dipanggil
  dari main.py kalau migrasi ke VPS dengan APScheduler.

- generate_weekly_summary() → str
  Compose weekly summary.
  Same principle — bisa dipanggil dari mana saja.

- generate_system_review(cycle_id) → str
  Cycle-end System Review. Analisis lengkap + rekomendasi.
  1. db.get_cycle_summary(cycle_id) → data lengkap cycle
  2. db.get_cycle_summary(prev_cycle_id) → data cycle lalu (perbandingan)
  3. db.get_category_usage(cycle_id) → frekuensi per kategori
  4. db.get_weekly_breakdown(cycle_id) → spending per minggu
  5. Hitung: saving rate, trend per group, unused categories
  6. Kirim semua data ke ai_engine.generate_review(data)
  7. Claude generate: budget suggestions, category suggestions, insights
  8. db.save_cycle_review(review_data)
  9. Return formatted review message

- apply_budget_change(changes) → str
  Apply saran budget dari System Review.
  1. Parse nomor saran yang di-pilih user
  2. db.save_budget_override(cycle_id, group, new_amount)
  3. Update config untuk cycle berikutnya
  4. Compose konfirmasi message

- apply_category_change(changes) → str
  Apply saran kategori dari System Review.
  1. Parse perubahan (tambah/hapus/rename/gabung)
  2. Update budget.yaml atau budget_overrides
  3. Compose konfirmasi message
```

### 8.3 `api/cron/reminder.py` (Cron Entry Point — Vercel-specific)

```
FUNGSI: Entry point untuk cron job. Delegasi ke handlers.
INI FILE YANG BERUBAH SAAT MIGRASI.

FLOW:
1. Verify CRON_SECRET (keamanan)
2. Cek: apakah hari ini = hari terakhir cycle?
   → Ya: Panggil handlers.generate_system_review(cycle_id)
   → Ini akan kirim System Review lengkap ke chat
3. Panggil handlers.generate_reminder_message()
4. Panggil telegram.send_message()
5. Return 200

VERCEL CONFIG:
{
  "crons": [{
    "path": "/api/cron/reminder",
    "schedule": "0 14 * * *"    // 14:00 UTC = 21:00 WIB
  }]
}
```

### 8.4 `api/health.py`

```
FUNGSI: Simple health check endpoint.
Return: { "status": "ok", "version": "2.0" }
```

### 8.5 `lib/ai_engine.py`

```
FUNGSI: Wrapper untuk Claude API.

FUNCTIONS:
- parse_message(text, context) → { intent, data, reply, advice }
  - Kirim text + budget context + recent expenses ke Claude
  - Parse JSON response
  - Return structured data

- scan_receipt(photo_base64) → { items, total, date, reply }
  - Kirim foto ke Claude Vision API
  - Extract line items, total, tanggal
  - Return structured data

- generate_review(cycle_data) → { budget_suggestions, category_suggestions, insights, review_text }
  - Kirim data lengkap cycle ke Claude dengan prompt khusus:
    "Analisis data keuangan cycle ini dan berikan System Review"
  - Claude menganalisis:
    → Budget mana yang over/under secara konsisten
    → Kategori yang tidak terpakai / perlu ditambah
    → Pattern spending (per minggu, per hari)
    → Saving rate dan trend
    → Pencapaian positif
  - Return structured review dengan actionable recommendations

CONTEXT yang dikirim ke Claude (supaya bisa kasih saran pintar):
- Daftar kategori & budget groups dari config
- Info cycle saat ini (start date, end date, hari tersisa)
- 5 expense terakhir (untuk konteks "hapus yang tadi")
- Sisa budget per group di cycle ini
- Rata-rata pengeluaran harian cycle ini
- Perbandingan vs cycle lalu (total per group)
- Frekuensi per kategori bulan ini (misal: "kopi 11x")
- Total pengeluaran hari ini
- Budget overrides yang aktif (jika ada)
- Review cycle sebelumnya (untuk tracking apakah saran diterapkan)
```

### 8.5 `lib/db.py`

```
FUNGSI: Semua operasi database via Supabase Python client.

FUNCTIONS:
- add_expense(data) → expense record
- delete_expense(expense_id) → bool
- edit_expense(expense_id, data) → bool
- get_expenses(cycle_id, filters?) → list
- get_budget_status(cycle_id) → { per_group: [{ name, budgeted, spent, remaining, pct }] }
- get_recent_expenses(limit=5) → list (untuk konteks AI)
- get_daily_summary(date) → { total, count, by_category }
- get_weekly_summary(start_date, end_date) → aggregated data
- get_cycle_summary(cycle_id) → full cycle report
- add_income(data) → income record
```

### 8.6 `lib/telegram.py`

```
FUNGSI: Helper untuk Telegram Bot API.

FUNCTIONS:
- send_message(chat_id, text, parse_mode="Markdown") → bool
- get_file(file_id) → file_bytes (untuk download foto struk)
- set_webhook(url) → bool (dipanggil sekali saat setup)
- delete_webhook() → bool

Semua pakai requests library langsung ke Telegram API.
Tidak pakai python-telegram-bot library (terlalu heavy untuk serverless).
```

### 8.7 `lib/sheets_sync.py`

```
FUNGSI: Sync data ke Google Sheets.

FUNCTIONS:
- sync_expense(expense_data) → append row ke tab Pengeluaran
- sync_delete(expense_id) → hapus row dari tab Pengeluaran
- update_dashboard(cycle_id) → recalculate tab Dashboard
- update_rekap() → update tab Rekap Bulanan
- sync_full(cycle_id) → full sync semua tab

CATATAN:
- Google Sheets API punya latency, jadi sync dilakukan setelah reply ke user
- Kalau sync gagal, data tetap aman di Supabase (source of truth)
- Bisa tambah retry mechanism nanti
```

### 8.8 `lib/config.py`

```
FUNGSI: Load environment variables dan budget config.

FUNCTIONS:
- get_current_cycle() → { start: date, end: date, id: str, days_remaining: int }
- get_budget_for_category(category) → { group_name, amount }
- get_all_categories() → flat list of sub-categories
- get_budget_groups() → list of { name, amount, categories[] }

LOADS:
- .env → TELEGRAM_TOKEN, ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY, etc
- budget.yaml → budget configuration
```

---

## 9. Google Sheets Design

Spreadsheet baru: **"Isha — Keuangan Keluarga"**, di-share ke istri.

### Tab 1: 📋 Pengeluaran (Raw Data)

| ID | Tanggal | Jam | Kategori | Budget Group | Deskripsi | Jumlah | Dicatat Oleh | Cycle |
|---|---|---|---|---|---|---|---|---|
| 1 | 2025-03-05 | 14:30 | makan-diluar | Makan & Minum | Nasi padang | Rp 25.000 | Gilar | 25 Feb - 24 Mar |

- Header: bold, background biru muda, freeze row 1
- Kolom Jumlah: format Rp (currency Indonesia)
- Auto-sort by Tanggal descending
- Conditional formatting: jumlah > 500rb → highlight merah muda

### Tab 2: 📊 Dashboard (Cycle Aktif)

| Budget Group | Budget | Terpakai | Sisa | % | Status |
|---|---|---|---|---|---|
| Makan & Minum | 3.000.000 | 1.575.000 | 1.425.000 | 53% | ✅ |
| Transport | 1.500.000 | 890.000 | 610.000 | 59% | ✅ |
| Tagihan | 2.000.000 | 1.800.000 | 200.000 | 90% | 🔴 |

- % < 70% → hijau (✅)
- % 70-90% → kuning (⚠️)
- % > 90% → merah (🔴)
- Detail sub-kategori bisa di-expand

### Tab 3: 📈 Rekap Bulanan

| Budget Group | Cycle 1 | Cycle 2 | Cycle 3 | Rata-rata | Trend |
|---|---|---|---|---|---|
| Makan & Minum | 2.800.000 | 3.100.000 | (ongoing) | 2.950.000 | ↑ |

- Trend: ↑ naik (merah), ↓ turun (hijau), → stabil
- Line chart per budget group across cycles

### Tab 4: 💰 Config (Reference)

| Budget Group | Sub-Kategori | Budget / Cycle |
|---|---|---|
| Makan & Minum | makan-diluar, groceries, kopi, jajan | 3.000.000 |

### Sync Strategy

```
REALTIME  → Setiap expense baru → update tab Pengeluaran + Dashboard
DAILY     → Via cron reminder → full recalculate Dashboard
ON DEMAND → User minta "sync sheets" → full sync semua tab
CYCLE END → Saat cycle berakhir → finalize Dashboard, update Rekap Bulanan
```

---

## 10. Contoh Interaksi

### Catat pengeluaran biasa (tanpa saran — normal expense):
```
👤: makan siang nasi padang 25rb
🤖: ✅ Tercatat!
    Nasi padang — Rp 25.000
    Kategori: Makan Diluar
    Budget Makan & Minum: Rp 1.575.000 / 3.000.000 (sisa Rp 1.425.000)
```

### Catat beberapa sekaligus:
```
👤: tadi belanja groceries 150rb, terus ngopi 35rb
🤖: ✅ 2 pengeluaran tercatat!
    1. Groceries — Rp 150.000
    2. Ngopi — Rp 35.000
    Total hari ini: Rp 185.000

    ☕ Btw, ini kopi ke-11 bulan ini (total Rp 275.000).
    Kalau kurangi jadi 2x/minggu, bisa hemat ~Rp 125.000 untuk tabungan!
```

### Pengeluaran besar (Isha proaktif kasih insight):
```
👤: beli sepatu 800rb
🤖: ✅ Tercatat! Sepatu — Rp 800.000
    Kategori: Lain-lain

    💡 Ini pengeluaran terbesar minggu ini. Budget Lain-lain sisa Rp 200.000
    untuk 12 hari ke depan. Mau aku bantu cari cara realokasi dari budget lain?
```

### Cek budget (dengan insight perbandingan):
```
👤: gimana budget transport bulan ini?
🤖: 🚗 Budget Transport (cycle 25 Feb - 24 Mar)
    Terpakai: Rp 890.000 / 1.500.000
    Sisa: Rp 610.000 (16 hari lagi)

    Detail:
    • Bensin: Rp 480.000
    • Tol: Rp 250.000
    • Parkir: Rp 100.000
    • Ojol: Rp 60.000

    📊 Dibanding bulan lalu di titik yang sama, kamu lebih hemat 8%! Keep it up 💪
```

### Budget alert (otomatis saat catat expense):
```
👤: bayar listrik 1.5jt
🤖: ✅ Tercatat! Listrik — Rp 1.500.000

    ⚠️ Budget Tagihan sudah 90% terpakai!
    Terpakai: Rp 1.800.000 / 2.000.000
    Sisa: Rp 200.000 untuk internet & pulsa.

    💡 Tagihan listrik bulan ini naik Rp 200.000 dari bulan lalu.
    Mungkin cek pemakaian AC atau peralatan yang standby?
```

### Reminder malam (dengan insight):
```
🤖: 🌙 Hai Gilar!

    📋 Hari ini kamu catat 3 pengeluaran, total Rp 185.000
    Ada yang belum dicatat?

    💡 Minggu ini kamu sudah hemat Rp 120.000 vs minggu lalu.
    Budget Makan masih aman di 52% — bagus! 👍

👤: oh iya tadi parkir 5rb
🤖: ✅ Tercatat! Parkir — Rp 5.000. Selamat istirahat! 😊
```

### User minta saran (Isha jadi full advisor):
```
👤: Isha, gimana kondisi keuangan bulan ini?
🤖: 📊 Ringkasan Cycle 25 Feb - 24 Mar (hari ke-18 dari 30)

    💰 Total pengeluaran: Rp 6.200.000 / 10.000.000
    📈 Rata-rata harian: Rp 344.000
    📅 Sisa hari: 12

    Status per budget:
    ✅ Makan & Minum: 58% (on track)
    ✅ Transport: 59% (on track)
    ⚠️ Tagihan: 90% (hampir habis)
    ✅ Kebutuhan Rumah: 27% (hemat!)
    ✅ Tabungan: 50% (on track)
    ✅ Lain-lain: 80% (hati-hati)

    💡 Saran Isha:
    1. Tagihan sudah 90% — cek apakah ada tagihan lain yang belum dibayar
    2. Kebutuhan Rumah masih banyak sisa — bisa alokasikan ke Tabungan
    3. Kalau bisa jaga rata-rata harian di bawah Rp 300.000 sisa cycle ini,
       kamu bisa tutup bulan dengan surplus Rp 400.000! 🎯
```

### User curhat soal keuangan (Isha supportive):
```
👤: bulan ini boros banget ya kayaknya :(
🤖: Hmm, aku cek dulu ya...

    Sebenarnya nggak separah yang kamu kira:
    • Total saat ini Rp 6.2jt — bulan lalu di titik yang sama Rp 6.5jt
    • Kamu justru lebih hemat 5% dari bulan lalu!

    Yang naik: Tagihan (+200rb karena listrik) dan Lain-lain (+300rb sepatu)
    Yang turun: Transport (-180rb) dan Makan (-120rb)

    Jadi sebenarnya kamu sudah improve di spending harian 👏
    Yang bikin "kerasa boros" itu pengeluaran besar satu kali (sepatu).
    Untuk 12 hari ke depan, kalau jaga di Rp 280rb/hari, kamu tetap on track!

    Semangat ya! 💪
```

### User tanya saran investasi/tabungan:
```
👤: Isha, bulan ini kayaknya ada sisa budget. Enaknya gimana ya?
🤖: 🎉 Nice! Aku lihat estimasi sisa cycle ini sekitar Rp 800.000.

    Beberapa opsi:
    1. 🏦 Tabungan darurat — kalau belum punya 3x pengeluaran bulanan,
       ini prioritas pertama
    2. 🥇 Top up emas Antam — kamu sudah punya, bisa tambah sedikit
    3. 💰 Simpan untuk buffer bulan depan — kalau ada tagihan tahunan
       yang mendekat

    Mau aku catatkan sebagai tabungan atau investasi?
```

### Awal cycle baru (Isha proaktif):
```
🤖: 🗓️ Cycle baru dimulai! (25 Mar - 24 Apr)

    📊 Rekap cycle lalu:
    Total pengeluaran: Rp 9.200.000 / 10.000.000
    Surplus: Rp 800.000 🎉

    💡 Saran untuk cycle ini:
    • Budget Tagihan kemarin pas-pasan. Mau naikkan Rp 200.000?
    • Budget Lain-lain juga sempat over. Mungkin perlu buffer tambahan?
    • Kamu konsisten nabung 5 cycle terakhir — amazing! Teruskan ya 🥇

    Mau adjust budget untuk cycle ini, atau tetap sama?
```

---

## 11. Vercel Configuration

### vercel.json

```json
{
  "version": 2,
  "builds": [
    { "src": "api/**/*.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/api/webhook", "dest": "/api/webhook.py" },
    { "src": "/api/cron/reminder", "dest": "/api/cron/reminder.py" },
    { "src": "/api/health", "dest": "/api/health.py" }
  ],
  "crons": [
    {
      "path": "/api/cron/reminder",
      "schedule": "0 14 * * *"
    }
  ]
}
```

### requirements.txt

```
anthropic>=0.40.0
supabase>=2.0.0
gspread>=6.0.0
google-auth>=2.0.0
pyyaml>=6.0.0
requests>=2.31.0
```

### Environment Variables (di Vercel Dashboard)

```
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_family_chat_id
ANTHROPIC_API_KEY=your_api_key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key
GOOGLE_SHEETS_CREDS={"type":"service_account",...}  # JSON string
SPREADSHEET_ID=your_sheet_id
CRON_SECRET=random_secret_string_16chars
```

---

## 12. Setup Guide (Step by Step)

### Prerequisites:
- Akun GitHub
- Akun Vercel (sign up via GitHub)
- Akun Supabase (free)
- Telegram Bot (dari @BotFather)
- Anthropic API key
- Google Cloud service account (untuk Sheets API)

### Phase 0: Setup Infrastructure (1 hari)

```
1. Buat Telegram Bot via @BotFather → catat TOKEN
2. Buat project Supabase → catat URL dan anon KEY
3. Jalankan SQL schema di Supabase SQL editor
4. Buat GitHub repo: isha-v2
5. Connect repo ke Vercel
6. Set semua environment variables di Vercel dashboard
7. Test: deploy hello world → pastikan Vercel jalan
```

### Phase 1A: MVP — Catat & Budget (2-3 hari) 🚀

Setelah phase ini selesai, Isha SUDAH BISA DIPAKAI sehari-hari.

```
Fitur:
✅ Catat pengeluaran via chat natural
✅ Multi-item sekaligus ("bakso 15rb, kopi 20rb")
✅ Hapus / edit pengeluaran yang salah
✅ Budget cycle dari tanggal gajian
✅ Cek sisa budget per kategori
✅ Budget alert otomatis (> 80%)

Development:
1. Buat file structure (api/ + lib/)
2. Implement lib/config.py + budget.yaml
3. Implement lib/db.py (Supabase CRUD)
4. Implement lib/ai_engine.py (Claude wrapper + system prompt)
5. Implement lib/telegram.py (send message helper)
6. Implement lib/handlers.py (handle_expense, handle_check_budget, handle_delete)
7. Implement api/webhook.py (entry point, delegasi ke handlers)
8. Deploy ke Vercel
9. Set webhook Telegram
10. Test: catat expense, cek budget, hapus expense
```

### Phase 1B: Family View — Sheets & Laporan (1-2 hari) 📊

Setelah phase ini, istri bisa buka spreadsheet dan lihat keuangan.

```
Fitur:
✅ Google Sheets sync (auto-update saat catat expense)
✅ Laporan per cycle (bulanan)
✅ Laporan harian (total hari ini)

Development:
1. Buat Google Sheets spreadsheet baru ("Isha — Keuangan Keluarga")
2. Setup Google Cloud service account untuk Sheets API
3. Implement lib/sheets_sync.py
4. Implement handle_report() di lib/handlers.py
5. Setup 4 tab: Pengeluaran, Dashboard, Rekap Bulanan, Config
6. Share spreadsheet ke istri
7. Test: catat expense → cek muncul di Sheets
```

### Phase 1C: Automation — Reminder & Income (1 hari) 🔔

Setelah phase ini, Isha v2.0 lengkap!

```
Fitur:
✅ Reminder malam ("ada pengeluaran belum dicatat?")
✅ Laporan mingguan (otomatis tiap Senin di reminder)
✅ Catat pemasukan (gaji, freelance, dll)

Development:
1. Implement api/cron/reminder.py
2. Implement handlers.generate_reminder_message()
3. Implement handlers.generate_weekly_summary()
4. Implement handle_income() di handlers.py
5. Update vercel.json dengan cron config
6. Test: trigger cron manual, catat income
```

### Phase 1D: Polish (1 hari) ✨

```
1. Error handling & edge cases
2. Test semua flow bareng istri
3. Finalize Google Sheets formatting
4. Buat README.md
5. Review & fix bugs
```

### Set Webhook Telegram (1x saja):

```
curl https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://isha-v2.vercel.app/api/webhook
```

### Timeline:

```
Hari 1       : Phase 0 (setup)
Hari 2-4     : Phase 1A (MVP) → 🎉 MULAI PAKAI ISHA!
Hari 5-6     : Phase 1B (sheets & laporan)
Hari 7       : Phase 1C (reminder & income)
Hari 8       : Phase 1D (polish)

Total: ~8 hari kerja (dengan Claude Code, bisa lebih cepat)
```

### Fitur yang ditunda ke v2.1+:

```
- Receipt scanning (foto struk) → Phase 2
- Trend analysis → Phase 2
- Multi-user roles → Phase 3
- Smart suggestions → Phase 4
- Telegram Mini App → Phase 5
```

---

## 13. Monitoring & Troubleshooting

### Vercel Dashboard:
- Lihat function logs di Vercel → Project → Logs
- Cek function invocations di Vercel → Project → Usage
- Monitor cron jobs di Vercel → Project → Cron Jobs

### Common Issues:
| Masalah | Solusi |
|---------|--------|
| Bot tidak balas | Cek webhook URL, cek logs di Vercel |
| Claude timeout | Pastikan Fluid Compute enabled di Vercel |
| Supabase error | Cek connection string, cek RLS policies |
| Sheets tidak sync | Cek service account credentials |
| Cron tidak jalan | Cek vercel.json, cek CRON_SECRET |

---

## 14. Scalability & Future Features

### 14.1 Feature Roadmap

Arsitektur Isha v2 didesain supaya fitur baru bisa ditambahkan dengan mudah.
Untuk setiap fitur baru, developer (Claude Code) cukup:
1. Tambah intent baru di ai_engine.py system prompt
2. Tambah handler function di lib/handlers.py
3. Tambah database query di lib/db.py (kalau perlu)
4. Selesai — tidak perlu sentuh entry point atau config

**Phase 1 (v2.0 — Launch):**
- ✅ 1A: Catat pengeluaran natural language + multi-item
- ✅ 1A: Budget cycle fleksibel + cek sisa + alert
- ✅ 1A: Hapus / edit expense
- ✅ 1B: Google Sheets sync + laporan harian & bulanan
- ✅ 1C: Daily reminder + weekly summary + catat pemasukan

**Phase 2 (v2.1 — Insight + Receipt):**
- Receipt scanning (foto struk)
- Trend analysis ("pengeluaran makan naik 20%")
- Monthly report otomatis di akhir cycle
- Perbandingan antar cycle

**Phase 3 (v2.2 — Multi-user):**
- Tiap anggota keluarga bisa catat sendiri
- Per-user tracking dalam 1 bot
- Role: admin (lihat semua) vs member (lihat sendiri)

**Phase 4 (v2.3 — Smart):**
- Smart suggestions berdasarkan pattern
- Prediksi: "Kamu biasanya kehabisan budget transport di minggu ke-3"
- Goal setting: "Target tabungan bulan ini Rp X"

**Phase 5 (v2.4 — Telegram Mini App & Platform):**
- Telegram Mini App (dashboard visual di dalam Telegram)
- WhatsApp integration
- Investment tracking (emas, saham)
- Voice note support

### 14.2 Telegram Mini App — Rencana Detail

Telegram Mini App adalah web app yang dibuka langsung di dalam Telegram.
User tap tombol di chat → muncul UI visual (dashboard, form, grafik).
Arsitektur Isha v2 sudah siap untuk ini tanpa perlu ubah code yang ada.

**Kenapa Mini App?**
- Istri bisa lihat dashboard tanpa harus chat bot
- Visual: grafik pengeluaran, pie chart kategori, progress bar budget
- Form input lebih rapi untuk multi-item expense
- History dengan filter & search

**Yang DITAMBAH (bukan diubah):**

```
isha-v2/
├── api/
│   ├── webhook.py              # Tetap sama
│   ├── cron/reminder.py        # Tetap sama
│   ├── miniapp/                # ← TAMBAH: API endpoints untuk Mini App
│   │   ├── expenses.py         #   GET: list expenses, POST: add expense
│   │   ├── budget.py           #   GET: budget status per cycle
│   │   ├── report.py           #   GET: ringkasan & chart data
│   │   └── auth.py             #   Validasi Telegram initData
│   └── health.py
├── webapp/                     # ← TAMBAH: Frontend Mini App
│   ├── index.html              #   Main entry (single page app)
│   ├── dashboard.html          #   Dashboard visual
│   ├── add-expense.html        #   Form input pengeluaran
│   └── history.html            #   Riwayat pengeluaran + filter
├── lib/                        # ← TIDAK BERUBAH
│   ├── handlers.py
│   ├── ai_engine.py
│   ├── db.py                   #   Mini App pakai db.py yang sama!
│   ├── telegram.py
│   ├── sheets_sync.py
│   └── config.py
```

**Flow Mini App:**

```
User di Telegram:
  ├─ Chat biasa → webhook.py → handlers.py → reply text
  │                                               (seperti sekarang)
  └─ Tap "📊 Dashboard" button
      └─ Buka webapp/dashboard.html di dalam Telegram
          └─ JavaScript fetch() ke api/miniapp/budget.py
              └─ budget.py panggil lib/db.py (SAMA dengan chat bot)
                  └─ Return JSON → render grafik di UI
```

**Kunci penting:**
- `api/miniapp/*.py` panggil `lib/db.py` yang sama dengan bot chat
- Data 100% konsisten: catat via chat, lihat via Mini App
- Mini App hanya READ (lihat data) + simple WRITE (tambah expense via form)
- Auth: Telegram kirim initData yang bisa divalidasi untuk keamanan

**Tech untuk Mini App:**
- Frontend: HTML + CSS + vanilla JS (atau Vue.js kalau mau lebih rapi)
- Chart: Chart.js (lightweight, gratis)
- Host: Vercel (bareng bot, gratis)
- Auth: Telegram Mini App initData validation

**Setup di BotFather:**
```
1. /mybots → pilih Isha bot
2. Bot Settings → Menu Button
3. Set URL: https://isha-v2.vercel.app/webapp/dashboard.html
4. Atau: tambah inline button di reply bot yang buka Mini App
```

**Estimasi effort:** 2-4 hari dengan Claude Code (setelah bot chat stabil)
**Kapan dikerjakan:** Setelah Phase 1-4 selesai dan bot sudah dipakai sehari-hari

### 14.2 Cara Tambah Fitur Baru (Contoh)

Misal mau tambah fitur "Catat Pemasukan":

```
Langkah 1: Update ai_engine.py → tambah RECORD_INCOME di system prompt
Langkah 2: Tambah di lib/handlers.py:
   - handle_income(data) → db.add_income(data) → compose reply
Langkah 3: Update handle_message() di handlers.py:
   - Tambah case RECORD_INCOME → handle_income()
Langkah 4: Kalau perlu tabel baru → tambah SQL di Supabase
Langkah 5: Done! Tidak perlu sentuh webhook.py atau vercel.json
```

### 14.3 Cara Tambah Reminder/Notifikasi Baru

```
Di Vercel (sekarang):
  - Hanya bisa 1x/hari via cron
  - Semua logic reminder ada di handlers.generate_reminder_message()
  - Tambah kondisi baru (misal: "reminder kalau 5 hari tidak catat")
    cukup di function itu saja

Di Railway/VPS (nanti):
  - Bisa pakai APScheduler
  - Tinggal panggil handlers.generate_reminder_message() dari scheduler
  - Bisa set interval: tiap jam, tiap 6 jam, custom
  - Logic reminder tetap sama 100%
```

---

## 15. Migration Guide (Vercel → Railway/VPS)

Saat keuangan membaik dan ingin pindah ke platform yang lebih powerful:

### 15.1 Yang Perlu Dibuat Baru

**File: `main.py` (pengganti api/webhook.py)**

```
FUNGSI: Entry point untuk polling mode. Menggantikan webhook.

STRUCTURE:
1. Import lib/handlers.py, lib/telegram.py, lib/config.py
2. Setup python-telegram-bot (polling mode)
3. Register handler: on_message → handlers.handle_message()
4. Setup APScheduler:
   - Tiap hari 21:00 → handlers.generate_reminder_message()
   - Tiap Senin 08:00 → handlers.generate_weekly_summary()
   - Custom interval untuk budget check
5. bot.run_polling()
```

**File: `Procfile` (untuk Railway)**

```
worker: python main.py
```

**Atau: `docker-compose.yml` (untuk VPS)**

```yaml
version: '3'
services:
  isha:
    build: .
    env_file: .env
    restart: always
```

### 15.2 Yang Bisa Dihapus

```
Hapus:
├── api/                  # Tidak perlu, diganti main.py
│   ├── webhook.py
│   ├── cron/reminder.py
│   └── health.py
└── vercel.json           # Diganti Procfile atau docker-compose
```

### 15.3 Yang TIDAK Berubah (Copy as-is)

```
Tetap sama:
├── lib/                  # 100% sama
│   ├── handlers.py       # ← Semua business logic
│   ├── ai_engine.py
│   ├── db.py
│   ├── telegram.py
│   ├── sheets_sync.py
│   └── config.py
├── budget.yaml
├── requirements.txt      # Tambah: python-telegram-bot, apscheduler
└── .env
```

### 15.4 Database Migration (Optional)

```
Opsi A: Tetap pakai Supabase (recommended)
  → Tidak perlu ubah apa-apa di db.py
  → Data tetap aman di cloud

Opsi B: Pindah ke SQLite (kalau mau fully self-hosted)
  → Ubah lib/db.py: ganti Supabase client → sqlite3
  → Export data dari Supabase → import ke SQLite
  → Effort: ~2-3 jam dengan Claude Code

Opsi C: Pindah ke PostgreSQL self-hosted
  → Ubah connection string di .env
  → lib/db.py hampir sama (Supabase = PostgreSQL)
  → Effort: ~1 jam
```

### 15.5 Estimasi Effort Migrasi

```
Total: 1-2 jam dengan Claude Code

Breakdown:
- Buat main.py (polling + scheduler): 30 menit
- Update requirements.txt: 5 menit
- Buat Procfile / docker-compose: 5 menit
- Test: 20 menit
- Deploy ke Railway: 15 menit
- Set webhook → polling: 5 menit
```

---

## 16. Catatan Penting untuk Claude Code

Saat develop dengan Claude Code, gunakan file ini sebagai referensi utama. Beberapa hal yang perlu diperhatikan:

1. **Vercel Python function** harus return HTTP response, bukan print()
2. **Setiap function harus selesai < 60 detik** (atau 300 detik dengan Fluid Compute)
3. **Tidak ada global state** — setiap invocation mulai fresh
4. **Environment variables** diakses via `os.environ`
5. **File budget.yaml** bisa dibaca karena di-bundle saat deploy
6. **Testing lokal** bisa pakai `vercel dev` atau langsung test endpoint
7. **Selalu return 200 ke Telegram** meskipun ada error (supaya Telegram tidak retry)
8. **Supabase client** harus di-init di setiap function call (tidak bisa persistent connection)
