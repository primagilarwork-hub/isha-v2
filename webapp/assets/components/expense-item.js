import { formatIDR } from '../utils/formatters.js';

/**
 * ExpenseItem component
 * @param {Object} props
 * @param {number} props.id
 * @param {string} props.description
 * @param {string} props.category
 * @param {string} props.budget_group
 * @param {number} props.amount
 * @param {string} props.expense_date
 * @param {string} [props.user_name]
 */
export function ExpenseItem({ id, description, category, budget_group, amount, expense_date, user_name = '' }) {
  return `
    <div class="expense-item" data-id="${id}" onclick="window.onExpenseClick && window.onExpenseClick(${id})">
      <div class="expense-item-left">
        <div class="expense-item-desc">${description || category}</div>
        <div class="expense-item-meta">${budget_group} · ${category}${user_name ? ` · ${user_name}` : ''}</div>
      </div>
      <div class="expense-item-amount">${formatIDR(amount)}</div>
    </div>
  `;
}
