import { useEffect, useState } from 'react';
import { Icon } from '../../common/ui/Icon.jsx';
import { Button, Callout, Chip, ErrorNotice, Field, Skeleton, Tabs, TypePill } from '../../common/ui/index.jsx';
import { catalogService } from '../../services/assistantService.js';
import { RelationsGraph } from '../graph.jsx';

const REL = {
  BELONGS_TO: { cls: '', top: 'pertenece a', bottom: 'código verificado' },
  AFFINITY: { cls: 'aff', top: 'afinidad temática', bottom: 'similitud semántica' },
  PLANNED: { cls: 'plan', top: 'contenido relacionado', bottom: 'integración prevista' }
};

function useItem(id) {
  const [s, set] = useState({ status: 'loading' });
  const load = () => {
    set({ status: 'loading' });
    Promise.all([catalogService.getItem(id), catalogService.getRelations(id)])
      .then(([item, relations]) => set({ status: 'done', item, relations }))
      .catch((error) => set({ status: 'error', error }));
  };
  useEffect(load, [id]);
  return [s, load];
}

export function DetailView({ id }) {
  const [s, reload] = useItem(id);
  const [mode, setMode] = useState('list');

  if (s.status === 'loading') {
    return (
      <section className="view" aria-busy="true">
        <div className="d-head"><Skeleton w={160} h={24} r={999} /><Skeleton w="60%" h={34} /><Skeleton w="80%" /></div>
        <div className="agrid" style={{ marginTop: 20 }}>{[0, 1, 2, 3, 4, 5].map((i) => <Skeleton key={i} h={86} r={13} />)}</div>
      </section>
    );
  }
  if (s.status === 'error') return <section className="view"><ErrorNotice error={s.error} onRetry={reload} title="no pude cargar el detalle" /></section>;

  const { item, relations } = s;
  const isProgram = item.kind === 'official_program';
  const missing = item.attributes.filter((a) => a.missing);

  return (
    <section className="view" aria-labelledby="det-t">
      <nav className="crumbs" aria-label="Ruta de navegación">
        <a href="#/conversacion">Resultados</a><span>/</span><span aria-current="page">{item.kindLabel}</span>
      </nav>
      <div className="detail">
        <div style={{ minWidth: 0, containerType: 'inline-size' }}>
          <div className="d-head">
            <div className="row">
              <TypePill pill={item.pill}>{item.kindLabel}</TypePill>
              {isProgram && item.units?.length > 0 && <Chip tone="ok">Encontrado mediante una unidad de estudio</Chip>}
            </div>
            <h2 id="det-t"><Field value={item.name} missingText="Nombre no registrado" /></h2>
            {item.reason && <p className="muted">{item.reason.charAt(0).toUpperCase() + item.reason.slice(1)}</p>}
            <div className="row">
              <Button variant="primary" icon="route" as="a" href="#/ruta">Ver ruta recuperada</Button>
              <Button variant="line" icon="db" as="a" href="#/fuentes">Ver fuente</Button>
            </div>
          </div>

          <div className="section-title"><h3>atributos disponibles</h3></div>
          <div className="agrid">
            {item.attributes.map((a) => (
              <div key={a.key} className={`tile ${a.missing ? 'miss' : ''}`}>
                <small>{a.label}</small>
                <span><Field value={a.value} missingText="No registrado en esta fuente" /></span>
                {a.field && <code>{a.field}</code>}
              </div>
            ))}
          </div>
          {missing.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <Callout tone="warn" icon="alert"><b>Datos incompletos.</b> {missing.map((m) => m.label.toLowerCase()).join(', ')} no {missing.length > 1 ? 'están registrados' : 'está registrado'} en la fuente consultada. El asistente no {missing.length > 1 ? 'los estima' : 'lo estima'}; consulta la información oficial antes de decidir.</Callout>
            </div>
          )}

          {item.units?.length > 0 && (
            <>
              <div className="section-title"><h3>unidades de estudio asociadas</h3></div>
              <div className="card" style={{ padding: '6px 20px' }}>
                <div className="units">
                  {item.units.map((u) => (
                    <div key={u.id} className="urow">
                      <TypePill pill="unit">Unidad</TypePill>
                      <span className="tblock"><b><Field value={u.name} /></b><small>{u.reason}</small></span>
                      {u.program?.link === 'verified' ? <Chip tone="ok">Vínculo verificado</Chip> : <Chip tone="warn">Solo afinidad</Chip>}
                      <Button size="sm" as="a" href="#/fuentes">Ver catálogo</Button>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          <div className="section-title">
            <h3>relaciones</h3>
            <Tabs label="Formato de relaciones" value={mode} onChange={setMode} options={[{ value: 'list', label: 'Lista', icon: 'list' }, { value: 'graph', label: 'Grafo', icon: 'graph' }]} />
          </div>
          {!relations.length && <Callout icon="link">La respuesta de esta consulta no incluye relaciones para este registro.</Callout>}
          {relations.length > 0 && mode === 'list' && (
            <div style={{ containerType: 'inline-size' }}>
              <div className="rels">
                {relations.map((r, i) => {
                  const k = REL[r.type] || REL.AFFINITY;
                  return (
                    <div key={i} className={`rel ${k.cls}`}>
                      <div className="node"><TypePill pill={r.from.pill}>{r.from.kindLabel}</TypePill><b><Field value={r.from.name} /></b></div>
                      <div className="edge">{k.top}<i />{k.bottom}</div>
                      <div className="node"><TypePill pill={r.to.pill}>{r.to.kindLabel}</TypePill><b><Field value={r.to.name} /></b></div>
                      {r.note && <p className="why">{r.note}</p>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {relations.length > 0 && mode === 'graph' && (
            <>
              <RelationsGraph relations={relations} title="Relaciones de esta formación: pertenencia verificada, afinidad temática e integraciones previstas." />
              <p className="g-note">Línea continua: vínculo estructural verificado. Discontinua: afinidad temática (no es equivalencia). Punteada: integración prevista. La lista contiene la misma información.</p>
            </>
          )}
        </div>

        <aside style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <span className="kicker">Procedencia</span>
            <h3 style={{ margin: '6px 0 12px' }}>fuente de este detalle</h3>
            <div className="mini-list">
              <div className="row"><span className="tblock"><b>{item.source?.name || 'Fuente no indicada'}</b><small>{item.source?.origin}</small></span><Chip tone="ok">Disponible</Chip></div>
            </div>
          </div>
          <div className="card">
            <span className="kicker">Cómo leer esta relación</span>
            <h3 style={{ margin: '6px 0 12px' }}>pertenencia vs. afinidad</h3>
            <p className="muted" style={{ fontSize: 13.5 }}>Una unidad <b style={{ color: 'var(--ink)' }}>pertenece</b> a un programa solo si existe un vínculo por código. Si solo hay similitud de contenido, se muestra como <b style={{ color: 'var(--ink)' }}>afinidad</b>, sin equivalencias ni prerrequisitos.</p>
          </div>
          <div className="card">
            <span className="kicker">Sin vínculo</span>
            <h3 style={{ margin: '6px 0 12px' }}>cuando falta el código</h3>
            <Callout tone="warn" icon="link">Si no hay un vínculo verificado entre una unidad y un programa, se muestra sin programa vinculado.</Callout>
          </div>
        </aside>
      </div>
    </section>
  );
}
