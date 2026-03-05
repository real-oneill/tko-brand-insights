const BASE = '/api';

export async function fetchApi(path, params = {}) {
  const url = new URL(path, window.location.origin);
  url.pathname = BASE + path;
  Object.entries(params).forEach(([k, v]) => {
    if (v != null && v !== '') url.searchParams.set(k, v);
  });
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
