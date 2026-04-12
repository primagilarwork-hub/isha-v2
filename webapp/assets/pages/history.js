import { api } from '../core/api.js';
import { ExpenseItem } from '../components/expense-item.js';
import { Button } from '../components/button.js';
import { Modal, showModal } from '../components/modal.js';
import { formatDateRelative, formatIDR } from '../utils/formatters.js';
import { tg } from '../core/telegram.js';

let _expenses = [];
let _offset = 0;
const PAGE_SIZE = 20;

export async function initHistory() {
  _expenses = [];
  _offset = 0;
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">Memuat riwayat...</div>';
  await loadMore(content);
}

async function loadMore(content) {
  try {
    const data = await api.getExpenses({ limit: PAGE_SIZE, offset: _offset });
    _expenses = [..._expenses, ...data.items];
    _offset += PAGE_SIZE;
    content.innerHTML = renderHistory(_expenses, data.has_more);
    setupHandlers();
  } catch (err) {
    content.innerHTML = `<div class="page"><div class="error-msg">Gagal memuat riwayat: ${err.message}</div></div>`;
  }
}

function renderHistory(expenses, hasMore) {
  if (!expenses.length) {
    return `<div class="page"><div class="loading">Belum ada pengeluaran.</div></div>`;
  }

  // Group by date
  const grouped = {};
  for (const e of expenses) {
    const key = e.expense_date;
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(e);
  }

  const sections = Object.entries(grouped).sort((a, b) => b[0].localeCompare(a[0])).map(([date, items]) => {
    const total = items.reduce((s, e) => s + parseFloat(e.amount), 0);
    return `
      <div class="history-date-group">
        <div class="history-date-header">
          <span>${formatDateRelative(date)}</span>
          <span>${formatIDR(total)}</span>
        </div>
        <div class="history-items">
          ${items.map(e => ExpenseItem(e)).join('')}
        </div>
      </div>
    `;
  }).join('');

  return `
    <div class="page history-page">
      ${sections}
      ${hasMore ? `<div style="padding: var(--space-4)">
        ${Button({ label: 'Muat Lebih Banyak', variant: 'secondary', fullWidth: true, onclick: 'loadMoreHistory()' })}
      </div>` : ''}
    </div>
  `;
}

function setupHandlers() {
  window.onExpenseClick = (id) => {
    const expense = _expenses.find(e => e.id === id);
    if (!expense) return;
    showModal(Modal({
      title: expense.description || expense.category,
      content: `
        <p style="color: var(--color-text-secondary); font-size: var(--text-sm)">
          ${formatIDR(expense.amount)} · ${expense.category} · ${formatDateRelative(expense.expense_date)}
        </p>
      `,
      confirmLabel: '🗑️ Hapus',
      cancelLabel: 'Tutup',
      onConfirm: `deleteExpense(${id})`,
    }));
  };

  window.deleteExpense = async (id) => {
    tg.showConfirm('Yakin mau hapus pengeluaran ini?', async (confirmed) => {
      if (!confirmed) return;
      try {
        await api.deleteExpense(id);
        tg.haptic('medium');
        closeModal();
        await initHistory();
      } catch (err) {
        tg.showAlert('Gagal hapus: ' + err.message);
      }
    });
  };

  window.loadMoreHistory = () => {
    const content = document.getElementById('content');
    loadMore(content);
  };
}
