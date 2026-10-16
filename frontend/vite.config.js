import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Permintaan /api dan /uploads diteruskan ke backend Flask (port 5000)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:5000',
      '/uploads': 'http://localhost:5000',
    },
  },
})
