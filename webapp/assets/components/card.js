/**
 * Card component
 * @param {Object} props
 * @param {string} [props.title]
 * @param {string} props.content - HTML content
 * @param {string} [props.className]
 */
export function Card({ title = '', content, className = '' }) {
  return `
    <div class="card ${className}">
      ${title ? `<div class="card-title">${title}</div>` : ''}
      ${content}
    </div>
  `;
}
