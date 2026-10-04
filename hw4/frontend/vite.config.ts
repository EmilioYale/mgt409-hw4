import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The FastAPI backend runs on :8000. Proxying keeps the browser on one origin,
// so /api calls and /media images "just work" in dev with no CORS setup.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
    },
  },
})
