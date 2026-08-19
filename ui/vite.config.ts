import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    watch: {
      // Tauri writes and locks temporary Windows .exe files under src-tauri/target.
      // Vite should not watch that build output folder; otherwise Windows can raise
      // EBUSY while Tauri is compiling/running the native shell.
      ignored: ['**/src-tauri/target/**'],
    },
  },
  preview: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true,
  },
})
