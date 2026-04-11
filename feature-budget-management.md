# Feature Spec: Budget Management Helper

## Overview

Fitur lengkap untuk mengelola budget via chat natural — tanpa perlu edit file YAML. Mencakup: view, edit, add, remove, reset, setup help, dan smart auto-detect kategori baru.

## User Stories

### US-1: View all active budgets
```
👤: budget aku berapa?
🤖: 💰 Budget aktif cycle 25 Mar - 24 Apr:
    
    • Makan & Minum: Rp 3.000.000 (30%)
      └ makan-diluar, groceries, kopi, jajan
    • Transport: Rp 1.500.000 (15%)
      └ bensin, parkir, tol, ojol
    • Tagihan: Rp 2.000.000 (20%)
      └ listrik, internet, pulsa, air
    • Kebutuhan Rumah: Rp 1.500.000 (15%)
    • Tabungan & Investasi: Rp 1.000.000 (10%)
    • Lain-lain: Rp 1.000.000 (10%)
    
    Total: Rp 10.000.000 / Rp 10.000.000 income ✅
```

### US-2: Edit single budget amount
```
👤: ubah budget makan jadi 3.5jt
🤖: ✅ "Makan & Minum" diubah: Rp 3.000.000 → Rp 3.500.000
    
    ⚠️ Total budget sekarang Rp 10.500.000 — over Rp 500.000 dari income.
    Mau kurangi budget lain? Atau tetap lanjut?
```

### US-3: Add new category to existing group
```
👤: tambah kategori "langganan" ke Tagihan
🤖: ✅ Kategori "langganan" ditambahkan ke "Tagihan".
    
    Sekarang Tagihan punya 5 kategori:
    • listrik
    • internet
    • pulsa
    • air
    • langganan (baru)
    
    Budget tetap Rp 2.000.000 (shared).
```

### US-4: Create new budget group
```
👤: bikin budget baru "Kebutuhan Anak" 1.5jt
🤖: ⚠️ Budget baru "Kebutuhan Anak" Rp 1.500.000 akan dibuat.
    
    Total budget jadi Rp 11.500.000 — over Rp 1.500.000 dari income Rp 10jt.
    
    Aku saranin salah satu opsi:
    1. Kurangi budget lain dulu (aku bantu alokasi)
    2. Naikkan income target (kalau ada pemasukan tambahan)
    3. Tetap lanjut (over budget, track saja)
    
    Pilih 1/2/3?

👤: 1
🤖: Oke, mari kita alokasi ulang. Budget mana yang bisa dikurangi?
    
    Saran berdasarkan pola pengeluaran kamu:
    • Lain-lain (1jt) → 500rb (jarang fully used)
    • Kebutuhan Rumah (1.5jt) → 1jt (rata-rata cuma pakai 800rb)
    
    Total kurangi: 1jt. Masih kurang 500rb.
    Dari mana lagi?

👤: dari hiburan
🤖: Hiburan tidak ada sebagai budget group, tapi ada di "Lain-lain".
    Oke, aku kurangi Lain-lain jadi 0? Atau mau pakai angka lain?

👤: Lain-lain jadi 0 aja
🤖: ⚠️ Lain-lain jadi 0 artinya tidak ada buffer untuk pengeluaran tak terduga.
    Sure? Ketik "ya" untuk konfirmasi.

👤: ya
🤖: ✅ Budget baru aktif:
    • Makan & Minum: Rp 3.000.000
    • Transport: Rp 1.500.000
    • Tagihan: Rp 2.000.000
    • Kebutuhan Rumah: Rp 1.000.000 (turun 500rb)
    • Tabungan: Rp 1.000.000
    • Lain-lain: Rp 0 (turun 1jt)
    • Kebutuhan Anak: Rp 1.500.000 (baru)
    
    Total: Rp 10.000.000 ✅
```

### US-5: Add new category to new group (one command)
```
👤: bikin budget "Kebutuhan Anak" 1.5jt dengan kategori: popok, susu, mainan, sekolah
🤖: ✅ Budget "Kebutuhan Anak" dibuat dengan Rp 1.500.000
    Kategori: popok, susu, mainan, sekolah
    
    ⚠️ Total over income Rp 1.500.000. Mau aku bantu alokasi ulang?
```

### US-6: Smart auto-detect saat catat expense unknown
```
👤: bayar netflix 186rb
🤖: 🤔 "netflix" belum ada di kategori manapun.
    
    Saran aku, masukkan ke:
    1. Tagihan > kategori baru "langganan" (recommended)
    2. Lain-lain > kategori baru "langganan"
    3. Bikin budget group baru "Subscription"
    
    Atau kasih tau mau masuk kategori apa.

👤: 1
🤖: ✅ Kategori "langganan" dibuat di Tagihan.
    Netflix Rp 186.000 tercatat di Tagihan > langganan.
    
    💡 Nanti kalau ada "spotify", "youtube premium", dll, aku otomatis
    masuk ke Tagihan > langganan ya. Tinggal catat seperti biasa.
```

### US-7: Remove category from group
```
👤: hapus kategori jajan dari Makan & Minum
🤖: ⚠️ Kategori "jajan" punya 12 expense di cycle ini (total Rp 240.000).
    
    Kalau dihapus:
    1. Expense lama tetap ada di history (dengan label "jajan")
    2. Tidak bisa catat expense baru dengan kategori "jajan"
    
    Yakin? Ketik "ya" untuk hapus.

👤: ya
🤖: ✅ Kategori "jajan" dihapus dari Makan & Minum.
```

### US-8: Remove entire budget group
```
👤: hapus budget Tabungan
🤖: ⚠️ Budget "Tabungan & Investasi" punya Rp 500.000 terpakai di cycle ini.
    Kalau dihapus:
    - Rp 1.000.000 alokasi akan hilang
    - Expense history tetap ada
    - Total budget jadi Rp 9.000.000
    
    Yakin? Ini jarang dilakukan. Ketik "ya hapus" untuk konfirmasi.

👤: ya hapus
🤖: ✅ Budget "Tabungan & Investasi" dihapus.
```

### US-9: Reset budget to YAML default
```
👤: reset budget makan
🤖: ✅ "Makan & Minum" dikembalikan ke default: Rp 3.000.000
    (Dari override Rp 3.500.000)

👤: reset semua budget
🤖: ⚠️ Ini akan kembalikan SEMUA budget ke nilai default YAML.
    Perubahan yang akan di-revert:
    • Makan & Minum: 3.5jt → 3jt
    • Transport: 1.2jt → 1.5jt
    • (3 override lain)
    
    Yakin? Ketik "ya reset" untuk konfirmasi.
```

### US-10: Setup budget from scratch (guided)
```
👤: Isha, bantu aku set budget dari awal dong
🤖: Tentu! Berapa pemasukan bulanan kamu?

👤: 10 juta
🤖: Oke, Rp 10jt. Ada 2 cara aku bantu:

    1. 📊 Data-driven: aku analisis pengeluaran 1-2 bulan terakhir,
       kasih saran berdasarkan pola asli kamu (recommended kalau sudah
       ada data minimal 1 bulan).
    
    2. 💡 Rule of thumb: pakai aturan keuangan umum:
       - 50% Kebutuhan pokok
       - 20% Tabungan & investasi
       - 30% Keinginan & lain-lain
    
    Pilih 1 atau 2?

👤: 1
🤖: 📊 Berdasarkan pengeluaran kamu cycle lalu:
    
    Rata-rata → Saran (dengan buffer 10%):
    • Makan & Minum: 2.8jt → 3jt
    • Transport: 1.1jt → 1.3jt
    • Tagihan: 2jt → 2.2jt
    • Kebutuhan Rumah: 800rb → 1jt
    • Tabungan: (target 10% income) → 1jt
    • Lain-lain: (sisa) → 1.5jt
    
    Total: Rp 10jt ✅
    
    Apply semua, atau adjust dulu?

👤: apply
🤖: ✅ Budget baru aktif untuk cycle ini!
```

## Technical Design

### Database Changes

**No schema change needed.** Pakai tabel yang sudah ada:
- `budget_overrides` — untuk perubahan amount per cycle
- Tabel baru: `category_overrides` untuk tambah/hapus kategori

```sql
-- Tabel baru untuk tracking perubahan kategori
CREATE TABLE category_overrides (
    id BIGSERIAL PRIMARY KEY,
    cycle_id TEXT NOT NULL,
    budget_group TEXT NOT NULL,
    action TEXT NOT NULL,              -- 'add' | 'remove'
    category_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel untuk budget group baru yang dibuat via chat
CREATE TABLE custom_budget_groups (
    id BIGSERIAL PRIMARY KEY,
    cycle_id TEXT NOT NULL,
    name TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    categories JSONB NOT NULL,         -- ["popok", "susu", ...]
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel untuk smart category learning (auto-detect)
CREATE TABLE category_mappings (
    id BIGSERIAL PRIMARY KEY,
    keyword TEXT NOT NULL UNIQUE,      -- "netflix", "spotify"
    budget_group TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### New Intents (lib/ai_engine.py)

```
BUDGET MANAGEMENT INTENTS:

1. VIEW_BUDGETS
   User: "budget aku berapa?", "lihat budget", "berapa total budget"
   data: {}

2. EDIT_BUDGET
   User: "ubah budget makan jadi 3.5jt"
   data: { group: "Makan & Minum", new_amount: 3500000 }

3. ADD_CATEGORY
   User: "tambah kategori langganan ke tagihan"
   data: { group: "Tagihan", category_name: "langganan" }

4. REMOVE_CATEGORY
   User: "hapus kategori jajan"
   data: { category_name: "jajan", group: "Makan & Minum" | null }

5. CREATE_BUDGET_GROUP
   User: "bikin budget baru kebutuhan anak 1.5jt"
   data: { name: "Kebutuhan Anak", amount: 1500000, categories: [] | [...] }

6. REMOVE_BUDGET_GROUP
   User: "hapus budget tabungan"
   data: { group: "Tabungan & Investasi" }

7. RESET_BUDGET
   User: "reset budget makan" | "reset semua budget"
   data: { group: "Makan & Minum" | "all" }

8. SETUP_BUDGET_HELP
   User: "bantu set budget dari awal"
   data: { step, income?, method? }

9. HANDLE_UNKNOWN_CATEGORY (internal, triggered dari RECORD_EXPENSE)
   Saat catat expense tapi deskripsi tidak match kategori existing
   data: { description, amount, suggested_mappings: [...] }
```

### Handler Functions (lib/handlers.py)

```python
def handle_view_budgets(user_id):
    """Tampilkan semua budget aktif (YAML + overrides + custom groups)."""
    
def handle_edit_budget(data, user_id):
    """
    Edit amount single budget.
    Flow:
    1. Validasi group exists
    2. Hitung total baru
    3. Cek vs income, kalau over → warning
    4. Save override
    5. Reply dengan konfirmasi + total baru
    """

def handle_add_category(data, user_id):
    """
    Tambah kategori ke group existing.
    1. Validasi group exists
    2. Cek kategori belum ada
    3. Save ke category_overrides dengan action='add'
    4. Reply dengan list kategori terbaru
    """

def handle_remove_category(data, user_id):
    """
    Hapus kategori dari group.
    1. Warning kalau ada expense dengan kategori tsb
    2. Minta konfirmasi
    3. Save ke category_overrides dengan action='remove'
    """

def handle_create_budget_group(data, user_id):
    """
    Bikin budget group baru.
    1. Validasi nama unik
    2. Hitung total baru dengan group baru
    3. Kalau over income → warning + offer help allocation
    4. Save ke custom_budget_groups
    5. Reply konfirmasi
    """

def handle_remove_budget_group(data, user_id):
    """
    Hapus budget group.
    1. Cek apakah custom atau built-in YAML
    2. Warning kalau ada expense aktif
    3. Double confirmation untuk built-in (rename jadi "archived")
    4. Untuk custom: set is_active = false
    """

def handle_reset_budget(data, user_id):
    """
    Reset budget ke YAML default.
    1. Delete dari budget_overrides
    2. Kalau "all", delete semua overrides untuk cycle ini
    3. Reply summary perubahan
    """

def handle_setup_budget_help(data, user_id, context):
    """
    Multi-step conversation untuk setup dari awal.
    State tracked via conversation context (last 5 messages).
    """

def handle_unknown_category(description, amount, user_id):
    """
    Saat catat expense dengan kategori unknown.
    1. Cek category_mappings untuk keyword match
    2. Kalau match → auto-assign
    3. Kalau tidak → tanya user dengan saran
    4. Save mapping ke category_mappings untuk next time
    """

def check_total_budget_vs_income(cycle_id):
    """
    Helper: return { total_budget, income, over_amount, is_over }
    """

def suggest_budget_reallocation(cycle_id, need_amount):
    """
    Helper: analyze spending patterns, suggest budget cuts
    that minimally impact user.
    """
```

### Database Functions (lib/db.py)

```python
# Budget overrides (sudah ada, perluasan)
def save_budget_override(cycle_id, group, amount, reason=None)
def get_budget_overrides(cycle_id)
def delete_budget_override(cycle_id, group)  # None = delete all

# Category overrides (BARU)
def add_category_override(cycle_id, group, category_name)
def remove_category_override(cycle_id, group, category_name)
def get_category_overrides(cycle_id)

# Custom budget groups (BARU)
def create_custom_group(cycle_id, name, amount, categories)
def get_custom_groups(cycle_id)
def deactivate_custom_group(cycle_id, name)

# Category mappings (BARU)
def save_category_mapping(keyword, group, category)
def get_category_mapping(keyword)
def get_all_mappings()

# Analytics helpers
def get_average_spending_by_group(cycles=2)
def count_expenses_by_category(cycle_id, category)
```

### Config Updates (lib/config.py)

```python
def get_active_budgets(cycle_id=None):
    """
    NEW: Return budget gabungan dari:
    1. budget.yaml (base)
    2. budget_overrides (amount changes)
    3. custom_budget_groups (new groups)
    4. category_overrides (add/remove categories)
    
    Return: list of { name, amount, categories, is_custom, is_overridden }
    """

def get_budget_for_category(category, cycle_id=None):
    """
    UPDATED: Cek dengan urutan:
    1. category_overrides (kalau di-remove, return None)
    2. custom_budget_groups (cek di groups custom dulu)
    3. budget.yaml (default)
    """

def find_category_by_keyword(keyword, cycle_id=None):
    """
    NEW: Cari kategori berdasarkan keyword.
    Urutan:
    1. Exact match di category list
    2. category_mappings (learned)
    3. Fuzzy match
    4. Return None kalau tidak ketemu → trigger handle_unknown_category
    """
```

## Tasks

### Setup (Database)
- [ ] **T-701**: Create SQL migration untuk category_overrides, custom_budget_groups, category_mappings
- [ ] **T-702**: Run migration di Supabase

### DB Layer
- [ ] **T-703**: Implement budget_overrides functions (save/get/delete)
- [ ] **T-704**: Implement category_overrides functions
- [ ] **T-705**: Implement custom_budget_groups functions
- [ ] **T-706**: Implement category_mappings functions
- [ ] **T-707**: Implement analytics helpers

### Config Layer
- [ ] **T-708**: Update config.get_budget_for_category() — support overrides
- [ ] **T-709**: Implement config.get_active_budgets() — merged view
- [ ] **T-710**: Implement config.find_category_by_keyword()

### AI Engine
- [ ] **T-711**: Update system prompt dengan 9 intents baru
- [ ] **T-712**: Test parsing semua intent variations

### Handlers
- [ ] **T-713**: Implement handle_view_budgets
- [ ] **T-714**: Implement handle_edit_budget (dengan over-income warning)
- [ ] **T-715**: Implement handle_add_category
- [ ] **T-716**: Implement handle_remove_category (dengan konfirmasi)
- [ ] **T-717**: Implement handle_create_budget_group (dengan reallocation flow)
- [ ] **T-718**: Implement handle_remove_budget_group
- [ ] **T-719**: Implement handle_reset_budget
- [ ] **T-720**: Implement handle_setup_budget_help (multi-step)
- [ ] **T-721**: Implement handle_unknown_category + smart suggestions
- [ ] **T-722**: Update handle_expense untuk call handle_unknown_category kalau kategori tidak match

### Safety & UX
- [ ] **T-723**: Implement check_total_budget_vs_income helper
- [ ] **T-724**: Implement suggest_budget_reallocation helper
- [ ] **T-725**: Confirmation flow untuk destructive actions (remove, reset all)

### Testing
- [ ] **T-726**: Test: view budgets dengan override aktif
- [ ] **T-727**: Test: edit budget → warning kalau over
- [ ] **T-728**: Test: add category → muncul di view
- [ ] **T-729**: Test: create group → warning + reallocation
- [ ] **T-730**: Test: catat netflix (unknown) → prompted → learned mapping
- [ ] **T-731**: Test: catat spotify (learned) → auto-assign ke langganan
- [ ] **T-732**: Test: reset single dan reset all
- [ ] **T-733**: Test: setup budget dari nol (data-driven)
- [ ] **T-734**: Test: cycle baru → overrides tetap berlaku (pakai logic yang tepat)

### Integration
- [ ] **T-735**: Update budget alert untuk pakai get_active_budgets()
- [ ] **T-736**: Update Google Sheets dashboard untuk reflect custom groups
- [ ] **T-737**: Update system prompt context dengan list budget aktif (bukan YAML)

## Design Decisions

### DD-F1: Override-based, not YAML modification
**Decision**: Jangan modify `budget.yaml`. Semua perubahan via tabel overrides.
**Reason**: 
- YAML adalah "source of truth" yang konsisten
- Override per-cycle memungkinkan tracking history
- User bisa reset ke default kapan saja
- Tidak conflict dengan Git deployment

### DD-F2: Warning over blocking
**Decision**: Kalau total budget > income, kasih warning tapi tetap allow.
**Reason**: 
- User mungkin punya konteks lain (tabungan existing, pemasukan tambahan)
- Isha advisor, bukan gatekeeper
- Sesuai preference user: "Iya, kasih warning kalau over"

### DD-F3: Confirmation untuk destructive
**Decision**: Minta konfirmasi eksplisit untuk: remove category (ada history), remove group, reset all.
**Reason**: Prevent accidental data loss, user safety.

### DD-F4: Smart learning via category_mappings
**Decision**: Saat user assign keyword unknown ke kategori, save mapping untuk next time.
**Reason**: 
- Reduce friction setelah learning
- Isha terasa makin pintar seiring waktu
- Essential untuk "subscription" use case (netflix, spotify, dll)

### DD-F5: Custom groups terpisah dari YAML
**Decision**: Budget group baru yang dibuat via chat masuk ke tabel `custom_budget_groups`, bukan YAML.
**Reason**:
- YAML tetap stabil dan version-controlled
- Custom groups bisa per-cycle (experiment dulu sebelum permanent)
- Mudah di-hapus/nonaktifkan

## Acceptance Criteria

✅ User bisa lihat semua budget aktif via chat
✅ User bisa edit budget amount dengan warning over-income
✅ User bisa tambah kategori ke group existing
✅ User bisa hapus kategori dengan konfirmasi kalau ada history
✅ User bisa bikin budget group baru dengan safety flow
✅ User bisa hapus budget group
✅ User bisa reset budget (single atau all)
✅ User bisa minta Isha bantu setup budget dari nol
✅ Expense dengan kategori unknown → smart prompt
✅ Mapping dipelajari untuk keyword yang sama di masa depan
✅ Semua perubahan tersimpan per-cycle
✅ Budget alert otomatis pakai budget aktif (bukan cuma YAML)
✅ Google Sheets dashboard reflect perubahan

## Out of Scope (Phase 3+)

- Budget templates untuk situasi berbeda (normal vs bulan ramadhan vs liburan)
- Shared budget antar user
- Budget goals jangka panjang (tabungan target)
- Automatic reallocation berdasarkan AI (tanpa konfirmasi)
