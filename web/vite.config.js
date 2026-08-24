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
    rollupOptions: {
      output: {
        // Keep the heavy three.js runtime in its own async chunk so the
        // initial paint doesn't pay for WebGL the user may never see.
        manualChunks(id) {
          if (id.includes('node_modules/three')) return 'three'
          if (id.includes('@designcodeio/threeui')) return 'threeui'
        },
      },
    },
  },
})
