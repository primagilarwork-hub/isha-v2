const TABS = [
  { path: '/', icon: '🏠', label: 'Home' },
  { path: '/add', icon: '➕', label: 'Tambah' },
  { path: '/history', icon: '📋', label: 'Riwayat' },
  { path: '/budgets', icon: '💰', label: 'Budget' },
  { path: '/reports', icon: '📊', label: 'Laporan' },
];

export function TabBar(currentPath) {
  const items = TABS.map(tab => `
    <button class="tab-item ${tab.path === currentPath ? 'active' : ''}"
            onclick="navigate('${tab.path}')">
      <span class="tab-icon">${tab.icon}</span>
      <span>${tab.label}</span>
    </button>
  `).join('');
  return `<nav class="tab-bar">${items}</nav>`;
}
