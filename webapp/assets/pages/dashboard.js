import { api } from '../core/api.js';
import { Card } from '../components/card.js';
import { BudgetCard } from '../components/budget-card.js';
import { ProgressBar } from '../components/progress-bar.js';
import { formatIDR, formatPct } from '../utils/formatters.js';

export async function initDashboard() {
  const content = document.getElementById('content');
  try {
    const data = await api.getDashboard();
    content.innerHTML = renderDashboard(data);
  } catch (err) {
    content.innerHTML = `<div class="page"><div class="error-msg">Gagal memuat dashboard: ${err.message}</div></div>`;
  }
}

function renderDashboard(data) {
  const { cycle, summary, budgets, today } = data;
  const topBudgets = budgets.slice(0, 4);
  const hasMore = budgets.length > 4;

  return `
    <div class="page dashboard-page">
      <div class="dashboard-cycle-info">
        <span class="cycle-label">${cycle.label}</span>
        <span class="cycle-days">${cycle.days_remaining} hari tersisa</span>
      </div>

      ${Card({
        content: `
          <div class="card-label">Total Terpakai</div>
          <div class="card-value">${formatIDR(summary.total_spent)}</div>
          <div class="card-label">dari ${formatIDR(summary.total_budget)}</div>
          ${ProgressBar({ percentage: summary.percentage, variant: 'primary' })}
          <div class="summary-pct">${summary.percentage}% terpakai · sisa ${formatIDR(summary.total_remaining)}</div>
        `
      })}

      <div class="section-title">Budget per Grup</div>

      ${topBudgets.map(b => BudgetCard(b)).join('')}

      ${hasMore ? `<button class="btn btn-ghost btn-sm" onclick="navigate('/budgets')">Lihat Semua →</button>` : ''}

      <div class="section-title">Hari Ini</div>
      ${Card({
        content: today.count > 0
          ? `<div class="today-total">${formatIDR(today.total)}</div>
             <div class="card-label">${today.count} pengeluaran</div>`
          : `<div class="card-label">Belum ada pengeluaran hari ini</div>`
      })}
    </div>
  `;
}
