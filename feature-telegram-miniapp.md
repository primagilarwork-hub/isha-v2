# Feature Spec: Telegram Mini App

## Overview

Telegram Mini App adalah web UI yang dibuka langsung di dalam Telegram. User tap tombol di chat → muncul full-screen web UI dengan dashboard, form, grafik, dll. Data ber-sync real-time dengan bot chat (same Supabase database).

## Architecture Principle

**Mini App adalah UI layer baru yang panggil `lib/db.py` yang sama dengan bot chat.**

Artinya:
- Tidak ada duplikasi business logic
- Data selalu konsisten (catat via chat atau Mini App sama aja)
- Layer separation tetap dijaga: entry point → handlers → services

```
┌─────────────────────────────────────────┐
│  ENTRY POINT LAYER                      │
│  api/webhook.py (chat bot)              │
│  api/miniapp/*.py (Mini App API) ← BARU │
│  webapp/*.html (Mini App UI) ← BARU     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  HANDLER LAYER (TIDAK BERUBAH)          │
│  lib/handlers.py                        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  SERVICE LAYER (TIDAK BERUBAH)          │
│  lib/db.py, lib/config.py, dll          │
└─────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Frontend HTML | Vanilla HTML5 | Tidak butuh build step |
| Styling | Tailwind CSS (via CDN) | Utility-first, cepat, minimalis |
| JavaScript | Vanilla JS (ES6+) | No framework overhead |
| Charts | Chart.js (via CDN) | Ringan, mudah, cukup untuk kebutuhan |
| Icons | Lucide Icons (via CDN) | Simple, clean, modern |
| Backend API | Python di api/miniapp/ | Sama dengan webhook, pakai handlers |
| Auth | Telegram initData validation | Built-in Telegram security |

**Total external deps:** 3 CDN link. Tidak ada npm install, tidak ada build.

## File Structure Additions

```
isha-v2/
├── api/
│   ├── webhook.py              # Existing
│   ├── cron/reminder.py        # Existing
│   ├── health.py               # Existing
│   └── miniapp/                # ← BARU
│       ├── __init__.py
│       ├── auth.py             # Validate Telegram initData
│       ├── dashboard.py        # GET dashboard data
│       ├── expenses.py         # GET/POST/DELETE expenses
│       ├── budgets.py          # GET/PUT budgets
│       └── reports.py          # GET report data
│
├── webapp/                     # ← BARU (static files)
│   ├── index.html              # Entry point (routing)
│   ├── pages/
│   │   ├── dashboard.html      # Dashboard visual
│   │   ├── add-expense.html    # Form input
│   │   ├── history.html        # History + filter
│   │   ├── budgets.html        # Budget management UI
│   │   └── reports.html        # Laporan & analytics
│   ├── assets/
│   │   ├── app.js              # Main JS (routing, API calls, state)
│   │   ├── api.js              # API client
│   │   ├── ui.js               # UI helpers (format currency, dates)
│   │   └── styles.css          # Custom styles (supplement Tailwind)
│   └── vercel-static.json      # Config untuk serve static files
│
└── lib/                        # Existing (tidak berubah)
```

## UI Design — Minimalis Principles

### Design Tokens

```css
/* Color palette (minimalis) */
--primary: #0088cc;      /* Telegram blue */
--success: #10b981;      /* Green for on-track */
--warning: #f59e0b;      /* Yellow for 70-90% */
--danger: #ef4444;       /* Red for > 90% */
--bg: #ffffff;           /* Light theme default */
--text: #1f2937;
--muted: #6b7280;
--border: #e5e7eb;

/* Dark theme (auto-detect from Telegram) */
--bg-dark: #0f172a;
--text-dark: #f1f5f9;
```

### Layout

```
┌─────────────────────────┐
│  [Header]               │  Fixed top, title + back button
├─────────────────────────┤
│                         │
│  [Content]              │  Scrollable, max-w-md (mobile-first)
│                         │
├─────────────────────────┤
│  [Bottom Tab Bar]       │  5 tabs: Home, Add, History, Budget, More
└─────────────────────────┘
```

**Prinsip minimalis:**
- Max 1-2 primary action per screen
- Banyak whitespace
- Typography hierarchy jelas (2-3 sizes max)
- Flat design, no shadows berlebihan
- Icons sederhana (outline style)

### Page 1: Dashboard (Home)

```
┌─────────────────────────────┐
│ 💰 Isha                     │
├─────────────────────────────┤
│                             │
│   Cycle 25 Mar - 24 Apr     │
│   17 hari tersisa           │
│                             │
│   ┌───────────────────┐     │
│   │   Rp 4.200.000    │     │
│   │ terpakai dari     │     │
│   │   10.000.000      │     │
│   │                   │     │
│   │   ████░░░ 42%     │     │
│   └───────────────────┘     │
│                             │
│   Budget Status             │
│                             │
│   ● Makan & Minum      53%  │
│     ████░░ 1.5jt/3jt        │
│                             │
│   ● Transport          59%  │
│     ████░░ 890rb/1.5jt      │
│                             │
│   ● Tagihan          ⚠ 90%  │
│     █████ 1.8jt/2jt         │
│                             │
│   [Lihat Semua →]           │
│                             │
│   Hari Ini                  │
│   Rp 85.000 • 3 expense     │
│                             │
├─────────────────────────────┤
│  🏠  ➕  📋  💰  ⋯          │
└─────────────────────────────┘
```

### Page 2: Add Expense

```
┌─────────────────────────────┐
│ ← Tambah Pengeluaran        │
├─────────────────────────────┤
│                             │
│   Jumlah                    │
│   ┌───────────────────┐     │
│   │ Rp  25.000        │     │
│   └───────────────────┘     │
│                             │
│   Deskripsi                 │
│   ┌───────────────────┐     │
│   │ Nasi padang       │     │
│   └───────────────────┘     │
│                             │
│   Kategori                  │
│   [makan-diluar] [▼]        │
│                             │
│   Budget Group              │
│   [Makan & Minum] (auto)    │
│                             │
│   Tanggal                   │
│   [Hari ini ▼]              │
│                             │
│   ┌───────────────────┐     │
│   │    💾 SIMPAN      │     │
│   └───────────────────┘     │
│                             │
└─────────────────────────────┘
```

### Page 3: History

```
┌─────────────────────────────┐
│ ← Riwayat                   │
├─────────────────────────────┤
│                             │
│   [Filter: Semua ▼]         │
│   [Sort: Terbaru ▼]         │
│                             │
│   Hari Ini                  │
│   ┌───────────────────┐     │
│   │ Nasi padang       │     │
│   │ Makan Diluar      │     │
│   │ 14:30  Rp 25.000  │     │
│   └───────────────────┘     │
│   ┌───────────────────┐     │
│   │ Parkir            │     │
│   │ Parkir            │     │
│   │ 12:15  Rp 5.000   │     │
│   └───────────────────┘     │
│                             │
│   Kemarin                   │
│   ┌───────────────────┐     │
│   │ Groceries         │     │
│   │ Groceries         │     │
│   │ 18:00  Rp 150.000 │     │
│   └───────────────────┘     │
│                             │
│   [Load More]               │
│                             │
└─────────────────────────────┘
```

**Tap expense → expand dengan action:** Edit, Hapus

### Page 4: Budget Management

```
┌─────────────────────────────┐
│ ← Budget                    │
├─────────────────────────────┤
│                             │
│   Total: Rp 10.000.000      │
│   [+ Tambah Budget Group]   │
│                             │
│   ┌───────────────────┐     │
│   │ Makan & Minum   ⋮ │     │
│   │ Rp 3.000.000      │     │
│   │ ████░░░░ 53%      │     │
│   │ Sisa Rp 1.425.000 │     │
│   │                   │     │
│   │ Kategori:         │     │
│   │ makan-diluar,     │     │
│   │ groceries, kopi,  │     │
│   │ jajan             │     │
│   │ [+ Tambah]        │     │
│   └───────────────────┘     │
│                             │
│   ┌───────────────────┐     │
│   │ Transport      ⋮  │     │
│   │ Rp 1.500.000      │     │
│   │ ████░░░░ 59%      │     │
│   │ ...               │     │
│   └───────────────────┘     │
│                             │
└─────────────────────────────┘
```

**Tap ⋮ (kebab menu) → Edit amount, Rename, Hapus, Reset**

### Page 5: Reports

```
┌─────────────────────────────┐
│ ← Laporan                   │
├─────────────────────────────┤
│                             │
│   [Cycle Ini ▼]             │
│                             │
│   Pengeluaran per Grup      │
│   ┌───────────────────┐     │
│   │                   │     │
│   │    [Pie Chart]    │     │
│   │                   │     │
│   └───────────────────┘     │
│                             │
│   Trend Harian              │
│   ┌───────────────────┐     │
│   │                   │     │
│   │    [Line Chart]   │     │
│   │                   │     │
│   └───────────────────┘     │
│                             │
│   Perbandingan Cycle        │
│   ┌───────────────────┐     │
│   │    [Bar Chart]    │     │
│   └───────────────────┘     │
│                             │
│   Top 5 Kategori            │
│   1. makan-diluar  1.2jt    │
│   2. bensin        480rb    │
│   3. groceries     450rb    │
│   ...                       │
│                             │
└─────────────────────────────┘
```

## API Endpoints

Semua endpoint di `api/miniapp/`. Semua butuh valid Telegram initData.

### Authentication

**Setiap request HARUS include header:**
```
X-Telegram-Init-Data: <initData dari Telegram WebApp>
```

`api/miniapp/auth.py` validate initData pakai HMAC-SHA256 dengan bot token.

### Endpoints

```
GET  /api/miniapp/dashboard
     → Return: { cycle_info, total_spent, budgets_summary, today_expenses }

GET  /api/miniapp/expenses?limit=20&offset=0&category=&date_from=&date_to=
     → Return: { expenses: [...], total, has_more }

POST /api/miniapp/expenses
     Body: { amount, category, description, expense_date? }
     → Return: { success, expense }

PUT  /api/miniapp/expenses/:id
     Body: { amount?, category?, description? }
     → Return: { success, expense }

DELETE /api/miniapp/expenses/:id
     → Return: { success }

GET  /api/miniapp/budgets
     → Return: { active_budgets: [...], income, total_allocated }

PUT  /api/miniapp/budgets/:group
     Body: { amount }
     → Return: { success, new_total }

POST /api/miniapp/budgets
     Body: { name, amount, categories }
     → Return: { success, budget_group }

DELETE /api/miniapp/budgets/:group
     → Return: { success }

POST /api/miniapp/budgets/:group/categories
     Body: { category_name }
     → Return: { success }

DELETE /api/miniapp/budgets/:group/categories/:category
     → Return: { success }

GET  /api/miniapp/reports/pie?cycle_id=
     → Return: { labels, data, colors }

GET  /api/miniapp/reports/trend?cycle_id=
     → Return: { dates, amounts }

GET  /api/miniapp/reports/compare?cycles=3
     → Return: { cycles, groups, data }

GET  /api/miniapp/reports/top-categories?cycle_id=&limit=5
     → Return: { categories: [...] }
```

## JavaScript Architecture

### webapp/assets/api.js

```javascript
// Simple API client
class IshaAPI {
  constructor() {
    this.baseUrl = '/api/miniapp';
    this.initData = window.Telegram.WebApp.initData;
  }

  async request(endpoint, options = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': this.initData,
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return response.json();
  }

  // Dashboard
  getDashboard() { return this.request('/dashboard'); }
  
  // Expenses
  getExpenses(params) { /* ... */ }
  addExpense(data) { /* ... */ }
  updateExpense(id, data) { /* ... */ }
  deleteExpense(id) { /* ... */ }
  
  // Budgets
  getBudgets() { /* ... */ }
  updateBudget(group, amount) { /* ... */ }
  addBudget(data) { /* ... */ }
  deleteBudget(group) { /* ... */ }
  
  // Reports
  getPieReport(cycleId) { /* ... */ }
  getTrendReport(cycleId) { /* ... */ }
  // dll
}

const api = new IshaAPI();
```

### webapp/assets/app.js

```javascript
// Simple SPA router
const routes = {
  '/': 'pages/dashboard.html',
  '/add': 'pages/add-expense.html',
  '/history': 'pages/history.html',
  '/budgets': 'pages/budgets.html',
  '/reports': 'pages/reports.html',
};

async function navigate(path) {
  const page = routes[path] || routes['/'];
  const html = await fetch(page).then(r => r.text());
  document.getElementById('content').innerHTML = html;
  
  // Init page-specific logic
  const pageName = path.replace('/', '') || 'dashboard';
  if (window[`init${pageName}`]) {
    window[`init${pageName}`]();
  }
}

// Telegram WebApp init
window.Telegram.WebApp.ready();
window.Telegram.WebApp.expand();

// Auto-detect theme
if (window.Telegram.WebApp.colorScheme === 'dark') {
  document.body.classList.add('dark');
}

// Initial route
navigate(location.hash.slice(1) || '/');

// Hash change = navigate
window.addEventListener('hashchange', () => {
  navigate(location.hash.slice(1) || '/');
});
```

## Authentication & Security

### initData Validation

Saat Telegram buka Mini App, dia kirim `initData` yang bisa divalidasi:

```python
# api/miniapp/auth.py
import hmac
import hashlib
from urllib.parse import parse_qsl
import os

def validate_telegram_init_data(init_data: str) -> dict | None:
    """
    Validate Telegram Mini App initData.
    Returns user data dict if valid, None if invalid.
    """
    if not init_data:
        return None
    
    try:
        parsed = dict(parse_qsl(init_data))
        received_hash = parsed.pop('hash', None)
        if not received_hash:
            return None
        
        # Sort keys and build data check string
        data_check = '\n'.join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )
        
        # Compute secret key
        bot_token = os.environ['TELEGRAM_TOKEN']
        secret_key = hmac.new(
            b'WebAppData',
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Compute expected hash
        expected_hash = hmac.new(
            secret_key,
            data_check.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if expected_hash != received_hash:
            return None
        
        # Parse user data
        import json
        user = json.loads(parsed.get('user', '{}'))
        return user
        
    except Exception:
        return None

def require_auth(handler):
    """Decorator untuk protect endpoint."""
    def wrapper(request):
        init_data = request.headers.get('X-Telegram-Init-Data')
        user = validate_telegram_init_data(init_data)
        if not user:
            return {'error': 'Unauthorized'}, 401
        
        # Check whitelist
        allowed_ids = os.environ.get('ALLOWED_USER_IDS', '').split(',')
        if str(user['id']) not in allowed_ids:
            return {'error': 'Forbidden'}, 403
        
        return handler(request, user)
    return wrapper
```

### User Whitelist

Di env var:
```
ALLOWED_USER_IDS=123456789,987654321  # Gilar dan istri
```

## Vercel Configuration

### vercel.json (Updated)

```json
{
  "version": 2,
  "builds": [
    { "src": "api/**/*.py", "use": "@vercel/python" },
    { "src": "webapp/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/api/webhook", "dest": "/api/webhook.py" },
    { "src": "/api/cron/reminder", "dest": "/api/cron/reminder.py" },
    { "src": "/api/health", "dest": "/api/health.py" },
    { "src": "/api/miniapp/(.*)", "dest": "/api/miniapp/$1.py" },
    { "src": "/webapp/(.*)", "dest": "/webapp/$1" },
    { "src": "/", "dest": "/webapp/index.html" }
  ],
  "crons": [
    {
      "path": "/api/cron/reminder",
      "schedule": "0 14 * * *"
    }
  ]
}
```

## Telegram Setup

### 1. Set Menu Button (via @BotFather)

```
/mybots → pilih Isha bot
→ Bot Settings
→ Menu Button
→ Configure menu button
→ Send URL: https://isha-v2.vercel.app/
→ Button text: 📊 Dashboard
```

### 2. Optional: Add inline button di reply bot

Update `lib/telegram.py` `send_message()` untuk support inline keyboard:

```python
def send_message(chat_id, text, open_miniapp_button=False):
    payload = {'chat_id': chat_id, 'text': text}
    
    if open_miniapp_button:
        payload['reply_markup'] = {
            'inline_keyboard': [[
                {
                    'text': '📊 Buka Dashboard',
                    'web_app': {'url': 'https://isha-v2.vercel.app/'}
                }
            ]]
        }
    
    # ... rest of send_message
```

## Tasks

### Phase 1: Infrastructure (0.5 hari)
- [ ] **T-801**: Setup folder webapp/ dan api/miniapp/
- [ ] **T-802**: Update vercel.json untuk static files + miniapp API routes
- [ ] **T-803**: Implement api/miniapp/auth.py dengan initData validation
- [ ] **T-804**: Test auth: coba request tanpa initData → 401
- [ ] **T-805**: Set ALLOWED_USER_IDS di Vercel env

### Phase 2: Core UI Shell (0.5 hari)
- [ ] **T-806**: Buat webapp/index.html dengan Telegram WebApp script
- [ ] **T-807**: Buat webapp/assets/app.js dengan simple router
- [ ] **T-808**: Buat webapp/assets/api.js dengan API client
- [ ] **T-809**: Buat webapp/assets/ui.js dengan helpers (format IDR, date)
- [ ] **T-810**: Setup Tailwind via CDN + dark mode detection
- [ ] **T-811**: Buat bottom tab navigation
- [ ] **T-812**: Test: buka URL di Telegram → UI shell muncul

### Phase 3: Dashboard Page (0.5 hari)
- [ ] **T-813**: Implement api/miniapp/dashboard.py
- [ ] **T-814**: Buat pages/dashboard.html + init logic
- [ ] **T-815**: Progress bar untuk total budget
- [ ] **T-816**: List budget cards dengan progress
- [ ] **T-817**: Today summary card
- [ ] **T-818**: Test: data sync dengan bot chat

### Phase 4: Add Expense Page (0.5 hari)
- [ ] **T-819**: Implement api/miniapp/expenses.py (POST)
- [ ] **T-820**: Buat pages/add-expense.html
- [ ] **T-821**: Form validation (amount > 0, required fields)
- [ ] **T-822**: Category dropdown (load dari budget groups)
- [ ] **T-823**: Auto-detect budget group dari kategori
- [ ] **T-824**: Date picker (default: today)
- [ ] **T-825**: Loading state saat submit
- [ ] **T-826**: Success feedback + redirect to dashboard

### Phase 5: History Page (0.5 hari)
- [ ] **T-827**: Implement api/miniapp/expenses.py (GET with filters)
- [ ] **T-828**: Buat pages/history.html
- [ ] **T-829**: Group by date (Hari Ini, Kemarin, dst)
- [ ] **T-830**: Filter by category
- [ ] **T-831**: Infinite scroll / load more
- [ ] **T-832**: Tap expense → expand dengan Edit/Delete
- [ ] **T-833**: Delete confirmation

### Phase 6: Budget Management Page (1 hari)
- [ ] **T-834**: Implement api/miniapp/budgets.py (GET/PUT/POST/DELETE)
- [ ] **T-835**: Buat pages/budgets.html
- [ ] **T-836**: List all budget groups dengan progress
- [ ] **T-837**: Edit amount modal
- [ ] **T-838**: Add category modal
- [ ] **T-839**: Remove category with confirmation
- [ ] **T-840**: Create new budget group flow
- [ ] **T-841**: Delete budget group dengan warning
- [ ] **T-842**: Integration dengan budget_overrides (sync dengan chat bot)

### Phase 7: Reports Page (0.5 hari)
- [ ] **T-843**: Implement api/miniapp/reports.py (pie, trend, compare, top)
- [ ] **T-844**: Buat pages/reports.html
- [ ] **T-845**: Pie chart: pengeluaran per group (Chart.js)
- [ ] **T-846**: Line chart: trend harian
- [ ] **T-847**: Bar chart: perbandingan cycle
- [ ] **T-848**: Top categories list

### Phase 8: Telegram Integration (0.25 hari)
- [ ] **T-849**: Set menu button via @BotFather
- [ ] **T-850**: Update lib/telegram.py untuk support web_app buttons
- [ ] **T-851**: Tambah inline button "📊 Dashboard" di budget alert message
- [ ] **T-852**: Tambah button di weekly summary

### Phase 9: Polish & Testing (0.5 hari)
- [ ] **T-853**: Test semua flow di Telegram mobile (iOS + Android)
- [ ] **T-854**: Test dark mode (auto dari Telegram)
- [ ] **T-855**: Test dengan akun istri (multi-user)
- [ ] **T-856**: Error handling (network, API errors)
- [ ] **T-857**: Loading states konsisten
- [ ] **T-858**: Haptic feedback via Telegram WebApp API
- [ ] **T-859**: Close button integration (Telegram back button)

## Design Decisions

### DD-M1: Vanilla HTML/JS over Vue/React
**Decision**: Pakai HTML + vanilla JS + Tailwind CDN.
**Reason**: No build step, serverless-friendly, cepat deploy, vibe-coding-friendly.
**Trade-off**: Lebih banyak boilerplate, tapi acceptable untuk app ukuran ini.

### DD-M2: SPA dengan hash routing
**Decision**: Single page app dengan hash-based routing (`/#/dashboard`).
**Reason**: Simpel, no server config, bisa deep-link.
**Trade-off**: URL kurang clean, tapi tidak masalah untuk Mini App.

### DD-M3: Share lib/handlers.py (via adapters)
**Decision**: Mini App API panggil function yang sama dengan chat bot (via handlers atau db directly).
**Reason**: Single source of truth untuk business logic.
**Trade-off**: Beberapa function perlu adapter untuk return JSON (bukan text).

### DD-M4: Whitelist-based auth
**Decision**: Hanya user ID yang di-whitelist (env var) yang bisa akses.
**Reason**: Security + privacy. Bot family-only.
**Trade-off**: Manual setup saat tambah user baru, acceptable untuk family use.

### DD-M5: Chart.js over D3
**Decision**: Pakai Chart.js untuk semua chart.
**Reason**: Mudah, ringan, cukup untuk kebutuhan. D3 overkill.
**Trade-off**: Kurang fleksibel untuk custom chart, tapi tidak butuh.

## Integration dengan Fitur Budget Management

**Penting:** Fitur Budget Management (spec sebelumnya) harus diselesaikan DULU atau paling tidak di-develop paralel, karena Mini App sangat bergantung padanya:

- `db.get_active_budgets()` — dipakai Mini App untuk dashboard
- `db.save_budget_override()` — dipakai saat edit via UI
- `db.add_category_override()` — dipakai saat tambah kategori via UI
- `db.create_custom_group()` — dipakai saat bikin budget baru via UI

**Strategi paralel (RECOMMENDED):**
1. Week 1: Implement Budget Management backend (DB layer + config + handlers untuk chat)
2. Week 2: Start Mini App infrastructure + Dashboard page (pakai function yang sudah siap)
3. Week 3: Finish Mini App pages sambil integrate dengan budget management
4. Week 4: Polish, test, deploy

## Acceptance Criteria

✅ Mini App bisa dibuka dari Telegram menu button
✅ Auth via initData bekerja (tidak bisa akses tanpa Telegram)
✅ Whitelist user works
✅ Dashboard menampilkan data real-time
✅ Add expense via form → muncul di bot chat dan di database
✅ Add via chat bot → muncul di Mini App (real-time sync)
✅ Edit expense dari history
✅ Delete expense dengan konfirmasi
✅ Edit budget amount via UI
✅ Tambah kategori via UI
✅ Bikin budget group baru via UI
✅ Charts render dengan baik di mobile
✅ Dark mode auto-detect dari Telegram
✅ Smooth navigation antar page
✅ Loading states di semua async operation
✅ Error handling friendly

## Out of Scope (Phase 3+)

- Offline mode (service worker)
- Push notifications dari Mini App
- Export ke PDF/Excel
- Advanced filters (date range picker kompleks)
- Image upload untuk receipt
- Voice input
- Multi-language (English)
