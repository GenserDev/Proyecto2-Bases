const container = (() => {
  const el = document.createElement('div');
  el.className = 'toast-container';
  document.body.appendChild(el);
  return el;
})();

export function showToast(msg, type = 'info', duration = 3500) {
  const el = document.createElement('div');
  el.className = `toast-msg ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  requestAnimationFrame(() => { el.classList.add('show'); });
  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.remove(), 300);
  }, duration);
}
