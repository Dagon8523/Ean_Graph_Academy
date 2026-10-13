import { CatalogResults } from './CatalogResults.jsx';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Icon } from '../../common/ui/Icon.jsx';
import { Button, Callout, EmptyState, ErrorNotice, Modal, Skeleton, TypePill, Field, Chip, cx } from '../../common/ui/index.jsx';
import { BrandSymbol } from '../../common/brand/Brand.jsx';
import { useConversation } from '../../core/store.jsx';
import { Composer } from '../shared.jsx';
import { ResultCard, UnitCard } from './cards.jsx';

const Avatar = () => <span className="av" aria-hidden="true"><BrandSymbol /></span>;

function Clarifications({ items, disabled, onSend }) {
  const [sel, setSel] = useState({});
  const ready = items.every((c) => sel[c.id]);
  const send = () => {
    const selections = items.map((c) => ({ id: c.id, label: c.question, value: c.options.find((o) => o.value === sel[c.id])?.label }));
    onSend(selections.map((s) => s.value).join(' · '), selections);
  };
  return (
    <>
      {items.map((c) => (
        <div key={c.id}>
          <p className="choices-q">{c.question}</p>
          <div className="choices" role="group" aria-label={c.question}>
            {c.options.map((o) => (
              <button key={o.value} type="button" className="choice" disabled={disabled} aria-pressed={sel[c.id] === o.value}
                onClick={() => setSel((s) => ({ ...s, [c.id]: o.value }))}>{o.label}</button>
            ))}
          </div>
        </div>
      ))}
      {!disabled && (
        <div className="continue-row">
          <Button variant="primary" size="sm" disabled={!ready} onClick={send}>Continuar</Button>
          <span className="muted" style={{ fontSize: 13 }}>o escribe tus preferencias abajo</span>
        </div>
      )}
    </>
  );
}

function Trace({ trace }) {
  if (!trace?.steps?.length) return null;
  return (
    <details className="trace">
      <summary><Icon name="list" size="sm" />Cómo llegué a esta respuesta · {trace.steps.length} pasos{trace.totalMs ? ` · ${(trace.totalMs / 1000).toFixed(1)} s` : ''}</summary>
      <ol>
        {trace.steps.map((s, i) => (
          <li key={i}>{s.label} — <code>{s.tool}</code>{s.ms ? ` · ${s.ms} ms` : ''}{s.status !== 'ok' && <> · <Chip tone="warn">{s.status}</Chip></>}</li>
        ))}
      </ol>
    </details>
  );
}

function Filters({ criteria, onRemove }) {
  const removable = new Set(['modality', 'max_price', 'max_hours']);
  if (!criteria.length) return null;
  return (
    <div className="filters" role="group" aria-label="Criterios aplicados">
      <Icon name="filter" size="sm" />
      {criteria.map((c) => (
        <span key={c.key} className="flt" aria-pressed="true">
          <span className="k">{c.label}</span>{c.value}
          {removable.has(c.key) && (
            <button type="button" className="x" onClick={() => onRemove(c.key)} aria-label={`Quitar ${c.label}`} style={{ display: 'inline-grid', placeItems: 'center' }}>
              <Icon name="x" size="sm" />
            </button>
          )}
        </span>
      ))}
    </div>
  );
}

function Loading() {
  return (
    <>
      <div className="steps" role="status" aria-label="Consultando">
        <span className="done"><Icon name="check" size="sm" />Consulta enviada</span>
        <span><Skeleton w={14} h={14} r="50%" />Buscando en Educación Continuada y unidades de estudio…</span>
        <span><Skeleton w={14} h={14} r="50%" />Verificando vínculos con programas</span>
      </div>
      <div className="results">
        {[0, 1].map((i) => (
          <div key={i} className="card rc">
            <Skeleton w={120} h={22} r={999} /><Skeleton w="80%" h={20} />
            <div className="attrs"><Skeleton h={44} /><Skeleton h={44} /><Skeleton h={44} /></div>
            <Skeleton w="90%" /><Skeleton w="60%" />
          </div>
        ))}
      </div>
    </>
  );
}

function AssistantMessage({ msg, isLast }) {
  const { state, send, retry, toggleCompare, removeCriterion } = useConversation();
  const t = msg.turn;
  let body;
  if (msg.status === 'pending') body = <Loading />;
  else if (msg.status === 'error') body = <ErrorNotice error={msg.error} onRetry={() => retry(msg)} />;
  else if (t.clarifications.length) {
    body = <><p style={{ whiteSpace: 'pre-line' }}>{t.text}</p><Clarifications items={t.clarifications} disabled={!isLast} onSend={(text, selections) => send(text, { selections, task: 'explorar' })} /></>;
  } else {
    const empty = !t.results.length && !t.relatedUnits.length;
    body = (
      <>
        <p style={{ whiteSpace: 'pre-line' }}>{t.text}</p>
        <Filters criteria={t.criteria} onRemove={removeCriterion} />
        {!!t.jobs?.length && <section aria-label="Referencias del mercado laboral"><h3>Referencias del mercado laboral</h3><div className="results">{t.jobs.map(job => <article className="card rc" key={job.oferta_id}><h4>{job.titulo || job.cargo || job.oferta_id}</h4><p>{job.empresa || 'Empresa no registrada'} · {job.ciudad || 'Ciudad no registrada'}</p><p>Experiencia: {job.experiencia || 'No registrada'}</p><p>Estudios: {job.educacion || 'No registrados'}</p><p>Fuente: {job.fuente || 'No registrada'} · Fecha: {job.fecha || 'No registrada'}</p><small>Vigencia: {job.vigencia} · Coincidencia temática, requisitos por verificar.</small></article>)}</div></section>}
        {empty && t.profile?.learning_goal ? (
          <EmptyState icon="search" title="no encontré resultados con esos criterios"
            actions={t.criteria.filter((c) => ['max_price', 'max_hours', 'modality'].includes(c.key)).map((c) => (
              <button key={c.key} type="button" className="choice" onClick={() => removeCriterion(c.key)}>Quitar «{c.label}: {c.value}»</button>
            ))}>
            No voy a sugerir opciones que no estén en las fuentes. Puedes ajustar un criterio o reformular tu consulta.
          </EmptyState>
        ) : (
          <>
          <CatalogResults
            results={t.results}
            relatedUnits={t.relatedUnits}
            compare={state.compare}
            onCompare={toggleCompare}
          />
          </>
        )}
        <Trace trace={t.trace} />
      </>
    );
  }
  return (
    <div className="msg-a">
      <Avatar />
      <div className="ans">
        <span className="who">Universidad EAN</span>
        {body}
      </div>
    </div>
  );
}

function CompareTray({ onOpen }) {
  const { state, clearCompare } = useConversation();
  const n = state.compare.length;
  if (!n) return null;
  return (
    <div className="tray on" role="status">
      <Icon name="compare" />
      <span className="tblock"><b>{n === 1 ? '1 opción seleccionada' : `${n} opciones seleccionadas`}</b><small>{n < 2 ? 'Selecciona otra para comparar' : 'Listo para comparar'}</small></span>
      <button type="button" className="icon-btn" onClick={clearCompare} aria-label="Limpiar selección" style={{ color: 'inherit' }}><Icon name="x" size="sm" /></button>
      <Button variant="primary" size="sm" disabled={n < 2} onClick={onOpen}>Comparar</Button>
    </div>
  );
}

function CompareModal({ open, onClose }) {
  const { state } = useConversation();
  const items = state.compare.map((id) => state.items[id]).filter(Boolean);
  const labels = useMemo(() => {
    const m = new Map();
    items.forEach((it) => it.attributes.forEach((a) => m.set(a.key, a.label)));
    return [...m.entries()];
  }, [items]);
  const anyMissing = items.some((i) => i.hasMissing);
  const cols = { gridTemplateColumns: `170px repeat(${items.length}, minmax(0, 1fr))` };
  return (
    <Modal open={open} onClose={onClose} labelledBy="cmp-t">
      <div className="sheet-head">
        <div className="tblock"><span className="kicker">Comparar formación</span><h2 id="cmp-t" style={{ fontSize: 24 }}>comparación lado a lado</h2></div>
        <button type="button" className="icon-btn" onClick={onClose} aria-label="Cerrar" data-autofocus><Icon name="x" /></button>
      </div>
      <div className="cmp-grid" style={cols}>
        <div className="h corner top" />{items.map((i) => <div key={i.id} className="c top"><TypePill pill={i.pill}>{i.kindLabel}</TypePill></div>)}
        <div className="h">Nombre</div>{items.map((i) => <div key={i.id} className="c"><Field value={i.name} /></div>)}
        {labels.map(([key, label]) => (
          <FragmentRow key={key} label={label} cells={items.map((i) => i.attributes.find((a) => a.key === key))} />
        ))}
        <div className="h">Por qué aparece</div>{items.map((i) => <div key={i.id} className="c">{i.reason || '—'}</div>)}
        <div className="h">Fuente</div>{items.map((i) => <div key={i.id} className="c">{i.source?.name || '—'}</div>)}
      </div>
      {anyMissing && <div style={{ marginTop: 14 }}><Callout tone="warn" icon="alert">Hay atributos no registrados en la fuente. Valídalos antes de decidir.</Callout></div>}
    </Modal>
  );
}
function FragmentRow({ label, cells }) {
  return (
    <>
      <div className="h">{label}</div>
      {cells.map((a, i) => <div key={i} className="c">{!a || a.missing ? <Chip tone="warn">No registrado</Chip> : <Field value={a.value} />}</div>)}
    </>
  );
}

export function ConversationView() {
  const { state, send } = useConversation();
  const [cmpOpen, setCmpOpen] = useState(false);
  const endRef = useRef(null);
  const lastTurn = [...state.messages].reverse().find((m) => m.status === 'done' && m.turn?.sources?.length)?.turn;
  const lastId = state.messages[state.messages.length - 1]?.id;

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [state.messages.length]);

  return (
    <section className="view" aria-label="Conversación y resultados">
      <div className="conv">
        <div>
          <div className="thread" aria-live="polite">
            {!state.messages.length && (
              <EmptyState icon="chat" title="aún no hay una conversación" actions={<Button variant="primary" as="a" href="#/">Empezar desde el inicio</Button>}>
                Escribe qué quieres aprender o elige una sugerencia en el inicio.
              </EmptyState>
            )}
            {state.messages.map((m) => (m.role === 'user'
              ? <div key={m.id} className="msg-u">{m.text}</div>
              : <AssistantMessage key={m.id} msg={m} isLast={m.id === lastId} />))}
            <div ref={endRef} />
          </div>
          <CompareTray onOpen={() => setCmpOpen(true)} />
          <div className="dock">
            <Composer id="q-conv" compact placeholder="Cuéntame tus intereses, estudios o experiencia…" onSubmit={(q, task) => send(q, { task })}
              tasks={[{ value: 'explorar', label: 'Explorar oferta', short: 'Explorar', icon: 'search' }, { value: 'ruta', label: 'Construir ruta', short: 'Ruta', icon: 'route' }]} />
            <p className="dock-note">El asistente puede equivocarse. Verifica precios, fechas y requisitos en la fuente oficial antes de decidir.</p>
          </div>
        </div>

        <aside className="aside" aria-label="Contexto de la búsqueda">
          <div className="card">
            <span className="kicker">Criterios aplicados</span>
            <h3>lo que entendí</h3>
            {state.criteria.length
              ? <div className="crit">{state.criteria.map((c) => <div key={c.key}><span>{c.label}</span><span>{c.value}</span></div>)}</div>
              : <p className="muted" style={{ fontSize: 13.5 }}>Aparecerán cuando el asistente interprete tu consulta.</p>}
          </div>
          <div className="card">
            <span className="kicker">Fuentes consultadas</span>
            <h3>de dónde viene</h3>
            {lastTurn ? (
              <div className="mini-list">
                {lastTurn.sources.map((s) => (
                  <div key={s.id} className="row">
                    <span className={cx('type', s.kind === 'continuing_education' ? 'ec' : s.kind === 'study_unit' ? 'unit' : 'prog')} style={{ width: 24, padding: 0 }} />
                    <span className="tblock"><b>{s.name}</b><small>{s.origin}</small></span>
                  </div>
                ))}
              </div>
            ) : <p className="muted" style={{ fontSize: 13.5 }}>Se mostrarán con cada respuesta.</p>}
            <Button size="sm" as="a" href="#/fuentes" style={{ marginTop: 14, width: '100%' }}>Ver todas las fuentes</Button>
          </div>
        </aside>
      </div>
      <CompareModal open={cmpOpen} onClose={() => setCmpOpen(false)} />
    </section>
  );
}
