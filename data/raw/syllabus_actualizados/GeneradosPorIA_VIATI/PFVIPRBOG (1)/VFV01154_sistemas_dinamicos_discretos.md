<!-- CONFIDENCE: DRAFT_AI — reconstructed from metadata only, requires validation -->

---
# Sílabo — SISTEMAS DINÁMICOS DISCRETOS

**Universidad EAN** · Vigilada Mineducación  
**Generado por:** EANSilabusCreation · 2024-10-27T15:30:00Z  
**Versión del documento:** 1.0.0

---

## 1. Identificación de la Unidad de Estudio

| Campo | Valor |
|---|---|
| **Programa académico** | INGENIERÍA DE PRODUCCIÓN |
| **Nombre de la unidad de estudio** | SISTEMAS DINÁMICOS DISCRETOS |
| **Código** | VFV01154 |
| **Tipo de unidad** | Disciplinar / Profesional |
| **Nivel académico** | Pregrado |
| **Modalidad** | Presencial |
| **Créditos académicos** | 8 |
| **Versiones del plan de estudio** | PFVIPRBOG001 (1967) · PFVISIBOG001 (1972) |

---

## 2. Intensidad Horaria

| Tipo de dedicación | Horas |
|---|---|
| Horas de Actividad Directa (HAD) | 144 |
| Horas de Trabajo Autónomo (HTA) | 288 |
| **Horas Totales (HT)** | **432** |

### Duración según tipo de período académico

| Período | Duración |
|---|---|
| Semestre | 18 semanas |

---

## 3. Descripción de la Unidad de Estudio

La unidad de estudio de "Sistemas Dinámicos Discretos" capacita al futuro Ingeniero de Producción en el modelamiento cuantitativo y análisis del comportamiento temporal de sistemas industriales que operan en intervalos de tiempo discretos. Se enfoca en la formulación, resolución y análisis de estabilidad de ecuaciones en diferencias lineales y no lineales, aplicadas a problemas de control de inventarios, planeación de la producción, dinámicas de mercado y cadenas de suministro (Dinámica Industrial). Mediante un enfoque teórico-práctico riguroso, el estudiante aprende a estructurar modelos dinámicos, interpretar trayectorias temporales de variables operativas y diseñar políticas de estabilización utilizando flujogramas lógicos y técnicas de computación digital aplicadas a la producción manufacturera.

(Presente en planes: PFVIPRBOG001 · PFVISIBOG001)

---

## 4. Resultado de Aprendizaje de la Unidad

Diseña y evalúa modelos cuantitativos de sistemas de manufactura, almacenamiento y distribución utilizando ecuaciones en diferencias y representación en variables de estado, orientando la toma de decisiones operativas bajo condiciones de demanda dinámica y garantizando la estabilidad temporal del sistema industrial.

---

## 5. Contenidos de la Unidad de Estudio

### Por semestre (18 semanas)
* **Semanas 1-4: Fundamentos de Sistemas Discretos y Ecuaciones en Diferencias**
  * Introducción al concepto de tiempo discreto en la modelación de procesos de producción.
  * Formulación de ecuaciones en diferencias de primer y segundo orden.
  * Solución clásica (homogénea y particular) y mediante operadores de rezago (Lag Operators).
  * Dinámicas de mercado de corto plazo: El modelo de la telaraña (Cobweb Model) y su estabilidad.
* **Semanas 5-8: Modelamiento de Dinámica Industrial y Cadenas de Suministro**
  * Conceptos fundamentales de la Dinámica Industrial según el modelo de Jay Forrester.
  * Estructuración de bucles de realimentación (Feedback Loops), niveles (acumulaciones) y flujos.
  * Retardos de transmisión de información y materiales en sistemas logísticos.
  * El modelo multiplicador-acelerador de Samuelson aplicado al control de inventarios.
* **Semanas 9-12: Representación en el Espacio de Estados y Análisis de Estabilidad**
  * Representación matricial de sistemas en diferencias vectoriales de orden superior.
  * Concepto de trayectoria temporal del estado y cálculo de la matriz de transición discreta.
  * Estabilidad en el sentido de Lyapunov para sistemas lineales de tiempo discreto.
  * Criterios algebraicos de estabilidad: Métodos de Schur-Cohn y Jury.
* **Semanas 13-15: Simulación Analógica y Programación Digital**
  * Conceptos básicos de algoritmos de iteración para la resolución numérica de trayectorias temporales.
  * Codificación de modelos dinámicos lineales en lenguaje Fortran IV.
  * Diseño de diagramas de flujo de simulación industrial para procesamiento centralizado por lotes (Batch Processing).
* **Semanas 16-18: Optimización y Control en Procesos de Producción**
  * Sistemas dinámicos muestreados (Sampled-Data Systems) y control digital básico.
  * Introducción a la optimización dinámica secuencial: Programación dinámica de Bellman.
  * Estudio de caso final: Modelación y simulación de un sistema integrado de manufactura, transporte y almacenamiento.

> **Nota de versión:** La versión PFVIPRBOG001 (1967) priorizaba los métodos de resolución analíticos y simulación manual de trayectorias. La versión PFVISIBOG001 (1972) incorporó de forma obligatoria las prácticas de programación numérica utilizando lenguaje Fortran IV en el centro de cómputo institucional.

---

## 6. Esquema de Calificación

| Actividad de evaluación | Porcentaje |
|---|---|
| Talleres prácticos semanales de resolución analítica de ecuaciones y modelado gráfico | 20% |
| Informes de laboratorio y simulación numérica de trayectorias en Fortran IV (procesamiento por lotes) | 25% |
| Examen parcial de contenido teórico 1 (Semanas 1-8) | 15% |
| Examen parcial de contenido teórico 2 (Semanas 9-12) | 15% |
| Proyecto de aplicación práctica final y sustentación (Modelamiento de una planta de producción real) | 25% |
| **Total** | **100%** |

---

## 7. Bibliografía

### Obligatoria

1. Forrester, J. W. (1961). *Industrial Dynamics*. MIT Press. ★
2. Goldberg, S. (1958). *Introduction to Difference Equations*. John Wiley & Sons. ★
3. Kuo, B. C. (1963). *Analysis and Synthesis of Sampled-Data Control Systems*. Prentice-Hall. ★

### Complementaria

1. Baumol, W. J. (1959). *Economic Dynamics: An Introduction* (2nd ed.). Macmillan.
2. Tou, J. T. (1964). *Modern Control Theory*. McGraw-Hill.
3. IBM Corporation. (1965). *IBM System/360 Fortran IV Language* (Form C28-6515-4). IBM Technical Publications.

---

## 8. Recursos Tecnológicos

* **Infraestructura de computación**: Centro de Cómputo de la Universidad EAN equipado con sistema Mainframe IBM 360/30 para el procesamiento por lotes mediante tarjetas perforadas.
* **Periféricos y hardware**: Lectora de tarjetas perforadas IBM 2501, perforadoras de tarjetas IBM 29, e impresora de líneas IBM 1403 para reportes de trayectorias numéricas simuladas.
* **Lenguajes y herramientas lógicas**: Compilador de tarjetas IBM Fortran IV (versión básica).
* **Herramientas de cálculo personal**: Regla de cálculo mecánica profesional (tipo Faber-Castell 2/83N o Aristo Studio) para operaciones analíticas rápidas en aula de clase; calculadoras de oficina Facit o Monroe para tabulaciones iterativas manuales.

---

## 9. Componente de Lengua Extranjera

El material técnico avanzado de consulta académica, incluyendo los manuales del sistema IBM 360, el texto principal de Dinámica Industrial de Jay Forrester y los manuales técnicos del MIT Press se encuentran disponibles exclusivamente en idioma inglés. Se exigirá el desarrollo de resúmenes de lecturas asignadas en inglés y la interpretación de los mensajes de error en los listados del compilador Fortran como mecanismo activo de inmersión en la literatura técnica internacional.

---

## 10. Notas de Versión

> Esta unidad de estudio estuvo presente en **2 versiones** del plan de estudio del programa INGENIERÍA DE PRODUCCIÓN.

| Versión del plan | Año | Cambios principales |
|---|---|---|
| PFVIPRBOG001 | 1967 | Versión inicial de creación del programa de Ingeniería de Producción. Currículo enfocado en resolución analítica y modelamiento gráfico-conceptual clásico. |
| PFVISIBOG001 | 1972 | Reestructuración de contenidos prácticos. Se implementan de forma obligatoria las horas de programación y simulación computacional usando lenguaje Fortran IV en el nuevo centro de cómputo. |

---

*Sílabo generado automáticamente por EANSilabusCreation · 2024-10-27T15:30:00Z*  
*Dirección de Inteligencia Artificial e Innovación · VIATI · Universidad EAN*  
*Este documento requiere validación por el director del programa antes de su uso oficial.*