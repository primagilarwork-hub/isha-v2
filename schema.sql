-- ============================================================
-- Isha v2 — Supabase PostgreSQL Schema
-- Jalankan di: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- Tabel pengeluaran
CREATE TABLE expenses (
    id BIGSERIAL PRIMARY KEY,
    amount DECIMAL(12,2) NOT NULL,
    category TEXT NOT NULL,
    budget_group TEXT NOT NULL,
    description TEXT,
    expense_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    user_id TEXT,
    user_name TEXT,
    receipt_photo_url TEXT,
    cycle_id TEXT NOT NULL
);

-- Tabel pemasukan
CREATE TABLE income (
    id BIGSERIAL PRIMARY KEY,
    amount DECIMAL(12,2) NOT NULL,
    source TEXT,
    income_date DATE NOT NULL,
    cycle_id TEXT NOT NULL,
    user_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel cycle reviews
CREATE TABLE cycle_reviews (
    id BIGSERIAL PRIMARY KEY,
    cycle_id TEXT NOT NULL,
    review_text TEXT NOT NULL,
    budget_suggestions JSONB,
    category_suggestions JSONB,
    insights JSONB,
    applied_changes JSONB,
    saving_rate DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel budget overrides
CREATE TABLE budget_overrides (
    id BIGSERIAL PRIMARY KEY,
    cycle_id TEXT NOT NULL,
    budget_group TEXT NOT NULL,
    original_amount DECIMAL(12,2),
    override_amount DECIMAL(12,2),
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_cycle ON expenses(cycle_id);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_expenses_budget_group ON expenses(budget_group);

-- View: ringkasan budget per cycle
CREATE VIEW budget_summary AS
SELECT
    cycle_id,
    budget_group,
    SUM(amount) AS total_spent,
    COUNT(*) AS transaction_count
FROM expenses
GROUP BY cycle_id, budget_group;
