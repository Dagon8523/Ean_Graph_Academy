import { BrandSymbol } from '../../common/brand/Brand.jsx';
import { Icon } from '../../common/ui/Icon.jsx';
import { Chip } from '../../common/ui/index.jsx';
import { Composer } from '../shared.jsx';

// Iniciadores de conversación aprobados. `go` decide a dónde lleva cada tarjeta.
const STARTERS = [
  { icon: 'spark', q: 'Quiero aprender inteligencia artificial. ¿Por dónde empiezo?', go: 'chat' },
  { icon: 'route', q: 'Ayúdame a construir una ruta hacia ciencia de datos.', go: 'ruta' },
  { icon: 'cap', q: '¿Qué programas incluyen temas que me interesan?', go: 'chat' },
  { icon: 'wallet', q: 'Explora cursos de Educación Continuada en inteligencia artificial.', go: 'chat' },
  { icon: 'compare', q: 'Busca programas de inteligencia de negocios para comparar.', go: 'chat', task: 'comparar' },
  { icon: 'link', q: 'Muéstrame cómo se conecta una unidad de estudio con su programa.', go: 'detalle' }
];

export function HomeView({ onAsk }) {
  const start = (s) => {
    onAsk(s.q, s.task || 'explorar');
  };
  return (
    <section className="view" aria-labelledby="home-t">
      <div className="home">
        <div className="hero">
          <BrandSymbol className="pattern" />
          <span className="kicker">Cerebro académico · Universidad EAN</span>
          <h2 id="home-t">¿qué quieres aprender? construyamos juntos tu futuro.</h2>
          <p>Cuéntame tus intereses, experiencia y objetivo profesional. Busco en la oferta de la Universidad EAN y te explico qué encontré, por qué es relevante y de qué fuente proviene.</p>
        </div>

        <Composer id="q-home" placeholder="Ej.: quiero aprender análisis de datos y trabajo de tiempo completo…" onSubmit={onAsk} autoFocus />

        <div className="sugs">
          {STARTERS.map((s) => (
            <button key={s.q} type="button" className="sug" onClick={() => start(s)}>
              <span className="i"><Icon name={s.icon} /></span><span><b>{s.q}</b></span>
            </button>
          ))}
          <button type="button" className="sug" disabled aria-disabled="true">
            <span className="i"><Icon name="brief" /></span>
            <span><b>¿Qué formación se relaciona con mi objetivo laboral?</b><small><Chip tone="plan">Próxima funcionalidad · empleabilidad</Chip></small></span>
          </button>
        </div>

        <p className="trust">
          <Chip tone="ok">Consulta pública · sin inicio de sesión</Chip>
          <span>El asistente orienta: no garantiza admisión, homologación, certificación ni contratación, y no consulta datos personales.</span>
        </p>
      </div>
    </section>
  );
}
