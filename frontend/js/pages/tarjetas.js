import { createPage } from './_entidad.js';
export const { render, mount, destroy } = createPage({
  titulo: 'Tarjetas', icon: 'bi-credit-card-fill', color: '#0891b2', prefix: 'tarjetas', idField: 'tarjetaId',
  campos: [
    { name: 'tarjetaId',    label: 'ID',           required: true },
    { name: 'tipoTarjeta',  label: 'Tipo',         placeholder: 'credito/debito' },
    { name: 'limiteCredito',label: 'Límite crédito',type: 'number' },
    { name: 'fechaVencimiento', label: 'Vencimiento', type: 'date' },
    { name: 'banco',        label: 'Banco' },
  ],
  filtrosCampos: [
    { name: 'tipoTarjeta', label: 'Tipo tarjeta' },
  ],
});
