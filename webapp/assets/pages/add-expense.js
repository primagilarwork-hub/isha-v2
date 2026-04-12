import { api } from '../core/api.js';
import { FormField, SelectField } from '../components/form-field.js';
import { Button } from '../components/button.js';
import { tg } from '../core/telegram.js';

export async function initAddExpense() {
  const content = document.getElementById('content');
  try {
    const { budgets } = await api.getBudgets();
    const categories = budgets.flatMap(b => b.categories.map(c => ({ value: c, label: `${c} (${b.name})` })));
    content.innerHTML = renderAddExpense(categories);
    setupForm();
  } catch (err) {
    content.innerHTML = `<div class="page"><div class="error-msg">Gagal memuat form: ${err.message}</div></div>`;
  }
}

function renderAddExpense(categories) {
  const today = new Date().toISOString().slice(0, 10);
  return `
    <div class="page">
      <h2 class="page-title">Tambah Pengeluaran</h2>
      <form id="expense-form" onsubmit="return false">
        ${FormField({ id: 'amount', label: 'Jumlah', type: 'number', placeholder: '25000', hint: 'Contoh: 25000' })}
        ${FormField({ id: 'description', label: 'Deskripsi', placeholder: 'Nasi padang' })}
        ${SelectField({ id: 'category', label: 'Kategori', options: [{ value: '', label: '-- Pilih kategori --' }, ...categories] })}
        ${FormField({ id: 'expense_date', label: 'Tanggal', type: 'date', value: today })}
        <div id="form-error" class="form-error" style="display:none"></div>
        ${Button({ label: '💾 Simpan', variant: 'primary', fullWidth: true, onclick: 'submitExpense()', type: 'button' })}
      </form>
    </div>
  `;
}

function setupForm() {
  window.submitExpense = async () => {
    const amount = parseFloat(document.getElementById('amount').value);
    const description = document.getElementById('description').value.trim();
    const category = document.getElementById('category').value;
    const expense_date = document.getElementById('expense_date').value;
    const errEl = document.getElementById('form-error');

    if (!amount || amount <= 0) { showError(errEl, 'Jumlah harus lebih dari 0'); return; }
    if (!category) { showError(errEl, 'Pilih kategori'); return; }

    errEl.style.display = 'none';
    try {
      await api.addExpense({ amount, description, category, expense_date });
      tg.haptic('medium');
      navigate('/');
    } catch (err) {
      showError(errEl, err.message);
    }
  };
}

function showError(el, msg) {
  el.textContent = msg;
  el.style.display = 'block';
}
