# Requisitos para la Memoria del Proyecto (Práctica 3)

Este documento consolida todos los elementos que deben incluirse en la memoria final del proyecto, extraídos de `practica-3-guion.md` y `docs/TODO.md`.

## Estructura General de la Memoria:
*   Formato: PDF.
*   Contenido principal:
    *   Descripción de los pasos llevados a cabo en cada tarea.
    *   Tablas de resultados (pueden ser capturas de DataFrames de Pandas o tablas generadas).
    *   Gráficos generados (con Python: Matplotlib/Seaborn).
    *   Análisis realizado para cada sección.

## 1. Pre-procesamiento para análisis de logs

### 1.1. Carga del registro log y pre-procesamiento inicial
*   (No hay requisitos explícitos de memoria aquí más allá de describir los pasos si es relevante).

### 1.2. Filtrado de datos
*   **Tabla**: Las 10 extensiones de página más repetidas y el número de repeticiones.
*   **Explicación**: Justificar por qué se deben realizar los pasos de filtrado de extensiones.

### 1.3. De-spidering
*   **Tabla**: Todos los bots y crawlers identificados, indicando las proporciones relativas.
*   **Explicación**: Justificar por qué se realizan los pasos de de-spidering.

### 1.4. Identificación de usuarios
*   (Describir los pasos y decisiones tomadas para la identificación de usuarios).

### 1.5. Identificación de sesiones
*   **Tabla**: Mostrar una porción del DataFrame resultante, ordenado por 'SessionID' y 'marca de tiempo', como ejemplo.

### 1.6. Problemas al estimar duraciones
*   **Discusión**: Abordar la dificultad para estimar la duración de la visualización de la última página de una sesión.
*   **Sugerencia**: Proponer una forma creativa de estimar la duración de la última página de una sesión.

### 1.7. Pre-procesamiento adicional
*   **Documentación**: Si se realizó pre-procesamiento adicional (ej. tratamiento de valores perdidos), describir la estrategia elegida y aplicada.

## 2. Análisis exploratorio de datos del log

**Nota General para la Sección 2**:
*   Para mejorar la visualización en histogramas y diagramas de dispersión, si es útil, omitir temporalmente valores por encima de un umbral muy alto. Estos datos no deben eliminarse, sino sólo ser omitidos en los diagramas.
*   **Indicar**: El umbral utilizado y el número y proporción de registros omitidos en cada caso.

### 2.1. Duración de la sesión
*   **Discusión**: Considerar sesiones que consten de una única visita. ¿Qué evidencia empírica tenemos respecto a la duración de esas sesiones?
*   **Histograma**: De la duración de la sesión (para sesiones con >1 visita).
*   **Resumen Estadístico**: Media, desviación estándar, mediana, moda, mínimo y máximo de la duración de la sesión.
*   **Análisis**: ¿Los resultados obtenidos subestiman o sobreestiman la verdadera duración de la sesión en todas las sesiones? ¿Por qué?

### 2.2. Tiempo medio por página
*   **Fórmula/Lógica**: Mostrar la fórmula o lógica utilizada para derivar el tiempo medio por página.
*   **Histograma**: Del tiempo medio por página.
*   **Resumen Estadístico**: Incluir los estadísticos habituales (media, DE, mediana, etc.) para el tiempo medio por página.
*   **Comentario**: Comentar los resultados obtenidos.

### 2.3. Eliminar comportamiento automático (revisión)
*   **Tabla**: Las 20 sesiones con menor tiempo medio por página.
*   **Documentación**: Si alguna sesión con tiempo medio < 0.5s se considera de usuario real, indicar todas las páginas de la sesión y un argumento que avale la hipótesis.
*   **Actualización**: En caso de haber eliminado sesiones, actualizar los histogramas y estadísticas de los apartados 2.1 y 2.2. Presentar los actualizados.

### 2.4. Páginas visitadas
*   **Histograma**: Del número de visitas de página por sesión.
*   **Resumen Estadístico**: Media, desviación estándar, mediana, moda, mínimo y máximo del número de visitas de página por sesión.

### 2.5. Relación entre visitas y duración
*   **Diagrama de Dispersión**: De visitas de página vs. duración de la sesión.
*   **Modelo de Regresión**: Ecuación de regresión lineal simple estimada.
*   **Gráfico**: Superponer la línea de regresión estimada en el diagrama de dispersión.
*   **Comparación**: Interpretación intuitiva del tiempo medio por página con la pendiente estimada de la regresión.
*   **Interpretación Clara**: Significado de la pendiente y el coeficiente de corte en el eje Y, y si tienen sentido en este contexto (para no especialistas).

### 2.6. Duración de la visita a las dos primeras páginas
*   **Histograma**: De la duración de la primera página.
*   **Resumen Estadístico**: Estadísticos habituales sobre la duración de la primera y segunda página visitada.
*   **Comparación y Comentario**: Comparar y comentar los resultados de duración de ambas páginas.

### 2.7. Determinación del tipo de página por su extensión
*   **Explicación**: Describir la clasificación de páginas (sin extensión = navegación, resto = contenido). Si se usa una forma mejor, explicarla y aplicarla.
*   **Comparación**: Duración media de página de cada una de las dos primeras páginas visitadas, separadas por tipo (navegación vs. contenido).
*   **Histograma Normalizado**: De la duración media de página de cada una de las dos primeras páginas, con solapamiento de navegación vs. contenido.
*   **Discusión**: Argumentar si esta forma de separar páginas de navegación y de contenido funciona o no, basándose en las evidencias.

### 2.8. Análisis de datos (Tablas y Gráficos Adicionales)
*   **Tabla 1**: 20 dominios más repetidos (extraer de 'Host remoto'), por número de visitas y de clics/hits.
*   **Tabla 2**: 7 tipos de dominio (ej: .com, .edu, de 'Host remoto') más repetidos, por visitas y clics/hits.
*   **Gráfico de Barras 3**: Longitud media de las visitas (sesiones) a lo largo de las 24 horas del día.
*   **Tabla 4**: 10 visitantes ('UserID') más repetidos, por número de visitas/sesiones.
*   **Tabla 5**: Número de visitantes ('UserID') únicos, por número de visitas/sesiones que realizan (1 a 9 sesiones).
*   **Tabla 6**: 10 páginas más visitadas, por número de hits totales y por número de sesiones distintas en las que aparecen.
*   **Tabla 7**: 10 directorios más visitados (extraer de 'Página'), por número de hits y por número de sesiones distintas.
*   **Tabla 8**: 10 tipos de fichero más repetidos (basado en extensión, ej: .gif), por número de accesos/hits.
*   **Tabla 9**: 10 páginas de entrada (primera página de una sesión) más repetidas, por número de sesiones que inician con ellas.
*   **Tabla 10**: 10 páginas de salida (última página de una sesión) más repetidas, por número de sesiones que terminan con ellas.
*   **Tabla 11**: 10 páginas de acceso único (sesiones con una sola página vista) más visitadas.
*   **Tabla 12**: Distribución de la duración de las visitas/sesiones en minutos (rangos: 0-1 min, 1-2 min, ...), por número de visitas/sesiones por rango.

## 3. Documentación y entrega (Elementos a incluir en el ZIP además de la memoria)
*   Si se usa Python, R, Excel, etc.: código fuente y/o hoja de cálculo que contenga el código de los estudios experimentales realizados.
*   Scripts de Python (`.py` files) ubicados en la carpeta `src/`.

---
Este archivo `memoria-TODO.md` servirá como una checklist para asegurar que todos los componentes requeridos se incluyan en el informe final. 