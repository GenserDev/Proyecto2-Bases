import { createPage } from './_entidad.js';
export const { render, mount, destroy } = createPage({
  titulo: 'Clientes', icon: 'bi-people-fill', color: '#4f46e5', prefix: 'clientes', idField: 'clienteId',
  campos: [
    { name: 'clienteId',       label: 'ID',               required: true },
    { name: 'nombre',          label: 'Nombre',            required: true },
    { name: 'apellido',        label: 'Apellido',          required: true },
    { name: 'email',           label: 'Email' },
    { name: 'telefono',        label: 'Teléfono' },
    { name: 'fechaNacimiento', label: 'Fecha nacimiento',  type: 'date' },
    { name: 'nivelRiesgo',     label: 'Nivel riesgo',      placeholder: 'bajo/medio/alto' },
    { name: 'ingresoMensual',  label: 'Ingreso mensual',   type: 'number' },
  ],
  filtrosCampos: [
    { name: 'nivelRiesgo', label: 'Nivel riesgo', placeholder: 'bajo/medio/alto' },
  ],
});
