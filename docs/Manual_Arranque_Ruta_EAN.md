# Ruta EAN — Manual de instalación y arranque local

## Configuración actual

- Proyecto en WSL: `~/Ean_Graph_Academy/Ruta_EAN_Cerebro_Academico`.
- Neo4j y frontend: administrados por un único `docker-compose.yml`.
- FastAPI y agente: ejecutados en WSL, fuera de Docker.
- Frontend: http://localhost:8080.
- Documentación de la API: http://localhost:8001/docs.
- FastAPI debe escuchar en `0.0.0.0:8001`.

## 1. Instalación inicial

Este apartado aplica si estás preparando el equipo. Si ya funciona, continúa en el apartado 2.

1. Instala Docker Desktop y habilita su integración con la distribución Ubuntu/WSL del proyecto.
2. Coloca el repositorio en la ruta indicada. Comprueba que contiene `apps/web/`, `ops/docker/`, `apps/api/` y `docker-compose.yml`.
3. Conserva el `.env` configurado del backend con las variables de Neo4j y del agente. No lo reemplaces con el ejemplo del frontend.
4. En Ubuntu/WSL, prepara el entorno Python si aún no existe:

```bash
cd ~/Ean_Graph_Academy/Ruta_EAN_Cerebro_Academico
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

5. Valida el Compose y construye los servicios:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

6. Continúa con el inicio de FastAPI descrito en el apartado 3.

> Construir los contenedores no importa el grafo. En un equipo nuevo se requiere restaurar o cargar los datos de Neo4j mediante el procedimiento del proyecto. En el equipo actual se reutilizan los volúmenes existentes.

## 2. Arranque diario: Docker, Neo4j y frontend

1. Abre **Docker Desktop** y espera a que el motor esté listo.
2. Abre una primera terminal **Ubuntu/WSL**.
3. Ejecuta:

```bash
cd ~/Ean_Graph_Academy/Ruta_EAN_Cerebro_Academico
docker compose up -d
docker compose ps
```

Comprueba que aparecen:

- `ruta-ean-cerebro-neo4j`: activo; espera a que esté `healthy`.
- `ruta-ean-cerebro-web`: activo, con el puerto `8080` publicado.

Para el arranque diario no necesitas `--build`.

## 3. Iniciar FastAPI y el agente

Abre una segunda terminal **Ubuntu/WSL** y ejecuta:

```bash
cd ~/Ean_Graph_Academy/Ruta_EAN_Cerebro_Academico
source .venv/bin/activate
uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8001
```

Espera el mensaje de arranque de Uvicorn. **Deja esta terminal abierta** durante el uso.

Si el agente utiliza Ollama local, asegúrate de que esté activo y de que el modelo configurado esté disponible. Si Ollama se administra manualmente en WSL, puedes iniciarlo en una tercera terminal:

```bash
ollama serve
```

No ejecutes una segunda instancia si Ollama ya está activo como aplicación o servicio.

## 4. Verificar la conexión

Desde la primera terminal:

```bash
curl -f http://localhost:8080/api/health
```

Respuesta esperada:

```json
{"status":"ok","neo4j":"connected"}
```

Después:

1. Abre http://localhost:8080.
2. Envía un mensaje al agente.
3. Comprueba que responde y que puede recuperar los resultados académicos.

La respuesta de salud comprueba FastAPI y Neo4j. El mensaje en el navegador comprueba adicionalmente el flujo conversacional del agente.

## 5. Acceder desde otros computadores

En **PowerShell o CMD de Windows**, ejecuta:

```powershell
ipconfig
```

Busca la IPv4 del adaptador **Wi-Fi o Ethernet conectado**. No uses la del adaptador virtual de WSL.

Comparte esta dirección, sustituyendo la IP:

```text
http://IP_DE_WINDOWS:8080
```

Ejemplo:

```text
http://192.168.80.93:8080
```

- Los computadores visitantes deben estar en una red que permita comunicarse con tu equipo.
- Si la IP cambia en la oficina, comparte la nueva dirección. No necesitas modificar código ni reconstruir el frontend.
- En tu propio equipo puedes seguir usando http://localhost:8080.
- Mantén el equipo encendido, sin suspensión, con Docker y FastAPI activos.

### Si Windows bloquea el puerto

En **PowerShell como administrador**, para una red con perfil privado:

```powershell
New-NetFirewallRule -DisplayName "EAN frontend local 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow -Profile Private -RemoteAddress LocalSubnet
```

Si la red institucional tiene otro perfil o aísla los equipos, coordina la habilitación con TI. No necesitas abrir los puertos de Neo4j a los visitantes.

Desde otro computador Windows puedes comprobar el puerto:

```powershell
Test-NetConnection IP_DE_WINDOWS -Port 8080
```

## 6. Aplicar cambios del frontend

Después de editar archivos en `apps/web/`, ejecuta desde la raíz del proyecto:

```bash
docker compose up -d --build web
```

Recarga el navegador con **Ctrl+F5**. Si el favicon conserva una versión anterior, cierra la pestaña y vuelve a abrirla.

## 7. Detener el proyecto

1. En la terminal de FastAPI, presiona **Ctrl+C**.
2. Desde la raíz del proyecto:

```bash
docker compose stop
```

Los datos permanecen en los volúmenes de Neo4j. Si iniciaste Ollama manualmente para esta sesión, puedes detenerlo con Ctrl+C en su terminal.

## 8. Diagnóstico rápido

| Problema | Comprobación |
|---|---|
| Docker no responde | Abre Docker Desktop y espera a que esté listo. |
| El frontend no abre | Ejecuta `docker compose ps` y revisa `docker compose logs --tail=100 web`. |
| Salud responde con error | Comprueba que Uvicorn esté activo en `0.0.0.0:8001` y revisa `curl -f http://localhost:8001/health`. |
| Neo4j no está listo | Revisa `docker compose logs --tail=100 neo4j`. |
| Salud funciona, pero el agente falla | Revisa la terminal de FastAPI y el proveedor/modelo configurado del agente. |
| Otro computador no abre la página | Revisa IP de Windows, firewall y permisos de comunicación de la red. |
| No aparecen cambios visuales | Reconstruye `web` y recarga con Ctrl+F5. |
| Build falla con `no such host` de Docker Hub | Reintenta la descarga de la imagen indicada; si persiste, revisa DNS/conectividad de Docker Desktop. |

Para reintentar la descarga de las imágenes utilizadas:

```bash
docker pull node:22-alpine
docker pull nginx:1.27-alpine
docker compose up -d --build web
```

## Lista de arranque diario

- [ ] Docker Desktop listo.
- [ ] `docker compose up -d` ejecutado.
- [ ] Neo4j activo y saludable.
- [ ] FastAPI activo en `0.0.0.0:8001`.
- [ ] Proveedor del agente disponible; Ollama activo si corresponde.
- [ ] `/api/health` devuelve `ok` y `connected`.
- [ ] Mensaje del agente probado en el navegador.
- [ ] IP de Windows actual compartida si habrá visitantes.
