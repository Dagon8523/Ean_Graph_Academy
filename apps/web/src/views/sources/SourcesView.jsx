import { useEffect, useState } from 'react';
import { Icon } from '../../common/ui/Icon.jsx';
import { Button, Chip, ErrorNotice, Field, Skeleton, Tabs } from '../../common/ui/index.jsx';
import { sourcesService } from '../../services/assistantService.js';
import { SOURCE_STATUS } from '../../services/adapters.js';

const ICON = { 'Catálogo': 'db', 'Syllabus': 'doc', 'Fuente externa': 'brief', 'Fuente institucional': 'spark' };

export function SourcesView() {
  const [s, set] = useState({ status: 'loading' });
  const [filter, setFilter] = useState('all');
  const load = () => {
    set({ status: 'loading' });
    sourcesService.list().then((list) => set({ status: 'done', list })).catch((error) => set({ status: 'error', error }));
  };
  useEffect(load, []);

  return (
    <section className="view" aria-labelledby="src-t">
      <div className="page-head">
        <div className="tblock">
          <span className="kicker">Fuentes de conocimiento</span>
          <h2 id="src-t">de dónde vienen las respuestas</h2>
          <p>El asistente combina catálogos estructurados y documentos académicos en un grafo de conocimiento. Aquí ves los catálogos incluidos en la última respuesta de la API.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 22 }}>
        <span className="kicker" style={{ marginBottom: 14 }}>Arquitectura de referencia</span>
        <div className="arch">
          <div className="box"><b>Fuentes</b><small>SAP/OData · syllabus procesados</small></div>
          <div className="arr"><Icon name="arrow" /></div>
          <div className="box"><b>Grafo Neo4j</b><small>Programas, unidades y Educación Continuada</small></div>
          <div className="arr"><Icon name="arrow" /></div>
          <div className="box"><b>API FastAPI</b><small>Herramientas de solo lectura</small></div>
          <div className="arr"><Icon name="arrow" /></div>
          <div className="box front"><b>Frontend React</b><small>Consume la API · sin credenciales ni consultas libres al grafo</small></div>
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <Tabs label="Filtrar por estado" value={filter} onChange={setFilter}
          options={[{ value: 'all', label: 'Todas' }, { value: 'available', label: 'Disponible' }, { value: 'pending_validation', label: 'Pendiente de validar' }, { value: 'planned', label: 'Integración prevista' }]} />
      </div>

      {s.status === 'loading' && <div className="srcs" aria-busy="true">{[0, 1, 2].map((i) => <Skeleton key={i} h={260} r={19} />)}</div>}
      {s.status === 'error' && <ErrorNotice error={s.error} onRetry={load} title="no pude cargar las fuentes" />}
      {s.status === 'done' && (
        <div className="srcs">
          {s.list.filter((x) => filter === 'all' || x.status === filter).map((x) => {
            const [tone, label] = SOURCE_STATUS[x.status] || ['plan', x.status];
            return (
              <article key={x.id} className="card sc">
                <div className="sc-head">
                  <span className="sc-ic"><Icon name={ICON[x.type] || 'db'} /></span>
                  <span className="tblock"><b>{x.name}</b><small>{x.type}</small></span>
                  <Chip tone={tone}>{label}</Chip>
                </div>
                <dl className="dl">
                  <dt>Tipo</dt><dd>{x.type}</dd>
                  <dt>Responsable</dt><dd>{x.owner || <span className="muted">Pendiente de identificar</span>}</dd>
                  <dt>Procedencia</dt><dd>{x.origin}</dd>
                  <dt>Actualización</dt><dd>{x.updatedAt ? <Field value={x.updatedAt} /> : <span className="muted">{x.status === 'planned' ? 'No aplica aún' : 'Sin fecha registrada'}</span>}</dd>
                </dl>
                <div className="sc-foot">
                  {x.hasRecords ? <Button size="sm" icon="list" as="a" href="#/conversacion">{'Ver resultados'}</Button> : <Button size="sm" disabled>Aún sin registros</Button>}
                </div>
              </article>
            );
          })}
        </div>
      )}
      <p className="muted" style={{ fontSize: 13, marginTop: 16 }}>Las fechas de actualización se muestran solo cuando la API las entrega. No se presentan cantidades de registros hasta contar con un inventario validado.</p>
    </section>
  );
}
