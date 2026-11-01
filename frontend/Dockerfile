# Dockerfile фронтенда: два этапа (multi-stage build).
#
# Идея: React нужно «собрать» (Vite превращает JSX+импорты в обычные
# HTML/JS/CSS файлы). Сборщик тяжёлый (Node.js ~сотни МБ), а отдавать
# результат будет лёгкий nginx. Поэтому собираем в одном образе,
# а в финальный берём только готовые статики из другого.

# ---------- Этап 1: сборка ----------
FROM node:22-alpine AS build
WORKDIR /app

# Копируем списки зависимостей первыми — ради кэширования слоёв
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build   # результат появится в /app/dist

# ---------- Этап 2: раздаём статикой через nginx ----------
FROM nginx:1.27-alpine

# Наша конфигурация nginx: отдаёт dist/ и проксирует /api на бэкенд
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Забираем собранные файлы из этапа 1 — весь node_modules остаётся позади
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
