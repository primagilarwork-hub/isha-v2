# ── Budget Alert Thresholds ────────────────────────────────
BUDGET_ALERT_WARNING = 70    # % → ⚠️
BUDGET_ALERT_CRITICAL = 90   # % → 🔴
BUDGET_ALERT_REMINDER = 80   # % → reminder malam

# ── Expense Limits ─────────────────────────────────────────
MAX_EXPENSE_AMOUNT = 100_000_000  # 100 juta
MIN_EXPENSE_AMOUNT = 0

# ── Query Limits ───────────────────────────────────────────
RECENT_EXPENSES_LIMIT = 10
SEARCH_EXPENSES_LIMIT = 10
DEFAULT_PAGE_SIZE = 20

# ── Pending Action TTL ─────────────────────────────────────
PENDING_ACTION_TTL_MINUTES = 5

# ── Cycle ──────────────────────────────────────────────────
DEFAULT_CYCLE_START_DAY = 25

# ── AI Model ───────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-5"
CLAUDE_MAX_TOKENS = 1024
