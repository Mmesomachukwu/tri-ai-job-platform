import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// No Docker - runs directly with `npm run dev`. Proxies /api to the
// FastAPI backend during development so the frontend never needs a
// hardcoded absolute URL or CORS workarounds in dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
