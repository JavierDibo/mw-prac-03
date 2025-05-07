# Práctica 3: Minería de Uso de la Web - Memoria

## Introducción

[Breve introducción al proyecto, objetivos de la práctica y estructura del documento.]

## 1. Pre-procesamiento para análisis de logs

[Descripción general de la fase de pre-procesamiento.]

### 1.1. Carga del registro log y pre-procesamiento inicial

El proceso de carga y pre-procesamiento inicial del log de acceso de la NASA (`NASA_access_log_FULL.txt`) se realizó utilizando la biblioteca Pandas en Python. Los pasos principales fueron:
1.  **Lectura del Archivo:** Se leyó el archivo línea por línea.
2.  **Parseo de Líneas:** Cada línea se parseó utilizando una expresión regular (`LOG_PATTERN` en `src/preprocessing.py`) para extraer los campos relevantes: Host remoto, Fecha/Hora, Método HTTP, Página solicitada, Protocolo HTTP, Código de estado HTTP (Resultado) y Tamaño de la respuesta.
3.  **Creación del DataFrame:** Los datos parseados se cargaron en un DataFrame de Pandas con las columnas: 'Host remoto', 'Fecha/Hora', 'Método', 'Página', 'Protocolo', 'Resultado', 'Tamaño'.
4.  **Conversión de Tipos:**
    *   La columna 'Resultado' (código de estado) se convirtió a tipo numérico.
    *   La columna 'Tamaño' se convirtió a tipo numérico, manejando los valores '-' como NaN.
    *   La columna 'Fecha/Hora' se convirtió a objetos `datetime` de Pandas, utilizando el formato `%d/%b/%Y:%H:%M:%S %z`. Se verificó la presencia de valores NaT (Not a Time) resultantes de errores de conversión.
5.  **Creación de Marca de Tiempo:** Se creó una nueva columna 'marca de tiempo'. Para ello, primero se convirtió la columna 'Fecha/Hora' a UTC (Coordinated Universal Time) para asegurar una referencia temporal consistente. Luego, se calculó la diferencia en segundos entre cada entrada de 'Fecha/Hora_UTC' y la fecha de referencia (1 de Enero de 1995, 00:00:00 UTC).

### 1.2. Filtrado de datos

*   **Tabla de Extensiones Más Repetidas:**
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
    Los pasos de filtrado (identificar las N extensiones de archivo principales y luego conservar solo extensiones específicas o extensiones en blanco) son cruciales por varias razones en el contexto del análisis de logs web:
    1.  **Enfoque en Contenido Relevante:** Los logs del servidor web capturan solicitudes para todo tipo de recursos, incluyendo imágenes (`.gif`, `.jpg`), hojas de estilo (`.css`), archivos JavaScript (`.js`) y páginas de contenido reales (`.html`, `.pdf`, etc.). Para muchos tipos de análisis (p.ej., comprender patrones de navegación del usuario, documentos de contenido populares), las solicitudes de archivos auxiliares como imágenes o scripts son ruido. El filtrado ayuda a aislar las solicitudes de contenido primario o elementos de navegación. Las extensiones elegidas (`.htm`, `.html`, `.pdf`, `.asp`, `.exe`, `.txt`, `.doc`, `.ppt`, `.xls`, `.xml`) generalmente representan dicho contenido primario o documentos descargables.
    2.  **Manejo de Casos "Sin Extensión":** Conservar registros donde la extensión de la página está en blanco es importante porque a menudo representan solicitudes de directorios (p.ej., `/ruta/al/directorio/`) o páginas dinámicas donde la extensión no es explícitamente parte de la URL visible para el usuario (p.ej., URLs limpias como `/productos/`). Estos son a menudo centrales para la navegación del sitio y la interacción del usuario. Por ejemplo, una solicitud a `/imagenes/` (sin extensión) podría servir un archivo `index.html` por defecto, representando un punto de navegación.
    3.  **Reducción del Volumen de Datos:** Los logs web pueden ser enormes. Filtrar solicitudes menos relevantes (basadas en extensiones consideradas menos importantes para los objetivos específicos del análisis) reduce significativamente el tamaño del conjunto de datos. Esto hace que el procesamiento, análisis y visualización subsiguientes sean más rápidos y manejables.
    4.  **Mejora de la Precisión del Análisis:** Al eliminar solicitudes de recursos incrustados (como imágenes dentro de una página HTML), los análisis como "páginas por sesión" o "tiempo empleado en la página" se vuelven más precisos. Si cada solicitud de imagen se contara como una "vista de página" separada, estas métricas estarían muy sesgadas y no reflejarían el comportamiento real del usuario con respecto al consumo de contenido.
    5.  **Simplificación del Análisis de Extensiones:** El paso de extraer todas las extensiones y encontrar las N principales (Tarea 1.2.1) ayuda a comprender la composición de las solicitudes al servidor. Este conocimiento puede luego informar la estrategia de filtrado en la Tarea 1.2.2 (conservar extensiones específicas). Por ejemplo, si una extensión inesperada pero importante aparece en la lista principal, podría agregarse a las extensiones a conservar.

### 1.3. De-spidering

Se implementó una estrategia para identificar bots y crawlers basada en el acceso al archivo `/robots.txt`. Los hosts que solicitaron este archivo fueron marcados como bots. Según la ejecución del script `src/preprocessing.py`:
1.  Se identificaron **55 hosts únicos** que accedieron a `/robots.txt`.
2.  Se añadió una nueva columna booleana `Is_Bot` al DataFrame principal.
3.  Las peticiones de estos hosts identificados como bots constituyeron **8608 peticiones**, lo que representa aproximadamente el **0.76%** del total de peticiones en el DataFrame filtrado por extensiones.
4.  Se generaron dos tablas de resumen en formato CSV, guardadas en el directorio `output/tables/`:
    *   `identified_bots_details.csv`: Contiene una lista de los 'Host remoto' identificados como bots y el número total de peticiones realizadas por cada uno (ej. `e659229.boeing.com` con 2296 peticiones).
    *   `bot_proportions_summary.csv`: Muestra el número total de peticiones de los bots identificados frente a las peticiones no identificadas como de bots, junto con sus proporciones relativas.

*   **Explicación del De-spidering:**
    El proceso de "de-spidering" (identificación y eliminación de registros de bots y crawlers) es crucial para el análisis de logs web. Su objetivo principal es **centrarse en el comportamiento humano**, ya que los bots (ej. indexadores de motores de búsqueda) tienen patrones de acceso muy diferentes que pueden distorsionar métricas clave. Incluir tráfico de bots infla el número de visitas, altera las características de las sesiones (duración, páginas por sesión) y puede mostrar una popularidad irreal de ciertos contenidos. Al eliminar estas entradas automatizadas —en nuestro caso, identificando los hosts que accedieron a `/robots.txt` y luego filtrando sus peticiones— se **mejora la precisión de los análisis** y se **reduce el ruido y el volumen de datos**. Esto permite que los patrones de comportamiento de los usuarios reales emerjan más claramente, llevando a conclusiones más fiables sobre la interacción con el sitio web.

### 1.4. Identificación de usuarios

Para la identificación de usuarios, se consideraron los campos disponibles en el log:
*   **Campos 'ident' y 'user':** Como se determinó en la Tarea 1.1.2 y se confirmó en la Tarea 1.4.1, los campos del log que corresponderían a 'ident' (equivalente a 'Contraseña' en la terminología inicial del proyecto) y 'user' (equivalente a 'Usuario') son consistentemente '-' en los datos. Por lo tanto, no fueron capturados como columnas en el DataFrame final y no aportan información para la identificación de usuarios.
*   **Campo 'Referrer':** El formato de log que se está procesando (Common Log Format con algunos añadidos, pero no extendido para incluir explícitamente el referrer como un campo estándar separado en la línea principal del log) no proporciona directamente un campo 'referrer' a través del patrón de expresiones regulares actual (`LOG_PATTERN` en `src/preprocessing.py`). Aunque la información del referrer podría estar en las cabeceras HTTP completas (no disponibles en estos logs), no es un campo que se parsea actualmente. Un análisis basado en la topología del sitio para inferir referrers internos requeriría un conocimiento detallado de la estructura del sitio web que está fuera del alcance de este preprocesamiento.
*   **Campo 'Host remoto' (IP):** Este campo es el candidato principal para la identificación de usuarios en ausencia de otros identificadores más fiables.

La estrategia para crear un 'UserID' se basará en el campo 'Host remoto'.

### 1.5. Identificación de sesiones

La identificación de sesiones se implementó en la función `identify_sessions` dentro de `src/preprocessing.py`. El proceso es el siguiente:
1.  **Ordenamiento:** El DataFrame se ordena primero por la columna 'UserID' (creada en el paso 1.4.3) y luego por la columna 'marca de tiempo'.
2.  **Cálculo de Diferencias de Tiempo:** Para cada usuario, se calcula la diferencia de tiempo (en segundos) entre cada petición consecutiva.
3.  **Detección de Inicio de Sesión:** Una nueva sesión comienza si es la primera petición del 'UserID' o si la diferencia de tiempo con la petición anterior excede 30 minutos (1800 segundos).
4.  **Asignación de 'SessionID':** Se genera un `SessionID` único concatenando el 'UserID' con un número de secuencia de sesión (e.g., `199.72.81.55_1`).

El script `src/preprocessing.py` reportó la creación de **289,666 sesiones únicas identificadas**. También imprime ejemplos de estas sesiones.

*   **Ejemplo de Tabla de Sesiones:**
    A continuación, se muestra un ejemplo de la salida del script `src/preprocessing.py`, ilustrando el formato de las sesiones. El DataFrame resultante está ordenado por `UserID` y `marca de tiempo`:

    | UserID      | marca de tiempo | SessionID     | Página                                      |
    |-------------|-----------------|---------------|---------------------------------------------|
    | ***.novo.dk | 16546629.0      | ***.novo.dk_1 | /ksc.html                                   |
    | ***.novo.dk | 16546668.0      | ***.novo.dk_1 | /shuttle/missions/missions.html             |
    | ...         | ...             | ...           | ...                                         |
    | ***.novo.dk | 19033368.0      | ***.novo.dk_2 | /shuttle/missions/sts-69/mission-sts-69.html|
    | ...         | ...             | ...           | ...                                         |


### 1.6. Problemas al estimar duraciones

*   **Discusión sobre la Última Página:**
    Estimar con precisión cuánto tiempo un usuario dedica a la última página de una sesión es un problema inherente y bien conocido en el análisis de logs web. La dificultad principal radica en que los logs del servidor registran cuándo se solicita una página, pero **no registran cuándo el usuario la abandona o cierra su navegador**.

    Para todas las páginas intermedias de una sesión, podemos inferir el tiempo de visualización de una página `A` como la diferencia entre la marca de tiempo de la solicitud de la página `A` y la marca de tiempo de la solicitud de la siguiente página `B` (dentro de la misma sesión). Asumimos que el usuario estuvo viendo la página `A` hasta que solicitó la página `B`.

    Sin embargo, para la última página de la sesión, no hay una "siguiente página solicitada" en el log que marque el final de su visualización. El usuario podría haber:
    *   Leído la página durante unos segundos y luego cerrado la pestaña/navegador.
    *   Leído la página detenidamente durante varios minutos.
    *   Dejado la página abierta en una pestaña del navegador durante horas mientras realizaba otras actividades (online u offline).
    *   Experimentado un problema de conexión o el cierre inesperado del navegador.

    El log del servidor no puede distinguir entre estos escenarios. Por lo tanto, cualquier cálculo directo del tiempo de visualización para la última página basado únicamente en los timestamps del log es imposible. Esto significa que si simplemente omitimos la duración de la última página, la duración total de la sesión y el tiempo medio por página pueden ser subestimados, especialmente en sesiones cortas o en sitios donde la última página es crucial (por ejemplo, una página de confirmación, un artículo largo).

*   **Sugerencia Creativa para Estimación:**
    Para estimar la duración de la visualización de la última página de una sesión, una aproximación consiste en **utilizar el tiempo medio de visualización de páginas similares** dentro del mismo dataset. Los pasos serían:

    1.  **Calcular Duraciones Conocidas y Medias Contextuales:**
        *   Primero, para todas las páginas que *no* son la última de su sesión, se calcula su duración (tiempo hasta el siguiente hit en la misma sesión).
        *   Luego, se calcula el tiempo medio de visualización para estas páginas, preferiblemente agrupando por un contexto relevante, como la extensión del archivo (ej. media para `.html`, media para `.pdf`, media para páginas sin extensión).

    2.  **Aplicar Duración a la Última Página:**
        *   A la última página de cada sesión se le asignaría la duración media precalculada correspondiente a su tipo o extensión. Por ejemplo, si la última página es un `.html`, se usaría la duración media de las páginas `.html` (no finales) calculada previamente.
        *   Si para un tipo específico de última página no hay una media contextual disponible (ej. extensión poco común), se podría recurrir a una media global de todas las páginas no finales.

    **Consideraciones y Limitaciones:**
    *   Esta técnica asume que la última página se consume de forma similar a otras páginas del mismo tipo que no fueron las últimas, lo cual es una generalización.
    *   No puede capturar la variabilidad individual de la visualización de la última página (abandono rápido vs. lectura prolongada).
    *   A pesar de sus limitaciones, esta imputación basada en datos es más informada que ignorar la duración o asignar una constante arbitraria.

    Una alternativa más simple sería asignar un valor constante predefinido (ej., 30 segundos), aunque esto carece de la adaptación a los datos que ofrece el método de la media contextual.

### 1.7. Pre-procesamiento adicional

Se revisó el DataFrame final (`df_final_processed` en el script `src/preprocessing.py`, después de la eliminación de bots y la creación de UserID y SessionID) para identificar valores perdidos (NaN) en columnas críticas.

1.  **Identificación de Valores Perdidos:**
    *   Basándose en la salida del método `.info()` del DataFrame, la mayoría de las columnas críticas para el análisis de sesiones y comportamiento del usuario (como `UserID`, `Fecha/Hora`, `marca de tiempo`, `Página`, `Extensión`, `SessionID`) no presentan valores perdidos.
    *   La columna `Tamaño` sí presenta valores NaN. Esto es un resultado esperado, ya que el script convierte las entradas "-" (guion) del log original en NaN cuando la columna `Tamaño` se convierte a tipo numérico. En la ejecución de ejemplo, se observaron aproximadamente 25,461 NaNs en esta columna sobre un total de 1,124,516 filas en el DataFrame procesado sin bots.

2.  **Estrategia de Tratamiento:**
    *   **Para la columna `Tamaño`:** Los valores NaN se consideran una representación válida de datos originalmente no disponibles (el servidor no reportó el tamaño del objeto). No se realizará una imputación general (como rellenar con 0 o la media) en esta etapa del preprocesamiento. Si análisis futuros específicos requieren un valor numérico en `Tamaño` para todos los registros (ej. cálculo de bytes totales promedio por sesión incluyendo estas peticiones), se abordará en ese momento (ej. tratando NaN como 0 para sumas, o excluyendo el registro si la media de tamaño es crítica y el NaN no puede ser significativamente interpretado).
    *   **Para otras columnas críticas:** Dado que no se identificaron NaNs, no se requiere tratamiento adicional.

Este enfoque asegura que no se introduce información artificial en el DataFrame y que la naturaleza de los datos originales se preserva en la medida de lo posible.

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
    *   `