import { Button } from './button.js';

/**
 * Modal component (bottom sheet)
 * @param {Object} props
 * @param {string} props.title
 * @param {string} props.content - HTML content
 * @param {string} [props.confirmLabel='OK']
 * @param {string} [props.cancelLabel='Batal']
 * @param {string} [props.onConfirm] - JS expression
 * @param {string} [props.onCancel='closeModal()']
 */
export function Modal({ title, content, confirmLabel = 'OK', cancelLabel = 'Batal', onConfirm = '', onCancel = 'closeModal()' }) {
  return `
    <div class="modal-overlay" id="modal-overlay" onclick="if(event.target===this) closeModal()">
      <div class="modal">
        <div class="modal-title">${title}</div>
        ${content}
        <div class="modal-actions">
          ${Button({ label: cancelLabel, variant: 'secondary', onclick: onCancel, fullWidth: true })}
          ${onConfirm ? Button({ label: confirmLabel, variant: 'primary', onclick: onConfirm, fullWidth: true }) : ''}
        </div>
      </div>
    </div>
  `;
}

export function showModal(html) {
  const existing = document.getElementById('modal-overlay');
  if (existing) existing.remove();
  document.body.insertAdjacentHTML('beforeend', html);
}

export function closeModal() {
  const overlay = document.getElementById('modal-overlay');
  if (overlay) overlay.remove();
}

// Make globally accessible
window.closeModal = closeModal;
