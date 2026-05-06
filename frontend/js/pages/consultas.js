import { apiGet } from '../api.js';
import { showToast } from '../toast.js';
import { jsonToTable } from '../utils.js';

const CONSULTAS = [
  { id: 'velocidad-geografica',  persona: 'P1', color: '#4f46e5', icon: '📍',
    titulo: 'Velocidad Geográfica',
    desc: 'Clientes con transacciones en 2+ países distintos',
    params: [{ name: 'min_paises', label: 'Mín. países', default: 2, type: 'number' }] },
  { id: 'anillos-fraude',        persona: 'P1', color: '#4f46e5', icon: '🔗',
    titulo: 'Anillos de Fraude',
    desc: 'Dispositivos compartidos entre múltiples clientes',
    params: [{ name: 'min_clientes', label: 'Mín. clientes', default: 2, type: 'number' }] },
  { id: 'cuentas-alto-riesgo',   persona: 'P2', color: '#16a34a', icon: '🏦',
    titulo: 'Cuentas de Alto Riesgo',
    desc: 'Cuentas con mayor volumen de transacciones sospechosas',
    params: [{ name: 'min_sospechosas', label: 'Mín. sospechosas', default: 3, type: 'number' }] },
  { id: 'comercios-sospechosos', persona: 'P2', color: '#16a34a', icon: '🏪',
    titulo: 'Comercios Sospechosos',
    desc: 'Ranking de comercios por transacciones fraudulentas',
    params: [{ name: 'limit', label: 'Límite', default: 20, type: 'number' }] },
  { id: 'resumen-mensual-fraude',persona: 'P3', color: '#d97706', icon: '📅',
    titulo: 'Resumen Mensual de Fraude',
    desc: 'Agregación temporal de transacciones sospechosas',
    params: [] },
  { id: 'paths-fraude',          persona: 'P3', color: '#d97706', icon: '🔀',
    titulo: 'Rutas de Fraude',
    desc: 'Cadenas de clientes conectados por TX y dispositivos',
    params: [{ name: 'limit', label: 'Límite', default: 15, type: 'number' }] },
];

export function render(container) {
  container.innerHTML = `
    <div class="page-header">
      <div class="icon-wrap" style="background:#1e293b"><i class="bi bi-terminal-fill"></i></div>
      <div><h2 class="mb-0">Consultas Cypher</h2><small class="text-muted">6 consultas de detección (2 por integrante)</small></div>
    </div>
    <div class="row g-3">
      ${CONSULTAS.map((q, i) => `
        <div class="col-md-6">
          <div class="card h-100" style="border-left:4px solid ${q.color}">
            <div class="d-flex align-items-center gap-2 mb-2">
              <span style="font-size:1.4rem">${q.icon}</span>
              <div>
                <h5 class="mb-0">${q.titulo}</h5>
                <span class="badge" style="background:${q.color};font-size:.65rem">${q.persona}</span>
              </div>
            </div>
            <p class="text-muted small mb-3">${q.desc}</p>
            ${q.params.map(p => `
              <div class="mb-2">
                <label>${p.label}</label>
                <input type="${p.type||'text'}" class="form-control" id="q-${i}-${p.name}" value="${p.default}">
              </div>`).join('')}
            <button class="btn btn-sm mt-auto" style="background:${q.color};color:#fff" data-qi="${i}">
              <i class="bi bi-play-fill me-1"></i>Ejecutar
            </button>
            <div id="q-res-${i}" class="result-box mt-3" style="display:none"></div>
          </div>
        </div>`).join('')}
    </div>`;
}

export async function mount() {
  document.querySelectorAll('[data-qi]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const i = Number(btn.dataset.qi);
      const q = CONSULTAS[i];
      const params = {};
      q.params.forEach(p => {
        const v = document.getElementById(`q-${i}-${p.name}`).value;
        params[p.name] = p.type === 'number' ? Number(v) : v;
      });
      btn.disabled = true;
      try {
        const rows = await apiGet(`/consultas/${q.id}`, params);
        const box = document.getElementById(`q-res-${i}`);
        box.style.display = 'block';
        box.innerHTML = jsonToTable(rows);
        showToast(`${rows.length} resultados`, 'success');
      } catch(e) {
        showToast(e.message, 'error');
      } finally { btn.disabled = false; }
    });
  });
}

export function destroy() {}
