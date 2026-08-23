import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Build into the existing GitHub Pages publish dir (./static_output)
// so the daily Python job (leaderboard.json + badges) stays intact.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: '../static_output',
    emptyOutDir: false,
  },
})
