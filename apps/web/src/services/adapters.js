// Traduce las respuestas de la API (snake_case) al modelo que usa la interfaz.
// Regla: un valor null/undefined significa "no registrado" y nunca se estima.

export const KIND = {
  continuing_education: { label: 'Educación Continuada', pill: 'ec' },
  official_program: { label: 'Programa oficial', pill: 'prog' },
  study_unit: { label: 'Unidad de estudio', pill: 'unit' },
  eanx: { label: 'EAN X', pill: 'eanx' },
  employability: { label: 'Empleabilidad', pill: 'emp' }
};

const money = (v) => (typeof v === 'number' ? '$' + v.toLocaleString('es-CO') : v);
const hours = (v) => (typeof v === 'number' ? `${v} h` : v);

// Atributos visibles por tipo: [clave en la API, etiqueta, formateador, campo de origen]
const ATTRS = {
  continuing_education: [
    ['modality', 'Modalidad'], ['duration_hours', 'Duración', hours], ['price_cop', 'Precio', money], ['start_date', 'Inicio']
  ],
  official_program: [
    ['snies_descripcion_abreviada', 'Nombre para búsqueda', null, 'SNIES_DESCRIPCION_ABREVIADA'],
    ['snies_distincion_genero', 'Denominación del título', null, 'SNIES_DISTINCION_GENERO'],
    ['code', 'Código del programa', null, 'clave del vínculo unidad → programa'],
    ['level', 'Nivel de formación', null, 'campo SNIES · si existe'],
    ['modality', 'Modalidad', null, 'campo SNIES · si existe'],
    ['price_cop', 'Precio', money, 'oferta institucional']
  ],
  study_unit: [['code', 'Código'], ['credits', 'Créditos']],
  eanx: []
};

export function toItem(raw) {
  if (!raw) return null;
  const a = raw.attributes || {};
  const attributes = (ATTRS[raw.kind] || []).map(([key, label, fmt, field]) => {
    const v = a[key];
    const missing = v === null || v === undefined || v === '';
    return { key, label, field, missing, value: missing ? null : fmt ? fmt(v) : v };
  });
  const program = raw.program
    ? { id: raw.program.id, name: raw.program.name, link: raw.program.link_type === 'code' ? 'verified' : raw.program.link_type === 'semantic' ? 'affinity' : 'none' }
    : null;
  return {
    id: raw.id,
    kind: raw.kind,
    kindLabel: KIND[raw.kind]?.label || raw.kind,
    pill: KIND[raw.kind]?.pill || 'prog',
    name: raw.name,
    attributes,
    hasMissing: attributes.some((x) => x.missing),
    reason: raw.reason || null,
    source: raw.source ? { id: raw.source.id, name: raw.source.name, origin: raw.source.origin } : null,
    program,
    units: (raw.units || []).map(toItem)
  };
}

export function toTurn(raw) {
  return {
    conversationId: raw.conversation_id,
    text: raw.reply?.text || '',
    clarifications: (raw.reply?.clarifications || []).map((c) => ({ id: c.id, question: c.question, options: c.options || [] })),
    criteria: (raw.criteria || []).map((c) => ({ key: c.key, label: c.label, value: c.value })),
    results: (raw.results || []).map(toItem),
    relatedUnits: (raw.related_units || []).map(toItem),
    sources: raw.sources_used || [],
    notices: raw.notices || [],
    trace: raw.trace ? { totalMs: raw.trace.total_ms, steps: raw.trace.steps || [] } : null
  };
}

export const toRelations = (raw) =>
  (raw.relations || []).map((r) => ({
    from: { ...r.from, kindLabel: KIND[r.from.kind]?.label, pill: KIND[r.from.kind]?.pill },
    to: { ...r.to, kindLabel: KIND[r.to.kind]?.label, pill: KIND[r.to.kind]?.pill },
    type: r.type, // BELONGS_TO | AFFINITY | PLANNED
    evidence: r.evidence,
    note: r.note
  }));

export const toRoute = (raw) => ({
  goal: raw.goal,
  profile: raw.profile || {},
  steps: (raw.steps || []).map((s) => ({
    order: s.order,
    item: toItem(s.item),
    kind: s.kind, // recommendation | official_requirement
    reason: s.reason,
    status: s.status, // available | planned
    connection: s.connection_to_next || null
  }))
});

export const SOURCE_STATUS = { available: ['ok', 'Disponible'], pending_validation: ['warn', 'Pendiente de validar'], planned: ['plan', 'Integración prevista'] };
export const SOURCE_TYPE = { catalog: 'Catálogo', syllabus: 'Syllabus', external: 'Fuente externa', institutional: 'Fuente institucional' };

export const toSource = (s) => ({
  id: s.id,
  name: s.name,
  type: SOURCE_TYPE[s.type] || s.type,
  owner: s.owner,
  origin: s.origin,
  updatedAt: s.updated_at,
  status: s.status,
  hasRecords: s.status !== 'planned'
});
