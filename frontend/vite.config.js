// Конфиг Vite — сборщика нашего React-приложения.
// https://vite.dev/config/

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  server: {
    // Прокси: все запросы, начинающиеся с /api, Vite пересылает на Flask.
    // Зачем: React работает на localhost:5173, а Flask — на localhost:5001.
    // Браузер считает их «разными сайтами» и без разрешения (CORS) не пускал бы
    // запросы. Через прокси фронтенд ходит в /api как в себя же — и проблема
    // исчезает. То есть fetch('/api/calculate') спокойно долетает до Flask.
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
      },
    },
  },
})
