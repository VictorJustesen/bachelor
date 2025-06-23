import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true,
    },

    // Add the proxy configuration here
    proxy: {
      // Proxy any request that starts with /api
      '/api': {
        // Forward it to your backend server
        target: 'http://backend:8000',
        // Needed for the proxy to work correctly
        changeOrigin: true,
      },
  },
}
})