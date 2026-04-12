import { api } from '../core/api.js';
import { BudgetCard } from '../components/budget-card.js';
import { Modal, showModal } from '../components/modal.js';
import { FormField } from '../components/form-field.js';
import { Button } from '../components/button.js';
import { formatIDR } from '../utils/formatters.js';
import { tg } from '../core/telegram.js';

export async function initBudgets() {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">Memuat budget...</div>';
  try {
    const data = await api.getBudgets();
    content.innerHTML = renderBudgets(data);
    setupHandlers(data);
  } catch (err) {
    content.innerHTML = `<div class="page"><div class="error-msg">Gagal memuat budget: ${err.message}</div></div>`;
  }
}

function renderBudgets({ budgets, income, total_allocated }) {
  const over = total_allocated > income;
  return `
    <div class="page budgets-page">
      <div class="budgets-summary">
        <span>Total: ${formatIDR(total_allocated)}</span>
        ${over ? `<span style="color: var(--color-danger)">⚠️ Over ${formatIDR(total_allocated - income)}</span>` : `<span style="color: var(--color-success)">✅ Sesuai income</span>`}
      </div>
      ${budgets.map(b => `
        <div class="budget-card-wrapper" data-name="${b.name}">
          ${BudgetCard(b)}
          <div class="budget-card-actions">
            ${Button({ label: 'Edit', variant: 'ghost', size: 'sm', onclick: `editBudget('${b.name}', ${b.amount})` })}
            ${Button({ label: 'Hapus', variant: 'ghost', size: 'sm', onclick: `deleteBudget('${b.name}')` })}
          </div>
        </div>
      `).join('')}
      <div style="margin-top: var(--space-4)">
        ${Button({ label: '+ Tambah Budget Group', variant: 'secondary', fullWidth: true, onclick: 'addBudgetGroup()' })}
      </div>
    </div>
  `;
}

function setupHandlers(data) {
  window.editBudget = (name, currentAmount) => {
    showModal(Modal({
      title: `Edit Budget: ${name}`,
      content: FormField({ id: 'new-amount', label: 'Jumlah Baru', type: 'number', value: currentAmount }),
      confirmLabel: 'Simpan',
      onConfirm: `saveBudgetEdit('${name}')`,
    }));
  };

  window.saveBudgetEdit = async (name) => {
    const amount = parseFloat(document.getElementById('new-amount').value);
    if (!amount || amount <= 0) { tg.showAlert('Jumlah harus lebih dari 0'); return; }
    try {
      await api.updateBudget(name, amount);
      tg.haptic('medium');
      closeModal();
      await initBudgets();
    } catch (err) {
      tg.showAlert('Gagal update: ' + err.message);
    }
  };

  window.deleteBudget = (name) => {
    tg.showConfirm(`Hapus budget "${name}"?`, async (confirmed) => {
      if (!confirmed) return;
      try {
        await api.deleteBudget(name);
        tg.haptic('medium');
        await initBudgets();
      } catch (err) {
        tg.showAlert('Gagal hapus: ' + err.message);
      }
    });
  };

  window.addBudgetGroup = () => {
    showModal(Modal({
      title: 'Tambah Budget Group',
      content: `
        ${FormField({ id: 'new-group-name', label: 'Nama Group', placeholder: 'Kebutuhan Anak' })}
        ${FormField({ id: 'new-group-amount', label: 'Budget', type: 'number', placeholder: '1500000' })}
      `,
      confirmLabel: 'Buat',
      onConfirm: 'saveNewBudgetGroup()',
    }));
  };

  window.saveNewBudgetGroup = async () => {
    const name = document.getElementById('new-group-name').value.trim();
    const amount = parseFloat(document.getElementById('new-group-amount').value);
    if (!name) { tg.showAlert('Nama group wajib diisi'); return; }
    if (!amount || amount <= 0) { tg.showAlert('Budget harus lebih dari 0'); return; }
    try {
      await api.createBudget({ name, amount, categories: [] });
      tg.haptic('medium');
      closeModal();
      await initBudgets();
    } catch (err) {
      tg.showAlert('Gagal buat: ' + err.message);
    }
  };
}
