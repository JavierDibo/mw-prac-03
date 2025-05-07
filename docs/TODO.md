# Información del Proyecto:
*   **Herramienta principal:** Python
*   **Bibliotecas clave:** Pandas, Matplotlib, Seaborn (y posiblemente otras como NumPy, scikit-learn).
*   **Directorio de datos:** `datos/` (contiene el archivo `.txt` del log de NASA).
*   **Directorio de código:** `src/` (contener todos los scripts `.py`).

---

# TODO List Actualizada:

## General Task:
*   [x] Descargar el conjunto de datos de registros web del sitio NASA-HTTP
*   [x] Familiarizarse con el formato del archivo de log en `datos/NASA_access_log_FULL.txt`.

## 1. Pre-procesamiento para análisis de logs (en `src/preprocessing.py` o similar)

### 1.1. Carga del registro log y pre-procesamiento inicial
*   [x] 1. Escribir un script en Python para cargar el fichero log (`datos/NASA_access_log_FULL.txt`) usando Pandas, parseando cada línea.
*   [x] 2. Asegurar la correcta división de los datos en columnas de un DataFrame de Pandas: Host remoto, Fecha/Hora, Método, Página, Protocolo, Resultado y Tamaño.
*   [x] 3. Usar Pandas para convertir la columna Fecha/Hora a objetos datetime.
*   [x] 4. Crear una nueva columna en el DataFrame (marca de tiempo) que represente el número de segundos transcurridos desde el 1 de Enero de 1995, usando las funcionalidades datetime de Pandas.

### 1.2. Filtrado de datos
*   [x] 1. Usar Pandas para extraer las extensiones de la columna 'Página', contar sus ocurrencias y construir una tabla (DataFrame) con las 10 extensiones más repetidas y su número de repeticiones.
*   [x] 2. Usar Pandas para filtrar el DataFrame, manteniendo solo registros con las extensiones: .htm, .html, .pdf, .asp, .exe, .txt, .doc, .ppt, .xls, .xml, O aquellos donde la extensión de página esté en blanco (o no exista).
*   [x] 3. En la memoria, explicar por qué se deben realizar los pasos de filtrado anteriores.

### 1.3. De-spidering
*   [x] 1. Usar Pandas para identificar registros de bots y crawlers (ej. analizando el campo 'Host remoto' o mediante heurísticas comunes, ya que el campo User-Agent no está disponible). Construir una tabla (DataFrame) con los bots/crawlers identificados y sus proporciones relativas.
*   [x] 2. Usar Pandas para eliminar todos los registros identificados como bots, arañas y rastreadores del DataFrame principal.
*   [x] 3. En la memoria, explicar por qué se realizan estos pasos de de-spidering.

### 1.4. Identificación de usuarios
*   [x] 1. Analizar el DataFrame de Pandas para determinar si el campo 'Usuario' es útil para la identificación. (Conclusión: Los campos 'ident' y 'user' del formato de log original son consistentemente '-' y no se han incluido como columnas separadas en el DataFrame; por lo tanto, no son útiles para la identificación directa de usuarios).
*   [x] 2. Analizar el DataFrame de Pandas para el campo 'referrer' (si se parseó previamente o se puede extraer) o considerar la topología del sitio si se conoce. (Conclusión: El campo 'referrer' no está disponible en el formato de log parseado actualmente. El análisis de topología del sitio está fuera del alcance actual).
*   [x] 3. Añadir una nueva columna 'UserID' al DataFrame de Pandas donde se incluiria la IP.

### 1.5. Identificación de sesiones
*   [x] 1. Implementar en Python (usando Pandas) la lógica para identificar sesiones: agrupar por 'UserID', ordenar por 'marca de tiempo', y aplicar un umbral de `timeout` de 30 minutos entre hits consecutivos para delimitar sesiones.
*   [x] 2. Añadir una nueva columna 'SessionID' al DataFrame de Pandas.
*   [x] 3. Mostrar una porción del DataFrame resultante, ordenado por 'SessionID' y 'marca de tiempo', como ejemplo en la memoria. (Nota: El script `src/preprocessing.py` ahora imprime ejemplos relevantes).

### 1.6. Problemas al estimar duraciones
*   [x] 1. En la memoria, discutir la dificultad para estimar la duración de la visualización de la última página de una sesión.
*   [x] 2. En la memoria, sugerir una forma creativa de estimar la duración de la última página de una sesión.

### 1.7. Pre-procesamiento adicional
*   [x] 1. (Si es necesario) Usar Pandas para identificar valores perdidos (NaN) en columnas críticas. (Conclusión: Solo 'Tamaño' tiene NaNs, lo cual es esperado. Otras columnas críticas están completas).
*   [x] 2. (Si se identificaron) Elegir una estrategia para su tratamiento (ej. imputación, eliminación) y aplicarla usando Pandas. Documentar la estrategia en la memoria. (Conclusión: NaNs en 'Tamaño' se mantienen, representan data faltante original. Se tratarán puntualmente si un análisis específico lo requiere).

## 2. Análisis exploratorio de datos del log (en `src/analysis.py`)
*(Nota: Usar Matplotlib/Seaborn para todos los gráficos. Para histogramas y diagramas de dispersión, si es útil, omitir temporalmente valores extremos, indicando el umbral y la proporción de datos omitidos en la memoria).*

### 2.1. Duración de la sesión
*   [x] 1. En la memoria, considerar sesiones de una única visita y discutir qué evidencia empírica existe sobre su duración.
*   [x] 2. Usar Pandas para filtrar sesiones que contienen más de una visita. Calcular la duración de estas sesiones (diferencia entre el timestamp del último y primer hit de la sesión).
*   [x] 3. Generar un histograma de la duración de la sesión (para sesiones con >1 visita) usando Matplotlib/Seaborn.
*   [x] 4. Calcular y presentar un resumen estadístico (media, desviación estándar, mediana, moda, mínimo y máximo) de la duración de la sesión usando Pandas (`.describe()` o cálculos individuales).
*   [x] 5. En la memoria, analizar si los resultados obtenidos subestiman o sobreestiman la verdadera duración de la sesión y explicar por qué.

### 2.2. Tiempo medio por página
*   [ ] 1. Calcular el tiempo medio por página. Esto implicará calcular la duración de cada página vista (excepto la última de cada sesión de forma directa). Mostrar la fórmula/lógica implementada en Python en la memoria.
*   [ ] 2. Construir un histograma del tiempo medio por página usando Matplotlib/Seaborn.
*   [ ] 3. Incluir los estadísticos habituales (media, DE, mediana, etc.) para el tiempo medio por página (usando Pandas) y comentar los resultados en la memoria.

### 2.3. Eliminar comportamiento automático (revisión)
*   [ ] 1. Usar Pandas para crear una tabla (DataFrame) con las 20 sesiones con menor tiempo medio por página.
*   [ ] 2. Identificar sesiones con un tiempo medio por página menor de 0.5 segundos.
*   [ ] 3. Eliminar estas sesiones del DataFrame, salvo que se pueda argumentar que son de usuarios reales (documentar tal caso en la memoria, indicando páginas de la sesión y justificación).
*   [ ] 4. (Si se eliminaron sesiones) Actualizar los histogramas y estadísticas de los apartados 2.1 y 2.2 usando Matplotlib/Seaborn y Pandas con el DataFrame filtrado.

### 2.4. Páginas visitadas
*   [ ] 1. Generar un histograma del número de visitas de página por sesión usando Matplotlib/Seaborn.
*   [ ] 2. Crear un resumen estadístico del número de visitas de página por sesión (media, desviación estándar, mediana, moda, mínimo y máximo) usando Pandas.

### 2.5. Relación entre visitas y duración
*   [ ] 1. Generar un diagrama de dispersión de visitas de página vs. duración de la sesión usando Matplotlib/Seaborn.
*   [ ] 2. Usar Python (e.g., `scikit-learn` o `statsmodels`) para aplicar un modelo de regresión lineal simple y encontrar la ecuación de regresión estimada.
*   [ ] 3. Superponer la línea de regresión estimada en el gráfico de dispersión.
*   [ ] 4. En la memoria, comparar la interpretación intuitiva del tiempo medio por página con la pendiente estimada de la regresión.
*   [ ] 5. En la memoria, interpretar claramente el significado de la pendiente y el coeficiente de corte en el eje Y, y si tienen sentido en este contexto.

### 2.6. Duración de la visita a las dos primeras páginas
*   [ ] 1. Usando Pandas, para cada sesión (donde sea posible), calcular la duración de la visita a la primera y segunda página.
*   [ ] 2. Generar un histograma de la duración de la primera página usando Matplotlib/Seaborn.
*   [ ] 3. Calcular los estadísticos habituales sobre la duración de la primera y la segunda página visitada usando Pandas.
*   [ ] 4. Comparar y comentar los resultados de duración de ambas páginas en la memoria.

### 2.7. Determinación del tipo de página por su extensión
*   [ ] 1. Implementar en Pandas la clasificación de páginas: sin extensión como "navegación", y el resto de extensiones como "contenido". (Si se considera una mejor forma, explicarla y aplicarla, documentando en la memoria). Crear una nueva columna para esto.
*   [ ] 2. Usar Pandas para comparar la duración media de página de cada una de las dos primeras páginas visitadas, separándolas por tipo (navegación vs. contenido).
*   [ ] 3. Generar un histograma normalizado (usando `density=True` en Matplotlib/Seaborn) de la duración media de página de cada una de las dos primeras páginas, con solapamiento de navegación vs. contenido.
*   [ ] 4. En la memoria, discutir si esta clasificación (navegación/contenido) parece funcionar basándose en las evidencias encontradas.

### 2.8. Análisis de datos (Tablas y Gráficos Adicionales)
    *(Generar todas las tablas como DataFrames de Pandas y mostrarlas/guardarlas. Generar gráficos con Matplotlib/Seaborn).*
*   [ ] 1. Tabla (DataFrame): 20 dominios más repetidos (extraer de 'Host remoto', por número de visitas y de clics/hits).
*   [ ] 2. Tabla (DataFrame): 7 tipos de dominio (ej: .com, .edu, etc., extraer de 'Host remoto') más repetidos (por visitas y clics/hits).
*   [ ] 3. Gráfico de barras: longitud media de las visitas (sesiones) a lo largo de las 24 horas del día.
*   [ ] 4. Tabla (DataFrame): 10 visitantes ('UserID') más repetidos (por número de visitas/sesiones).
*   [ ] 5. Tabla (DataFrame): número de visitantes ('UserID') únicos, por número de visitas/sesiones que realizan (ej. cuántos usuarios tienen 1 sesión, cuántos tienen 2, ..., hasta 9).
*   [ ] 6. Tabla (DataFrame): 10 páginas más visitadas (por número de hits totales y por número de sesiones distintas en las que aparecen).
*   [ ] 7. Tabla (DataFrame): 10 directorios más visitados (extraer de 'Página', por número de hits y por número de sesiones distintas).
*   [ ] 8. Tabla (DataFrame): 10 tipos de fichero más repetidos (basado en extensión, ej: .gif, .jpg) (por número de accesos/hits).
*   [ ] 9. Tabla (DataFrame): 10 páginas de entrada (primera página de una sesión) más repetidas (por número de sesiones que inician con ellas).
*   [ ] 10. Tabla (DataFrame): 10 páginas de salida (última página de una sesión) más repetidas (por número de sesiones que terminan con ellas).
*   [ ] 11. Tabla (DataFrame): 10 páginas de acceso único (sesiones con una sola página vista) más visitadas.
*   [ ] 12. Tabla (DataFrame): distribución de la duración de las visitas/sesiones en minutos (rangos: 0-1 min, 1-2 min, ..., etc.) (contar número de visitas/sesiones por rango).

## 3. Documentación y entrega
*   [ ] 1. Preparar una memoria en formato PDF que incluya:
    *   Los pasos llevados a cabo en cada tarea.
    *   Las tablas de resultados (pueden ser capturas de DataFrames de Pandas o tablas generadas a partir de ellos).
    *   Los gráficos generados con Python (Matplotlib/Seaborn).
    *   El análisis realizado para cada sección.
*   [ ] 2. Incluir todos los scripts de Python (`.py` files) ubicados en la carpeta `src/`. 
*   [ ] 3. Comprimir todo (PDF, `src/` con scripts, `datos/` si es necesario (aunque el profesor ya lo tiene)) en un fichero ZIP.

## 4. Envío
*   [ ] 1. Enviar el fichero ZIP a través de la tarea de PLATEA habilitada.
*   [ ] 2. **Fecha tope de entrega: 16 de mayo a las 23:59.**