import { apiPost, apiPatch, apiDelete } from '../api.js';
import { showToast } from '../toast.js';

const TIPOS = [
  'POSEE','TIENE_TARJETA','REALIZO','ORIGEN','DESTINO','EN_COMERCIO',
  'USO_DISPOSITIVO','EN_UBICACION','COMPARTE_DISPOSITIVO','ASOCIADA_A','VIVE_EN','SIMILAR_A',
];

export function render(container) {
  container.innerHTML = `
    <div class="page-header">
      <div class="icon-wrap" style="background:#dc2626"><i class="bi bi-diagram-2-fill"></i></div>
      <div><h2 class="mb-0">Relaciones</h2><small class="text-muted">Gestión de los 12 tipos de relaciones</small></div>
    </div>

    <!-- Crear relación -->
    <div class="card mb-3">
      <h5 class="mb-3"><i class="bi bi-plus-circle me-2"></i>Crear relación</h5>
      <div class="row g-2">
        <div class="col-md-3">
          <label>Tipo de relación</label>
          <select id="rel-tipo" class="form-select">
            ${TIPOS.map(t => `<option value="${t}">${t}</option>`).join('')}
          </select>
        </div>
        <div class="col-md-2">
          <label>Label origen</label>
          <input type="text" id="rel-label-a" class="form-control" placeholder="Cliente">
        </div>
        <div class="col-md-2">
          <label>ID origen</label>
          <input type="text" id="rel-id-a" class="form-control" placeholder="CL-0001">
        </div>
        <div class="col-md-2">
          <label>Label destino</label>
          <input type="text" id="rel-label-b" class="form-control" placeholder="Cuenta">
        </div>
        <div class="col-md-2">
          <label>ID destino</label>
          <input type="text" id="rel-id-b" class="form-control" placeholder="CU-0001">
        </div>
        <div class="col-md-4">
          <label>Propiedades JSON</label>
          <input type="text" id="rel-props" class="form-control" placeholder='{"fechaAsignacion":"2024-01-01","esTitular":true}'>
        </div>
        <div class="col-12">
          <button class="btn btn-primary" id="btn-crear-rel">Crear relación</button>
        </div>
      </div>
      <div id="res-rel-crear" class="result-box mt-3" style="display:none"></div>
    </div>

    <!-- Gestionar propiedades de relación -->
    <div class="card mb-3">
      <h5 class="mb-3"><i class="bi bi-pencil me-2"></i>Gestionar propiedades de relación</h5>
      <div class="row g-2">
        <div class="col-md-2">
          <label>Tipo</label>
          <select id="mgmt-tipo" class="form-select">
            ${TIPOS.map(t => `<option value="${t}">${t}</option>`).join('')}
          </select>
        </div>
        <div class="col-md-2"><label>Label A</label><input type="text" id="mgmt-la" class="form-control" placeholder="Cliente"></div>
        <div class="col-md-2"><label>ID A</label><input type="text" id="mgmt-ida" class="form-control"></div>
        <div class="col-md-2"><label>Label B</label><input type="text" id="mgmt-lb" class="form-control" placeholder="Cuenta"></div>
        <div class="col-md-2"><label>ID B</label><input type="text" id="mgmt-idb" class="form-control"></div>
        <div class="col-md-3">
          <label>Props JSON (agregar/actualizar)</label>
          <input type="text" id="mgmt-props" class="form-control" placeholder='{"clave":"valor"}'>
        </div>
        <div class="col-md-3">
          <label>Props a eliminar (coma)</label>
          <input type="text" id="mgmt-del-keys" class="form-control" placeholder="prop1, prop2">
        </div>
        <div class="col-12 d-flex gap-2">
          <button class="btn btn-warning" id="btn-add-props-rel">Agregar props</button>
          <button class="btn btn-danger btn-sm" id="btn-del-props-rel">Eliminar props</button>
          <button class="btn btn-danger" id="btn-del-rel">Eliminar relación</button>
        </div>
      </div>
      <div id="res-rel-mgmt" class="result-box mt-3" style="display:none"></div>
    </div>`;
}

export async function mount() {
  document.getElementById('btn-crear-rel').addEventListener('click', async () => {
    const tipo = document.getElementById('rel-tipo').value;
    const labelA = document.getElementById('rel-label-a').value;
    const idA = document.getElementById('rel-id-a').value;
    const labelB = document.getElementById('rel-label-b').value;
    const idB = document.getElementById('rel-id-b').value;
    let props = {};
    try { props = JSON.parse(document.getElementById('rel-props').value || '{}'); } catch { return showToast('JSON inválido', 'error'); }
    try {
      const res = await apiPost('/relaciones/', { tipo, labelA, idA, labelB, idB, propiedades: props });
      _show('res-rel-crear', res, 'success');
      showToast('Relación creada', 'success');
    } catch(e) { _show('res-rel-crear', { error: e.message }, 'error'); showToast(e.message, 'error'); }
  });

  document.getElementById('btn-add-props-rel').addEventListener('click', async () => {
    try {
      const res = await apiPatch('/relaciones/propiedades', _mgmtBody());
      _show('res-rel-mgmt', res, 'success');
      showToast('Propiedades de relación actualizadas', 'success');
    } catch(e) { _show('res-rel-mgmt', { error: e.message }, 'error'); showToast(e.message, 'error'); }
  });

  document.getElementById('btn-del-props-rel').addEventListener('click', async () => {
    const keys = document.getElementById('mgmt-del-keys').value.split(',').map(s => s.trim()).filter(Boolean);
    try {
      const res = await apiDelete('/relaciones/propiedades', { ..._mgmtBody(false), propiedades: keys });
      _show('res-rel-mgmt', res, 'success');
      showToast('Props eliminadas', 'success');
    } catch(e) { _show('res-rel-mgmt', { error: e.message }, 'error'); showToast(e.message, 'error'); }
  });

  document.getElementById('btn-del-rel').addEventListener('click', async () => {
    if (!confirm('¿Eliminar esta relación?')) return;
    try {
      const res = await apiDelete('/relaciones/', _mgmtBody(false));
      _show('res-rel-mgmt', res, 'success');
      showToast('Relación eliminada', 'success');
    } catch(e) { _show('res-rel-mgmt', { error: e.message }, 'error'); showToast(e.message, 'error'); }
  });
}

export function destroy() {}

function _mgmtBody(includeProps = true) {
  let props = {};
  if (includeProps) {
    try { props = JSON.parse(document.getElementById('mgmt-props').value || '{}'); } catch { props = {}; }
  }
  return {
    tipo:   document.getElementById('mgmt-tipo').value,
    labelA: document.getElementById('mgmt-la').value,
    idA:    document.getElementById('mgmt-ida').value,
    labelB: document.getElementById('mgmt-lb').value,
    idB:    document.getElementById('mgmt-idb').value,
    propiedades: props,
  };
}

function _show(id, data, type) {
  const el = document.getElementById(id);
  el.style.display = 'block';
  el.textContent = JSON.stringify(data, null, 2);
}
