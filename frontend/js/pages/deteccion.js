import { apiGet, apiPost } from '../api.js';
import { showToast } from '../toast.js';
import { fmt, scoreColor, jsonToTable } from '../utils.js';

export function render(container) {
  container.innerHTML = `
    <div class="page-header">
      <div class="icon-wrap" style="background:#dc2626"><i class="bi bi-shield-exclamation"></i></div>
      <div><h2 class="mb-0">Motor de Detección de Fraude</h2><small class="text-muted">Detección automática por algoritmos</small></div>
    </div>

    <!-- Acciones del motor -->
    <div class="card mb-3">
      <h5 class="mb-3">Algoritmos de detección</h5>
      <div class="d-flex flex-wrap gap-2 mb-3">
        <button class="btn btn-danger" id="btn-pipeline"><i class="bi bi-play-fill me-1"></i>Ejecutar pipeline completo</button>
        <button class="btn btn-secondary btn-sm" data-algo="velocidad">📍 Velocidad geográfica</button>
        <button class="btn btn-secondary btn-sm" data-algo="anillos">🔗 Anillos de fraude</button>
        <button class="btn btn-secondary btn-sm" data-algo="mula">💸 Cuentas mula</button>
        <button class="btn btn-secondary btn-sm" data-algo="outliers">📊 Outliers de monto</button>
        <button class="btn btn-secondary btn-sm" data-algo="horarios">🌙 Horarios anómalos</button>
      </div>
      <div id="pipeline-status" class="text-muted small">Sin ejecutar aún. Presiona "Ejecutar pipeline completo" para iniciar la detección automática.</div>
    </div>

    <!-- Estadísticas -->
    <div class="card mb-3">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">Estadísticas globales</h5>
        <button class="btn btn-sm btn-secondary" id="btn-stats"><i class="bi bi-arrow-clockwise"></i></button>
      </div>
      <div id="stats-box" class="text-muted small">Cargando...</div>
    </div>

    <!-- Alertas -->
    <div class="card mb-3">
      <h5 class="mb-3">Alertas de fraude</h5>
      <div class="row g-2 mb-3">
        <div class="col-auto">
          <label>Score mínimo</label>
          <input type="range" min="0" max="1" step="0.05" value="0.5" id="slider-score" class="form-range" style="width:140px">
          <span id="score-val" class="badge bg-danger ms-1">0.50</span>
        </div>
        <div class="col-auto">
          <label>País</label>
          <input type="text" id="filtro-pais" class="form-control form-control-sm" placeholder="Todos" style="width:120px">
        </div>
        <div class="col-auto">
          <label>Fecha inicio</label>
          <input type="date" id="filtro-fecha-ini" class="form-control form-control-sm">
        </div>
        <div class="col-auto">
          <label>Fecha fin</label>
          <input type="date" id="filtro-fecha-fin" class="form-control form-control-sm">
        </div>
        <div class="col-auto d-flex align-items-end">
          <button class="btn btn-primary btn-sm" id="btn-alertas"><i class="bi bi-search me-1"></i>Buscar</button>
        </div>
      </div>
      <div id="alertas-box">Presiona "Buscar" para ver alertas.</div>
    </div>

    <!-- Anillos -->
    <div class="card mb-3">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">Anillos de fraude detectados</h5>
        <button class="btn btn-sm btn-secondary" id="btn-anillos"><i class="bi bi-arrow-clockwise"></i></button>
      </div>
      <div id="anillos-box" class="text-muted small">Presiona actualizar.</div>
    </div>

    <!-- Clientes riesgo -->
    <div class="card">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">Clientes de mayor riesgo</h5>
        <button class="btn btn-sm btn-secondary" id="btn-clientes-riesgo"><i class="bi bi-arrow-clockwise"></i></button>
      </div>
      <div id="clientes-riesgo-box" class="text-muted small">Presiona actualizar.</div>
    </div>`;
}

export async function mount() {
  _loadStats();

  document.getElementById('btn-pipeline').addEventListener('click', async () => {
    const btn = document.getElementById('btn-pipeline');
    const status = document.getElementById('pipeline-status');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Ejecutando...';
    status.innerHTML = '<span class="text-warning">⏳ Ejecutando pipeline… puede tardar 10-30 segundos.</span>';
    try {
      const res = await apiPost('/deteccion/recalcular');
      status.innerHTML = `<span class="text-success">✅ Pipeline completado.</span><pre class="mt-2 result-box">${JSON.stringify(res, null, 2)}</pre>`;
      showToast('Pipeline ejecutado correctamente', 'success');
      _loadStats();
    } catch(e) {
      status.innerHTML = `<span class="text-danger">❌ Error: ${e.message}</span>`;
      showToast('Error ejecutando pipeline: ' + e.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-play-fill me-1"></i>Ejecutar pipeline completo';
    }
  });

  document.querySelectorAll('[data-algo]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const algo = btn.dataset.algo;
      btn.disabled = true;
      try {
        const res = await apiPost(`/deteccion/${algo}`);
        showToast(`${algo}: ${JSON.stringify(res)}`, 'info', 5000);
        _loadStats();
      } catch(e) {
        showToast('Error: ' + e.message, 'error');
      } finally { btn.disabled = false; }
    });
  });

  document.getElementById('slider-score').addEventListener('input', e => {
    document.getElementById('score-val').textContent = Number(e.target.value).toFixed(2);
  });

  document.getElementById('btn-alertas').addEventListener('click', _loadAlertas);
  document.getElementById('btn-stats').addEventListener('click', _loadStats);
  document.getElementById('btn-anillos').addEventListener('click', _loadAnillos);
  document.getElementById('btn-clientes-riesgo').addEventListener('click', _loadClientesRiesgo);
}

export function destroy() {}

async function _loadStats() {
  const box = document.getElementById('stats-box');
  if (!box) return;
  try {
    const d = await apiGet('/deteccion/estadisticas');
    const tx = d.transacciones || {};
    box.innerHTML = `
      <div class="row g-3">
        <div class="col-6 col-md-3"><div class="card text-center py-2">
          <div class="fw-bold fs-5">${tx.totalTransacciones || 0}</div><div class="text-muted small">Total TX</div>
        </div></div>
        <div class="col-6 col-md-3"><div class="card text-center py-2" style="border-left:4px solid #dc2626">
          <div class="fw-bold fs-5 text-danger">${tx.sospechosas || 0}</div><div class="text-muted small">Sospechosas</div>
        </div></div>
        <div class="col-6 col-md-3"><div class="card text-center py-2" style="border-left:4px solid #d97706">
          <div class="fw-bold fs-5">${d.anillosActivos || 0}</div><div class="text-muted small">Anillos</div>
        </div></div>
        <div class="col-6 col-md-3"><div class="card text-center py-2" style="border-left:4px solid #0891b2">
          <div class="fw-bold fs-5">${d.cuentasMula || 0}</div><div class="text-muted small">Cuentas mula</div>
        </div></div>
      </div>
      <div class="mt-2 text-muted small">Score promedio fraude: <strong>${fmt.score(tx.avgFraudScore)}</strong> | Monto en fraude: <strong>${fmt.money(tx.montoFraude)}</strong></div>`;
  } catch(e) {
    box.innerHTML = `<span class="text-danger">Error: ${e.message}</span>`;
  }
}

async function _loadAlertas() {
  const box = document.getElementById('alertas-box');
  box.innerHTML = '<span class="text-muted">Cargando...</span>';
  const minScore = document.getElementById('slider-score').value;
  const pais = document.getElementById('filtro-pais').value;
  const fechaInicio = document.getElementById('filtro-fecha-ini').value;
  const fechaFin = document.getElementById('filtro-fecha-fin').value;
  try {
    const rows = await apiGet('/deteccion/alertas', { minScore, pais, fechaInicio, fechaFin, limit: 50 });
    if (!rows.length) { box.innerHTML = '<p class="text-muted small">Sin alertas con ese filtro.</p>'; return; }
    box.innerHTML = `<div class="table-responsive"><table class="table table-hover table-sm">
      <thead><tr><th>TX</th><th>Score</th><th>Nivel</th><th>Monto</th><th>Cliente</th><th>País</th><th>Fecha</th><th>Ver</th></tr></thead>
      <tbody>${rows.map(r => `<tr>
        <td><code>${r.transaccionId}</code></td>
        <td>
          <div class="score-bar"><div class="score-fill" style="width:${(r.fraudScore||0)*100}%;background:${scoreColor(r.fraudScore||0)}"></div></div>
          <small>${fmt.score(r.fraudScore)}</small>
        </td>
        <td>${fmt.nivel(r.nivelRiesgo)}</td>
        <td>${fmt.money(r.monto)}</td>
        <td>${r.clienteNombre||''} ${r.clienteApellido||''}</td>
        <td>${r.ciudad||''}, ${r.pais||''}</td>
        <td>${fmt.date(r.fecha)}</td>
        <td><a href="#/grafo?id=${r.transaccionId}" class="btn btn-sm btn-secondary"><i class="bi bi-diagram-3"></i></a></td>
      </tr>`).join('')}</tbody>
    </table></div>`;
  } catch(e) {
    box.innerHTML = `<span class="text-danger">Error: ${e.message}</span>`;
  }
}

async function _loadAnillos() {
  const box = document.getElementById('anillos-box');
  box.innerHTML = '<span class="text-muted">Cargando...</span>';
  try {
    const rows = await apiGet('/deteccion/anillos');
    if (!rows.length) { box.innerHTML = '<p class="text-muted small">No hay anillos detectados. Ejecuta el pipeline primero.</p>'; return; }
    box.innerHTML = jsonToTable(rows);
  } catch(e) {
    box.innerHTML = `<span class="text-danger">Error: ${e.message}</span>`;
  }
}

async function _loadClientesRiesgo() {
  const box = document.getElementById('clientes-riesgo-box');
  box.innerHTML = '<span class="text-muted">Cargando...</span>';
  try {
    const rows = await apiGet('/deteccion/clientes-riesgo', { top: 20 });
    if (!rows.length) { box.innerHTML = '<p class="text-muted small">Sin datos. Ejecuta el pipeline primero.</p>'; return; }
    box.innerHTML = `<div class="table-responsive"><table class="table table-hover table-sm">
      <thead><tr><th>Cliente</th><th>Total TX</th><th>Sospechosas</th><th>Score max</th><th>Score prom.</th><th>Monto total</th><th>Ver grafo</th></tr></thead>
      <tbody>${rows.map(r => `<tr>
        <td><strong>${r.nombre} ${r.apellido}</strong><br><small class="text-muted">${r.clienteId}</small></td>
        <td>${r.totalTx}</td>
        <td><span class="badge bg-danger">${r.sospechosas}</span></td>
        <td>
          <div class="score-bar"><div class="score-fill" style="width:${(r.maxScore||0)*100}%;background:${scoreColor(r.maxScore||0)}"></div></div>
          <small>${fmt.score(r.maxScore)}</small>
        </td>
        <td>${fmt.score(r.avgScore)}</td>
        <td>${fmt.money(r.montoTotal)}</td>
        <td><a href="#/grafo?id=${r.clienteId}" class="btn btn-sm btn-secondary"><i class="bi bi-diagram-3"></i></a></td>
      </tr>`).join('')}</tbody>
    </table></div>`;
  } catch(e) {
    box.innerHTML = `<span class="text-danger">Error: ${e.message}</span>`;
  }
}
