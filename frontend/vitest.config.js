import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// Vitest reuses Vite's transformer, so JSX/ESM/path resolution Just Work.
// Kept separate from vite.config.js purely for clarity.
export default defineConfig({
  // jsxRuntime: 'automatic' tells the React plugin to insert the JSX runtime
  // imports automatically — so test files don't need `import React from 'react'`
  // at the top (matches the production behaviour).
  plugins: [react({ jsxRuntime: 'automatic' })],
  esbuild: {
    jsx: 'automatic',
    jsxImportSource: 'react',
  },
  test: {
    // jsdom gives components a fake DOM to render into. happy-dom is faster
    // but slightly less spec-accurate; jsdom is the conservative choice.
    environment: 'jsdom',
    // Lets test files use describe/it/expect without importing them per-file.
    globals: true,
    setupFiles: ['./src/setupTests.js'],
    // Components import .css for layout. Tests don't care about styles —
    // skipping CSS parsing speeds up startup and avoids unrelated parse errors.
    css: false,
  },
})
