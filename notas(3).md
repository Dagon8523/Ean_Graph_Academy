# Consultas Cypher — Cerebro Institucional de Oferta Académica

Este documento contiene diez consultas para presentar el estado actual del grafo en Neo4j Browser.

- Las consultas **1 y 10** muestran resultados en tabla.
- Las consultas **2 a 9** están diseñadas para visualizarse en modo **Graph**.
- Actualmente, `ProgramaOficial` y `UnidadEstudio` forman el componente de oferta oficial.
- `Formacion` y `Evento` forman el componente de Educación Continuada.
- No existe todavía un camino entre `ProgramaOficial` y `Formacion`; por eso el documento no representa una relación que aún no está creada.

---

## 1. Inventario ejecutivo de la oferta académica

**Tipo de resultado:** tabla.

**Objetivo:** mostrar el volumen de información disponible en las cuatro entidades principales del cerebro institucional.

**Interpretación:** permite presentar cuántos programas oficiales, unidades de estudio, formaciones de Educación Continuada y eventos existen actualmente en Neo4j.

```cypher
MATCH (n)
WHERE n:ProgramaOficial
   OR n:UnidadEstudio
   OR n:Formacion
   OR n:Evento
UNWIND labels(n) AS etiqueta
WITH etiqueta, count(DISTINCT n) AS cantidad
WHERE etiqueta IN ["ProgramaOficial", "UnidadEstudio", "Formacion", "Evento"]
RETURN etiqueta, cantidad
ORDER BY cantidad DESC;
```

---

## 2. Programas oficiales y unidades de estudio

**Tipo de resultado:** visualización del grafo.

**Objetivo:** mostrar la estructura curricular de la oferta oficial mediante las conexiones directas entre programas y unidades de estudio.

**Interpretación:** cada nodo de programa representa una oferta académica oficial; los nodos conectados representan las unidades de estudio que forman parte de su estructura.

```cypher
MATCH path =
    (programa:ProgramaOficial)-[relacion]-(unidad:UnidadEstudio)
RETURN path
LIMIT 150;
```

---

## 3. Vista ampliada de los programas oficiales

**Tipo de resultado:** visualización del grafo.

**Objetivo:** recorrer hasta dos niveles alrededor de los programas oficiales para mostrar su contexto dentro del cerebro institucional.

**Interpretación:** permite visualizar el programa como punto de partida y explorar las entidades que dependen directa o indirectamente de él.

```cypher
MATCH path =
    (programa:ProgramaOficial)-[*1..2]-(entidad)
RETURN path
LIMIT 150;
```

---

## 4. Unidades de estudio y su contexto académico

**Tipo de resultado:** visualización del grafo.

**Objetivo:** centrar la presentación en las unidades de estudio y observar con qué entidades se encuentran relacionadas.

**Interpretación:** muestra que la unidad de estudio es un elemento reutilizable y navegable dentro de la estructura académica, no solamente una columna en una tabla.

```cypher
MATCH path =
    (unidad:UnidadEstudio)-[relacion]-(entidad)
RETURN path
LIMIT 150;
```

---

## 5. Educación Continuada: formaciones y eventos

**Tipo de resultado:** visualización del grafo.

**Objetivo:** mostrar cómo una formación de Educación Continuada puede tener uno o varios eventos académicos asociados.

**Interpretación:** `Formacion` representa el producto académico y `Evento` representa su ejecución concreta, con fechas, capacidades, duración, estado u otros atributos provenientes de SAP.

```cypher
MATCH path =
    (formacion:Formacion)-[:TIENE_EVENTO]->(evento:Evento)
RETURN path
LIMIT 150;
```

---

## 6. Contexto completo de Educación Continuada

**Tipo de resultado:** visualización del grafo.

**Objetivo:** expandir hasta dos niveles desde cada formación para observar eventos y demás entidades institucionales relacionadas.

**Interpretación:** permite mostrar que Educación Continuada no está almacenada como una lista plana: cada formación se integra con ejecuciones y contexto administrativo u operativo.

```cypher
MATCH path =
    (formacion:Formacion)-[*1..2]-(entidad)
RETURN path
LIMIT 180;
```

---

## 7. Ecosistema institucional alrededor de los eventos

**Tipo de resultado:** visualización del grafo.

**Objetivo:** mostrar cómo los eventos se relacionan con formación, grupo, método, sede, oferente, facultad y centro de costos.

**Interpretación:** esta vista evidencia que un evento académico contiene contexto institucional suficiente para ser consultado y explicado desde diferentes perspectivas.

```cypher
MATCH path =
    (evento:Evento)-[relacion]-(entidad)
WHERE entidad:Formacion
   OR entidad:GrupoFormacion
   OR entidad:MetodoFormacion
   OR entidad:Sede
   OR entidad:Oferente
   OR entidad:Facultad
   OR entidad:CentroCostos
RETURN path
LIMIT 200;
```

---

## 8. Vista ejecutiva de oferta oficial y Educación Continuada

**Tipo de resultado:** visualización del grafo.

**Objetivo:** mostrar en una misma pantalla una muestra del componente de programas oficiales y otra del componente de Educación Continuada.

**Interpretación:** los dos conjuntos aparecerán separados porque todavía no existe una relación entre `ProgramaOficial` y `Formacion`. Esta vista permite explicar cuál es el siguiente puente que deberá incorporar el cerebro institucional.

```cypher
CALL {
    MATCH pathOficial =
        (programa:ProgramaOficial)-[relacionOficial]-(unidad:UnidadEstudio)
    RETURN pathOficial
    LIMIT 12
}
CALL {
    MATCH pathContinuada =
        (formacion:Formacion)-[:TIENE_EVENTO]->(evento:Evento)
    RETURN pathContinuada
    LIMIT 12
}
RETURN pathOficial, pathContinuada;
```

---

## 9. Cerebro institucional combinado con contexto

**Tipo de resultado:** visualización del grafo.

**Objetivo:** presentar simultáneamente programas con unidades de estudio y formaciones con su contexto institucional.

**Interpretación:** ofrece una visión amplia de las dos ofertas académicas existentes. La separación visual entre componentes representa fielmente el estado actual y permite explicar la evolución futura del grafo.

```cypher
CALL {
    MATCH pathOficial =
        (programa:ProgramaOficial)-[*1..2]-(unidad:UnidadEstudio)
    RETURN pathOficial
    LIMIT 10
}
CALL {
    MATCH pathContinuada =
        (formacion:Formacion)-[*1..2]-(entidad)
    RETURN pathContinuada
    LIMIT 15
}
RETURN pathOficial, pathContinuada;
```

---

## 10. Mapa técnico de relaciones académicas

**Tipo de resultado:** tabla.

**Objetivo:** identificar qué tipos de nodos conecta cada relación y cuántas conexiones existen en el modelo.

**Interpretación:** funciona como cierre técnico de la demostración, comprueba la arquitectura real del grafo y evita asumir etiquetas o relaciones inexistentes.

```cypher
MATCH (origen)-[relacion]->(destino)
WHERE origen:ProgramaOficial
   OR origen:UnidadEstudio
   OR origen:Formacion
   OR origen:Evento
   OR destino:ProgramaOficial
   OR destino:UnidadEstudio
   OR destino:Formacion
   OR destino:Evento
RETURN
    labels(origen) AS origen,
    type(relacion) AS relacion,
    labels(destino) AS destino,
    count(*) AS cantidad
ORDER BY cantidad DESC;
```

CALL {
    MATCH rutaOficial =
        (programa:ProgramaOficial)-[relacion]-(unidad:UnidadEstudio)
    RETURN rutaOficial
    LIMIT 400
}
CALL {
    MATCH rutaContinuada =
        (formacion:Formacion)-[:TIENE_EVENTO]->(evento:Evento)
    RETURN rutaContinuada
    LIMIT 400
}
RETURN rutaOficial, rutaContinuada;
