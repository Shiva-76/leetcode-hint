import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { crx } from '@crxjs/vite-plugin';
import { viteStaticCopy } from 'vite-plugin-static-copy';
import manifest from './manifest.json' with { type: 'json' };
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [
    react(),
    crx({ manifest }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
      // Shim Node built-ins used by web-tree-sitter so Vite doesn't warn
      fs:   path.resolve(__dirname, 'src/shims/empty.js'),
      path: path.resolve(__dirname, 'src/shims/empty.js'),
    },
  },
  build: {
    assetsInlineLimit: 0,    // Don't inline wasm files
    sourcemap: false,
    rollupOptions: {
      // Suppress web-tree-sitter eval warnings
      onwarn(warning, warn) {
        if (warning.code === 'EVAL' && warning.id?.includes('web-tree-sitter')) return;
        warn(warning);
      },
    },
  },
  // Exclude web-tree-sitter from pre-bundling (it handles its own wasm loading)
  optimizeDeps: {
    exclude: ['web-tree-sitter'],
  },
  server: {
    port: 5173,
    strictPort: true,
    hmr: { port: 5173 },
  },
});
