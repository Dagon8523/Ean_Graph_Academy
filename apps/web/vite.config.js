import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// En desarrollo, /api se redirige al backend FastAPI (sin exponer credenciales al navegador).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const target = env.VITE_API_PROXY_TARGET || 'http://localhost:8001';
  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      strictPort: true,
      proxy: {
        '/api/health': { target, changeOrigin: true, rewrite: () => '/health' },
        '/api': { target, changeOrigin: true }
      }
    },
    build: { outDir: 'dist', sourcemap: false }
  };
});
