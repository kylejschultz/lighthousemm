import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const DEV_DOMAIN = process.env.DEV_DOMAIN || 'lhmm.dev'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    strictPort: true,
    allowedHosts: [DEV_DOMAIN, 'localhost'],
    hmr: {
      host: DEV_DOMAIN,
      protocol: 'wss',
      clientPort: 443,
    },
  },
})
