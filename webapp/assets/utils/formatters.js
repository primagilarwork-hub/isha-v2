/**
 * Format number as Indonesian Rupiah
 * @param {number} amount
 * @returns {string} e.g. "Rp 25.000"
 */
export function formatIDR(amount) {
  return 'Rp ' + Math.round(amount).toLocaleString('id-ID');
}

/**
 * Format date string to human-readable
 * @param {string} dateStr - YYYY-MM-DD
 * @returns {string} e.g. "7 Apr 2026"
 */
export function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
}

/**
 * Format date relative to today
 * @param {string} dateStr
 * @returns {string} "Hari Ini" | "Kemarin" | "7 Apr 2026"
 */
export function formatDateRelative(dateStr) {
  const today = new Date().toISOString().slice(0, 10);
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
  if (dateStr === today) return 'Hari Ini';
  if (dateStr === yesterday) return 'Kemarin';
  return formatDate(dateStr);
}

/**
 * Format percentage safely
 * @param {number} value
 * @param {number} total
 * @returns {number}
 */
export function formatPct(value, total) {
  if (!total || total <= 0) return 0;
  return Math.round((value / total) * 100);
}
