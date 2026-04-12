import { TabBar } from '../components/tab-bar.js';

const ROUTES = {
  '/': () => import('../pages/dashboard.js').then(m => m.initDashboard()),
  '/add': () => import('../pages/add-expense.js').then(m => m.initAddExpense()),
  '/history': () => import('../pages/history.js').then(m => m.initHistory()),
  '/budgets': () => import('../pages/budgets.js').then(m => m.initBudgets()),
  '/reports': () => import('../pages/reports.js').then(m => m.initReports()),
};

let currentPath = '/';

export async function navigate(path) {
  currentPath = path;

  // Update tab bar
  const tabBar = document.getElementById('tab-bar');
  if (tabBar) tabBar.outerHTML = TabBar(path);
  else document.getElementById('app').insertAdjacentHTML('beforeend', TabBar(path));

  // Clear content
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">Memuat...</div>';

  // Run page init
  const route = ROUTES[path] || ROUTES['/'];
  try {
    await route();
  } catch (err) {
    console.error('Route error:', err);
    content.innerHTML = `<div class="page"><div class="error-msg">Gagal memuat halaman. Coba lagi.</div></div>`;
  }
}

// Make globally accessible
window.navigate = navigate;
