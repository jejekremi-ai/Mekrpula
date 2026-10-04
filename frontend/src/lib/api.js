import { useCallback, useEffect, useRef, useState } from 'react';
export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const publicErrors = {
  'Hanya kreator terverifikasi yang dapat mengoperasikan agent resmi token ini.': 'Only the verified creator can operate this token’s official agent.',
  'Agent komunitas hanya tersedia dalam mode kredit uji.': 'Community research is available only in internal test mode.',
};
export async function api(path, options = {}) {
  const token = sessionStorage.getItem('mart-session');
  const form = options.body instanceof FormData;
  const response = await fetch(`${API}${path}`, { ...options, headers: { ...(form ? {} : { 'Content-Type': 'application/json' }), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers }, body: options.body ? (form ? options.body : JSON.stringify(options.body)) : undefined });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) { const detail = typeof data.detail === 'string' ? data.detail : data.detail?.[0]?.msg || 'Something went wrong. Please try again.'; const e = new Error(publicErrors[detail] || detail); e.status = response.status; throw e; }
  return data;
}
export function useData(path) {
  const [data, setData] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState('');
  const [version, setVersion] = useState(0);
  const lastPath = useRef(null);
  const reload = useCallback(() => setVersion(v => v + 1), []);
  useEffect(() => { let active = true; const changed = lastPath.current !== path; lastPath.current = path; if (changed) { setLoading(true); setData(null); } setError(''); if (!path) { setLoading(false); return; }
    api(path).then(x => { if (active) setData(x); }).catch(e => { if (active) setError(e.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [path, version]);
  return { data, loading, error, reload, setData };
}
export const short = s => s ? `${s.slice(0, 4)}…${s.slice(-4)}` : '';
export const money = n => n == null ? '—' : '$' + new Intl.NumberFormat('en-US', { notation: n >= 10000 ? 'compact' : 'standard', maximumFractionDigits: n > 1 ? 2 : 7 }).format(n);
export const count = n => new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(n || 0);
export const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '-');
export const ART = 'https://images.unsplash.com/photo-1704426882813-8acfff020487?auto=format&fit=crop&w=900&q=85';
export const SHAPES = 'https://images.unsplash.com/photo-1710244182004-1c708b3f146d?auto=format&fit=crop&w=800&q=85';
export const HOODIE = 'https://images.unsplash.com/photo-1614214191247-5b2d3a734f1b?auto=format&fit=crop&w=800&q=85';