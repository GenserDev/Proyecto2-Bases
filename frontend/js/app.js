import { register, init, navigate } from './router.js';
import * as dashboard     from './pages/dashboard.js';
import * as clientes      from './pages/clientes.js';
import * as cuentas       from './pages/cuentas.js';
import * as tarjetas      from './pages/tarjetas.js';
import * as transacciones from './pages/transacciones.js';
import * as comercios     from './pages/comercios.js';
import * as dispositivos  from './pages/dispositivos.js';
import * as ubicaciones   from './pages/ubicaciones.js';
import * as relaciones    from './pages/relaciones.js';
import * as consultas     from './pages/consultas.js';
import * as deteccion     from './pages/deteccion.js';
import * as grafo         from './pages/grafo.js';
import * as csv           from './pages/csv.js';

register('/dashboard',     dashboard);
register('/clientes',      clientes);
register('/cuentas',       cuentas);
register('/tarjetas',      tarjetas);
register('/transacciones', transacciones);
register('/comercios',     comercios);
register('/dispositivos',  dispositivos);
register('/ubicaciones',   ubicaciones);
register('/relaciones',    relaciones);
register('/consultas',     consultas);
register('/deteccion',     deteccion);
register('/grafo',         grafo);
register('/csv',           csv);

// Sidebar navigation
document.querySelectorAll('.nav-link[data-page]').forEach(link => {
  link.addEventListener('click', () => navigate(link.dataset.page));
});

// Health check → status dot
fetch((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : window.location.origin) + '/health')
  .then(r => {
    const dot = document.querySelector('.status-dot');
    if (dot) dot.className = `status-dot ${r.ok ? '' : 'offline'}`;
  })
  .catch(() => {
    const dot = document.querySelector('.status-dot');
    if (dot) dot.className = 'status-dot offline';
  });

init();
