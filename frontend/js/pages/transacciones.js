import { createPage } from './_entidad.js';
export const { render, mount, destroy } = createPage({
  titulo: 'Transacciones', icon: 'bi-credit-card-2-front-fill', color: '#d97706', prefix: 'transacciones', idField: 'transaccionId',
  campos: [
    { name: 'transaccionId', label: 'ID',           required: true },
    { name: 'monto',         label: 'Monto',        type: 'number' },
    { name: 'fecha',         label: 'Fecha',        type: 'date' },
    { name: 'canal',         label: 'Canal',        placeholder: 'online/presencial/app' },
    { name: 'estado',        label: 'Estado',       placeholder: 'completada/pendiente' },
    { name: 'horaLocal',     label: 'Hora local',   type: 'number', placeholder: '0-23' },
    { name: 'moneda',        label: 'Moneda',       placeholder: 'GTQ' },
    { name: 'categoriaGasto',label: 'Categoría' },
  ],
  filtrosCampos: [
    { name: 'canal',  label: 'Canal' },
    { name: 'estado', label: 'Estado' },
  ],
});
