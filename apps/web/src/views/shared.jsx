import { useEffect, useRef, useState } from 'react';
import { Icon } from '../common/ui/Icon.jsx';

// Tareas del asistente (no son agentes distintos).
export const TASKS = [
  { value: 'explorar', label: 'Explorar oferta', short: 'Explorar', icon: 'search' },
  { value: 'comparar', label: 'Comparar', short: 'Comparar', icon: 'compare' },
  { value: 'ruta', label: 'Construir ruta', short: 'Ruta', icon: 'route' },
  { value: 'fuentes', label: 'Fuentes', short: 'Fuentes', icon: 'db' },
  { value: 'conexiones', label: 'Conexiones', short: 'Conexiones', icon: 'graph' }
];

export function Composer({ placeholder, onSubmit, tasks = TASKS, compact, autoFocus, initialTask = 'explorar', id }) {
  const [text, setText] = useState('');
  const [task, setTask] = useState(initialTask);
  const ta = useRef(null);
  useEffect(() => { if (autoFocus) ta.current?.focus(); }, [autoFocus]);
  const resize = (el) => { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 180) + 'px'; };
  const submit = (e) => {
    e?.preventDefault();
    const q = text.trim();
    if (!q) return;
    onSubmit(q, task);
    setText('');
    if (ta.current) ta.current.style.height = 'auto';
  };
  return (
    <form className="composer" onSubmit={submit}>
      <label className="sr-only" htmlFor={id}>Escribe tu consulta</label>
      <textarea id={id} ref={ta} rows={compact ? 1 : 2} placeholder={placeholder} value={text}
        onChange={(e) => { setText(e.target.value); resize(e.target); }}
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) submit(e); }} />
      <div className="c-row" role="group" aria-label="Tarea del asistente">
        {tasks.map((t) => (
          <button key={t.value} type="button" className="task" aria-pressed={task === t.value} title={t.label} onClick={() => setTask(t.value)}>
            <Icon name={t.icon} size="sm" /><span className="lbl">{compact ? t.short : t.label}</span>
          </button>
        ))}
        <button type="submit" className="send" aria-label="Enviar consulta" disabled={!text.trim()}><Icon name="up" /></button>
      </div>
    </form>
  );
}
