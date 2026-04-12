import { api } from '../core/api.js';
import { Card } from '../components/card.js';
import { formatIDR } from '../utils/formatters.js';

export async function initReports() {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">Memuat laporan...</div>';
  try {
    const [pie, trend, top] = await Promise.all([
      api.getReport('pie'),
      api.getReport('trend'),
      api.getReport('top', { limit: 5 }),
    ]);
    content.innerHTML = renderReports(pie, trend, top);
    renderCharts(pie, trend);
  } catch (err) {
    content.innerHTML = `<div class="page"><div class="error-msg">Gagal memuat laporan: ${err.message}</div></div>`;
  }
}

function renderReports(pie, trend, top) {
  return `
    <div class="page reports-page">
      <div class="section-title">Pengeluaran per Grup</div>
      ${Card({ content: '<canvas id="pie-chart" height="200"></canvas>' })}

      <div class="section-title">Trend Harian</div>
      ${Card({ content: '<canvas id="trend-chart" height="150"></canvas>' })}

      <div class="section-title">Top Kategori</div>
      ${Card({
        content: top.categories.map((c, i) => `
          <div class="top-cat-item">
            <span>${i + 1}. ${c.name}</span>
            <span>${formatIDR(c.total)}</span>
          </div>
        `).join('')
      })}
    </div>
  `;
}

function renderCharts(pie, trend) {
  if (!window.Chart) return;

  // Pie chart
  const pieCtx = document.getElementById('pie-chart');
  if (pieCtx && pie.labels?.length) {
    new Chart(pieCtx, {
      type: 'doughnut',
      data: { labels: pie.labels, datasets: [{ data: pie.data, backgroundColor: pie.colors }] },
      options: { plugins: { legend: { position: 'bottom' } }, cutout: '60%' },
    });
  }

  // Trend chart
  const trendCtx = document.getElementById('trend-chart');
  if (trendCtx && trend.dates?.length) {
    new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: trend.dates,
        datasets: [{
          data: trend.amounts,
          borderColor: getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim(),
          tension: 0.3,
          fill: false,
        }]
      },
      options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
    });
  }
}
