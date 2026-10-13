// ============================================================
// CORRECCIÓN DE ÍNDICES
// Relación estructural por código.
// Búsqueda semántica del programa exclusivamente por campos SNIES.
// ============================================================


// Eliminar índices de la interpretación anterior

DROP INDEX programa_nombre_match_idx IF EXISTS;

DROP INDEX unidad_programa_normalizado_idx IF EXISTS;


// El índice full-text existente debe reconstruirse,
// porque IF NOT EXISTS no cambia sus propiedades.

DROP INDEX programa_busqueda_fulltext_idx IF EXISTS;


// Crear índices para la relación estructural por código

CREATE INDEX programa_codigo_relacion_idx IF NOT EXISTS
FOR (p:ProgramaOficial)
ON (p.codigo_programa);

CREATE INDEX unidad_codigo_programa_idx IF NOT EXISTS
FOR (u:UnidadEstudio)
ON (u.codigo_programa);


// Búsqueda semántica directa de programas:
// solamente descripción abreviada y distinción de género.

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
CREATE CONSTRAINT oferente_id_unique IF NOT EXISTS
FOR (n:Oferente)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT facultad_id_unique IF NOT EXISTS
FOR (n:Facultad)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT sede_id_unique IF NOT EXISTS
FOR (n:Sede)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT centro_costos_id_unique IF NOT EXISTS
FOR (n:CentroCostos)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT grupo_formacion_id_unique IF NOT EXISTS
FOR (n:GrupoFormacion)
REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT metodo_formacion_id_unique IF NOT EXISTS
FOR (n:MetodoFormacion)
REQUIRE n.id IS UNIQUE;