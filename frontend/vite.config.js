import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: { // Vitest configuration
    globals: true,
    environment: 'jsdom', // or 'jsdom'
    testTimeout: 5000,
    setupFiles: './src/setupTests.js', // Optional: if you have a setup file
  },
})
