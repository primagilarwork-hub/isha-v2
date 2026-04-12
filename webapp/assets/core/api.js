/**
 * Isha API Client
 * Semua request ke /api/miniapp/* lewat sini.
 */
class IshaAPI {
  constructor() {
    this.baseUrl = '/api/miniapp';
    this._initData = null;
  }

  get initData() {
    if (!this._initData && window.Telegram?.WebApp?.initData) {
      this._initData = window.Telegram.WebApp.initData;
    }
    return this._initData || '';
  }

  async request(endpoint, options = {}) {
    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': this.initData,
        ...(options.headers || {}),
      },
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error?.message || `API error ${res.status}`);
    }
    return data.data ?? data;
  }

  // Dashboard
  getDashboard() { return this.request('/dashboard'); }

  // Expenses
  getExpenses(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this.request(`/expenses${qs ? '?' + qs : ''}`);
  }
  addExpense(data) { return this.request('/expenses', { method: 'POST', body: JSON.stringify(data) }); }
  updateExpense(id, data) { return this.request(`/expenses/${id}`, { method: 'PUT', body: JSON.stringify(data) }); }
  deleteExpense(id) { return this.request(`/expenses/${id}`, { method: 'DELETE' }); }

  // Budgets
  getBudgets() { return this.request('/budgets'); }
  updateBudget(group, amount) { return this.request(`/budgets/${encodeURIComponent(group)}`, { method: 'PUT', body: JSON.stringify({ amount }) }); }
  createBudget(data) { return this.request('/budgets', { method: 'POST', body: JSON.stringify(data) }); }
  deleteBudget(group) { return this.request(`/budgets/${encodeURIComponent(group)}`, { method: 'DELETE' }); }

  // Reports
  getReport(type, params = {}) {
    const qs = new URLSearchParams({ type, ...params }).toString();
    return this.request(`/reports?${qs}`);
  }
}

export const api = new IshaAPI();
