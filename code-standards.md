# Code Standards & Scalability Guidelines — Isha v2

## Tujuan

Memastikan code Isha v2 tetap **rapi, konsisten, dan mudah dikembangkan** seiring bertambahnya fitur. Dokumen ini berlaku untuk SEMUA development ke depan (Mini App, Phase 2+, dll).

---

## 1. Core Principles

### 1.1 Single Responsibility
Setiap file, class, dan function punya **satu tanggung jawab jelas**.

❌ **Bad:**
```python
def handle_expense(data):
    # validate
    if data['amount'] <= 0:
        raise ValueError()
    # save to DB
    supabase.table('expenses').insert(data).execute()
    # sync sheets
    sheet.append_row([...])
    # send telegram message
    requests.post(telegram_url, json={...})
```

✅ **Good:**
```python
def handle_expense(data):
    validate_expense(data)           # validation.py
    expense = db.add_expense(data)    # db.py
    sheets_sync.sync_expense(expense) # sheets_sync.py
    return compose_reply(expense)     # reply_composer.py
```

### 1.2 Don't Repeat Yourself (DRY)
Kalau ada logic yang muncul 2x atau lebih, extract jadi function/helper.

### 1.3 Consistent Over Clever
Code yang konsisten lebih mudah dibaca daripada code yang "pintar". Pilih style yang sama sepanjang project.

### 1.4 Fail Fast, Fail Clearly
Error harus ketahuan secepat mungkin dengan message yang jelas.

```python
# Bad
def get_budget(group):
    return config.get(group)  # Return None diam-diam kalau tidak ada

# Good
def get_budget(group):
    if group not in config:
        raise ValueError(f"Budget group '{group}' tidak ditemukan")
    return config[group]
```

---

## 2. File Organization

### 2.1 Layer Rules (STRICT)

```
api/              → Entry point, NO business logic
lib/handlers.py   → Business logic, orchestration
lib/services/     → External integrations (db, ai, telegram, sheets)
lib/models/       → Data classes / schemas
lib/utils/        → Pure helpers (format, validation, dates)
```

**Aturan wajib:**
- `api/*` TIDAK boleh import dari `lib/services/` langsung
- `api/*` HANYA boleh import dari `lib/handlers`
- `lib/handlers.py` orchestrate services, TIDAK direct database access
- `lib/services/*` TIDAK boleh import dari `handlers.py` (no circular)
- `lib/utils/*` pure functions, NO side effects, NO external calls

### 2.2 Proposed Refactored Structure

```
isha-v2/
├── api/                          # Entry points only
│   ├── webhook.py                # Chat bot webhook
│   ├── health.py
│   ├── cron/
│   │   └── reminder.py
│   └── miniapp/                  # Mini App API
│       ├── __init__.py
│       ├── auth.py               # Telegram initData validation
│       ├── dashboard.py
│       ├── expenses.py
│       ├── budgets.py
│       └── reports.py
│
├── lib/
│   ├── handlers/                 # Business logic (split per domain)
│   │   ├── __init__.py
│   │   ├── base.py               # Shared handler logic
│   │   ├── expense_handler.py    # Expense operations
│   │   ├── budget_handler.py     # Budget operations
│   │   ├── report_handler.py     # Reports & analytics
│   │   ├── reminder_handler.py   # Reminders & notifications
│   │   └── advisor_handler.py    # Financial advice logic
│   │
│   ├── services/                 # External integrations
│   │   ├── __init__.py
│   │   ├── db_service.py         # Supabase client + queries
│   │   ├── ai_service.py         # Claude API
│   │   ├── telegram_service.py   # Telegram Bot API
│   │   └── sheets_service.py     # Google Sheets API
│   │
│   ├── models/                   # Data schemas
│   │   ├── __init__.py
│   │   ├── expense.py            # Expense dataclass
│   │   ├── budget.py             # Budget, BudgetGroup dataclass
│   │   ├── cycle.py              # Cycle info dataclass
│   │   └── user.py               # User dataclass
│   │
│   ├── utils/                    # Pure helpers
│   │   ├── __init__.py
│   │   ├── formatters.py         # format_idr, format_date, etc
│   │   ├── validators.py         # validate_amount, validate_category
│   │   ├── date_utils.py         # cycle calculation, date parsing
│   │   └── parsers.py            # parse informal Indonesian numbers
│   │
│   ├── config.py                 # Config loader
│   └── constants.py              # App constants
│
├── webapp/                       # Mini App frontend
│   ├── index.html
│   ├── pages/
│   └── assets/
│       ├── core/                 # Core modules
│       │   ├── api.js            # API client class
│       │   ├── router.js         # SPA router
│       │   ├── state.js          # Simple state management
│       │   └── telegram.js       # Telegram WebApp wrapper
│       ├── components/           # Reusable UI components
│       │   ├── button.js
│       │   ├── card.js
│       │   ├── modal.js
│       │   └── chart.js
│       ├── pages/                # Page logic
│       │   ├── dashboard.js
│       │   ├── add-expense.js
│       │   ├── history.js
│       │   ├── budgets.js
│       │   └── reports.js
│       └── utils/
│           ├── formatters.js
│           └── validators.js
│
├── tests/                        # Manual test scenarios
│   └── test_scenarios.md         # Checklist untuk manual testing
│
├── .kiro/                        # Kiro specs & steering
├── budget.yaml
├── vercel.json
├── requirements.txt
├── .env.example
└── README.md
```

### 2.3 Why Split handlers.py?

Kalau `handlers.py` sudah > 500 baris, SPLIT berdasarkan domain:
- `expense_handler.py` — add, edit, delete, list expenses
- `budget_handler.py` — view, edit, create, remove budgets
- `report_handler.py` — daily, weekly, cycle summaries
- `reminder_handler.py` — daily reminder, weekly, cycle-end
- `advisor_handler.py` — insights, suggestions, system review

Setiap file max 300-400 baris. Kalau lebih, split lagi.

---

## 3. Python Code Standards

### 3.1 Naming Conventions

```python
# Files: snake_case
expense_handler.py

# Functions: snake_case, verb-first
def add_expense(data): ...
def get_active_budgets(): ...
def is_over_budget(cycle_id): ...

# Variables: snake_case, descriptive
total_expense = 1000000
active_cycle_id = "2025-03-25"

# Constants: UPPER_SNAKE_CASE
DEFAULT_CURRENCY = "IDR"
MAX_RETRY = 3
BUDGET_ALERT_THRESHOLD = 0.7

# Classes: PascalCase (jarang dipakai, prefer functions)
class ExpenseService:
    pass

# Private: prefix _
def _internal_helper():
    pass
```

### 3.2 Function Design

**Max 50 baris per function.** Kalau lebih, split.

**Argumen max 5.** Kalau lebih, pakai dataclass atau dict.

```python
# Bad
def add_expense(amount, category, description, date, user_id, user_name, cycle_id, photo_url):
    ...

# Good
from lib.models.expense import Expense

def add_expense(expense: Expense) -> Expense:
    ...
```

### 3.3 Type Hints (Recommended)

Pakai type hints untuk **public functions** supaya IDE & Claude Code bisa bantu.

```python
from typing import Optional
from lib.models.expense import Expense

def get_expenses(
    cycle_id: str,
    category: Optional[str] = None,
    limit: int = 20,
) -> list[Expense]:
    """Get expenses for a cycle with optional category filter."""
    ...
```

### 3.4 Docstrings

Format Google style untuk public functions:

```python
def calculate_budget_percentage(spent: float, budget: float) -> float:
    """
    Calculate budget usage percentage.
    
    Args:
        spent: Amount spent so far
        budget: Total budget allocated
    
    Returns:
        Percentage (0-100+, can be > 100 if over budget)
    
    Raises:
        ValueError: If budget is 0 or negative
    """
    if budget <= 0:
        raise ValueError("Budget must be positive")
    return (spent / budget) * 100
```

### 3.5 Error Handling

**Always catch specific exceptions, never bare `except:`**

```python
# Bad
try:
    result = api_call()
except:
    return None

# Good
try:
    result = api_call()
except requests.Timeout:
    logger.warning("API timeout, using fallback")
    return fallback_value
except requests.ConnectionError:
    logger.error("Cannot reach API")
    raise ServiceUnavailable("API down")
```

**Custom exceptions untuk domain errors:**

```python
# lib/exceptions.py
class IshaError(Exception):
    """Base exception for Isha."""

class ValidationError(IshaError):
    """Invalid input data."""

class BudgetNotFoundError(IshaError):
    """Budget group not found."""

class OverBudgetError(IshaError):
    """Operation would exceed budget."""
```

### 3.6 Imports Order

```python
# 1. Standard library
import os
import json
from datetime import datetime
from typing import Optional

# 2. Third-party
import requests
from anthropic import Anthropic
from supabase import create_client

# 3. Local (absolute imports)
from lib import config
from lib.services import db_service, ai_service
from lib.models.expense import Expense
from lib.utils.formatters import format_idr
```

---

## 4. JavaScript Standards (Mini App)

### 4.1 Module Pattern

**Each file = one responsibility.** Export explicitly.

```javascript
// webapp/assets/core/api.js
class IshaAPI {
  constructor() {
    this.baseUrl = '/api/miniapp';
    this.initData = window.Telegram.WebApp.initData;
  }

  async request(endpoint, options = {}) {
    // ...
  }

  // Domain methods
  async getDashboard() { /* ... */ }
  async getExpenses(params) { /* ... */ }
}

// Export single instance (singleton)
export const api = new IshaAPI();
```

### 4.2 State Management

**Simple global state, no Redux complexity.**

```javascript
// webapp/assets/core/state.js
class AppState {
  constructor() {
    this.data = {
      currentCycle: null,
      budgets: [],
      recentExpenses: [],
    };
    this.listeners = new Map();
  }

  set(key, value) {
    this.data[key] = value;
    this.notify(key);
  }

  get(key) {
    return this.data[key];
  }

  subscribe(key, callback) {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, []);
    }
    this.listeners.get(key).push(callback);
  }

  notify(key) {
    const callbacks = this.listeners.get(key) || [];
    callbacks.forEach(cb => cb(this.data[key]));
  }
}

export const state = new AppState();
```

### 4.3 Component Pattern

**Reusable UI components as functions.**

```javascript
// webapp/assets/components/budget-card.js
export function BudgetCard({ name, amount, spent, categories }) {
  const percentage = (spent / amount) * 100;
  const status = percentage > 90 ? 'danger' : percentage > 70 ? 'warning' : 'success';
  
  return `
    <div class="budget-card ${status}">
      <h3 class="text-lg font-semibold">${name}</h3>
      <div class="flex justify-between mt-2">
        <span class="text-sm text-muted">${formatIDR(spent)}</span>
        <span class="text-sm">${formatIDR(amount)}</span>
      </div>
      <div class="progress-bar mt-2">
        <div class="progress-fill" style="width: ${Math.min(percentage, 100)}%"></div>
      </div>
    </div>
  `;
}
```

### 4.4 Error Handling

**Never let errors crash the UI.**

```javascript
async function loadDashboard() {
  try {
    showLoading();
    const data = await api.getDashboard();
    renderDashboard(data);
  } catch (error) {
    console.error('Failed to load dashboard:', error);
    showError('Tidak dapat memuat dashboard. Coba lagi.');
  } finally {
    hideLoading();
  }
}
```

### 4.5 Async/Await (No Callbacks)

```javascript
// Good
async function handleSubmit(data) {
  const result = await api.addExpense(data);
  state.set('recentExpenses', [result, ...state.get('recentExpenses')]);
  navigate('/');
}

// Bad
function handleSubmit(data) {
  api.addExpense(data).then(result => {
    api.getBudgets().then(budgets => {
      // Callback hell
    });
  });
}
```

---

## 5. Scalability Patterns

### 5.1 Data Access Abstraction

**NEVER query Supabase directly dari handlers.** Selalu via `db_service`.

```python
# Bad (handlers.py)
def handle_expense(data):
    supabase.table('expenses').insert(data).execute()

# Good (handlers.py)
def handle_expense(data):
    expense = db_service.add_expense(data)
    return expense
```

**Keuntungan:**
- Ganti Supabase ke SQLite? Cukup update `db_service.py`
- Tambah caching? Tambah di `db_service.py`
- Unit test? Mock `db_service`

### 5.2 Configuration over Hardcode

```python
# Bad
if percentage > 90:
    alert = "critical"

# Good
# lib/constants.py
BUDGET_ALERT_WARNING = 0.70
BUDGET_ALERT_CRITICAL = 0.90

# handlers
from lib.constants import BUDGET_ALERT_CRITICAL
if percentage > BUDGET_ALERT_CRITICAL:
    alert = "critical"
```

### 5.3 Feature Flags

Untuk fitur experimental:

```python
# lib/config.py
FEATURES = {
    'system_review': True,
    'receipt_scanning': False,  # Belum siap
    'ai_suggestions': True,
    'mini_app': True,
}

# handlers
from lib.config import FEATURES
if FEATURES['receipt_scanning']:
    handle_receipt(photo)
```

Dengan flag, kamu bisa deploy fitur tapi tidak aktifkan sampai siap.

### 5.4 Graceful Degradation

Kalau external service down, app tetap jalan dengan fallback.

```python
def handle_expense(data):
    expense = db_service.add_expense(data)  # Critical
    
    # Non-critical, bisa gagal
    try:
        sheets_service.sync_expense(expense)
    except Exception as e:
        logger.warning(f"Sheets sync failed: {e}")
        # Lanjut aja, data tetap aman di DB
    
    return expense
```

### 5.5 Plugin Pattern untuk Intent

Supaya tambah intent baru nggak perlu modify core routing:

```python
# lib/handlers/registry.py
INTENT_HANDLERS = {}

def register_handler(intent):
    def decorator(func):
        INTENT_HANDLERS[intent] = func
        return func
    return decorator

# lib/handlers/expense_handler.py
from lib.handlers.registry import register_handler

@register_handler('RECORD_EXPENSE')
def handle_expense(data, user):
    # ...

@register_handler('DELETE_EXPENSE')
def handle_delete_expense(data, user):
    # ...

# lib/handlers/base.py
from lib.handlers.registry import INTENT_HANDLERS

def route_intent(intent, data, user):
    handler = INTENT_HANDLERS.get(intent)
    if not handler:
        raise ValueError(f"Unknown intent: {intent}")
    return handler(data, user)
```

**Tambah intent baru = tambah file + decorator. NO modify routing code.**

---

## 6. Database Patterns

### 6.1 Migration Strategy

Setiap perubahan schema → file SQL baru di `migrations/`:

```
migrations/
├── 001_initial_schema.sql
├── 002_add_budget_overrides.sql
├── 003_add_category_mappings.sql
└── 004_add_miniapp_user_prefs.sql
```

Dokumentasikan di `migrations/README.md` urutan apply.

### 6.2 Query Optimization

**Jangan N+1 queries.**

```python
# Bad: 1 query untuk expenses, N query untuk budget per expense
expenses = db.get_expenses(cycle_id)
for expense in expenses:
    budget = db.get_budget(expense.budget_group)  # N queries!

# Good: JOIN atau batch fetch
expenses_with_budgets = db.get_expenses_with_budgets(cycle_id)
```

### 6.3 Soft Delete (Optional)

Untuk data penting, pakai soft delete:

```sql
ALTER TABLE expenses ADD COLUMN deleted_at TIMESTAMPTZ;

-- "Delete"
UPDATE expenses SET deleted_at = NOW() WHERE id = 123;

-- Query active only
SELECT * FROM expenses WHERE deleted_at IS NULL;
```

Keuntungan: bisa undo, audit trail. Kerugian: lebih kompleks, extra column.

**Untuk Isha v2, cukup hard delete.** Soft delete untuk Phase 3+.

---

## 7. API Design (Mini App)

### 7.1 RESTful Conventions

```
GET    /api/miniapp/expenses          # List
POST   /api/miniapp/expenses          # Create
GET    /api/miniapp/expenses/:id      # Get one
PUT    /api/miniapp/expenses/:id      # Update
DELETE /api/miniapp/expenses/:id      # Delete

GET    /api/miniapp/budgets
PUT    /api/miniapp/budgets/:group
POST   /api/miniapp/budgets           # Create new group
```

### 7.2 Consistent Response Format

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Amount must be positive",
    "field": "amount"
  }
}
```

### 7.3 Pagination Standard

```
GET /api/miniapp/expenses?limit=20&offset=0
```

Response:
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 150,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

### 7.4 Versioning (Future)

Kalau breaking change, versioning via URL:
```
/api/miniapp/v1/expenses   # Current
/api/miniapp/v2/expenses   # New, incompatible
```

Untuk sekarang v2.0, tidak perlu versioning.

---

## 8. Testing Strategy

### 8.1 Manual Test Scenarios

Karena vibe coding, unit test formal nggak realistis. Tapi **manual test checklist** wajib.

`tests/test_scenarios.md`:

```markdown
# Manual Test Scenarios

## Expense Management

### TS-001: Add single expense
1. Kirim: "makan siang 25rb"
2. Expected: ✅ Tercatat, kategori "makan-diluar"
3. Check DB: expense dengan amount 25000 ada
4. Check Sheets: row baru di tab Pengeluaran

### TS-002: Add multi-item
...
```

Setiap fitur baru → tambah TS-XXX. Run semua TS sebelum deploy.

### 8.2 Smoke Tests

Endpoint `/api/health` yang cek:
- Database connection OK
- Anthropic API key valid
- Telegram bot responding
- Google Sheets accessible

Bisa di-ping setiap deploy.

### 8.3 Logging for Debug

```python
# lib/utils/logger.py
import logging
import os

logging.basicConfig(
    level=logging.INFO if os.environ.get('PROD') else logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

def get_logger(name):
    return logging.getLogger(name)

# Usage
logger = get_logger(__name__)
logger.info(f"Processing expense: {data}")
logger.warning(f"Budget over 90%: {group}")
logger.error(f"Sheets sync failed: {error}")
```

Di Vercel, logs otomatis muncul di dashboard.

---

## 9. Documentation Standards

### 9.1 README.md di Root

```markdown
# Isha v2

AI Financial Advisor untuk keluarga via Telegram bot.

## Setup
1. Clone repo
2. Copy `.env.example` ke `.env`
3. Isi credentials
4. Deploy ke Vercel

## Architecture
Lihat `.kiro/specs/isha-v2/design.md`

## Features
- Chat bot natural language
- Budget management
- Telegram Mini App

## Development
Lihat `.kiro/steering/` untuk coding standards.

## Roadmap
Lihat `ROADMAP.md`
```

### 9.2 Inline Comments

**Jelaskan WHY, bukan WHAT.**

```python
# Bad
# Loop through expenses
for exp in expenses:
    total += exp.amount

# Good
# Sum manual, not using sum() because we need to skip deleted items
for exp in expenses:
    if exp.deleted_at is None:
        total += exp.amount
```

### 9.3 CHANGELOG.md

Track perubahan per version:

```markdown
# Changelog

## [2.1.0] - 2026-04-20
### Added
- Telegram Mini App (dashboard, history, reports)
- Budget management via UI

### Fixed
- Budget alert threshold calculation
- Timezone bug in cycle detection

## [2.0.1] - 2026-04-15
### Fixed
- Google Sheets ID column empty
```

---

## 10. Git Workflow

### 10.1 Branch Strategy

```
main                 # Production (auto-deploy Vercel)
├── feature/miniapp  # Feature branch
├── feature/reports
└── fix/sheets-id    # Bug fix branch
```

### 10.2 Commit Messages

Format: `<type>: <description>`

**Types:**
- `feat:` fitur baru
- `fix:` bug fix
- `refactor:` refactor tanpa ubah behavior
- `docs:` update dokumentasi
- `style:` formatting, no logic change
- `test:` add/update tests
- `chore:` maintenance (deps, config, dll)

**Examples:**
```
feat: add Mini App dashboard page
fix: correct sheets sync ID column
refactor: split handlers.py by domain
docs: update README with Mini App setup
```

### 10.3 Commit Per Logical Unit

**Bad:** Satu commit besar dengan semua perubahan Mini App.
**Good:** Satu commit per task T-XXX.

```
feat: T-801 setup miniapp folder structure
feat: T-802 update vercel.json for miniapp routes
feat: T-803 implement telegram initData validation
...
```

Kalau ada bug, gampang git bisect atau rollback.

---

## 11. Performance Guidelines

### 11.1 Vercel Cold Starts

**Minimize imports di top level.**

```python
# Bad: import semua di top, cold start lambat
from anthropic import Anthropic
from supabase import create_client
import gspread
from google.oauth2 import service_account

client_anthropic = Anthropic()
client_supabase = create_client(...)

def handler(request):
    ...
```

```python
# Good: lazy import, cuma yang dipakai
def handler(request):
    from lib.services import db_service
    data = db_service.add_expense(...)
```

### 11.2 Database Query Budget

**Setiap request max 3-5 queries.** Kalau lebih, optimize.

```python
# Bad: 10+ queries
for category in categories:
    budget = db.get_budget(category)  # 1 query per category

# Good: 1 query
all_budgets = db.get_all_budgets()  # Cache in memory
```

### 11.3 Mini App Asset Loading

- CDN untuk libraries (Tailwind, Chart.js, Lucide)
- Minify JS/CSS untuk production (optional, Vercel bisa auto)
- Lazy load pages (fetch HTML on demand, bukan bundle semua)

---

## 12. Security Checklist

- [ ] Semua secrets di env vars, NOT hardcode
- [ ] `.env` di `.gitignore`
- [ ] `CRON_SECRET` untuk protect cron endpoint
- [ ] Telegram user whitelist untuk Mini App
- [ ] Supabase RLS enabled
- [ ] Telegram initData validation di setiap Mini App API
- [ ] Input sanitization (jangan langsung interpolate ke SQL)
- [ ] Rate limiting (future)
- [ ] HTTPS only (Vercel enforce by default)
- [ ] No logging sensitive data (amounts OK, credentials NO)

---

## 13. Action Items untuk Refactor (Opsional)

Kalau mau refactor code existing supaya match standards ini, ini urutan prioritas:

### Priority 1 (Recommended sebelum Mini App)
- [ ] Split `lib/handlers.py` kalau > 500 baris jadi `lib/handlers/` folder
- [ ] Create `lib/models/` dengan dataclass untuk Expense, Budget, Cycle
- [ ] Create `lib/utils/formatters.py` untuk format IDR, date, dll
- [ ] Create `lib/constants.py` untuk thresholds, defaults

### Priority 2 (Bisa sambil jalan)
- [ ] Rename `lib/db.py` → `lib/services/db_service.py`
- [ ] Rename `lib/ai_engine.py` → `lib/services/ai_service.py`
- [ ] Rename `lib/telegram.py` → `lib/services/telegram_service.py`
- [ ] Rename `lib/sheets_sync.py` → `lib/services/sheets_service.py`
- [ ] Add type hints ke public functions
- [ ] Create `lib/exceptions.py` dengan custom exceptions

### Priority 3 (Nice to have)
- [ ] Implement handler registry pattern
- [ ] Add structured logging
- [ ] Create `tests/test_scenarios.md`
- [ ] Add `CHANGELOG.md`

---

## 14. How to Use This Document

**Saat start task baru di Kiro, kasih prompt:**

```
Ikuti code standards di .kiro/steering/code-standards.md.

Khususnya:
- Layer separation (api → handlers → services)
- Single responsibility per function
- Type hints untuk public functions
- Error handling dengan custom exceptions
- Consistent naming & formatting
```

**Setelah task selesai, review dengan checklist:**

- [ ] Function di bawah 50 baris?
- [ ] Satu tanggung jawab per function?
- [ ] Import order benar?
- [ ] Error handling ada?
- [ ] Type hints di public API?
- [ ] Docstring untuk function penting?
- [ ] No hardcoded values?
- [ ] No direct DB access dari handlers?
- [ ] Consistent dengan existing code?

---

## 15. Anti-Patterns — JANGAN LAKUKAN

❌ **God file:** `handlers.py` 2000 baris  
→ Split per domain

❌ **Magic numbers:** `if pct > 0.9:`  
→ Pakai constant `BUDGET_ALERT_CRITICAL`

❌ **Bare except:** `except: pass`  
→ Catch specific exception

❌ **Mutable default args:** `def f(items=[])`  
→ Pakai `def f(items=None): items = items or []`

❌ **Deep nesting:** 5+ level if/for  
→ Early return, extract function

❌ **Copy-paste code:** Same logic di 3 tempat  
→ Extract function

❌ **God object:** Class dengan 20+ methods  
→ Split jadi beberapa class

❌ **Hidden side effects:** `get_user()` yang juga update cache  
→ Explicit: `get_user()` dan `update_user_cache()` terpisah

❌ **Tight coupling:** Handler langsung query DB  
→ Via service layer

❌ **Hardcoded config:** `TOKEN = "abc123"` di code  
→ Env variable
