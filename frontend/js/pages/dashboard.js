import { apiGet } from '../api.js';
import { fmt, scoreColor } from '../utils.js';

let _charts = [];

export function render(container) {
  container.innerHTML = `
    <div class="page-header">
      <div class="icon-wrap" style="background:#4f46e5"><i class="bi bi-speedometer2"></i></div>
      <div><h2 class="mb-0">Dashboard</h2><small class="text-muted">Métricas en tiempo real</small></div>
      <button class="btn btn-sm btn-secondary ms-auto" id="btn-refresh-dash"><i class="bi bi-arrow-clockwise me-1"></i>Actualizar</button>
    </div>

    <div class="row g-3 mb-4" id="stat-cards">
      ${['clientes','transacciones','sospechosas','relaciones'].map(k=>`
        <div class="col-6 col-xl-3">
          <div class="card stat-card" id="stat-${k}">
            <div class="icon" style="background:#ede9fe;color:#4f46e5"><i class="bi bi-hourglass-split"></i></div>
            <div><div class="val">—</div><div class="lbl">${k}</div></div>
          </div>
        </div>`).join('')}
    </div>

    <div class="row g-3 mb-4">
      <div class="col-md-8">
        <div class="card">
          <h5 class="mb-3"><i class="bi bi-graph-up-arrow me-2 text-primary"></i>TX sospechosas por mes</h5>
          <canvas id="chart-mes" height="130"></canvas>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <h5 class="mb-3"><i class="bi bi-pie-chart me-2 text-warning"></i>Nivel de riesgo</h5>
          <canvas id="chart-nivel" height="160"></canvas>
        </div>
      </div>
    </div>

    <div class="row g-3">
      <div class="col-md-6">
        <div class="card">
          <h5 class="mb-3"><i class="bi bi-bar-chart me-2 text-success"></i>Top países sospechosos</h5>
          <canvas id="chart-pais" height="180"></canvas>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <h5 class="mb-3"><i class="bi bi-clock-history me-2 text-info"></i>TX por hora del día</h5>
          <canvas id="chart-hora" height="180"></canvas>
        </div>
      </div>
    </div>`;

  document.getElementById('btn-refresh-dash').addEventListener('click', mount);
}

export async function mount() {
  destroy();
  try {
    const d = await apiGet('/dashboard/metricas');
    _renderStats(d);
    _renderCharts(d);
  } catch(e) {
    document.getElementById('stat-cards').innerHTML =
      `<div class="col-12"><p class="text-danger">Error cargando métricas: ${e.message}</p></div>`;
  }
}

export function destroy() {
  _charts.forEach(c => c.destroy());
  _charts = [];
}

function _renderStats(d) {
  const c = d.conteos || {};
  const s = d.sospechosas || {};

  const configs = [
    { id: 'clientes',      val: c.clientes || 0,           icon: 'bi-people-fill',       color: '#4f46e5', bg: '#ede9fe', lbl: 'Clientes' },
    { id: 'transacciones', val: c.transacciones || 0,      icon: 'bi-credit-card-2-front',color: '#0891b2', bg: '#e0f2fe', lbl: 'Transacciones' },
    { id: 'sospechosas',   val: s.totalSospechosas || 0,   icon: 'bi-shield-exclamation', color: '#dc2626', bg: '#fee2e2', lbl: 'Sospechosas' },
    { id: 'relaciones',    val: c.relaciones || 0,         icon: 'bi-diagram-3-fill',     color: '#16a34a', bg: '#dcfce7', lbl: 'Relaciones' },
  ];
  configs.forEach(({ id, val, icon, color, bg, lbl }) => {
    const el = document.getElementById(`stat-${id}`);
    if (!el) return;
    el.style.borderLeftColor = color;
    el.innerHTML = `
      <div class="icon" style="background:${bg};color:${color}"><i class="bi ${icon}"></i></div>
      <div><div class="val">${Number(val).toLocaleString()}</div><div class="lbl">${lbl}</div></div>`;
  });
}

function _renderCharts(d) {
  const Chart = window.Chart;
  if (!Chart) return;

  // Línea: TX por mes
  const mes = (d.porMes || []).slice(-12);
  _charts.push(new Chart(document.getElementById('chart-mes'), {
    type: 'line',
    data: {
      labels: mes.map(r => `${r.anio}-${String(r.mes).padStart(2,'0')}`),
      datasets: [
        { label: 'Total', data: mes.map(r => r.total),       borderColor: '#4f46e5', backgroundColor: 'rgba(79,70,229,.08)', fill: true, tension: .4 },
        { label: 'Sospechosas', data: mes.map(r => r.sospechosas), borderColor: '#dc2626', backgroundColor: 'rgba(220,38,38,.08)', fill: true, tension: .4 },
      ],
    },
    options: { plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true } } },
  }));

  // Donut: nivel riesgo
  const niv = d.porNivel || [];
  const colMap = { alto: '#dc2626', medio: '#d97706', bajo: '#16a34a' };
  _charts.push(new Chart(document.getElementById('chart-nivel'), {
    type: 'doughnut',
    data: {
      labels: niv.map(r => r.nivel),
      datasets: [{ data: niv.map(r => r.cantidad), backgroundColor: niv.map(r => colMap[r.nivel] || '#94a3b8') }],
    },
    options: { plugins: { legend: { position: 'bottom' } }, cutout: '60%' },
  }));

  // Barra: países
  const pais = d.porPais || [];
  _charts.push(new Chart(document.getElementById('chart-pais'), {
    type: 'bar',
    data: {
      labels: pais.map(r => r.pais),
      datasets: [{ label: 'TX sospechosas', data: pais.map(r => r.cantidad), backgroundColor: '#4f46e5' }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } }, indexAxis: 'y' },
  }));

  // Barras: horas
  const hora = d.porHora || [];
  _charts.push(new Chart(document.getElementById('chart-hora'), {
    type: 'bar',
    data: {
      labels: hora.map(r => `${r.hora}h`),
      datasets: [
        { label: 'Total',       data: hora.map(r => r.total),       backgroundColor: 'rgba(79,70,229,.3)' },
        { label: 'Sospechosas', data: hora.map(r => r.sospechosas), backgroundColor: '#dc2626' },
      ],
    },
    options: { plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true } } },
  }));
}
