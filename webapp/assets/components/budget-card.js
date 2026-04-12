import { ProgressBar } from './progress-bar.js';
import { formatIDR } from '../utils/formatters.js';

/**
 * BudgetCard component
 * @param {Object} props
 * @param {string} props.name
 * @param {number} props.amount
 * @param {number} props.spent
 * @param {number} props.percentage
 * @param {string} props.status - ok|warning|danger
 * @param {string[]} [props.categories]
 */
export function BudgetCard({ name, amount, spent, percentage, status, categories = [] }) {
  const remaining = amount - spent;
  const cats = categories.slice(0, 4).join(', ') + (categories.length > 4 ? ` +${categories.length - 4}` : '');
  return `
    <div class="budget-card">
      <div class="budget-card-header">
        <span class="budget-card-name">${name}</span>
        <span class="budget-card-pct ${status}">${percentage}%</span>
      </div>
      ${ProgressBar({ percentage, variant: status })}
      <div class="budget-card-amounts">
        <span>${formatIDR(spent)} terpakai</span>
        <span>sisa ${formatIDR(remaining)}</span>
      </div>
      ${cats ? `<div class="budget-card-categories">${cats}</div>` : ''}
    </div>
  `;
}
