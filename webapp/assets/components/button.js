/**
 * Button component
 * @param {Object} props
 * @param {string} props.label
 * @param {string} [props.variant='primary'] - primary|secondary|danger|ghost
 * @param {string} [props.size='md'] - sm|md|lg
 * @param {boolean} [props.fullWidth=false]
 * @param {string} [props.icon]
 * @param {string} [props.onclick]
 * @param {string} [props.type='button']
 */
export function Button({ label, variant = 'primary', size = 'md', fullWidth = false, icon = '', onclick = '', type = 'button' }) {
  const classes = ['btn', `btn-${variant}`, `btn-${size}`, fullWidth ? 'btn-full' : ''].filter(Boolean).join(' ');
  return `
    <button type="${type}" class="${classes}" ${onclick ? `onclick="${onclick}"` : ''}>
      ${icon ? `<span class="btn-icon">${icon}</span>` : ''}
      <span>${label}</span>
    </button>
  `;
}
