export const fmt = {
  money:   v => v != null ? `Q ${Number(v).toLocaleString('es-GT', { minimumFractionDigits: 2 })}` : '—',
  date:    v => v != null ? String(v) : '—',
  pct:     v => v != null ? `${Number(v).toFixed(1)}%` : '—',
  score:   v => v != null ? Number(v).toFixed(3) : '0.000',
  bool:    v => v ? '<span class="badge bg-success">Sí</span>' : '<span class="badge bg-secondary">No</span>',
  nivel: v => {
    const cls = { alto: 'badge-alto', medio: 'badge-medio', bajo: 'badge-bajo' };
    return `<span class="badge ${cls[v] || 'bg-secondary'}">${v || 'N/A'}</span>`;
  },
};

export function scoreColor(s) {
  if (s >= 0.8) return '#dc2626';
  if (s >= 0.5) return '#d97706';
  return '#16a34a';
}

export function debounce(fn, ms = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

export function jsonToTable(rows) {
  if (!rows || !rows.length) return '<p class="text-muted small">Sin resultados.</p>';
  const keys = Object.keys(rows[0]);
  const head = keys.map(k => `<th>${k}</th>`).join('');
  const body = rows.map(r =>
    `<tr>${keys.map(k => `<td>${r[k] != null ? r[k] : '—'}</td>`).join('')}</tr>`
  ).join('');
  return `<div class="table-responsive"><table class="table table-hover table-sm mb-0">
    <thead><tr>${head}</tr></thead><tbody>${body}</tbody>
  </table></div>`;
}

export function el(html) {
  const div = document.createElement('div');
  div.innerHTML = html.trim();
  return div.firstChild;
}
