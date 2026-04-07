# Panduan Workflow: Kiro + Claude Code untuk Isha v2

## Setup Awal

### 1. Install Tools

**Kiro:**
- Download dari https://kiro.dev/downloads/
- Install untuk OS kamu (Mac/Windows/Linux)
- Login dengan GitHub account

**Claude Code:**
- Sudah ada di Claude.ai Pro subscription
- Atau install CLI: `npm install -g @anthropic-ai/claude-code`
- Login dengan akun Claude

### 2. Setup Project di Kiro

1. Buka Kiro
2. File → Open Folder → pilih folder project (kosong dulu)
3. Copy folder `.kiro/` (yang aku buat) ke project root
4. Kiro otomatis detect specs dan steering files

### 3. Setup Claude Code di Project Yang Sama

1. Di terminal, masuk ke folder project
2. Jalankan: `claude` (akan buka Claude Code session)
3. Atau buka VS Code biasa, install extension Claude Code

## Workflow Harian

### Pattern 1: Mulai Task Baru

**Langkah:**

1. **Di Kiro** — Review spec dan task
   ```
   Buka .kiro/specs/isha-v2/tasks.md
   Pilih task berikutnya (misal T-101)
   ```

2. **Di Kiro Chat** — Minta planning
   ```
   "Aku mau kerjakan T-101: implement lib/config.py.
   Lihat requirements.md REQ-1A-04 dan design.md untuk konteks.
   Buat plan implementation-nya."
   ```
   
   Kiro akan generate plan dengan steps yang jelas.

3. **Di Claude Code** — Execute coding
   ```
   "Implement lib/config.py sesuai plan dari Kiro:
   - Load .env dengan python-dotenv
   - Load budget.yaml dengan PyYAML
   - Function get_current_cycle() yang return start, end, id, days_remaining
   - Function get_budget_for_category(category)
   - Function get_all_categories()
   
   Ikuti coding style dari .kiro/steering/structure.md"
   ```
   
   Claude Code generate kode lengkap.

4. **Di Kiro** — Review & commit
   ```
   - Lihat diff visual di Kiro
   - Approve perubahan
   - Commit dengan message: "T-101: implement lib/config.py"
   - Centang [x] T-101 di tasks.md
   ```

### Pattern 2: Debugging

**Saat ada error:**

1. **Copy error message** dari terminal/Vercel logs

2. **Di Claude Code** — Paste & fix
   ```
   "Error ini muncul saat run lib/config.py:
   [paste error]
   
   Fix dan jelaskan apa yang salah."
   ```

3. **Di Kiro** — Verify fix
   ```
   Review perubahan di Kiro
   Test ulang
   ```

### Pattern 3: Refactor / Feature Update

1. **Di Kiro** — Update spec dulu
   ```
   Edit requirements.md atau design.md
   Tambah requirement/design baru
   ```

2. **Di Kiro Chat** — Generate impact analysis
   ```
   "Aku update REQ-1A-06 untuk include kategori detail.
   Apa saja file yang perlu diubah?"
   ```

3. **Di Claude Code** — Execute changes
   ```
   "Update handlers.py dan db.py sesuai perubahan REQ-1A-06.
   Pastikan tidak break existing tests."
   ```

### Pattern 4: Tanya Konsep / Diskusi

Untuk diskusi arsitektur, bisnis, atau decision making:

**Pakai Claude.ai Chat (di sini)** — Bukan Kiro atau Claude Code
```
"Aku bingung antara approach A dan B untuk fitur X.
Pros & cons-nya apa?"
```

Claude.ai chat lebih cocok untuk:
- Diskusi tanpa eksekusi code
- Brainstorming
- Review keputusan arsitektur
- Update blueprint

## Pembagian Tugas

| Tugas | Tool | Kenapa |
|---|---|---|
| Update specs (requirements/design/tasks) | **Kiro** | Spec-driven, version-controlled |
| Generate kode dari task | **Claude Code** | Model Opus lebih kuat untuk coding |
| Review diff visual | **Kiro** | UI-friendly, step-by-step |
| Approve perubahan | **Kiro** | Built-in approval flow |
| Quick fix / debug | **Claude Code** | Lebih cepat di terminal |
| Refactor multi-file | **Claude Code** | Handle context besar |
| Auto-update docs | **Kiro hooks** | Otomatis tiap save |
| Brainstorming | **Claude.ai chat** | Diskusi tanpa eksekusi |
| Deploy | **Git push** | Vercel auto-deploy |

## Tips Vibe Coding

### DO ✅

1. **Selalu refer ke specs** — Kiro & Claude Code keduanya bisa baca `.kiro/`
2. **Commit per task** — Gampang rollback kalau bermasalah
3. **Test setiap milestone** — Jangan biarkan bug menumpuk
4. **Tanya kalau ragu** — Lebih baik tanya dulu daripada salah arah
5. **Update tasks.md** — Centang task yang selesai
6. **Backup data** — Sebelum perubahan besar, export data Supabase

### DON'T ❌

1. **Jangan skip planning** — Gunakan Kiro untuk plan dulu
2. **Jangan modify code tanpa understand** — Kalau ragu, tanya Claude
3. **Jangan commit secrets** — `.env` harus di `.gitignore`
4. **Jangan deploy tanpa test** — Test di local atau preview dulu
5. **Jangan over-engineer** — Ikuti spec, jangan tambah fitur tanpa rencana

## Contoh Sesi Lengkap

### Sesi 1: Setup Phase 0

**Gilar di Kiro:**
> "Aku mau mulai Phase 0 setup. Lihat tasks.md dan kasih tau apa aja yang perlu aku siapkan dulu (akun, token, dll)."

**Kiro response:**
> Untuk Phase 0, kamu perlu siapkan dulu:
> 1. Akun Telegram (sudah ada)
> 2. Daftar @BotFather → buat bot baru
> 3. Daftar Supabase.com → buat project baru
> 4. Daftar Vercel.com (login pakai GitHub)
> 5. Buat repo `isha-v2` di GitHub
> 
> Setelah semua siap, kasih tau aku token dan URL-nya, aku bantu setup .env dan structure folder.

**Gilar (setelah setup akun):**
> "Sudah Kiro. Bot token: 123:abc, Supabase URL: https://xxx.supabase.co, dst."

**Kiro:**
> Bagus! Sekarang aku akan:
> 1. Buat struktur folder project
> 2. Buat .env.example
> 3. Buat requirements.txt awal
> 4. Buat .gitignore
> 
> [Kiro execute & show diff]
> Approve perubahan?

**Gilar:** Approve.

**Kiro:** 
> Done. Selanjutnya, kamu perlu:
> 1. Copy .env.example jadi .env, isi credentials
> 2. Run SQL schema di Supabase (file: scripts/schema.sql)
> 3. Connect repo ke Vercel
> 
> Siap lanjut ke task berikutnya?

### Sesi 2: Coding Pertama (di Claude Code)

**Gilar di Claude Code terminal:**
> "Implement lib/config.py sesuai task T-101.
> Baca .kiro/specs/isha-v2/design.md dan .kiro/steering/tech.md untuk konteks.
> Pastikan ikut layer architecture."

**Claude Code:**
> [Generate lib/config.py lengkap dengan:
> - Load env via python-dotenv
> - Load budget.yaml via PyYAML
> - Helper functions sesuai spec
> - Type hints untuk clarity
> - Docstrings]

**Gilar:** "Test dulu, jalan ga?"

**Claude Code:**
> [Run python -c "from lib import config; print(config.get_current_cycle())"]
> Output: {'start': '2026-03-25', 'end': '2026-04-24', 'id': '2026-03-25', 'days_remaining': 17}
> ✅ Jalan!

**Gilar:** "Commit ya."

**Claude Code:**
> [Run git add lib/config.py budget.yaml]
> [Run git commit -m "T-101: implement lib/config.py"]
> ✅ Committed.

## Troubleshooting

### Kiro tidak detect specs
- Pastikan folder `.kiro/specs/isha-v2/` ada di project root
- Restart Kiro
- Run `Kiro: Reload Window` dari command palette

### Claude Code tidak baca `.kiro/`
- Tambah ke prompt eksplisit: "Baca file `.kiro/specs/isha-v2/design.md` dulu"
- Atau buat `CLAUDE.md` di root yang link ke `.kiro/`

### Conflict antara Kiro dan Claude Code
- Selalu commit perubahan dari satu tool sebelum pakai tool lain
- Pakai `git status` untuk cek perubahan yang belum di-commit

### Kehabisan free tier Kiro
- Switch ke Claude Code untuk coding
- Pakai Kiro hanya untuk review & approve
- Atau upgrade ke Pro $19/bulan selama development aktif

## Resources

- Kiro Docs: https://kiro.dev/docs/
- Claude Code Docs: https://docs.claude.com/en/docs/claude-code
- Supabase Docs: https://supabase.com/docs
- Vercel Python: https://vercel.com/docs/functions/runtimes/python
- Telegram Bot API: https://core.telegram.org/bots/api
