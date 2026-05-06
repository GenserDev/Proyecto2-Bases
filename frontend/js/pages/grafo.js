import { apiGet } from '../api.js';
import { showToast } from '../toast.js';

let _network = null;

export function render(container) {
  container.innerHTML = `
    <div class="page-header">
      <div class="icon-wrap" style="background:#7c3aed"><i class="bi bi-diagram-3-fill"></i></div>
      <div><h2 class="mb-0">Visualización del Grafo</h2><small class="text-muted">Explora el grafo interactivamente</small></div>
    </div>
    <div class="card mb-3">
      <div class="row g-2 align-items-end">
        <div class="col-md-4">
          <label>Buscar nodo (ID de cliente, TX, cuenta…)</label>
          <input type="text" id="grafo-id" class="form-control" placeholder="ej. CL-0001 o TX-0042">
        </div>
        <div class="col-auto">
          <label>Saltos</label>
          <select id="grafo-saltos" class="form-select" style="width:80px">
            <option value="1">1</option>
            <option value="2" selected>2</option>
            <option value="3">3</option>
          </select>
        </div>
        <div class="col-auto">
          <button class="btn btn-primary" id="btn-buscar-grafo"><i class="bi bi-search me-1"></i>Buscar</button>
          <button class="btn btn-secondary ms-2" id="btn-overview">Vista general</button>
        </div>
      </div>
      <!-- Leyenda -->
      <div class="mt-3 d-flex flex-wrap gap-2" id="leyenda">
        ${[
          ['Cliente','#4f46e5'],['Cuenta','#16a34a'],['Tarjeta','#0891b2'],
          ['Transaccion','#d97706'],['Comercio','#7c3aed'],
          ['Dispositivo','#64748b'],['Ubicacion','#0d9488'],
          ['TX Sospechosa','#dc2626'],
        ].map(([l,c]) => `<span class="badge" style="background:${c}">${l}</span>`).join('')}
      </div>
    </div>
    <div class="card p-0" style="height:560px;overflow:hidden;position:relative">
      <div id="grafo-canvas" style="width:100%;height:100%"></div>
      <div id="grafo-loading" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.8);display:none">
        <span class="spinner-border text-primary"></span>
      </div>
      <!-- Panel de propiedades -->
      <div id="node-panel" style="position:absolute;top:12px;right:12px;width:260px;background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;font-size:.78rem;display:none;max-height:90%;overflow-y:auto;box-shadow:0 4px 16px rgba(0,0,0,.12)">
        <div class="d-flex justify-content-between mb-2">
          <strong id="panel-title">Propiedades</strong>
          <button class="btn btn-sm btn-secondary py-0" id="btn-close-panel">×</button>
        </div>
        <div id="panel-content"></div>
      </div>
    </div>`;
}

export async function mount() {
  // Cargar vis-network si no está
  if (!window.vis) {
    await _loadScript('https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js');
    await _loadStyle('https://unpkg.com/vis-network@9.1.9/dist/dist/vis-network.min.css');
  }

  document.getElementById('btn-buscar-grafo').addEventListener('click', async () => {
    const id = document.getElementById('grafo-id').value.trim();
    if (!id) { showToast('Ingresa un ID', 'warning'); return; }
    const saltos = document.getElementById('grafo-saltos').value;
    await _drawGraph(`/grafo/subgrafo/${encodeURIComponent(id)}?saltos=${saltos}`);
  });

  document.getElementById('btn-overview').addEventListener('click', () => _drawGraph('/grafo/overview'));
  document.getElementById('btn-close-panel').addEventListener('click', () => {
    document.getElementById('node-panel').style.display = 'none';
  });

  // Si viene parámetro en hash (#/grafo?id=...)
  const params = new URLSearchParams(window.location.hash.split('?')[1] || '');
  const id = params.get('id');
  if (id) {
    document.getElementById('grafo-id').value = id;
    await _drawGraph(`/grafo/subgrafo/${encodeURIComponent(id)}?saltos=2`);
  } else {
    await _drawGraph('/grafo/overview');
  }
}

export function destroy() {
  if (_network) { _network.destroy(); _network = null; }
}

async function _drawGraph(endpoint) {
  const loading = document.getElementById('grafo-loading');
  if (loading) loading.style.display = 'flex';
  try {
    const data = await apiGet(endpoint);
    if (!data.nodes || !data.nodes.length) {
      showToast('Sin resultados para ese nodo', 'warning');
      return;
    }
    const container = document.getElementById('grafo-canvas');
    if (_network) _network.destroy();

    const dataset = {
      nodes: new window.vis.DataSet(data.nodes),
      edges: new window.vis.DataSet(data.edges),
    };
    _network = new window.vis.Network(container, dataset, {
      nodes: { shape: 'dot', size: 18, font: { size: 11, color: '#1a202c' }, borderWidth: 2 },
      edges: { font: { size: 9, align: 'middle' }, smooth: { type: 'curvedCW', roundness: .2 } },
      physics: { stabilization: { iterations: 150 }, barnesHut: { gravitationalConstant: -3000 } },
      interaction: { hover: true, tooltipDelay: 200 },
    });

    _network.on('click', params => {
      if (!params.nodes.length) return;
      const node = dataset.nodes.get(params.nodes[0]);
      const panel = document.getElementById('node-panel');
      document.getElementById('panel-title').textContent = node.group || 'Nodo';
      document.getElementById('panel-content').innerHTML = `<pre style="font-size:.72rem;white-space:pre-wrap">${node.title || ''}</pre>`;
      panel.style.display = 'block';
    });
  } catch(e) {
    showToast('Error cargando grafo: ' + e.message, 'error');
  } finally {
    if (loading) loading.style.display = 'none';
  }
}

function _loadScript(src) {
  return new Promise((res, rej) => {
    const s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = rej;
    document.head.appendChild(s);
  });
}
function _loadStyle(href) {
  const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = href;
  document.head.appendChild(l);
}
