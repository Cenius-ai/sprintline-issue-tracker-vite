import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The API lives on its own port; the dev server proxies /api so the browser
// sees a single origin. Both halves are started by ../start.sh.
const apiTarget = process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000';
const port = Number(process.env.FRONTEND_PORT || process.env.PORT || 5173);

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port,
    strictPort: true,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port,
    strictPort: true,
  },
});
