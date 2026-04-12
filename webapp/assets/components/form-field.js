/**
 * FormField component (input + label + error)
 * @param {Object} props
 * @param {string} props.id
 * @param {string} props.label
 * @param {string} [props.type='text']
 * @param {string} [props.value]
 * @param {string} [props.placeholder]
 * @param {string} [props.hint]
 * @param {string} [props.error]
 * @param {string} [props.oninput]
 */
export function FormField({ id, label, type = 'text', value = '', placeholder = '', hint = '', error = '', oninput = '' }) {
  return `
    <div class="form-field">
      <label class="form-label" for="${id}">${label}</label>
      <input
        class="form-input"
        id="${id}"
        name="${id}"
        type="${type}"
        value="${value}"
        placeholder="${placeholder}"
        ${oninput ? `oninput="${oninput}"` : ''}
      />
      ${error ? `<div class="form-error">${error}</div>` : ''}
      ${hint ? `<div class="form-hint">${hint}</div>` : ''}
    </div>
  `;
}

/**
 * SelectField component
 */
export function SelectField({ id, label, options = [], value = '', onchange = '' }) {
  const opts = options.map(o => {
    const val = typeof o === 'string' ? o : o.value;
    const lbl = typeof o === 'string' ? o : o.label;
    return `<option value="${val}" ${val === value ? 'selected' : ''}>${lbl}</option>`;
  }).join('');
  return `
    <div class="form-field">
      <label class="form-label" for="${id}">${label}</label>
      <select class="form-select" id="${id}" name="${id}" ${onchange ? `onchange="${onchange}"` : ''}>
        ${opts}
      </select>
    </div>
  `;
}
