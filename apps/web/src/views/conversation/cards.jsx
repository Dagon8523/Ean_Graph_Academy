import { Icon } from '../../common/ui/Icon.jsx';
import { Button, Chip, Field, TypePill } from '../../common/ui/index.jsx';

export function SourceLine({ source, icon = 'db' }) {
  if (!source) return null;
  return <div className="src"><Icon name={icon} size="sm" />{source.name}{source.origin ? ` · ${source.origin}` : ''}</div>;
}

export function ResultCard({ item, selected, onCompare, onAddRoute }) {
  const shown = item.attributes.slice(0, 3);
  return (
    <article className="card rc">
      <div className="rc-top">
        <TypePill pill={item.pill}>{item.kindLabel}</TypePill>
        {item.hasMissing && <Chip tone="warn">Datos incompletos</Chip>}
      </div>
      <h4><Field value={item.name} missingText="Nombre no registrado" /></h4>
      <div className="attrs">
        {shown.map((a) => (
          <div key={a.key} className={`attr ${a.missing ? 'miss' : ''}`}>
            <small>{a.label}</small><span><Field value={a.value} /></span>
          </div>
        ))}
      </div>
      {item.reason && <p className="why"><b>Por qué te lo muestro:</b> {item.reason}</p>}
      <SourceLine source={item.source} />
      <div className="rc-actions">
        <Button size="sm" as="a" href={`#/detalle/${item.id}`}>Ver detalle</Button>
        {onAddRoute && <Button size="sm" icon="route" onClick={onAddRoute}>A mi ruta</Button>}
        {onCompare && (
          <label className="cmp"><input type="checkbox" checked={selected} onChange={onCompare} />Comparar</label>
        )}
      </div>
    </article>
  );
}

export function UnitCard({ item }) {
  const linked = item.program?.link === 'verified';
  return (
    <article className="card rc">
      <div className="rc-top">
        <TypePill pill="unit">Unidad de estudio</TypePill>
        {linked ? <Chip tone="ok">Vínculo verificado</Chip> : <Chip tone="warn">Sin programa vinculado</Chip>}
      </div>
      <h4><Field value={item.name} /></h4>
      {linked ? (
        <div className="link-row"><Icon name="link" size="sm" />Pertenece a <Field value={item.program.name} /></div>
      ) : (
        <div className="link-row"><Icon name="alert" size="sm" />La API no devolvió un programa vinculado para esta unidad.</div>
      )}
      {item.reason && <p className="why"><b>Por qué te la muestro:</b> {item.reason}</p>}
      <SourceLine source={item.source} icon="doc" />
      <div className="rc-actions">
        {linked
          ? <Button variant="primary" size="sm" as="a" href={`#/detalle/${item.program.id}`}>Explorar programa</Button>
          : <Button size="sm" disabled>Sin programa asociado</Button>}
        <Button size="sm" as="a" href="#/fuentes">Ver catálogo</Button>
      </div>
    </article>
  );
}
