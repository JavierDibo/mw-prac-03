import pandas as pd
import re
import os

# Regex to parse a single log line based on Combined Log Format.
# Fields captured: host, datetime, method, page, protocol, status, size
LOG_PATTERN = re.compile(
    r'^(?P<host>\S+)\s+'                               # Host remoto
    r'-\s+-\s+'                                     # ident and user fields (always "-", not captured)
    r'\[(?P<datetime>[^\]]+)\]\s+'                     # Fecha/Hora (e.g., 01/Jul/1995:00:00:01 -0400)
    r'"(?P<method>GET|POST|HEAD|PUT|DELETE|OPTIONS|PATCH)\s+'  # Método HTTP
    r'(?P<page>\S+)\s+'                                # Página (Requested resource path)
    r'(?P<protocol>HTTP\/\d\.\d)"\s+'                  # Protocolo HTTP (e.g., HTTP/1.0)
    r'(?P<status>\d{3})\s+'                            # Resultado (HTTP status code)
    r'(?P<size>\S+)$'                                  # Tamaño (Size of object in bytes, can be '-')
)

# Column names as specified in TODO.md (updated)
COLUMN_NAMES = [
    'Host remoto', 'Fecha/Hora',
    'Método', 'Página', 'Protocolo', 'Resultado', 'Tamaño'
]

def _extract_extension_from_page(page_path: str) -> str:
    """
    Extrae la extensión de un path de página. Devuelve la extensión en minúsculas
    sin el punto inicial, o una cadena vacía si no hay extensión o es inválida.
    Ej: '/path/file.HTML' -> 'html'; '/path/' -> ''; '/path/nodot' -> ''.
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
        # Ensure the order matches COLUMN_NAMES (updated)
        return [parts['host'], parts['datetime'],
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

def generate_all_extensions_report(df: pd.DataFrame, save_path: str | None = None) -> pd.DataFrame:
    """
    Genera un informe con el conteo de todas las extensiones únicas en la columna 'Extensión'.
    Guarda el informe en un archivo CSV si se especifica la ruta.

    Args:
        df (pd.DataFrame): DataFrame de entrada con la columna 'Extensión' ya creada.
        save_path (str | None): Ruta para guardar el informe CSV.

    Returns:
        pd.DataFrame: DataFrame con las columnas ['Extensión', 'Número de Repeticiones'].
    """
    print("\nGenerando informe de distribución de todas las extensiones...")
    if 'Extensión' not in df.columns:
        print("Error: La columna 'Extensión' no existe. No se puede generar el informe.")
        return pd.DataFrame(columns=['Extensión', 'Número de Repeticiones'])

    # Contar todas las ocurrencias, incluyendo "" para sin extensión.
    # value_counts por defecto ordena de mayor a menor frecuencia.
    extension_counts = df['Extensión'].value_counts(dropna=False).reset_index()
    extension_counts.columns = ['Extensión', 'Número de Repeticiones']
    
    # Reemplazar NaN en la columna 'Extensión' por una cadena representativa si existiera
    # (aunque _extract_extension_from_page está diseñado para devolver "")
    extension_counts['Extensión'] = extension_counts['Extensión'].fillna('[NaN_Ext]')

    print(f"Número total de tipos de extensiones únicas (incluyendo sin extensión y NaN si los hubiera): {len(extension_counts)}")
    print("Primeras 20 extensiones por frecuencia (de todas las existentes):")
    print(extension_counts.head(20))
    if len(extension_counts) > 20:
        print(f"(... y {len(extension_counts) - 20} más. Ver el archivo CSV para la lista completa.)")

    if save_path:
        try:
            output_dir = os.path.dirname(save_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"Directorio creado: {output_dir}")
            extension_counts.to_csv(save_path, index=False)
            print(f"Informe completo de distribución de extensiones guardado en: {save_path}")
        except Exception as e:
            print(f"Error al guardar el informe de distribución de extensiones: {e}")
            
    return extension_counts

def identify_bots_by_robots_txt(df: pd.DataFrame, save_path_details: str | None = None, save_path_summary: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Identifica hosts que accedieron a '/robots.txt' como bots, añade una columna 'Is_Bot' al DataFrame,
    y genera tablas de resumen de los bots identificados y sus proporciones.

    Args:
        df (pd.DataFrame): El DataFrame de logs de entrada.
        save_path_details (str | None): Ruta para guardar la tabla de detalles de bots.
        save_path_summary (str | None): Ruta para guardar la tabla de resumen de proporciones de bots.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: 
            - DataFrame original con la columna 'Is_Bot' añadida.
            - DataFrame con detalles de los hosts identificados como bots y su número de peticiones.
            - DataFrame con el resumen de peticiones de bots vs. no bots y sus proporciones.
    """
    print("\nIdentificando bots por acceso a '/robots.txt'...")
    if 'Página' not in df.columns or 'Host remoto' not in df.columns:
        print("Error: Las columnas 'Página' y/o 'Host remoto' son necesarias y no se encuentran en el DataFrame.")
        empty_details = pd.DataFrame(columns=['Bot Host Remoto', 'Número de Peticiones del Bot'])
        empty_summary = pd.DataFrame(columns=['Categoría', 'Número de Peticiones', 'Proporción'])
        return df, empty_details, empty_summary

    # Identificar hosts que accedieron a /robots.txt (insensible a mayúsculas/minúsculas para /robots.txt)
    # Asegurarse de que 'Página' no tenga NaNs que puedan causar problemas con .str
    bot_hosts = df[df['Página'].fillna('').str.lower() == '/robots.txt']['Host remoto'].unique()

    if len(bot_hosts) == 0:
        print("No se identificaron hosts que hayan accedido a '/robots.txt'.")
        df['Is_Bot'] = False
        identified_bots_details_df = pd.DataFrame(columns=['Bot Host Remoto', 'Número de Peticiones del Bot'])
    else:
        print(f"Se identificaron {len(bot_hosts)} hosts como bots por acceder a '/robots.txt'.")
        df['Is_Bot'] = df['Host remoto'].isin(bot_hosts)
        
        # Crear tabla de detalles de bots identificados
        bot_requests_df = df[df['Is_Bot']]
        identified_bots_details_df = bot_requests_df.groupby('Host remoto').size().reset_index(name='Número de Peticiones del Bot')
        identified_bots_details_df.rename(columns={'Host remoto': 'Bot Host Remoto'}, inplace=True)
        identified_bots_details_df.sort_values(by='Número de Peticiones del Bot', ascending=False, inplace=True)
        print("\nTop 5 hosts identificados como bots y su número de peticiones:")
        print(identified_bots_details_df.head())

    # Crear tabla de resumen de proporciones
    total_requests = len(df)
    total_bot_requests = df['Is_Bot'].sum()
    total_human_requests = total_requests - total_bot_requests
    
    bot_proportion = total_bot_requests / total_requests if total_requests > 0 else 0
    human_proportion = total_human_requests / total_requests if total_requests > 0 else 0
    
    overall_bot_proportions_df = pd.DataFrame({
        'Categoría': ['Bots Identificados', 'Peticiones No Identificadas como Bot'],
        'Número de Peticiones': [total_bot_requests, total_human_requests],
        'Proporción': [bot_proportion, human_proportion]
    })
    print("\nResumen de proporciones de bots:")
    print(overall_bot_proportions_df)

    # Guardar tablas si se especificaron las rutas
    if save_path_details and not identified_bots_details_df.empty:
        try:
            output_dir_details = os.path.dirname(save_path_details)
            if output_dir_details and not os.path.exists(output_dir_details):
                os.makedirs(output_dir_details)
            identified_bots_details_df.to_csv(save_path_details, index=False)
            print(f"Tabla de detalles de bots guardada en: {save_path_details}")
        except Exception as e:
            print(f"Error al guardar la tabla de detalles de bots: {e}")

    if save_path_summary:
        try:
            output_dir_summary = os.path.dirname(save_path_summary)
            if output_dir_summary and not os.path.exists(output_dir_summary):
                os.makedirs(output_dir_summary)
            overall_bot_proportions_df.to_csv(save_path_summary, index=False)
            print(f"Tabla de resumen de proporciones de bots guardada en: {save_path_summary}")
        except Exception as e:
            print(f"Error al guardar la tabla de resumen de proporciones de bots: {e}")
            
    return df, identified_bots_details_df, overall_bot_proportions_df

def identify_sessions(df: pd.DataFrame, user_col: str = 'UserID', timestamp_col: str = 'marca de tiempo', timeout_seconds: int = 1800) -> pd.DataFrame:
    """
    Identifica sesiones de usuario basadas en un timeout entre hits consecutivos.
    Añade una columna 'SessionID' al DataFrame.

    Args:
        df (pd.DataFrame): DataFrame de entrada. Debe tener user_col y timestamp_col.
        user_col (str): Nombre de la columna con el identificador de usuario.
        timestamp_col (str): Nombre de la columna con la marca de tiempo en segundos.
        timeout_seconds (int): Umbral de tiempo en segundos para definir una nueva sesión.

    Returns:
        pd.DataFrame: El DataFrame con la columna 'SessionID' añadida.
    """
    print(f"\nIdentificando sesiones con un timeout de {timeout_seconds / 60} minutos...")
    if user_col not in df.columns or timestamp_col not in df.columns:
        print(f"Error: Las columnas '{user_col}' y/o '{timestamp_col}' son necesarias y no se encuentran.")
        return df

    # Asegurar que el DataFrame esté ordenado correctamente
    # Es crucial para que el cálculo de la diferencia de tiempo sea correcto dentro de cada grupo de usuario
    df_sorted = df.sort_values(by=[user_col, timestamp_col])

    # Calcular la diferencia de tiempo con el hit anterior PARA EL MISMO USUARIO
    df_sorted['time_diff_prev_hit'] = df_sorted.groupby(user_col)[timestamp_col].diff()

    # Una nueva sesión comienza si:
    # 1. Es el primer hit del usuario (time_diff_prev_hit es NaT/NaN)
    # 2. La diferencia de tiempo con el hit anterior excede el timeout
    df_sorted['_is_new_session_start'] = (
        df_sorted['time_diff_prev_hit'].isnull() | 
        (df_sorted['time_diff_prev_hit'] > timeout_seconds)
    )

    # Crear un contador de sesión para cada usuario
    df_sorted['_session_increment'] = df_sorted.groupby(user_col)['_is_new_session_start'].cumsum()

    # Crear el SessionID combinando UserID y el contador de sesión
    df_sorted['SessionID'] = df_sorted[user_col].astype(str) + "_" + df_sorted['_session_increment'].astype(str)

    # Eliminar columnas intermedias
    df_out = df_sorted.drop(columns=['time_diff_prev_hit', '_is_new_session_start', '_session_increment'])
    
    print(f"Columna 'SessionID' creada. Número de sesiones únicas identificadas: {df_out['SessionID'].nunique()}")
    return df_out

if __name__ == '__main__':
    # Get the absolute path of the directory where this script is located (src/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the absolute path to the project root (one level up from src/)
    project_root = os.path.join(script_dir, '..')
    
    # Construct the absolute path to the log file
    log_file_name = 'NASA_access_log_FULL.txt' # O usa 'NASA_access_log_sample_for_testing.txt' para pruebas
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

        # Nueva función para contar TODAS las extensiones
        all_extensions_report_path = os.path.join(output_base_dir, 'all_extensions_distribution.csv')
        generate_all_extensions_report(df_log, save_path=all_extensions_report_path)

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
        
        print("\nInformación del DataFrame filtrado (antes de identificar bots):")
        df_log_filtered.info()
        # print(df_log_filtered.head()) # Comentado para reducir output, ya se imprimió info

        # 1.3.1. Identificar bots por acceso a /robots.txt y generar tablas
        bots_details_csv_path = os.path.join(output_base_dir, 'identified_bots_details.csv')
        bot_proportions_csv_path = os.path.join(output_base_dir, 'bot_proportions_summary.csv')
        
        df_log_with_bot_flag, bots_details_table, bot_proportions_table = identify_bots_by_robots_txt(
            df_log_filtered.copy(), 
            save_path_details=bots_details_csv_path,
            save_path_summary=bot_proportions_csv_path
        )
        
        # print("\nInformación del DataFrame después de añadir la bandera 'Is_Bot':")
        # df_log_with_bot_flag.info()
        # print(df_log_with_bot_flag[['Host remoto', 'Página', 'Is_Bot']].head())
        # if df_log_with_bot_flag['Is_Bot'].any():
        #     print("\nEjemplos de filas marcadas como bots:")
        #     print(df_log_with_bot_flag[df_log_with_bot_flag['Is_Bot']].head())

        # 1.3.2. Eliminar los registros identificados como bots
        df_log_no_bots = df_log_with_bot_flag[~df_log_with_bot_flag['Is_Bot']].copy()
        print("\nInformación del DataFrame después de eliminar los bots identificados (df_log_no_bots):")
        # df_log_no_bots.info() # Comentado para reducir output
        # print("\nPrimeras 5 filas del DataFrame sin bots (df_log_no_bots):")
        # print(df_log_no_bots.head())
        
        # 1.4.3. Añadir columna 'UserID' (basada en 'Host remoto')
        print("\nAñadiendo columna 'UserID'...")
        df_log_no_bots['UserID'] = df_log_no_bots['Host remoto']
        print("Columna 'UserID' añadida.")
        # print(df_log_no_bots[['Host remoto', 'UserID']].head())

        # 1.5.1 & 1.5.2. Identificar sesiones y añadir 'SessionID'
        df_final_processed = identify_sessions(df_log_no_bots)
        print("\nInformación del DataFrame después de añadir 'SessionID':")
        df_final_processed.info()
        print("\nPrimeras filas del DataFrame con 'SessionID' (ordenado por UserID, marca de tiempo):")
        print(df_final_processed[['UserID', 'marca de tiempo', 'SessionID', 'Página']].head(10))
        
        # Guardar el DataFrame procesado para ser usado en el análisis
        output_processed_data_dir = os.path.join(project_root, 'output')
        if not os.path.exists(output_processed_data_dir):
            os.makedirs(output_processed_data_dir)
            print(f"Directorio creado: {output_processed_data_dir}")
        
        processed_data_path = os.path.join(output_processed_data_dir, 'processed_log_data.parquet')
        try:
            df_final_processed.to_parquet(processed_data_path, index=False)
            print(f"DataFrame procesado guardado en: {processed_data_path}")
        except Exception as e:
            print(f"Error al guardar el DataFrame procesado en Parquet: {e}")

        # Mostrar un ejemplo de varias sesiones para un mismo usuario si es posible
        if df_final_processed['SessionID'].nunique() < len(df_final_processed):
            # Buscar un UserID que tenga más de una sesión
            user_session_counts = df_final_processed.groupby('UserID')['SessionID'].nunique()
            multi_session_users = user_session_counts[user_session_counts > 1].index
            if not multi_session_users.empty:
                example_user = multi_session_users[0]
                print(f"\nEjemplo de sesiones para el UserID: {example_user}")
                print(df_final_processed[df_final_processed['UserID'] == example_user][['UserID', 'Fecha/Hora', 'marca de tiempo', 'SessionID', 'Página']].head(15))
            else:
                print("\nNo se encontraron usuarios con múltiples sesiones para mostrar como ejemplo detallado (raro).")
        else:
            print("\nCada petición es una sesión única o solo hay un usuario/sesión (raro para un dataset grande).")

    else:
        print("La carga del DataFrame falló.") 