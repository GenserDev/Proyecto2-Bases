import { createPage } from './_entidad.js';
export const { render, mount, destroy } = createPage({
  titulo: 'Cuentas', icon: 'bi-bank', color: '#16a34a', prefix: 'cuentas', idField: 'cuentaId',
  campos: [
    { name: 'cuentaId',     label: 'ID',           required: true },
    { name: 'numeroCuenta', label: 'Número cuenta', required: true },
    { name: 'tipoCuenta',   label: 'Tipo',          placeholder: 'corriente/ahorro' },
    { name: 'saldo',        label: 'Saldo',         type: 'number' },
    { name: 'fechaApertura',label: 'Fecha apertura',type: 'date' },
    { name: 'moneda',       label: 'Moneda',        placeholder: 'GTQ' },
  ],
  filtrosCampos: [
    { name: 'tipoCuenta', label: 'Tipo cuenta' },
  ],
});
