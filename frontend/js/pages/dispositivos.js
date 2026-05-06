import { createPage } from './_entidad.js';
export const { render, mount, destroy } = createPage({
  titulo: 'Dispositivos', icon: 'bi-phone-fill', color: '#64748b', prefix: 'dispositivos', idField: 'dispositivoId',
  campos: [
    { name: 'dispositivoId', label: 'ID',       required: true },
    { name: 'tipo',          label: 'Tipo',     placeholder: 'movil/desktop/tablet' },
    { name: 'sistemaOperativo', label: 'SO' },
    { name: 'ip',            label: 'IP' },
    { name: 'marcaModelo',   label: 'Marca/Modelo' },
    { name: 'ultimoUso',     label: 'Último uso', type: 'date' },
  ],
  filtrosCampos: [
    { name: 'tipo', label: 'Tipo' },
  ],
});
