import { apiGet } from '../api.js';
import { showToast } from '../toast.js';

const BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : window.location.origin;

const UPLOADS = [
  { id: 'clientes',     label: 'Clientes',        endpoint: '/csv/clientes',     icon: 'bi-people',        color: '#4f46e5' },
  { id: 'cuentas',      label: 'Cuentas',          endpoint: '/csv/cuentas',      icon: 'bi-bank',          color: '#16a34a' },
  { id: 'transacciones',label: 'Transacciones',    endpoint: '/csv/transacciones',icon: 'bi-credit-card',   color: '#d97706' },
  { id: 'relaciones',   label: 'Relaciones POSEE', endpoint: '/csv/relaciones',   icon: 'bi-diagram-2',     color: '#dc2626' },
];

export function render(container) {
  container.innerHTML = `
    <div class="page-header">
      <div class="icon-wrap" style="background:#475569"><i class="bi bi-file-earmark-arrow-up-fill"></i></div>
      <div><h2 class="mb-0">Carga de CSV</h2><small class="text-muted">Importar datos desde archivos CSV</small></div>
    </div>

    <div class="card mb-3">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="mb-0">Estado de la base de datos</h5>
        <button class="btn btn-sm btn-secondary" id="btn-estado"><i class="bi bi-arrow-clockwise"></i></button>
      </div>
      <div id="estado-box" class="text-muted small">Cargando...</div>
    </div>

    <div class="row g-3">
      ${UPLOADS.map(u => `
        <div class="col-md-6">
          <div class="card" style="border-left:4px solid ${u.color}">
            <div class="d-flex align-items-center gap-2 mb-3">
              <i class="bi ${u.icon} fs-4" style="color:${u.color}"></i>
              <h5 class="mb-0">${u.label}</h5>
            </div>
            <input type="file" accept=".csv" class="form-control mb-2" id="file-${u.id}">
            <button class="btn btn-sm" style="background:${u.color};color:#fff" data-endpoint="${u.endpoint}" data-file="${u.id}">
              <i class="bi bi-upload me-1"></i>Subir CSV
            </button>
            <div id="res-${u.id}" class="result-box mt-2" style="display:none"></div>
          </div>
        </div>`).join('')}
    </div>`;
}

export async function mount() {
  _loadEstado();

  document.getElementById('btn-estado').addEventListener('click', _loadEstado);

  document.querySelectorAll('[data-endpoint]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const fileId = btn.dataset.file;
      const endpoint = btn.dataset.endpoint;
      const fileInput = document.getElementById(`file-${fileId}`);
      if (!fileInput.files.length) { showToast('Selecciona un archivo CSV', 'warning'); return; }

      btn.disabled = true;
      const fd = new FormData();
      fd.append('file', fileInput.files[0]);

      try {
        const res = await fetch(BASE + endpoint, { method: 'POST', body: fd });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || res.statusText);
        const box = document.getElementById(`res-${fileId}`);
        box.style.display = 'block';
        box.textContent = JSON.stringify(data, null, 2);
        showToast(`Cargado: ${JSON.stringify(data)}`, 'success', 5000);
        _loadEstado();
      } catch(e) {
        showToast('Error: ' + e.message, 'error');
      } finally { btn.disabled = false; }
    });
  });
}

export function destroy() {}

async function _loadEstado() {
  const box = document.getElementById('estado-box');
  if (!box) return;
  try {
    const d = await apiGet('/csv/estado');
    box.innerHTML = `<div class="row g-2">
      ${Object.entries(d).map(([k, v]) => `
        <div class="col-6 col-md-3">
          <div class="card text-center py-2">
            <div class="fw-bold">${Number(v).toLocaleString()}</div>
            <div class="text-muted small">${k}</div>
          </div>
        </div>`).join('')}
    </div>`;
  } catch(e) {
    box.innerHTML = `<span class="text-danger">Error: ${e.message}</span>`;
  }
}
