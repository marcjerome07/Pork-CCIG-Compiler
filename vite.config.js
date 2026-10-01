import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The Python lexer server (backend/server.py) listens on this address.
const lexerServer = 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, open: true, proxy: { '/api': lexerServer } },
  preview: { proxy: { '/api': lexerServer } },
});
