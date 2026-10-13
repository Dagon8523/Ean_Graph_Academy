// Grafos SVG simples y accesibles. Son vistas complementarias: la lista equivalente siempre se muestra al lado.
const NODE = { w: 220, h: 64 };
const nodeClass = (pill, planned) => (planned ? ['n-plan', 't-plan', 't-plan'] : pill === 'unit' ? ['n-unit', 't-unit', 't-unit'] : pill === 'ec' ? ['n-ec', 't-ec', 't-ec'] : ['n-prog', 't-ink', 't-muted']);
const EDGE = { BELONGS_TO: ['e-ok', 'url(#ar)', 'pertenece a · código', 't-lbl'], AFFINITY: ['e-aff', 'url(#ar2)', 'afinidad temática', 't-lbl'], PLANNED: ['e-plan', null, 'prevista', 't-plan'] };
const clean = (s) => (s || '').replace(/^‹|›$/g, '');

function Node({ x, y, w = NODE.w, h = NODE.h, kicker, name, pill, planned }) {
  const [n, tk, tn] = nodeClass(pill, planned);
  return (
    <g>
      <rect className={n} x={x} y={y} width={w} height={h} rx="13" />
      <text className={`${tk} t-k`} x={x + w / 2} y={y + h / 2 - 5} textAnchor="middle">{(kicker || '').toUpperCase()}</text>
      <text className={`${tn} t-ph`} x={x + w / 2} y={y + h / 2 + 15} textAnchor="middle">{clean(name).slice(0, 30)}</text>
    </g>
  );
}

export function RelationsGraph({ relations, title }) {
  const key = (n) => `${n.kind}:${n.id}:${n.name}`;
  const left = [], right = [];
  relations.forEach((r) => { if (!left.some((n) => key(n) === key(r.from))) left.push(r.from); });
  relations.forEach((r) => { if (!right.some((n) => key(n) === key(r.to)) && !left.some((n) => key(n) === key(r.to))) right.push(r.to); });
  const rowH = 100, H = Math.max(left.length, right.length) * rowH + 40;
  const pos = new Map();
  left.forEach((n, i) => pos.set(key(n), { x: 30, y: 20 + i * rowH + (H - 40 - left.length * rowH) / 2 + 18 }));
  right.forEach((n, i) => pos.set(key(n), { x: 510, y: 20 + i * rowH + 18 }));
  return (
    <svg className="graph" viewBox={`0 0 760 ${H}`} role="img" aria-label={title}>
      {relations.map((r, i) => {
        const a = pos.get(key(r.from)), b = pos.get(key(r.to));
        if (!a || !b) return null;
        const [cls, mk, label, tcls] = EDGE[r.type] || EDGE.AFFINITY;
        const x1 = a.x + NODE.w, y1 = a.y + NODE.h / 2, x2 = b.x - (b.x > a.x ? 4 : -NODE.w - 4), y2 = b.y + NODE.h / 2;
        const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
        return (
          <g key={i}>
            <line className={cls} x1={x1} y1={y1} x2={x2} y2={y2} markerEnd={mk || undefined} />
            <rect className="lbl-bg" x={mx - 72} y={my - 13} width="144" height="26" rx="13" />
            <text className={tcls} x={mx} y={my + 5} textAnchor="middle">{label}</text>
          </g>
        );
      })}
      {[...left, ...right].map((n) => {
        const p = pos.get(key(n));
        return <Node key={key(n)} x={p.x} y={p.y} kicker={n.kindLabel || n.kind} name={n.name} pill={n.pill} planned={false} />;
      })}
    </svg>
  );
}

export function RouteGraph({ steps, title }) {
  const avail = steps.filter((s) => s.status !== 'planned');
  const planned = steps.filter((s) => s.status === 'planned');
  const w = 180, gap = Math.max(20, (760 - 40 - avail.length * w) / Math.max(1, avail.length - 1));
  const xs = avail.map((_, i) => 20 + i * (w + gap));
  const H = planned.length ? 260 : 170;
  return (
    <svg className="graph" viewBox={`0 0 760 ${H}`} role="img" aria-label={title}>
      {avail.slice(0, -1).map((s, i) => {
        const aff = s.connection?.type === 'affinity';
        return (
          <g key={i}>
            <line className={aff ? 'e-aff' : 'e-ok'} x1={xs[i] + w} y1="90" x2={xs[i + 1] - 4} y2="90" markerEnd={aff ? 'url(#ar2)' : 'url(#ar)'} />
            <text className={`${aff ? 't-warn' : 't-ink'} t-lab`} x={(xs[i] + w + xs[i + 1]) / 2} y="78" textAnchor="middle">{aff ? 'afinidad' : 'pertenece a'}</text>
          </g>
        );
      })}
      {avail.map((s, i) => <Node key={s.order} x={xs[i]} y={58} w={w} kicker={`${s.order} · ${s.item.kindLabel}`} name={s.item.name} pill={s.item.pill} />)}
      {planned.map((s, i) => {
        const x = 760 - 20 - (planned.length - i) * 200;
        return <Node key={s.order} x={x} y={190} w={180} h={50} kicker={`${s.item.kindLabel} · prevista`} name="" planned />;
      })}
    </svg>
  );
}
