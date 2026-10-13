// ============================================================
// RUTA EAN - CEREBRO ACADÉMICO
// Schema Neo4j
//
// Fuente oficial del esquema del grafo.
// Debe poder ejecutarse sobre una instancia Neo4j 5.x vacía.
//
// PRINCIPIOS:
// - Relaciones estructurales y semánticas son diferentes.
// - No se modela FuenteDatos como nodo central.
// - ProgramaOficial y UnidadEstudio forman el núcleo oficial.
// - Formacion representa Educación Continuada.
// - Preparado para incorporar EANX y OfertaLaboral en Fase 3.
// ============================================================


// ============================================================
// 1. CONSTRAINTS - NÚCLEO ACADÉMICO
// ============================================================

CREATE CONSTRAINT programa_oficial_id_unique IF NOT EXISTS
FOR (n:ProgramaOficial)
REQUIRE n.programa_id IS UNIQUE;

CREATE CONSTRAINT unidad_estudio_id_unique IF NOT EXISTS
FOR (n:UnidadEstudio)
REQUIRE n.unidad_id IS UNIQUE;


// ============================================================
// 2. CONSTRAINTS - DIMENSIONES ACADÉMICAS
// ============================================================

CREATE CONSTRAINT modalidad_id_unique IF NOT EXISTS
FOR (n:Modalidad)
REQUIRE n.modalidad_id IS UNIQUE;

CREATE CONSTRAINT nivel_formacion_id_unique IF NOT EXISTS
FOR (n:NivelFormacion)
REQUIRE n.nivel_id IS UNIQUE;

CREATE CONSTRAINT tipo_programa_id_unique IF NOT EXISTS
FOR (n:TipoPrograma)
REQUIRE n.tipo_programa_id IS UNIQUE;


// ============================================================
// 3. CONSTRAINTS - EDUCACIÓN CONTINUADA
// ============================================================

CREATE CONSTRAINT evento_id_unique IF NOT EXISTS
FOR (n:Evento)
REQUIRE n.evento_id IS UNIQUE;

CREATE CONSTRAINT formacion_id_unique IF NOT EXISTS
FOR (n:Formacion)
REQUIRE n.formacion_id IS UNIQUE;

CREATE CONSTRAINT grupo_formacion_id_unique IF NOT EXISTS
FOR (n:GrupoFormacion)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT metodo_formacion_id_unique IF NOT EXISTS
FOR (n:MetodoFormacion)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT sede_id_unique IF NOT EXISTS
FOR (n:Sede)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT oferente_id_unique IF NOT EXISTS
FOR (n:Oferente)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT facultad_id_unique IF NOT EXISTS
FOR (n:Facultad)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT centro_costos_id_unique IF NOT EXISTS
FOR (n:CentroCostos)
REQUIRE n.id IS UNIQUE;


// ============================================================
// 4. ÍNDICES ESTRUCTURALES
//
// Relación determinística:
//
// ProgramaOficial
//       |
//       | CONTIENE_UNIDAD
//       v
// UnidadEstudio
//
// La unión se realiza por codigo_programa.
// ============================================================

CREATE INDEX programa_codigo_relacion_idx IF NOT EXISTS
FOR (p:ProgramaOficial)
ON (p.codigo_programa);

CREATE INDEX unidad_codigo_programa_idx IF NOT EXISTS
FOR (u:UnidadEstudio)
ON (u.codigo_programa);


// ============================================================
// 5. BÚSQUEDA SEMÁNTICA - PROGRAMAS OFICIALES
//
// REGLA FUNCIONAL:
// ProgramaOficial participa en búsqueda semántica utilizando
// EXCLUSIVAMENTE:
//
// - snies_descripcion_abreviada
// - snies_distincion_genero
//
// No agregar facultad, modalidad, school, nivel, ubicación,
// etc. al texto semántico sin cambiar explícitamente la regla
// funcional del proyecto.
// ============================================================

CREATE FULLTEXT INDEX programa_busqueda_fulltext_idx IF NOT EXISTS
FOR (p:ProgramaOficial)
ON EACH [
    p.snies_descripcion_abreviada,
    p.snies_distincion_genero
]
OPTIONS {
    indexConfig: {
        `fulltext.analyzer`: 'spanish',
        `fulltext.eventually_consistent`: true
    }
};


// ============================================================
// 6. BÚSQUEDA - EDUCACIÓN CONTINUADA
// ============================================================

CREATE FULLTEXT INDEX formacion_busqueda_fulltext_idx IF NOT EXISTS
FOR (f:Formacion)
ON EACH [
    f.nombre,
    f.nombre_corto,
    f.texto_semantico
]
OPTIONS {
    indexConfig: {
        `fulltext.analyzer`: 'spanish',
        `fulltext.eventually_consistent`: true
    }
};


// ============================================================
// 7. MODELO DE RELACIONES
// ============================================================
//
// RELACIONES ESTRUCTURALES ACTUALES
// --------------------------------
//
// (:ProgramaOficial)-[:CONTIENE_UNIDAD]->(:UnidadEstudio)
//
// (:ProgramaOficial)-[:TIENE_MODALIDAD]->(:Modalidad)
//
// (:ProgramaOficial)-[:TIENE_NIVEL]->(:NivelFormacion)
//
// (:ProgramaOficial)-[:ES_TIPO]->(:TipoPrograma)
//
// (:Formacion)-[:TIENE_EVENTO]->(:Evento)
//
//
// RELACIONES SEMÁNTICAS - FASE 2
// ------------------------------
//
// (:Formacion)-[:SIMILAR_A_PROGRAMA]->(:ProgramaOficial)
//
// (:Formacion)-[:SIMILAR_A_UNIDAD]->(:UnidadEstudio)
//
// Estas relaciones son inferidas algorítmicamente.
// Deben almacenar evidencia del cálculo, por ejemplo:
//
// - similitud
// - metodo
// - modelo
// - version_modelo
// - fecha_calculo
// - validada
//
//
// EXTENSIBILIDAD - FASE 3
// -----------------------
//
// Se incorporarán nuevas fuentes sin modificar el núcleo:
//
// (:FormacionEANX)
// (:OfertaLaboral)
//
// y posteriormente se evaluará:
//
// (:Competencia)
//
// El motor semántico deberá ser reutilizable entre diferentes
// tipos de entidades y no depender exclusivamente de Formacion.
// ============================================================