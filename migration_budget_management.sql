-- ============================================================
-- Migration: Budget Management Helper
-- Jalankan di: Supabase Dashboard → SQL Editor
-- ============================================================

-- T-701: Tabel untuk tracking perubahan kategori per cycle
CREATE TABLE IF NOT EXISTS category_overrides (
    id BIGSERIAL PRIMARY KEY,
    cycle_id TEXT NOT NULL,
    budget_group TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('add', 'remove')),
    category_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel untuk budget group baru yang dibuat via chat
CREATE TABLE IF NOT EXISTS custom_budget_groups (
    id BIGSERIAL PRIMARY KEY,
    cycle_id TEXT NOT NULL,
    name TEXT NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    categories JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabel untuk smart category learning
CREATE TABLE IF NOT EXISTS category_mappings (
    id BIGSERIAL PRIMARY KEY,
    keyword TEXT NOT NULL UNIQUE,
    budget_group TEXT NOT NULL,
    category TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_category_overrides_cycle ON category_overrides(cycle_id);
CREATE INDEX IF NOT EXISTS idx_custom_groups_cycle ON custom_budget_groups(cycle_id);
CREATE INDEX IF NOT EXISTS idx_category_mappings_keyword ON category_mappings(keyword);
