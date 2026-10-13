import { useId, useMemo } from 'react';
import { Button, TypePill } from '../../common/ui/index.jsx';
import { Icon } from '../../common/ui/Icon.jsx';
import './catalog-results.css';

const attr = (item, keys) => item.attributes?.find(a => keys.includes(a.key) && !a.missing)?.value;
const dedupe = list => [...new Map(list.map(it => [it.id, it])).values()];
const levelRank = item => {
  const level = String(attr(item, ['level', 'nivel_formacion']) || '').toLowerCase();
  if (level.includes('doctor')) return 4;
  if (level.includes('maestr') || level.includes('mag')) return 3;
  if (level.includes('especial')) return 2;
  if (level.includes('pregrado') || level.includes('profesional')) return 1;
  return 0;
};
function CourseRow({ item, selected, onCompare, units = [] }) {
  const level = attr(item, ['level', 'nivel_formacion']);
  const difficulty = attr(item, ['difficulty', 'difficulty_level', 'nivel_dificultad']);
  const modality = attr(item, ['modality', 'modalidad']);
  const availability = attr(item, ['disponibilidad', 'availability']);
  return <article className="catalog-row">
    <div className="catalog-row-main">
      <span className={`catalog-icon ${item.pill || ''}`} aria-hidden="true"><Icon name={item.kind === 'official_program' ? 'cap' : 'doc'} /></span>
      <div className="catalog-title"><h4>{item.name || 'Nombre no registrado'}</h4><TypePill pill={item.pill}>{item.kindLabel}</TypePill></div>
      <div className="catalog-meta">
        {item.kind === 'official_program' ? <span>{level || 'Nivel académico no informado'}</span> : <span>{difficulty ? `Nivel: ${difficulty}` : 'Nivel: no informado'}</span>}
        {modality ? <span>{modality}</span> : null}
        {availability ? <span className="catalog-availability">{availability}</span> : null}
      </div>
      <div className="catalog-actions">
        <Button disabled={item.referenceOnly} size="sm" variant={item.kind === 'official_program' ? 'primary' : 'line'} as="a" href={`#/detalle/${item.id}`}>{item.kind === 'official_program' ? 'Explorar programa' : 'Ver detalle'}</Button>
        <label className="cmp"><input type="checkbox" disabled={item.referenceOnly} checked={selected} onChange={onCompare} />Comparar</label>
      </div>
    </div>
    {units.length ? <details className="catalog-units"><summary><Icon name="doc" size="sm" />Unidades de estudio del programa <span>{units.length}</span></summary><ul>{units.map(u => <li key={u.id}><span>{u.name || 'Nombre no registrado'}</span><span className="catalog-link">Vínculo por código</span></li>)}</ul></details> : null}
  </article>;
}
export function CatalogResults({ results = [], relatedUnits = [], compare = [], onCompare }) {
  const prefix = useId();
  const groups = useMemo(() => {
    const eanx = results.filter(it => it.kind === 'eanx');
    const continuing = results.filter(it => it.kind === 'continuing_education');
    const programs = new Map(results.filter(it => it.kind === 'official_program').map(p => [p.id, { ...p, linkedUnits: [...(p.units || [])] }]));
    const unattached = [];
    for (const u of relatedUnits) {
      if (u.program?.link === 'verified' && u.program.id) {
        if (!programs.has(u.program.id)) programs.set(u.program.id, { id: u.program.id, name: u.program.name, kind: 'official_program', kindLabel: 'Programa oficial', pill: 'prog', attributes: [], linkedUnits: [], referenceOnly: true });
        programs.get(u.program.id).linkedUnits.push(u);
      } else unattached.push(u);
    }
    const official = [...programs.values()].map(p => ({ ...p, linkedUnits: dedupe(p.linkedUnits) })).sort((a,b) => levelRank(a) - levelRank(b));
    return { eanx, continuing, official, unattached: dedupe(unattached) };
  }, [results, relatedUnits]);
  const blocks = [
    { id: 'eanx', title: 'Explorar', subtitle: 'EAN X · formación flexible', icon: 'spark', items: groups.eanx },
    { id: 'ec', title: 'Aplicar', subtitle: 'Educación Continuada · oferta formativa', icon: 'doc', items: groups.continuing },
    { id: 'official', title: 'Profundizar', subtitle: 'Programas oficiales · formación académica', icon: 'cap', items: groups.official }
  ];
  return <div className="catalog-results"><div className="catalog-heading"><h3>elige cómo avanzar</h3><p>Explora opciones y profundiza en tu formación.</p></div>
    {blocks.map(block => block.items.length ? <section className={`catalog-group catalog-${block.id}`} key={block.id} aria-labelledby={`${prefix}-catalog-${block.id}-title`}>
      <header className="catalog-group-head"><span className="catalog-step" aria-hidden="true"><Icon name={block.icon} /></span><div><h3 id={`${prefix}-catalog-${block.id}-title`}>{block.title}</h3><p>{block.subtitle}</p></div><span className="catalog-count">{block.items.length} {block.items.length === 1 ? 'opción' : 'opciones'}</span></header>
      <div className="catalog-rows">{block.items.map(item => <CourseRow key={item.id} item={item} units={item.linkedUnits} selected={compare.includes(item.id)} onCompare={() => onCompare(item.id)} />)}</div>
    </section> : null)}
    {groups.unattached.length ? <details className="catalog-unattached"><summary><Icon name="doc" size="sm" />Unidades sin programa vinculado <span>{groups.unattached.length}</span></summary><ul>{groups.unattached.map(u => <li key={u.id}>{u.name || 'Nombre no registrado'}</li>)}</ul></details> : null}
    <p className="catalog-note">El catálogo no determina la dificultad. El nivel se muestra cuando está informado.</p>
  </div>;
}
