import { createPage } from './_entidad.js';
export const { render, mount, destroy } = createPage({
  titulo: 'Comercios', icon: 'bi-shop', color: '#7c3aed', prefix: 'comercios', idField: 'comercioId',
  campos: [
    { name: 'comercioId',  label: 'ID',         required: true },
    { name: 'nombre',      label: 'Nombre',     required: true },
    { name: 'categoria',   label: 'Categoría' },
    { name: 'pais',        label: 'País' },
    { name: 'calificacion',label: 'Calificación',type: 'number' },
    { name: 'registrado',  label: 'Registrado', type: 'date' },
  ],
  filtrosCampos: [
    { name: 'categoria', label: 'Categoría' },
    { name: 'pais',      label: 'País' },
  ],
});
