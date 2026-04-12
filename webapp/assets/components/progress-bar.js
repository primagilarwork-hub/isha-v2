/**
 * ProgressBar component
 * @param {Object} props
 * @param {number} props.percentage - 0-100+
 * @param {string} [props.variant] - ok|warning|danger|primary (auto-detect if not set)
 */
export function ProgressBar({ percentage, variant = null }) {
  const capped = Math.min(percentage, 100);
  const autoVariant = variant || (percentage >= 90 ? 'danger' : percentage >= 70 ? 'warning' : 'ok');
  return `
    <div class="progress-bar">
      <div class="progress-fill ${autoVariant}" style="width: ${capped}%"></div>
    </div>
  `;
}
