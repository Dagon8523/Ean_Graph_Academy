#!/bin/sh
# Escribe /usr/share/nginx/html/config.js a partir de variables de entorno.
# Solo valores públicos: nunca poner aquí llaves ni credenciales.
set -eu
cat > /usr/share/nginx/html/config.js <<EOC
window.__APP_CONFIG__ = {
  apiBaseUrl: "${API_BASE_URL:-/api}",
  useMocks: "${USE_MOCKS:-false}",
  requestTimeoutMs: "${REQUEST_TIMEOUT_MS:-120000}",
  appEnv: "${APP_ENV:-production}"
};
EOC
echo "config.js generado (useMocks=${USE_MOCKS:-false}, apiBaseUrl=${API_BASE_URL:-/api})"
