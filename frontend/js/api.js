const BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : window.location.origin;

async function _req(method, path, body, params) {
  let url = BASE + path;
  if (params) {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''))
    ).toString();
    if (qs) url += '?' + qs;
  }
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const apiGet    = (path, params) => _req('GET',    path, undefined, params);
export const apiPost   = (path, body)   => _req('POST',   path, body);
export const apiPut    = (path, body)   => _req('PUT',    path, body);
export const apiPatch  = (path, body)   => _req('PATCH',  path, body);
export const apiDelete = (path, body, params) => _req('DELETE', path, body, params);
