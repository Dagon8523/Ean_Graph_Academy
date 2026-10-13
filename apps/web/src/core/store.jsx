import { createContext, useCallback, useContext, useMemo, useReducer, useRef } from 'react';
import { assistantService, resetResults } from '../services/assistantService.js';

// Estado de la conversación en memoria (sin persistencia: guardar historial es función propuesta).
const Ctx = createContext(null);
let seq = 0;
const uid = () => `m${++seq}`;

const initial = { conversationId: null, messages: [], criteria: [], compare: [], items: {} };

function reducer(state, a) {
  switch (a.type) {
    case 'reset': return initial;
    case 'user': return { ...state, messages: [...state.messages, { id: uid(), role: 'user', text: a.text }] };
    case 'pending': return { ...state, messages: [...state.messages, { id: a.id, role: 'assistant', status: 'pending', request: a.request }] };
    case 'done': {
      const items = { ...state.items };
      [...a.turn.results, ...a.turn.relatedUnits].forEach((it) => { items[it.id] = it; });
      return {
        ...state,
        conversationId: a.turn.conversationId,
        criteria: a.turn.criteria.length ? a.turn.criteria : state.criteria,
        items,
        messages: state.messages.map((m) => (m.id === a.id ? { ...m, status: 'done', turn: a.turn } : m))
      };
    }
    case 'error': return { ...state, messages: state.messages.map((m) => (m.id === a.id ? { ...m, status: 'error', error: a.error } : m)) };
    case 'retrying': return { ...state, messages: state.messages.map((m) => (m.id === a.id ? { ...m, status: 'pending', error: null } : m)) };
    case 'compare': {
      const has = state.compare.includes(a.id);
      const compare = has ? state.compare.filter((x) => x !== a.id) : [...state.compare, a.id].slice(-3);
      return { ...state, compare };
    }
    case 'compare-clear': return { ...state, compare: [] };
    default: return state;
  }
}

export function ConversationProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initial);
  const busyRef = useRef(false);
  const ref = useRef(state);
  ref.current = state;

  const run = useCallback(async (id, request) => {
    try {
      const turn = await assistantService.send({ conversationId: ref.current.conversationId, ...request });
      dispatch({ type: 'done', id, turn });
    } catch (error) {
      dispatch({ type: 'error', id, error });
    } finally { busyRef.current = false; }
  }, []);

  const send = useCallback((text, extra = {}) => {
    if (busyRef.current) return;
    busyRef.current = true;
    if (text) dispatch({ type: 'user', text });
    const id = uid();
    const request = { message: text, ...extra };
    dispatch({ type: 'pending', id, request });
    run(id, request);
  }, [run]);

  const api = useMemo(() => ({
    state,
    send,
    retry: (msg) => { if(busyRef.current)return;busyRef.current=true;dispatch({ type: 'retrying', id: msg.id }); run(msg.id, msg.request); },
    reset: () => { if(busyRef.current)return;resetResults(ref.current.conversationId); dispatch({ type: 'reset' }); },
    toggleCompare: (id) => dispatch({ type: 'compare', id }),
    clearCompare: () => dispatch({ type: 'compare-clear' }),
    removeCriterion: (key) => {
      const criteria = ref.current.criteria.filter((c) => c.key !== key);
      send(null, { criteria, task: 'explorar' });
    }
  }), [state, send, run]);

  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}

export const useConversation = () => useContext(Ctx);
