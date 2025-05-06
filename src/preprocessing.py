import pandas as pd
import re
import os

# Regex to parse a single log line based on Combined Log Format.
# Fields captured: host, ident, user, datetime, method, page, protocol, status, size
LOG_PATTERN = re.compile(
    r'^(?P<host>\S+)\s+'                               # Host remoto
    r'(?P<ident>\S+)\s+'                               # Contraseña (Remote logname, often '-')
    r'(?P<user>\S+)\s+'                                # Usuario (Remote user, often '-')
    r'\[(?P<datetime>[^\]]+)\]\s+'                     # Fecha/Hora (e.g., 01/Jul/1995:00:00:01 -0400)
    r'"(?P<method>GET|POST|HEAD|PUT|DELETE|OPTIONS|PATCH)\s+'  # Método HTTP
    r'(?P<page>\S+)\s+'                                # Página (Requested resource path)
    r'(?P<protocol>HTTP\/\d\.\d)"\s+'                  # Protocolo HTTP (e.g., HTTP/1.0)
    r'(?P<status>\d{3})\s+'                            # Resultado (HTTP status code)
    r'(?P<size>\S+)$'                                  # Tamaño (Size of object in bytes, can be '-')
)

# Column names as specified in TODO.md
COLUMN_NAMES = [
    'Host remoto', 'Contraseña', 'Usuario', 'Fecha/Hora',
    'Método', 'Página', 'Protocolo', 'Resultado', 'Tamaño'
]

def _extract_extension_from_page(page_path: str) -> str:
    """
    Extrae la extensión de un path de página. Devuelve la extensión en minúsculas
    sin el punto inicial, o una cadena vacía si no hay extensión o es inválida.
    Ej: '/path/file.HTML' -> 'html'; '/path/' -> ''; '/path/nodot' -> ''
    """
    if pd.isna(page_path):
        return ""
    # os.path.splitext devuelve ('root', '.ext') o ('root', '')
    _root, ext = os.path.splitext(str(page_path))
    if ext.startswith('.'):
        return ext[1:].lower() # Eliminar el punto inicial y convertir a minúsculas
    return "" # Si no hay punto (ext es '') o es una extensión vacía rara.

def parse_log_line(line: str) -> list | None:
    """
    Parses a single log line using the precompiled regex LOG_PATTERN.
    Returns a list of captured string values in the order of COLUMN_NAMES, 
    or None if the line does not match the pattern.
    """
    match = LOG_PATTERN.match(line)
    if match:
        parts = match.groupdict()
        # Ensure the order matches COLUMN_NAMES
        return [parts['host'], parts['ident'], parts['user'], parts['datetime'],
                parts['method'], parts['page'], parts['protocol'],
                parts['status'], parts['size']]
    return None

def load_log_data(log_file_path: str) -> pd.DataFrame | None:
    """
    Carga el fichero log de NASA y lo convierte en un DataFrame de Pandas,
    parseando cada línea con expresiones regulares.

    Args:
        log_file_path (str): Path to the NASA access log file.

    Returns:
        pd.DataFrame | None: DataFrame containing the parsed log data, or None if an error occurs.
    """
    print(f"Cargando y parseando datos desde {log_file_path}...")
    parsed_data = []
    processed_lines = 0
    skipped_lines = 0

    try:
        # Using utf-8 with errors='ignore' for robustness against potential encoding issues.
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                processed_lines += 1
                stripped_line = line.strip()
                if not stripped_line: # Skip empty lines
                    skipped_lines +=1
                    continue
                
                parsed_line_data = parse_log_line(stripped_line)
                if parsed_line_data:
                    parsed_data.append(parsed_line_data)
                else:
                    skipped_lines += 1
                    # Uncomment for debugging malformed lines:
                    # print(f"Advertencia: Línea no parseada [{processed_lines}]: {stripped_line}") 
                
                if processed_lines % 500000 == 0: # Provide feedback for very large files
                    print(f"Procesadas {processed_lines} líneas... ({len(parsed_data)} válidas, {skipped_lines} omitidas)")

    except FileNotFoundError:
        print(f"Error: El archivo {log_file_path} no fue encontrado.")
        return None
    except Exception as e:
        print(f"Ocurrió un error al leer o parsear el archivo: {e}")
        return None

    if not parsed_data:
        print("No se pudieron parsear datos válidos del archivo log.")
        return None

    df = pd.DataFrame(parsed_data, columns=COLUMN_NAMES)
    print(f"Procesamiento finalizado. Total líneas leídas: {processed_lines}, Filas en DataFrame: {len(df)}, Líneas omitidas/no parseadas: {skipped_lines}")
    
    # Convertir columnas 'Resultado' (status) y 'Tamaño' (size) a tipos numéricos.
    # Para 'Tamaño', los valores '-' se convertirán a NaN (Not a Number).
    df['Resultado'] = pd.to_numeric(df['Resultado'], errors='coerce') # Status code should be numeric
    df['Tamaño'] = pd.to_numeric(df['Tamaño'], errors='coerce')     # Size can be '-'

    # 1.1.3. Convertir la columna Fecha/Hora a objetos datetime
    print("Convirtiendo la columna 'Fecha/Hora' a objetos datetime...")
    # El formato es como: 01/Jul/1995:00:00:01 -0400
    df['Fecha/Hora'] = pd.to_datetime(df['Fecha/Hora'], format='%d/%b/%Y:%H:%M:%S %z', errors='coerce')

    # Comprobar si hubo errores de conversión (NaT) y reportar
    nat_count = df['Fecha/Hora'].isnull().sum()
    if nat_count > 0:
        print(f"Advertencia: {nat_count} entradas en 'Fecha/Hora' no pudieron ser convertidas a datetime y son NaT.")

    # 1.1.4. Crear columna 'marca de tiempo' (segundos desde 1 Enero 1995)
    print("Creando columna 'marca de tiempo'...")
    if not df['Fecha/Hora'].isnull().all(): # Proceed if there are any valid datetimes
        # Convertir Fecha/Hora a UTC para consistencia, si no lo está ya por el %z.
        # pd.to_datetime con %z ya los hace tz-aware.
        # Para asegurar una base común, convertimos a UTC.
        df['Fecha/Hora_UTC'] = df['Fecha/Hora'].dt.tz_convert('UTC')
        
        # Definir la fecha de referencia como UTC
        ref_date_utc = pd.Timestamp("1995-01-01 00:00:00", tz='UTC')
        
        # Calcular la diferencia en segundos
        # Solo calcular si la fecha no es NaT
        df['marca de tiempo'] = (df['Fecha/Hora_UTC'] - ref_date_utc).dt.total_seconds()
        
        # Opcional: eliminar la columna intermedia Fecha/Hora_UTC si no se necesita más
        # df.drop(columns=['Fecha/Hora_UTC'], inplace=True)
        
        # Si Fecha/Hora original era NaT, marca de tiempo también será NaT. Esto es correcto.
        print("Columna 'marca de tiempo' creada.")
    else:
        print("Columna 'Fecha/Hora' no contiene fechas válidas para calcular 'marca de tiempo'.")
        df['marca de tiempo'] = pd.NaT # O np.nan si se prefiere float para esta columna en caso de fallo total

    return df

def get_top_extensions(df: pd.DataFrame, top_n: int = 10, save_to_csv_path: str | None = None) -> pd.DataFrame:
    """
    Usa la columna pre-calculada 'Extensión' del DataFrame, cuenta sus ocurrencias y 
    devuelve un DataFrame con las top_n extensiones más repetidas.
    Opcionalmente guarda el DataFrame en un archivo CSV.
    """
    if 'Extensión' not in df.columns:
        print("Error: La columna 'Extensión' no existe en el DataFrame. Asegúrate de crearla primero.")
        return pd.DataFrame()

    print(f"\nExtrayendo las {top_n} extensiones de página más comunes desde la columna 'Extensión'...")
    
    valid_extensions = df['Extensión'][df['Extensión'] != ""]
    
    if valid_extensions.empty:
        print("No se encontraron extensiones válidas en la columna 'Extensión'.")
        return pd.DataFrame({'Extensión': [], 'Número de Repeticiones': []})

    extension_counts = valid_extensions.value_counts().head(top_n)
    top_extensions_df = extension_counts.reset_index()
    top_extensions_df.columns = ['Extensión', 'Número de Repeticiones']
    
    print(f"Top {top_n} extensiones encontradas:")
    print(top_extensions_df)

    if save_to_csv_path:
        try:
            output_dir = os.path.dirname(save_to_csv_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"Directorio creado: {output_dir}")
            top_extensions_df.to_csv(save_to_csv_path, index=False)
            print(f"Tabla de extensiones guardada en: {save_to_csv_path}")
        except Exception as e:
            print(f"Error al guardar la tabla de extensiones en CSV: {e}")
            
    return top_extensions_df

def filter_dataframe_by_extensions(df: pd.DataFrame, allowed_extensions: set[str]) -> pd.DataFrame:
    """
    Filtra el DataFrame manteniendo solo los registros cuyas extensiones de página
    estén en la lista `allowed_extensions` o aquellos donde la extensión esté en blanco.
    La columna 'Extensión' debe existir en el DataFrame.
    """
    if 'Extensión' not in df.columns:
        print("Error: La columna 'Extensión' no existe para el filtrado. Asegúrate de crearla primero.")
        return df # Devuelve el DataFrame original si no se puede filtrar

    print(f"\nFiltrando el DataFrame por extensiones permitidas: {allowed_extensions} o sin extensión...")
    rows_before_filter = len(df)
    
    # Condición: la extensión está en la lista O la extensión es una cadena vacía
    condition = df['Extensión'].isin(allowed_extensions) | (df['Extensión'] == "")
    
    df_filtered = df[condition].copy() # Usar .copy() para evitar SettingWithCopyWarning más adelante
    
    rows_after_filter = len(df_filtered)
    print(f"Filas antes del filtro: {rows_before_filter}")
    print(f"Filas después del filtro: {rows_after_filter}")
    print(f"Filas eliminadas: {rows_before_filter - rows_after_filter}")
    
    return df_filtered

if __name__ == '__main__':
    # Get the absolute path of the directory where this script is located (src/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the absolute path to the project root (one level up from src/)
    project_root = os.path.join(script_dir, '..')
    
    # Construct the absolute path to the log file
    log_file_name = 'NASA_access_log_FULL.txt'
    log_path = os.path.join(project_root, 'datos', log_file_name)
    log_path = os.path.normpath(log_path) # Normalize the path (e.g., src/../datos -> datos)

    # output_base_dir is already robustly defined relative to script_dir
    output_base_dir = os.path.join(project_root, 'output', 'tables') # Adjusted to be from project_root too for consistency
    output_base_dir = os.path.normpath(output_base_dir)

    print(f"Intentando cargar el log desde la ruta: {log_path}")
    df_log = load_log_data(log_path)
    
    if df_log is not None:
        print("\nPrimeras 5 líneas del DataFrame resultante (antes de añadir 'Extensión'):")
        print(df_log.head())
        
        # Crear la columna 'Extensión' en el DataFrame principal
        print("\nCreando columna 'Extensión' en el DataFrame principal...")
        df_log['Extensión'] = df_log['Página'].apply(_extract_extension_from_page)
        print("Columna 'Extensión' creada.")
        print(f"Número de valores únicos en 'Extensión' (incluyendo vacíos): {df_log['Extensión'].nunique()}")
        print(df_log[['Página', 'Extensión']].head())

        print("\nInformación del DataFrame (después de añadir 'Extensión'):")
        df_log.info()

        # 1.2.1. Obtener y mostrar las 10 extensiones más comunes
        top_extensions_csv_path = os.path.join(output_base_dir, 'top_10_extensions.csv')
        top_ext_df = get_top_extensions(df_log, top_n=10, save_to_csv_path=top_extensions_csv_path)
        
        # 1.2.2. Filtrar el DataFrame por extensiones específicas
        # Extensiones permitidas (en minúsculas, sin punto)
        EXTENSIONS_TO_KEEP = {
            'htm', 'html', 'pdf', 'asp', 'exe',
            'txt', 'doc', 'ppt', 'xls', 'xml'
        }
        df_log_filtered = filter_dataframe_by_extensions(df_log, EXTENSIONS_TO_KEEP)
        
        print("\nInformación del DataFrame filtrado:")
        df_log_filtered.info()
        print(df_log_filtered.head())
        
        # Aquí df_log_filtered es el DataFrame que se usará para los siguientes pasos
        # Si se quisiera modificar df_log en sí, se haría df_log = filter_dataframe_by_extensions(df_log, ...)

    else:
        print("La carga del DataFrame falló.") 