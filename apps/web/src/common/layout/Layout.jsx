import { useEffect, useState } from 'react';
import { Icon } from '../ui/Icon.jsx';
import { Logo, BrandSymbol, Vigilada } from '../brand/Brand.jsx';
import { useTheme } from '../../core/theme.jsx';



const NAV = [
  { name: 'inicio', path: '/', label: 'Inicio', short: 'Inicio', icon: 'home' },
  { name: 'conversacion', path: '/conversacion', label: 'Conversación', short: 'Chat', icon: 'chat' },
  { name: 'ruta', path: '/ruta', label: 'Mi ruta formativa', short: 'Mi ruta', icon: 'route' },
  { name: 'fuentes', path: '/fuentes', label: 'Fuentes', short: 'Fuentes', icon: 'db' }
];
// El detalle cuelga de la conversación en la navegación.
const section = (name) => (name === 'detalle' ? 'conversacion' : name);

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const dark = theme === 'dark';
  const label = dark ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
  return (
    <button type="button" className="icon-btn" onClick={toggle} aria-label={label} title={label}>
      <Icon name={dark ? 'sun' : 'moon'} />
    </button>
  );
}

function Sidebar({ route, onNew }) {
  return (
    <aside className="side" aria-label="Navegación principal">
      <a className="lockup" href="#/" aria-label="Universidad EAN — inicio"><Logo className="logo" title="Universidad EAN" /></a>
      <BrandSymbol className="sym" decorative={false} />
      <a className="btn btn-primary btn-new" href="#/" onClick={onNew} aria-label="Nueva consulta" title="Nueva consulta">
        <Icon name="plus" size="sm" /><span className="lbl">Nueva consulta</span>
      </a>
      <nav className="nav" aria-label="Secciones">
        {NAV.map((n) => (
          <a key={n.name} href={`#${n.path}`} aria-label={n.label} title={n.label} aria-current={section(route.name) === n.name ? 'page' : undefined}>
            <Icon name={n.icon} /><span className="lbl">{n.label}</span>
          </a>
        ))}
      </nav>
      <div className="side-sec">
        <h4>Próximamente</h4>
        <div className="soon"><Icon name="history" size="sm" />Historial de consultas</div>
      </div>
      <div className="side-foot"><Vigilada /></div>
    </aside>
  );
}

function MobileNav({ route }) {
  const items = [...NAV.slice(0, 2), { name: 'detalle', path: '/conversacion', short: 'Detalle', icon: 'doc', hidden: route.name !== 'detalle' }, ...NAV.slice(2)].filter((n) => !n.hidden);
  return (
    <nav className="mnav" aria-label="Secciones" style={{ gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))` }}>
      {items.map((n) => (
        <a key={n.name} href={`#${n.path}`} aria-current={route.name === n.name ? 'page' : undefined}><Icon name={n.icon} /><span>{n.short}</span></a>
      ))}
    </nav>
  );
}

const TITLES = {
  inicio: ['Inicio', 'inicio'],
  conversacion: ['Conversación', 'conversación y resultados'],
  detalle: ['Detalle de formación', 'detalle de formación'],
  ruta: ['Mi ruta formativa', 'mi ruta formativa'],
  fuentes: ['Fuentes de conocimiento', 'fuentes de conocimiento']
};

export function AppShell({ route, onNew, children }) {
  const [kicker, title] = TITLES[route.name] || TITLES.inicio;
  useEffect(() => { document.title = `${title} · Universidad EAN`; }, [title]);
  return (
    <div className="stage">
      <div className="app">
        <Sidebar route={route} onNew={onNew} />
        <div className="main">
          <header className="topbar">
            <div className="m-lockup">
              <a href="#/" aria-label="Universidad EAN — inicio" style={{ display: 'flex' }}><Logo className="logo" /></a>
              <span style={{ marginLeft: 'auto', display: 'flex', gap: 2 }}>
                <ThemeToggle />
                <a className="icon-btn" href="#/" onClick={onNew} aria-label="Nueva consulta" title="Nueva consulta"><Icon name="plus" /></a>
              </span>
            </div>
            <div className="tblock"><span className="kicker">{kicker}</span><h1>{title}</h1></div>
            <span className="top-theme"><ThemeToggle /></span>
          </header>
          <main>{children}</main>
          <footer className="foot">
            <Vigilada />
            <span>Universidad EAN · El asistente orienta; no reemplaza la información oficial ni garantiza admisión, homologación, certificación o contratación.</span>
          </footer>
          <MobileNav route={route} />
        </div>
      </div>

    </div>
  );
}
