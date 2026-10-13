#!/usr/bin/env bash
# Ejecutar en tu equipo local. Detiene solamente Neo4j de Ruta EAN mientras crea el dump.
set -euo pipefail
container=ruta-ean-cerebro-neo4j
[[ "$(docker inspect -f '{{.State.Running}}' "$container")" == true ]] || { echo "El contenedor local debe estar activo"; exit 1; }
image=$(docker inspect -f '{{.Config.Image}}' "$container")
[[ "$image" == neo4j:5.26.30-community ]] || { echo "Versión inesperada: $image"; exit 1; }
backup_dir="$PWD/backups/neo4j_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
backup_dir=$(realpath "$backup_dir")
trap 'docker start "$container" >/dev/null' EXIT
docker stop --time 120 "$container"
docker run --rm --user 0 --volumes-from "$container"   --mount "type=bind,source=$backup_dir,target=/backups"   --entrypoint neo4j-admin "$image" database dump neo4j --to-path=/backups
sudo chown "$(id -u):$(id -g)" "$backup_dir/neo4j.dump"
(cd "$backup_dir" && sha256sum neo4j.dump > SHA256SUMS)
echo "Dump listo en: $backup_dir"
