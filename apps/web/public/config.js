// Configuración en tiempo de ejecución. En Docker este archivo se reescribe al iniciar
// el contenedor (ops/docker/40-runtime-config.sh) a partir de variables de entorno.
// No incluir credenciales: el frontend solo consume la API.
window.__APP_CONFIG__ = window.__APP_CONFIG__ || {};
