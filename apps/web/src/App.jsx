import { useCallback } from 'react';
import { IconSprite } from './common/ui/Icon.jsx';
import { AppShell } from './common/layout/Layout.jsx';
import { useRoute, navigate } from './core/router.js';
import { useConversation } from './core/store.jsx';
import { HomeView } from './views/home/HomeView.jsx';
import { ConversationView } from './views/conversation/ConversationView.jsx';
import { DetailView } from './views/detail/DetailView.jsx';
import { RouteView } from './views/route/RouteView.jsx';
import { SourcesView } from './views/sources/SourcesView.jsx';

export default function App() {
  const route = useRoute();
  const { send, reset } = useConversation();

  const ask = useCallback((text, task) => {
    reset();
    navigate('/conversacion');
    send(text, { task });
  }, [send, reset]);

  let view;
  switch (route.name) {
    case 'conversacion': view = <ConversationView />; break;
    case 'detalle': view = <DetailView key={route.params.id} id={route.params.id} />; break;
    case 'ruta': view = <RouteView />; break;
    case 'fuentes': view = <SourcesView />; break;
    default: view = <HomeView onAsk={ask} />;
  }

  return (
    <>
      <IconSprite />
      <AppShell route={route} onNew={reset}>{view}</AppShell>
    </>
  );
}
