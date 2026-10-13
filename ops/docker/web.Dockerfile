# Frontend Cerebro Académico EAN — React 18 + Vite 6, servido con Nginx.
# Construir desde la raíz del repositorio:
#   docker build -f ops/docker/web.Dockerfile -t cae-web .

# ---------- 1) Build ----------
FROM node:22-alpine AS build
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/web/ ./
RUN npm run build

# ---------- 2) Runtime ----------
FROM nginx:1.27-alpine
# Plantilla de Nginx: la imagen oficial reemplaza ${VARIABLES} al iniciar (envsubst).
COPY ops/docker/nginx/default.conf.template /etc/nginx/templates/default.conf.template
# Genera /config.js con la configuración en tiempo de ejecución (sin credenciales).
COPY ops/docker/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
RUN chmod +x /docker-entrypoint.d/40-runtime-config.sh
COPY --from=build /app/dist /usr/share/nginx/html

# URL interna del backend FastAPI (red de Docker). El navegador nunca la ve: llama a /api.
ENV API_UPSTREAM=http://api:8001 \
    USE_MOCKS=false \
    APP_ENV=production \
    REQUEST_TIMEOUT_MS=120000

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1
