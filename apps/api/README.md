# API — Ruta EAN

La capa HTTP vive en `apps/api/src/`. Configuración, servicios y repositorios
compartidos permanecen en `src/`, según la separación de la plantilla.

Ejecutar desde la raíz del proyecto, con el entorno virtual activo:

```bash
python -m ops.scripts.init_academic_api_indexes
uvicorn apps.api.src.main:app --port 8001 --reload
```

Documentación: http://127.0.0.1:8001/docs.
Endpoint: `POST /api/v1/recommendations/learning-path`.

```json
{"learning_goal": "Quiero aprender programación orientada a objetos con Java", "limit": 5}
```

La respuesta conserva los campos anteriores y añade `unidades_estudio`, `eanx`
y `ruta_academica`. Los recorridos usan conexiones temáticas revisadas y vigentes
por hash/versión del embedding. Las relaciones estructurales muestran el programa
de la unidad y el curso del módulo EAN X. La afinidad no establece homologaciones
ni orden de prerrequisitos; la cobertura actual es parcial.

Los textos idénticos pueden compartir un representante de comparación. El campo
`usa_representante_textual` distingue este caso; los contenedores se recuperan
por sus relaciones estructurales reales, no por semejanza del nombre.

Pruebas de esta integración:

```bash
python -m unittest discover -s tests/unit -p 'test_academic_path_v1.py' -v
```

Después ejecutar también la suite completa existente. Los dobles de repositorio
antiguos deben incorporar `search_units`, `search_eanx`, `find_semantic_paths`,
`find_containers` y `get_continuing_education_by_ids`.
