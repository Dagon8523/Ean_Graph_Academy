#!/usr/bin/env bash
set -euo pipefail
port="${1:-8088}"
[[ "$port" =~ ^[0-9]+$ ]] && (( port >= 1024 && port <= 65535 )) || { echo "Puerto inválido"; exit 1; }
echo "Contenedores y puertos publicados:"
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}'
echo "Proyectos Compose:"
docker compose ls
echo "Listeners del servidor:"
sudo ss -lntup
listeners=$(sudo ss -H -lntup "sport = :$port")
if [[ -n "$listeners" ]]; then
  echo "OCUPADO: $port. No desplegar usando ese puerto."; exit 1
fi
echo "Sin listener en $port en este momento. Revisar también contenedores detenidos y Nginx."
echo "Recursos disponibles:"
free -h
df -h /var/lib/docker
sudo nginx -t
