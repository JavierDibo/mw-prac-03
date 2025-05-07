# Práctica 3: Minería de Uso de la Web - Memoria

## Introducción

[Breve introducción al proyecto, objetivos de la práctica y estructura del documento.]

## 1. Pre-procesamiento para análisis de logs

[Descripción general de la fase de pre-procesamiento.]

### 1.1. Carga del registro log y pre-procesamiento inicial

[Describir los pasos realizados para cargar y realizar el pre-procesamiento inicial del log. Incluir detalles sobre el parseo de campos, la conversión de fechas/horas y la creación de la marca de tiempo en segundos desde el 1 de Enero de 1995.]
El proceso de carga y pre-procesamiento inicial del log de acceso de la NASA (`NASA_access_log_FULL.txt`) se realizó utilizando la biblioteca Pandas en Python. Los pasos principales fueron:
1.  **Lectura del Archivo:** Se leyó el archivo línea por línea.
2.  **Parseo de Líneas:** Cada línea se parseó utilizando una expresión regular (`LOG_PATTERN` en `src/preprocessing.py`) para extraer los campos relevantes: Host remoto, Contraseña (ident), Usuario, Fecha/Hora, Método HTTP, Página solicitada, Protocolo HTTP, Código de estado HTTP (Resultado) y Tamaño de la respuesta. Las líneas que no coincidían con el patrón o estaban vacías fueron omitidas.
3.  **Creación del DataFrame:** Los datos parseados se cargaron en un DataFrame de Pandas con las columnas: 'Host remoto', 'Contraseña', 'Usuario', 'Fecha/Hora', 'Método', 'Página', 'Protocolo', 'Resultado', 'Tamaño'.
4.  **Conversión de Tipos:**
    *   La columna 'Resultado' (código de estado) se convirtió a tipo numérico.
    *   La columna 'Tamaño' se convirtió a tipo numérico, manejando los valores '-' como NaN.
    *   La columna 'Fecha/Hora' se convirtió a objetos `datetime` de Pandas, utilizando el formato `%d/%b/%Y:%H:%M:%S %z`. Se verificó la presencia de valores NaT (Not a Time) resultantes de errores de conversión.
5.  **Creación de Marca de Tiempo:** Se creó una nueva columna 'marca de tiempo'. Para ello, primero se convirtió la columna 'Fecha/Hora' a UTC (Coordinated Universal Time) para asegurar una referencia temporal consistente. Luego, se calculó la diferencia en segundos entre cada entrada de 'Fecha/Hora_UTC' y la fecha de referencia (1 de Enero de 1995, 00:00:00 UTC).

### 1.2. Filtrado de datos

*   **Tabla de Extensiones Más Repetidas:**
    *   `[Insertar aquí la Tabla con las 10 extensiones de página más repetidas y su número de repeticiones. Puede ser un enlace a una imagen de la tabla, una tabla Markdown, o una descripción textual si es breve.]`
    Se extrajeron las extensiones de la columna 'Página' y se contó su frecuencia. La tabla con las 10 extensiones más repetidas se generó y guardó en `output/tables/top_10_extensions.csv`. Su contenido es el siguiente:

    ```
    Extensión,Número de Repeticiones
    gif,1986781
    html,750366
    xbm,110249
    jpg,79638
    pl,65304
    txt,51483
    mpg,44657
    htm,22623
    jpeg,12170
    wav,6686
    ```

*   **Explicación del Filtrado:**
    *   `[Explicar aquí por qué se realizaron los pasos de filtrado de extensiones, manteniendo solo .htm, .html, .pdf, .asp, .exe, .txt, .doc, .ppt, .xls, .xml y registros con extensión en blanco.]`
    Posteriormente, el DataFrame se filtró para mantener únicamente los registros correspondientes a un conjunto específico de extensiones de archivo (`.htm`, `.html`, `.pdf`, `.asp`, `.exe`, `.txt`, `.doc`, `.ppt`, `.xls`, `.xml`) o aquellos registros donde la extensión de la página estaba en blanco (considerados como posible navegación o directorios). La justificación detallada de este paso de filtrado se encuentra pendiente y se añadirá según el progreso del `TODO.md` (Tarea 1.2.3).

### 1.3. De-spidering

*   **Tabla de Bots y Crawlers:**
    *   `[Insertar aquí la Tabla con todos los bots y crawlers identificados, indicando las proporciones relativas de estos elementos.]`

*   **Explicación del De-spidering:**
    *   `[Explicar aquí por qué se realizaron los pasos para eliminar bots, arañas y rastreadores de los datos.]`

### 1.4. Identificación de usuarios

[Describir los pasos y decisiones tomadas para la identificación de usuarios. Explicar cómo se comprobó el campo de nombre de usuario, el campo referrer o la topología del sitio, y cómo se añadió el nuevo campo/atributo para la identificación de usuarios (e.g., 'UserID').]

### 1.5. Identificación de sesiones

[Describir el proceso de identificación de sesiones, incluyendo el uso de direcciones IP únicas y el umbral de timeout de 30 minutos. Explicar cómo se añadió el atributo con el identificador de sesión ('SessionID').]

*   **Ejemplo de Tabla de Sesiones:**
    *   `[Insertar aquí una porción del DataFrame resultante, ordenado por 'SessionID' y 'marca de tiempo', como ejemplo.]`

### 1.6. Problemas al estimar duraciones

*   **Discusión sobre la Última Página:**
    *   `[Discutir aquí la dificultad para estimar la duración de la visualización de la última página de una sesión.]`

*   **Sugerencia Creativa para Estimación:**
    *   `[Sugerir aquí una forma creativa de estimar la duración de la última página de una sesión.]`

### 1.7. Pre-procesamiento adicional

[Si se realizaron tareas adicionales de pre-procesamiento (ej. para identificar valores perdidos), describir la estrategia elegida para su tratamiento y cómo se aplicó.]
*   `[Documentar aquí la estrategia de tratamiento de valores perdidos, si aplica.]`

## 2. Análisis exploratorio de datos del log

[Descripción general de la fase de análisis exploratorio.]

**Nota sobre Visualizaciones:**
*   [Si se omitieron valores atípicos en histogramas o diagramas de dispersión para mejorar la visualización, indicar aquí de forma general. Luego, en cada sección específica, detallar el umbral utilizado y la proporción de registros omitidos para ESE gráfico/análisis en particular.]

### 2.1. Duración de la sesión

*   **Discusión sobre Sesiones de Única Visita:**
    *   `[Considerar aquí sesiones que consten de una única visita. Discutir qué evidencia empírica se tiene respecto a la duración de esas sesiones.]`

*   **Análisis de Duración de Sesiones (>1 visita):**
    *   Cálculo de la duración: [Describir brevemente cómo se calcularon las duraciones para sesiones con más de una visita.]
    *   **Histograma de Duración de Sesión:**
        *   `[Insertar aquí el Histograma de la duración de la sesión (para sesiones con >1 visita). Indicar si se omitieron valores y bajo qué umbral.]`
    *   **Resumen Estadístico de Duración de Sesión:**
        *   `[Insertar aquí el Resumen estadístico: media, desviación estándar, mediana, moda, mínimo y máximo de la duración de la sesión.]`

*   **Análisis de Estimación (Subestimación/Sobreestimación):**
    *   `[Analizar aquí si los resultados obtenidos subestiman o sobreestiman la verdadera duración de la sesión en todas las sesiones y explicar por qué.]`

### 2.2. Tiempo medio por página

*   **Fórmula/Lógica para Tiempo Medio por Página:**
    *   `[Mostrar aquí la fórmula o lógica utilizada en Python para derivar el tiempo medio por página.]`

*   **Análisis del Tiempo Medio por Página:**
    *   **Histograma del Tiempo Medio por Página:**
        *   `[Insertar aquí el Histograma del tiempo medio por página. Indicar si se omitieron valores y bajo qué umbral.]`
    *   **Resumen Estadístico del Tiempo Medio por Página:**
        *   `[Insertar aquí el Resumen estadístico habitual (media, DE, mediana, etc.) para el tiempo medio por página.]`
    *   **Comentario sobre Resultados:**
        *   `[Comentar aquí los resultados obtenidos para el tiempo medio por página.]`

### 2.3. Eliminar comportamiento automático (revisión)

*   **Tabla de Sesiones con Menor Tiempo Medio por Página:**
    *   `[Insertar aquí la Tabla con las 20 sesiones con menor tiempo medio por página.]`

*   **Documentación de Sesiones < 0.5s (si alguna se mantuvo):**
    *   `[Si alguna sesión con tiempo medio por página menor de 0.5 segundos se consideró de usuario real, indicar aquí todas las páginas de dicha sesión y un argumento que avale la hipótesis.]`

*   **Actualización de Análisis Anteriores (si aplica):**
    *   `[Si se eliminaron sesiones en este paso, indicar que los histogramas y estadísticas de los apartados 2.1 y 2.2 fueron actualizados. Presentar o referenciar los histogramas/estadísticas actualizados si son significativamente diferentes. Ejemplo: "Tras este filtrado, el histograma de duración de sesión (2.1) se actualizó a..."]`

### 2.4. Páginas visitadas

*   **Análisis del Número de Visitas de Página por Sesión:**
    *   **Histograma del Número de Visitas por Sesión:**
        *   `[Insertar aquí el Histograma del número de visitas de página por sesión. Indicar si se omitieron valores y bajo qué umbral.]`
    *   **Resumen Estadístico del Número de Visitas por Sesión:**
        *   `[Insertar aquí el Resumen estadístico: media, desviación estándar, mediana, moda, mínimo y máximo del número de visitas de página por sesión.]`

### 2.5. Relación entre visitas y duración

*   **Análisis de la Relación:**
    *   **Diagrama de Dispersión (Visitas vs. Duración):**
        *   `[Insertar aquí el Diagrama de dispersión de visitas de página vs. duración de la sesión. Indicar si se omitieron valores y bajo qué umbral.]`
    *   **Modelo de Regresión Lineal Simple:**
        *   Ecuación de Regresión Estimada: `[Indicar aquí la ecuación de regresión estimada.]`
        *   Gráfico con Línea de Regresión: `[Asegurarse de que el diagrama de dispersión anterior incluya la línea de regresión superpuesta, o insertar un nuevo gráfico.]`
    *   **Comparación e Interpretación:**
        *   `[Comparar aquí la interpretación intuitiva del tiempo medio por página con la pendiente estimada de la regresión.]`
        *   `[Interpretar aquí claramente (para no especialistas) el significado de la pendiente y el coeficiente de corte en el eje Y, y si tienen sentido en este contexto.]`

### 2.6. Duración de la visita a las dos primeras páginas

*   **Análisis de Duración (Primeras Dos Páginas):**
    *   Cálculo: [Describir brevemente cómo se calculó la duración para la primera y segunda página de cada sesión.]
    *   **Histograma de Duración de la Primera Página:**
        *   `[Insertar aquí el Histograma de la duración de la primera página. Indicar si se omitieron valores y bajo qué umbral.]`
    *   **Resumen Estadístico (Duración Primera y Segunda Página):**
        *   `[Insertar aquí los Estadísticos habituales sobre la duración de la primera y segunda página visitada.]`
    *   **Comparación y Comentario:**
        *   `[Comparar y comentar aquí los resultados de duración de ambas páginas.]`

### 2.7. Determinación del tipo de página por su extensión

*   **Explicación de la Clasificación (Navegación vs. Contenido):**
    *   `[Describir aquí la clasificación de páginas: sin extensión como "navegación", y el resto de extensiones como "contenido". Si se consideró una forma mejor, explicarla y justificarla.]`

*   **Análisis por Tipo de Página:**
    *   **Comparación de Duración Media (Primeras Dos Páginas por Tipo):**
        *   `[Presentar aquí la comparación de la duración media de página de cada una de las dos primeras páginas visitadas, separadas por tipo (navegación vs. contenido). Puede ser una tabla o texto descriptivo.]`
    *   **Histograma Normalizado (Duración Media, Primeras Dos Páginas, Navegación vs. Contenido):**
        *   `[Insertar aquí el Histograma normalizado de la duración media de página de cada una de las dos primeras páginas, con solapamiento de navegación vs. contenido. Indicar si se omitieron valores y bajo qué umbral.]`
    *   **Discusión sobre la Clasificación:**
        *   `[Discutir aquí si esta forma de separar páginas de navegación y de contenido parece funcionar o no, basándose en las evidencias encontradas.]`

### 2.8. Análisis de datos (Tablas y Gráficos Adicionales)

*   **Tabla 1: 20 Dominios Más Repetidos**
    *   `[Insertar aquí la Tabla de los 20 dominios más repetidos (extraídos de 'Host remoto'), por número de visitas y de clics/hits.]`
*   **Tabla 2: 7 Tipos de Dominio Más Repetidos**
    *   `[Insertar aquí la Tabla de los 7 tipos de dominio (ej: .com, .edu, de 'Host remoto') más repetidos, por visitas y clics/hits.]`
*   **Gráfico de Barras 3: Longitud Media de Visitas por Hora del Día**
    *   `[Insertar aquí el Gráfico de barras de la longitud media de las visitas (sesiones) a lo largo de las 24 horas del día.]`
*   **Tabla 4: 10 Visitantes ('UserID') Más Repetidos**
    *   `[Insertar aquí la Tabla de los 10 visitantes ('UserID') más repetidos, por número de visitas/sesiones.]`
*   **Tabla 5: Número de Visitantes Únicos por Número de Sesiones (1-9)**
    *   `[Insertar aquí la Tabla del número de visitantes ('UserID') únicos, por número de visitas/sesiones que realizan (ej. cuántos usuarios tienen 1 sesión, cuántos tienen 2, ..., hasta 9).]`
*   **Tabla 6: 10 Páginas Más Visitadas**
    *   `[Insertar aquí la Tabla de las 10 páginas más visitadas, por número de hits totales y por número de sesiones distintas en las que aparecen.]`
*   **Tabla 7: 10 Directorios Más Visitados**
    *   `[Insertar aquí la Tabla de los 10 directorios más visitados (extraídos de 'Página'), por número de hits y por número de sesiones distintas.]`
*   **Tabla 8: 10 Tipos de Fichero Más Repetidos**
    *   `[Insertar aquí la Tabla de los 10 tipos de fichero más repetidos (basado en extensión, ej: .gif), por número de accesos/hits.]`
*   **Tabla 9: 10 Páginas de Entrada Más Repetidas**
    *   `[Insertar aquí la Tabla de las 10 páginas de entrada (primera página de una sesión) más repetidas, por número de sesiones que inician con ellas.]`
*   **Tabla 10: 10 Páginas de Salida Más Repetidas**
    *   `[Insertar aquí la Tabla de las 10 páginas de salida (última página de una sesión) más repetidas, por número de sesiones que terminan con ellas.]`
*   **Tabla 11: 10 Páginas de Acceso Único Más Visitadas**
    *   `[Insertar aquí la Tabla de las 10 páginas de acceso único (sesiones con una sola página vista) más visitadas.]`
*   **Tabla 12: Distribución de Duración de Visitas en Minutos**
    *   `[Insertar aquí la Tabla de la distribución de la duración de las visitas/sesiones en minutos (rangos: 0-1 min, 1-2 min, ...), por número de visitas/sesiones por rango.]`

## 3. Conclusiones

[Resumir las principales conclusiones del análisis realizado. Comentar los hallazgos más significativos, las limitaciones del estudio y posibles trabajos futuros.]

## 4. Anexos (Opcional)

[Si es necesario, incluir aquí cualquier material suplementario, como por ejemplo, fragmentos de código extensos si no se quieren poner en el cuerpo principal, o tablas muy grandes.]

---
*Este es un esqueleto para la memoria. Deberás rellenar cada sección con tus análisis, tablas, gráficos y explicaciones, basándote en los resultados de tus scripts de Python y los requisitos de la práctica.* 