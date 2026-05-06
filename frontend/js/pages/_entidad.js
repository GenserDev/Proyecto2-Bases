/**
 * Fábrica de páginas para entidades CRUD genéricas.
 * Cada entidad importa esto y llama createPage(config).
 */
import { apiGet, apiPost, apiPut, apiPatch, apiDelete } from '../api.js';
import { showToast } from '../toast.js';
import { jsonToTable } from '../utils.js';

export function createPage({ titulo, icon, color, prefix, idField, campos, filtrosCampos = [] }) {

  function render(container) {
    container.innerHTML = `
      <div class="page-header">
        <div class="icon-wrap" style="background:${color}"><i class="bi ${icon}"></i></div>
        <div><h2 class="mb-0">${titulo}</h2></div>
      </div>

      <!-- Crear 1 label -->
      <div class="card mb-3">
        <h5 class="mb-3"><i class="bi bi-plus-circle me-2"></i>Crear (1 label)</h5>
        <div class="row g-2" id="form-crear">
          ${campos.map(c => `
            <div class="col-md-4">
              <label>${c.label}</label>
              <input type="${c.type||'text'}" class="form-control" id="c-${c.name}" placeholder="${c.placeholder||c.label}" ${c.required?'required':''}>
            </div>`).join('')}
          <div class="col-12 mt-2">
            <button class="btn btn-primary" id="btn-crear">Crear ${titulo}</button>
            <button class="btn btn-secondary ms-2" id="btn-crear-multilabel">+ Crear con 2ª label</button>
            <input type="text" class="form-control d-inline-block ms-2" id="extra-label" placeholder="Label extra (ej. VIP)" style="width:160px">
          </div>
        </div>
        <div id="res-crear" class="result-box mt-3" style="display:none"></div>
      </div>

      <!-- Buscar / Listar -->
      <div class="card mb-3">
        <h5 class="mb-3"><i class="bi bi-search me-2"></i>Buscar / Listar</h5>
        <div class="row g-2 mb-3">
          <div class="col-md-3">
            <label>ID exacto</label>
            <input type="text" class="form-control" id="buscar-id" placeholder="${idField}">
          </div>
          ${filtrosCampos.map(f => `
            <div class="col-md-3">
              <label>${f.label}</label>
              <input type="text" class="form-control" id="filtro-${f.name}" placeholder="${f.placeholder||f.label}">
            </div>`).join('')}
          <div class="col-auto d-flex align-items-end gap-2">
            <button class="btn btn-primary" id="btn-buscar-id">Buscar por ID</button>
            <button class="btn btn-secondary" id="btn-listar">Listar</button>
            <button class="btn btn-secondary" id="btn-agregaciones">Agregaciones</button>
          </div>
        </div>
        <div id="res-lista"></div>
      </div>

      <!-- Editar propiedades -->
      <div class="card mb-3">
        <h5 class="mb-3"><i class="bi bi-pencil me-2"></i>Actualizar / Agregar propiedades</h5>
        <div class="row g-2">
          <div class="col-md-3">
            <label>ID del nodo</label>
            <input type="text" class="form-control" id="edit-id" placeholder="${idField}">
          </div>
          <div class="col-md-5">
            <label>Propiedades JSON <small class="text-muted">(ej. {"nombre":"Juan"})</small></label>
            <input type="text" class="form-control" id="edit-props" placeholder='{"clave":"valor"}'>
          </div>
          <div class="col-auto d-flex align-items-end gap-2">
            <button class="btn btn-warning" id="btn-actualizar">Actualizar</button>
            <button class="btn btn-secondary" id="btn-agregar-props">Agregar props</button>
          </div>
        </div>
        <div id="res-edit" class="result-box mt-3" style="display:none"></div>
      </div>

      <!-- Eliminar propiedades -->
      <div class="card mb-3">
        <h5 class="mb-3"><i class="bi bi-eraser me-2"></i>Eliminar propiedades</h5>
        <div class="row g-2">
          <div class="col-md-3">
            <label>ID del nodo</label>
            <input type="text" class="form-control" id="delprop-id" placeholder="${idField}">
          </div>
          <div class="col-md-5">
            <label>Propiedades a eliminar <small class="text-muted">(separadas por coma)</small></label>
            <input type="text" class="form-control" id="delprop-keys" placeholder="prop1, prop2">
          </div>
          <div class="col-auto d-flex align-items-end">
            <button class="btn btn-danger" id="btn-eliminar-props">Eliminar props</button>
          </div>
        </div>
        <div id="res-delprop" class="result-box mt-3" style="display:none"></div>
      </div>

      <!-- Eliminar nodo -->
      <div class="card">
        <h5 class="mb-3"><i class="bi bi-trash me-2"></i>Eliminar nodo</h5>
        <div class="row g-2">
          <div class="col-md-3">
            <label>ID del nodo</label>
            <input type="text" class="form-control" id="del-id" placeholder="${idField}">
          </div>
          <div class="col-md-5">
            <label>IDs múltiples <small class="text-muted">(separados por coma, para eliminar varios)</small></label>
            <input type="text" class="form-control" id="del-ids" placeholder="ID1, ID2, ID3">
          </div>
          <div class="col-auto d-flex align-items-end gap-2">
            <button class="btn btn-danger" id="btn-eliminar">Eliminar 1</button>
            <button class="btn btn-danger" id="btn-eliminar-bulk">Eliminar múltiples</button>
          </div>
        </div>
        <div id="res-del" class="result-box mt-3" style="display:none"></div>
      </div>`;
  }

  async function mount() {
    // Crear 1 label
    document.getElementById('btn-crear').addEventListener('click', async () => {
      const body = {};
      campos.forEach(c => {
        const v = document.getElementById(`c-${c.name}`).value;
        body[c.name] = c.type === 'number' ? Number(v) : c.type === 'checkbox' ? v === 'true' : v;
      });
      try {
        const res = await apiPost(`/${prefix}/`, body);
        _show('res-crear', res, 'success');
        showToast(`${titulo} creado`, 'success');
      } catch(e) { _show('res-crear', {error: e.message}, 'error'); showToast(e.message, 'error'); }
    });

    // Crear multilabel
    document.getElementById('btn-crear-multilabel').addEventListener('click', async () => {
      const body = {};
      campos.forEach(c => {
        const v = document.getElementById(`c-${c.name}`).value;
        body[c.name] = c.type === 'number' ? Number(v) : v;
      });
      const extraLabel = document.getElementById('extra-label').value || 'VIP';
      try {
        const res = await apiPost(`/${prefix}/multilabel?label_extra=${extraLabel}`, body);
        _show('res-crear', res, 'success');
        showToast(`${titulo} creado con label ${extraLabel}`, 'success');
      } catch(e) { _show('res-crear', {error: e.message}, 'error'); showToast(e.message, 'error'); }
    });

    // Buscar por ID
    document.getElementById('btn-buscar-id').addEventListener('click', async () => {
      const id = document.getElementById('buscar-id').value.trim();
      if (!id) return showToast('Ingresa un ID', 'warning');
      try {
        const res = await apiGet(`/${prefix}/${id}`);
        document.getElementById('res-lista').innerHTML = jsonToTable([_unwrap(res)]);
      } catch(e) { document.getElementById('res-lista').innerHTML = `<p class="text-danger">${e.message}</p>`; }
    });

    // Listar
    document.getElementById('btn-listar').addEventListener('click', async () => {
      const params = {};
      filtrosCampos.forEach(f => {
        const v = document.getElementById(`filtro-${f.name}`).value;
        if (v) params[f.name] = v;
      });
      try {
        const rows = await apiGet(`/${prefix}/`, { ...params, limit: 50 });
        document.getElementById('res-lista').innerHTML = jsonToTable(rows.map(_unwrap));
      } catch(e) { document.getElementById('res-lista').innerHTML = `<p class="text-danger">${e.message}</p>`; }
    });

    // Agregaciones
    document.getElementById('btn-agregaciones').addEventListener('click', async () => {
      try {
        const res = await apiGet(`/${prefix}/agregaciones/resumen`);
        document.getElementById('res-lista').innerHTML = jsonToTable(Array.isArray(res) ? res : [res]);
      } catch(e) { document.getElementById('res-lista').innerHTML = `<p class="text-danger">${e.message}</p>`; }
    });

    // Actualizar props
    document.getElementById('btn-actualizar').addEventListener('click', async () => {
      const id = document.getElementById('edit-id').value.trim();
      const raw = document.getElementById('edit-props').value;
      try {
        const props = JSON.parse(raw);
        const res = await apiPut(`/${prefix}/${id}`, { propiedades: props });
        _show('res-edit', res, 'success');
        showToast('Actualizado', 'success');
      } catch(e) { _show('res-edit', {error: e.message}, 'error'); showToast(e.message, 'error'); }
    });

    // Agregar props
    document.getElementById('btn-agregar-props').addEventListener('click', async () => {
      const id = document.getElementById('edit-id').value.trim();
      const raw = document.getElementById('edit-props').value;
      try {
        const props = JSON.parse(raw);
        const res = await apiPatch(`/${prefix}/${id}/propiedades`, { propiedades: props });
        _show('res-edit', res, 'success');
        showToast('Propiedades agregadas', 'success');
      } catch(e) { _show('res-edit', {error: e.message}, 'error'); showToast(e.message, 'error'); }
    });

    // Eliminar props
    document.getElementById('btn-eliminar-props').addEventListener('click', async () => {
      const id = document.getElementById('delprop-id').value.trim();
      const keys = document.getElementById('delprop-keys').value.split(',').map(s => s.trim()).filter(Boolean);
      try {
        const res = await apiDelete(`/${prefix}/${id}/propiedades`, undefined, { propiedades: keys });
        _show('res-delprop', res, 'success');
        showToast('Propiedades eliminadas', 'success');
      } catch(e) { _show('res-delprop', {error: e.message}, 'error'); showToast(e.message, 'error'); }
    });

    // Eliminar 1
    document.getElementById('btn-eliminar').addEventListener('click', async () => {
      const id = document.getElementById('del-id').value.trim();
      if (!confirm(`¿Eliminar ${titulo} "${id}"?`)) return;
      try {
        const res = await apiDelete(`/${prefix}/${id}`);
        _show('res-del', res, 'success');
        showToast(`${titulo} eliminado`, 'success');
      } catch(e) { _show('res-del', {error: e.message}, 'error'); showToast(e.message, 'error'); }
    });

    // Eliminar bulk
    document.getElementById('btn-eliminar-bulk').addEventListener('click', async () => {
      const ids = document.getElementById('del-ids').value.split(',').map(s => s.trim()).filter(Boolean);
      if (!ids.length) return showToast('Ingresa al menos un ID', 'warning');
      if (!confirm(`¿Eliminar ${ids.length} nodos?`)) return;
      try {
        const res = await apiDelete(`/${prefix}/bulk/eliminar`, ids);
        _show('res-del', res, 'success');
        showToast(`${ids.length} nodos eliminados`, 'success');
      } catch(e) { _show('res-del', {error: e.message}, 'error'); showToast(e.message, 'error'); }
    });
  }

  function destroy() {}

  function _show(id, data, type) {
    const el = document.getElementById(id);
    el.style.display = 'block';
    el.className = `result-box mt-3 border-${type === 'success' ? 'success' : 'danger'}`;
    el.textContent = JSON.stringify(data, null, 2);
  }

  // El backend devuelve {c: {...}} para clientes, {t: {...}} para transacciones, etc.
  // Si el objeto tiene una sola clave cuyo valor es un objeto, extrae ese valor.
  function _unwrap(r) {
    if (!r || typeof r !== 'object' || Array.isArray(r)) return r;
    const vals = Object.values(r);
    if (vals.length === 1 && vals[0] && typeof vals[0] === 'object' && !Array.isArray(vals[0])) {
      return vals[0];
    }
    return r;
  }

  return { render, mount, destroy };
}
