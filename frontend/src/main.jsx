// Точка входа React-приложения.
// Здесь мы «монтируем» (рисуем) компонент <App /> внутри <div id="root">
// из index.html.

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
