import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de Seaborn para los gráficos
sns.set_theme(style="whitegrid")

def load_processed_data(file_path: str) -> pd.DataFrame | None:
    """Carga el DataFrame procesado desde un archivo Parquet."""
    print(f"Cargando datos procesados desde: {file_path}")
    if not os.path.exists(file_path):
        print(f"Error: El archivo {file_path} no fue encontrado. Asegúrate de ejecutar preprocessing.py primero.")
        return None
    try:
        df = pd.read_parquet(file_path)
        print("Datos procesados cargados exitosamente.")
        df.info()
        return df
    except Exception as e:
        print(f"Error al cargar el archivo Parquet: {e}")
        return None

def calculate_session_durations(df: pd.DataFrame) -> pd.Series:
    """
    Filtra sesiones que contienen más de una visita y calcula la duración de estas sesiones.
    La duración es la diferencia entre el timestamp del último y primer hit de la sesión.
    Devuelve una Serie de Pandas con las duraciones de las sesiones (en segundos).
    """
    print("\nCalculando duraciones de sesión para sesiones con más de una visita...")
    
    # Contar hits por sesión
    session_hit_counts = df.groupby('SessionID')['marca de tiempo'].count()
    
    # Identificar sesiones con más de un hit
    multi_hit_sessions = session_hit_counts[session_hit_counts > 1].index
    
    if len(multi_hit_sessions) == 0:
        print("No se encontraron sesiones con más de una visita.")
        return pd.Series(dtype='float64')
        
    print(f"Se encontraron {len(multi_hit_sessions)} sesiones con más de una visita (de un total de {df['SessionID'].nunique()} sesiones).")
    
    # Filtrar el DataFrame para incluir solo estas sesiones
    df_multi_hit = df[df['SessionID'].isin(multi_hit_sessions)]
    
    # Calcular min y max timestamp por sesión
    session_min_max_times = df_multi_hit.groupby('SessionID')['marca de tiempo'].agg(['min', 'max'])
    
    # Calcular duración
    session_durations = session_min_max_times['max'] - session_min_max_times['min']
    
    print(f"Duraciones calculadas para {len(session_durations)} sesiones.")
    print("Primeras 5 duraciones de sesión (en segundos):")
    print(session_durations.head())
    
    return session_durations

def plot_session_duration_histogram(
    session_durations_seconds: pd.Series, 
    output_dir: str,
    filename: str = "session_duration_histogram.png",
    threshold_percentile: float | None = 0.99 # e.g. 0.99 to cap at 99th percentile
) -> None:
    """
    Genera y guarda un histograma de la duración de la sesión (para sesiones con >1 visita).
    Las duraciones se esperan en segundos.
    Permite el filtrado de valores atípicos basado en un percentil.
    """
    if session_durations_seconds.empty:
        print("No hay duraciones de sesión para generar el histograma.")
        return

    durations_to_plot = session_durations_seconds.copy()
    original_count = len(durations_to_plot)
    description_for_memoria = ""

    if threshold_percentile is not None and 0 < threshold_percentile < 1:
        cap_value = durations_to_plot.quantile(threshold_percentile)
        durations_to_plot_filtered = durations_to_plot[durations_to_plot <= cap_value]
        omitted_count = original_count - len(durations_to_plot_filtered)
        if omitted_count > 0:
            description_for_memoria = (
                f"Para mejorar la visualización, se omitieron los valores de duración de sesión por encima del percentil "
                f"{threshold_percentile*100:.0f} ({cap_value:.2f} segundos). "
                f"Esto afectó a {omitted_count} sesiones ({omitted_count/original_count*100:.2f}% del total de sesiones con >1 visita)."
            )
            print(description_for_memoria)
            durations_to_plot = durations_to_plot_filtered
        else:
            description_for_memoria = "No se omitieron valores atípicos para este histograma."
            print(description_for_memoria)
    else:
        description_for_memoria = "No se aplicó filtrado de valores atípicos para este histograma."
        print(description_for_memoria)

    # Convertir a minutos para una mejor escala en el histograma si las duraciones son grandes
    # Decision: si la mediana o la media de las duraciones (después del cap) es > pocos minutos, convertir a minutos
    # Por ahora, graficaremos en segundos y luego evaluaremos si es necesario convertir a minutos.
    # O mejor, siempre mostrar en X minutos si el cap_value es grande.

    plt.figure(figsize=(12, 7))
    # Usar bins apropiados; 'auto' es un buen comienzo, o calcular Sturges/Freedman-Diaconis si es necesario
    sns.histplot(durations_to_plot, kde=True, bins='auto') 
    
    # Determinar la unidad para el eje X basado en la magnitud de los datos
    max_duration_to_plot = durations_to_plot.max()
    if max_duration_to_plot > 300: # Si el max es más de 5 minutos, considerar escala en minutos
        # Podríamos re-plotear con datos convertidos a minutos o simplemente ajustar las etiquetas
        # Para simplicidad ahora, mantenemos segundos pero hacemos el título claro
        plt.title(f'Histograma de Duración de Sesión (>1 visita)\n{description_for_memoria.split(". ")[0]}')
        plt.xlabel("Duración de la Sesión (segundos)")
    else:
        plt.title(f'Histograma de Duración de Sesión (>1 visita)\n{description_for_memoria.split(". ")[0]}')
        plt.xlabel("Duración de la Sesión (segundos)")
        
    plt.ylabel("Número de Sesiones")
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    file_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(file_path)
        print(f"Histograma de duración de sesión guardado en: {file_path}")
    except Exception as e:
        print(f"Error al guardar el histograma: {e}")
    plt.close()
    
    # Guardar la descripción para la memoria en un archivo de texto
    memoria_notes_path = os.path.join(output_dir, "session_duration_histogram_notes.txt")
    with open(memoria_notes_path, "w") as f:
        f.write(description_for_memoria)
    print(f"Notas para la memoria guardadas en: {memoria_notes_path}")

def get_session_duration_stats(
    session_durations_seconds: pd.Series, 
    output_dir: str,
    filename: str = "session_duration_stats.txt"
) -> pd.DataFrame | None:
    """
    Calcula y guarda un resumen estadístico de la duración de la sesión.
    Devuelve un DataFrame con las estadísticas y también las guarda en un archivo.
    """
    if session_durations_seconds.empty:
        print("No hay duraciones de sesión para calcular estadísticas.")
        return None

    print("\nCalculando estadísticas descriptivas para la duración de la sesión (>1 visita)...")
    
    # Usar .describe() para la mayoría de las estadísticas
    stats_desc = session_durations_seconds.describe()
    
    # Calcular la moda (puede haber múltiples modas)
    modes = session_durations_seconds.mode()
    # Convertir a DataFrame para unificar la salida
    stats_df = stats_desc.to_frame().T

    # Añadir la moda (o modas)
    # Si hay múltiples modas, las concatenamos como string para la tabla resumen
    if not modes.empty:
        stats_df['mode'] = ", ".join(map(str, modes.tolist()))
    else:
        stats_df['mode'] = 'N/A' # Caso improbable para datos continuos, pero por si acaso
        
    # Renombrar columnas para claridad si es necesario (describe() ya usa nombres bastante buenos)
    # stats_df.rename(columns={'mean': 'Media', 'std': 'Desv. Estándar', ...}, inplace=True)
    # Por ahora, los nombres por defecto son aceptables.

    print("\nResumen Estadístico de Duración de Sesión (segundos):")
    print(stats_df.to_string())

    file_path = os.path.join(output_dir, filename)
    try:
        with open(file_path, 'w') as f:
            f.write("Resumen Estadístico de Duración de Sesión (segundos) para sesiones con >1 visita:\n")
            f.write(stats_df.to_string())
        print(f"Estadísticas de duración de sesión guardadas en: {file_path}")
    except Exception as e:
        print(f"Error al guardar las estadísticas: {e}")
        
    return stats_df

if __name__ == '__main__':
    # Construir rutas de manera robusta
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..')
    
    input_data_path = os.path.join(project_root, 'output', 'processed_log_data.parquet')
    input_data_path = os.path.normpath(input_data_path)
    
    output_graphics_dir = os.path.join(project_root, 'output', 'graphics', 'analysis')
    output_graphics_dir = os.path.normpath(output_graphics_dir)
    if not os.path.exists(output_graphics_dir):
        os.makedirs(output_graphics_dir)
        print(f"Directorio para gráficos creado: {output_graphics_dir}")

    # Cargar datos
    df_processed = load_processed_data(input_data_path)
    
    if df_processed is not None:
        # --- Tarea 2.1.2: Calcular duración de sesiones (>1 visita) ---
        session_durations_seconds = calculate_session_durations(df_processed)
        
        if not session_durations_seconds.empty:
            print(f"\nTotal de sesiones con >1 visita para análisis de duración: {len(session_durations_seconds)}")
            # --- Tarea 2.1.3: Generar histograma de duración de sesión ---
            plot_session_duration_histogram(session_durations_seconds, output_graphics_dir)

            # --- Tarea 2.1.4: Calcular resumen estadístico de duración de sesión ---
            session_duration_stats_df = get_session_duration_stats(session_durations_seconds, output_graphics_dir) # Guardar en el mismo dir que los gráficos
            # La variable session_duration_stats_df se puede usar más adelante si es necesario

        else:
            print("No hay duraciones de sesión para analizar más a fondo.")

        # Aquí se añadirán las llamadas a las funciones para las tareas 2.1.4, etc.

    else:
        print("No se pudieron cargar los datos procesados. Terminando el script de análisis.") 