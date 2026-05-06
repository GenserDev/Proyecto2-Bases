let _current = null;

const routes = {};

export function register(hash, mod) {
  routes[hash] = mod;
}

export function navigate(hash) {
  window.location.hash = hash;
}

async function _load() {
  const hash = window.location.hash.replace('#', '') || '/dashboard';
  const mod = routes[hash];

  // Destroy current
  if (_current && _current.destroy) _current.destroy();

  // Update sidebar active
  document.querySelectorAll('.nav-link').forEach(l => {
    l.classList.toggle('active', l.dataset.page === hash);
  });

  const container = document.getElementById('app');
  if (!mod) {
    container.innerHTML = '<div class="card"><p class="text-muted">Página no encontrada.</p></div>';
    return;
  }

  container.innerHTML = '<div class="text-muted small p-3">Cargando...</div>';
  try {
    mod.render(container);
    if (mod.mount) await mod.mount();
    _current = mod;
  } catch (e) {
    container.innerHTML = `<div class="card"><p class="text-danger">Error: ${e.message}</p></div>`;
  }
}

export function init() {
  window.addEventListener('hashchange', _load);
  _load();
}
