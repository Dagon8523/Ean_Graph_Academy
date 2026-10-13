import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import { ThemeProvider } from './core/theme.jsx';
import { ConversationProvider } from './core/store.jsx';
import './core/styles/app.css';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <ConversationProvider>
        <App />
      </ConversationProvider>
    </ThemeProvider>
  </StrictMode>
);
