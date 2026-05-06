import { createPage } from './_entidad.js';
export const { render, mount, destroy } = createPage({
  titulo: 'Ubicaciones', icon: 'bi-geo-alt-fill', color: '#0d9488', prefix: 'ubicaciones', idField: 'ubicacionId',
  campos: [
    { name: 'ubicacionId', label: 'ID',       required: true },
    { name: 'ciudad',      label: 'Ciudad',   required: true },
    { name: 'pais',        label: 'País',     required: true },
    { name: 'latitud',     label: 'Latitud',  type: 'number' },
    { name: 'longitud',    label: 'Longitud', type: 'number' },
    { name: 'region',      label: 'Región' },
    { name: 'poblacion',   label: 'Población',type: 'number' },
  ],
  filtrosCampos: [
    { name: 'pais',   label: 'País' },
    { name: 'ciudad', label: 'Ciudad' },
  ],
});
