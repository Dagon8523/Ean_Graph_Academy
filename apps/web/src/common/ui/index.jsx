import { useEffect, useRef } from 'react';
import { Icon } from './Icon.jsx';

const cx = (...c) => c.filter(Boolean).join(' ');

/* Valor que puede venir como marcador ‹…› (datos simulados) o faltar (no registrado). */
export function Field({ value, missingText = 'No registrado' }) {
  if (value === null || value === undefined || value === '') return <span className="miss-text">{missingText}</span>;
  if (typeof value === 'string' && value.startsWith('‹') && value.endsWith('›')) return <span className="ph">{value.slice(1, -1)}</span>;
  return <>{value}</>;
}

export function Button({ variant = 'ghost', size, icon, children, className, as: Tag = 'button', ...rest }) {
  return (
    <Tag className={cx('btn', `btn-${variant}`, size === 'sm' && 'btn-sm', className)} {...(Tag === 'button' ? { type: 'button' } : {})} {...rest}>
      {icon && <Icon name={icon} size="sm" />}
      {children}
    </Tag>
  );
}

export function IconButton({ icon, label, ...rest }) {
  return <button type="button" className="icon-btn" aria-label={label} title={label} {...rest}><Icon name={icon} /></button>;
}

/* Estado: punto + texto (nunca solo color). tone: ok | warn | bad | plan */
export const Chip = ({ tone = 'ok', children }) => <span className={`chip ${tone}`}>{children}</span>;

/* Tipo de formación con color de segmento AA */
export const TypePill = ({ pill, children }) => <span className={`type ${pill}`}>{children}</span>;

export function Callout({ tone, icon = 'info', children }) {
  return <div className={cx('callout', tone)} role={tone === 'warn' ? 'note' : undefined}><Icon name={icon} /><span>{children}</span></div>;
}

export function Tabs({ label, value, onChange, options }) {
  return (
    <div className="tabs" role="tablist" aria-label={label}>
      {options.map((o) => (
        <button key={o.value} type="button" role="tab" className="tab" aria-selected={value === o.value} onClick={() => onChange(o.value)}>
          {o.icon && <Icon name={o.icon} size="sm" />}{o.label}
        </button>
      ))}
    </div>
  );
}

export const Skeleton = ({ w = '100%', h = 14, r }) => <span className="skel" style={{ display: 'block', width: w, height: h, borderRadius: r }} />;

export function EmptyState({ icon = 'search', title, children, actions, error }) {
  return (
    <div className={cx('card empty', error && 'err')} role={error ? 'alert' : undefined}>
      <span className="big"><Icon name={icon} /></span>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {actions && <div className="choices">{actions}</div>}
    </div>
  );
}

export const Hex = ({ tone, children }) => <span className={cx('hex', tone)}>{children}</span>;

export const Kicker = ({ children }) => <span className="kicker">{children}</span>;

export function Modal({ open, onClose, labelledBy, children }) {
  const ref = useRef(null);
  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement;
    ref.current?.querySelector('[data-autofocus]')?.focus();
    const onKey = (e) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('keydown', onKey); prev?.focus?.(); };
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="modal on" role="dialog" aria-modal="true" aria-labelledby={labelledBy} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="sheet" ref={ref}>{children}</div>
    </div>
  );
}

export function ErrorNotice({ error, onRetry, title = 'no pude conectar con el servicio de búsqueda' }) {
  const msg = error?.kind === 'timeout' ? 'La API tardó demasiado en responder.' : error?.kind === 'http' ? `La API respondió con un error${error.status ? ` (${error.status})` : ''}.` : 'La API no respondió.';
  return (
    <EmptyState error icon="wifi" title={title}
      actions={<>{onRetry && <Button variant="dark" icon="refresh" onClick={onRetry}>Reintentar</Button>}<Button as="a" href="#/fuentes">Ver estado de las fuentes</Button></>}>
      {msg} Tu conversación se conserva; puedes reintentar en unos segundos. No muestro resultados sin consultar las fuentes.
    </EmptyState>
  );
}

export { cx };
