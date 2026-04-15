import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    // Bind to all interfaces so the dev server is reachable from the host
    // when running inside a Docker container.
    host: '0.0.0.0',
  },
})
