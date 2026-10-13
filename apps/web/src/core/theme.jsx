import { createContext, useCallback, useContext, useEffect, useState } from 'react';

// Tema claro/oscuro: sigue al sistema hasta que la persona elige; la elección se recuerda.
const KEY = 'cae-theme';
const ThemeContext = createContext({ theme: 'light', toggle: () => {} });

const systemTheme = () => (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
const readStored = () => { try { const t = localStorage.getItem(KEY); return t === 'light' || t === 'dark' ? t : null; } catch { return null; } };

export function ThemeProvider({ children }) {
  const [chosen, setChosen] = useState(readStored);
  const [system, setSystem] = useState(systemTheme);
  const theme = chosen || system;

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const on = (e) => setSystem(e.matches ? 'dark' : 'light');
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);

  useEffect(() => { document.documentElement.setAttribute('data-theme', theme); }, [theme]);

  const toggle = useCallback(() => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setChosen(next);
    try { localStorage.setItem(KEY, next); } catch { /* almacenamiento no disponible */ }
  }, [theme]);

  return <ThemeContext.Provider value={{ theme, toggle }}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);
