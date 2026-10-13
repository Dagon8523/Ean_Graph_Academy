import { useEffect, useState } from 'react';

// Enrutador mínimo por hash (sin dependencias extra): #/ruta/:param
const ROUTES = [
  { name: 'inicio', pattern: /^\/?$/ },
  { name: 'conversacion', pattern: /^\/conversacion\/?$/ },
  { name: 'detalle', pattern: /^\/detalle\/([^/]+)\/?$/, params: ['id'] },
  { name: 'ruta', pattern: /^\/ruta\/?$/ },
  { name: 'fuentes', pattern: /^\/fuentes\/?$/ }
];

function parse() {
  const path = decodeURI(window.location.hash.replace(/^#/, '')) || '/';
  for (const r of ROUTES) {
    const m = path.match(r.pattern);
    if (m) {
      const params = {};
      (r.params || []).forEach((k, i) => { params[k] = m[i + 1]; });
      return { name: r.name, params };
    }
  }
  return { name: 'inicio', params: {} };
}

export function navigate(path) {
  window.location.hash = path.startsWith('#') ? path : '#' + path;
}

export const href = (path) => '#' + path;

export function useRoute() {
  const [route, setRoute] = useState(parse);
  useEffect(() => {
    const on = () => { setRoute(parse()); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  return route;
}
