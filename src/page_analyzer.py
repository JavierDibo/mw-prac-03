import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np # Added for potential use with NaN or specific conditions

# Configuración de Seaborn para los gráficos (si es específico o global)
# sns.set_theme(style="whitegrid") # Puede ser global en el main script

def _extract_extension(page_path: str) -> str:
    """
    Extrae la extensión de un path de página.
    Devuelve una cadena vacía si no hay extensión o si el path es NaN.
    """
    if pd.isna(page_path):
        return ""
    # Considerar que la 'página' puede ser solo '/' o similar sin un '.'
    # También manejar casos donde la página es un directorio (termina en '/')
    if '.' in str(page_path) and not str(page_path).endswith('/'):
        # Tomar la última parte después del último punto
        ext = str(page_path).split('.')[-1].lower()
        # Filtrar posibles parámetros en la URL después de la extensión
        ext_cleaned = ext.split('?')[0].split('#')[0]
        # Evitar que extensiones sean directorios completos si hay un error
        if '/' in ext_cleaned: # Si la "extensión" todavía contiene un '/', es probable que no sea una extensión real.
            return ""
        return ext_cleaned
    return ""

def classify_page_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clasifica las páginas en 'navegación' (sin extensión) o 'contenido' (con extensión)
    y añade una nueva columna 'PageType' al DataFrame.
    """
    print("\nClasificando tipos de página (navegación/contenido)...")
    if 'Página' not in df.columns:
        print("Error: La columna 'Página' no existe en el DataFrame.")
        # Añadir columna vacía para evitar errores posteriores si la columna no existe
        df['PageType'] = "desconocido" 
        return df

    # Asegurarse que la columna 'Página' sea de tipo string para evitar errores con .str
    df['extension'] = df['Página'].astype(str).apply(_extract_extension)
    
    # Clasificar basado en la presencia de una extensión
    # Si la extensión es una cadena vacía, se considera 'navegación'
    df['PageType'] = np.where(df['extension'] == '', 'navegación', 'contenido')
    
    print(f"Tipos de página clasificados. Distribución:\n{df['PageType'].value_counts(normalize=True)}")
    # Eliminar la columna temporal 'extension' si no se necesita más
    # df = df.drop(columns=['extension']) # Opcional: mantenerla si es útil para debugging
    return df

def calculate_mean_time_per_page(df: pd.DataFrame) -> tuple[pd.Series, float | None]:
    """
    Calcula el tiempo de visualización para cada página (excepto la última de cada sesión)
    y luego el tiempo medio por página.
    """
    print("\nCalculando el tiempo medio por página...")
    df_sorted = df.sort_values(by=['SessionID', 'marca de tiempo'])
    df_sorted['page_view_duration'] = df_sorted.groupby('SessionID')['marca de tiempo'].diff().shift(-1)
    all_page_view_durations = df_sorted['page_view_duration'].dropna()
    all_page_view_durations = all_page_view_durations[all_page_view_durations >= 0]

    if all_page_view_durations.empty:
        print("No se pudieron calcular duraciones de visualización de página.")
        return pd.Series(dtype='float64'), None

    mean_time_per_page = all_page_view_durations.mean()
    print(f"Se calcularon {len(all_page_view_durations)} duraciones de visualización de página individuales.")
    print(f"Tiempo medio por página (excluyendo la última de cada sesión): {mean_time_per_page:.2f} segundos.")
    return all_page_view_durations, mean_time_per_page

def plot_page_view_duration_histogram(
    page_view_durations_seconds: pd.Series,
    output_dir: str,
    filename: str = "page_view_duration_histogram.png",
    threshold_percentile: float | None = 0.99
) -> None:
    """
    Genera y guarda un histograma de las duraciones de visualización de página individuales.
    """
    if page_view_durations_seconds.empty:
        print("No hay duraciones de visualización de página para generar el histograma.")
        return

    durations_to_plot = page_view_durations_seconds.copy()
    original_count = len(durations_to_plot)
    description_for_memoria = ""

    if threshold_percentile is not None and 0 < threshold_percentile < 1:
        cap_value = durations_to_plot.quantile(threshold_percentile)
        if cap_value < 1 and (durations_to_plot > cap_value).any():
            description_for_memoria = "No se aplicó filtrado de valores atípicos significativos para este histograma (el umbral era demasiado bajo)."
        else:
            durations_to_plot_filtered = durations_to_plot[durations_to_plot <= cap_value]
            omitted_count = original_count - len(durations_to_plot_filtered)
            if omitted_count > 0:
                description_for_memoria = (
                    f"Para mejorar la visualización, se omitieron los valores de duración de página por encima del percentil "
                    f"{threshold_percentile*100:.0f} ({cap_value:.2f} segundos). "
                    f"Esto afectó a {omitted_count} vistas de página ({omitted_count/original_count*100:.2f}% del total de vistas de página)."
                )
                durations_to_plot = durations_to_plot_filtered
            else:
                description_for_memoria = "No se omitieron valores atípicos para este histograma."
    else:
        description_for_memoria = "No se aplicó filtrado de valores atípicos para este histograma."
    print(description_for_memoria)

    plt.figure(figsize=(12, 7))
    sns.histplot(durations_to_plot, kde=True, bins='auto')
    title_note = description_for_memoria.split(". ")[0]
    plt.title(f'Histograma de Tiempos de Visualización de Página\n{title_note}')
    plt.xlabel("Tiempo de Visualización de Página (segundos)")
    plt.ylabel("Número de Vistas de Página")
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    file_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(file_path)
        print(f"Histograma de tiempo de visualización de página guardado en: {file_path}")
    except Exception as e:
        print(f"Error al guardar el histograma: {e}")
    plt.close()

    memoria_notes_path = os.path.join(output_dir, "page_view_duration_histogram_notes.txt")
    with open(memoria_notes_path, "w") as f:
        f.write(description_for_memoria)
    print(f"Notas para la memoria (histograma tiempo por página) guardadas en: {memoria_notes_path}")

def get_page_view_duration_stats(
    page_view_durations_seconds: pd.Series,
    output_dir: str,
    filename: str = "page_view_duration_stats.txt"
) -> pd.DataFrame | None:
    """
    Calcula y guarda un resumen estadístico de las duraciones de visualización de página.
    """
    if page_view_durations_seconds.empty:
        print("No hay duraciones de visualización de página para calcular estadísticas.")
        return None

    print("\nCalculando estadísticas descriptivas para los tiempos de visualización de página...")
    stats_desc = page_view_durations_seconds.describe()
    modes = page_view_durations_seconds.mode()
    stats_df = stats_desc.to_frame().T

    if not modes.empty:
        stats_df['mode'] = ", ".join(map(str, modes.tolist()))
    else:
        stats_df['mode'] = 'N/A'

    print("\nResumen Estadístico de Tiempos de Visualización de Página (segundos):")
    print(stats_df.to_string())

    file_path = os.path.join(output_dir, filename)
    try:
        with open(file_path, 'w') as f:
            f.write("Resumen Estadístico de Tiempos de Visualización de Página (segundos):\n")
            f.write(stats_df.to_string())
        print(f"Estadísticas de tiempo de visualización de página guardadas en: {file_path}")
    except Exception as e:
        print(f"Error al guardar las estadísticas de tiempo de visualización de página: {e}")
    return stats_df

def calculate_first_second_page_durations(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    Calcula la duración de la visita a la primera y segunda página de cada sesión, donde sea posible.
    """
    print("\nCalculando duraciones de la primera y segunda página por sesión...")
    if 'SessionID' not in df.columns or 'marca de tiempo' not in df.columns:
        print("Error: Se requieren las columnas 'SessionID' y 'marca de tiempo'.")
        return pd.Series(dtype='float64'), pd.Series(dtype='float64')

    df_sorted = df.sort_values(by=['SessionID', 'marca de tiempo'])
    first_page_durs = []
    second_page_durs = []

    for session_id, group in df_sorted.groupby('SessionID'):
        timestamps = group['marca de tiempo'].tolist()
        if len(timestamps) >= 2:
            duration_first_page = timestamps[1] - timestamps[0]
            if duration_first_page >= 0:
                first_page_durs.append(duration_first_page)
        if len(timestamps) >= 3:
            duration_second_page = timestamps[2] - timestamps[1]
            if duration_second_page >= 0:
                second_page_durs.append(duration_second_page)
                
    s_first_page_durations = pd.Series(first_page_durs, dtype='float64')
    s_second_page_durs = pd.Series(second_page_durs, dtype='float64')
    print(f"Calculadas {len(s_first_page_durs)} duraciones para primeras páginas.")
    print(f"Calculadas {len(s_second_page_durs)} duraciones para segundas páginas.")
    return s_first_page_durs, s_second_page_durs

def plot_first_page_duration_histogram(
    first_page_durations_seconds: pd.Series,
    output_dir: str,
    filename: str = "first_page_duration_histogram.png",
    threshold_percentile: float | None = 0.99
) -> None:
    """
    Genera y guarda un histograma de las duraciones de la primera página de las sesiones.
    """
    if first_page_durations_seconds.empty:
        print("No hay duraciones de primera página para generar el histograma.")
        return

    durations_to_plot = first_page_durations_seconds.copy()
    original_count = len(durations_to_plot)
    description_for_memoria = ""

    if threshold_percentile is not None and 0 < threshold_percentile < 1:
        cap_value = durations_to_plot.quantile(threshold_percentile)
        if cap_value < 1 and (durations_to_plot > cap_value).any():
            description_for_memoria = "No se aplicó filtrado de valores atípicos significativos (umbral bajo)."
        else:
            durations_to_plot_filtered = durations_to_plot[durations_to_plot <= cap_value]
            omitted_count = original_count - len(durations_to_plot_filtered)
            if omitted_count > 0:
                description_for_memoria = (
                    f"Para mejorar la visualización, se omitieron duraciones de primera página por encima del percentil "
                    f"{threshold_percentile*100:.0f} ({cap_value:.2f} segundos). "
                    f"Esto afectó a {omitted_count} primeras páginas ({omitted_count/original_count*100:.2f}% del total)."
                )
                durations_to_plot = durations_to_plot_filtered
            else:
                description_for_memoria = "No se omitieron valores atípicos para este histograma."
    else:
        description_for_memoria = "No se aplicó filtrado de valores atípicos para este histograma."
    print(description_for_memoria)

    plt.figure(figsize=(12, 7))
    sns.histplot(durations_to_plot, kde=True, bins='auto')
    title_note = description_for_memoria.split(". ")[0]
    plt.title(f'Histograma de Duración de la Primera Página en Sesiones\n{title_note}')
    plt.xlabel("Duración de la Primera Página (segundos)")
    plt.ylabel("Número de Sesiones")
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    file_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(file_path)
        print(f"Histograma de duración de primera página guardado en: {file_path}")
    except Exception as e:
        print(f"Error al guardar el histograma: {e}")
    plt.close()

    memoria_notes_path = os.path.join(output_dir, "first_page_duration_histogram_notes.txt")
    with open(memoria_notes_path, "w") as f:
        f.write(description_for_memoria)
    print(f"Notas para la memoria (histograma duración primera página) guardadas en: {memoria_notes_path}")

def get_first_second_page_duration_stats(
    first_page_durations: pd.Series,
    second_page_durations: pd.Series,
    output_dir: str,
    filename: str = "first_second_page_duration_stats.txt"
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """
    Calcula y guarda estadísticas descriptivas para las duraciones de la primera y segunda página.
    """
    stats_dfs = []
    series_to_process = [
        ("Primera Página", first_page_durations),
        ("Segunda Página", second_page_durations)
    ]
    output_text_content = ""

    for name, series_data in series_to_process:
        print(f"\nCalculando estadísticas para Duración de la {name}...")
        if series_data.empty:
            print(f"No hay datos de duración para la {name}.")
            stats_dfs.append(None)
            output_text_content += f"Resumen Estadístico para Duración de la {name} (segundos):\nNo hay datos disponibles.\n\n"
            continue
        
        stats_desc = series_data.describe()
        modes = series_data.mode()
        stats_df = stats_desc.to_frame().T

        if not modes.empty:
            stats_df['mode'] = ", ".join(map(str, modes.tolist()))
        else:
            stats_df['mode'] = 'N/A'
        
        stats_df.index = [f"Duración {name}"]
        print(stats_df.to_string())
        stats_dfs.append(stats_df)
        output_text_content += f"Resumen Estadístico para Duración de la {name} (segundos):\n{stats_df.to_string()}\n\n"

    file_path = os.path.join(output_dir, filename)
    try:
        with open(file_path, 'w') as f:
            f.write(output_text_content.strip())
        print(f"Estadísticas de duración de primera/segunda página guardadas en: {file_path}")
    except Exception as e:
        print(f"Error al guardar las estadísticas: {e}")
        
    return tuple(stats_dfs)

def get_first_second_page_durations_by_type(df: pd.DataFrame, output_dir: str, filename: str = "first_second_page_duration_by_type_stats.txt") -> tuple[pd.Series | None, pd.Series | None]:
    """
    Calcula la duración de la visita a la primera y segunda página de cada sesión,
    luego agrupa por 'PageType' y calcula la media de estas duraciones.
    Guarda las estadísticas en un archivo.
    """
    print("\nCalculando duraciones medias de primera y segunda página por tipo (navegación/contenido)...")
    if not all(col in df.columns for col in ['SessionID', 'marca de tiempo', 'PageType']):
        print("Error: Se requieren las columnas 'SessionID', 'marca de tiempo' y 'PageType'.")
        return None, None

    df_sorted = df.sort_values(by=['SessionID', 'marca de tiempo'])
    
    first_page_data = [] # Store tuples of (duration, page_type)
    second_page_data = [] # Store tuples of (duration, page_type)

    for session_id, group in df_sorted.groupby('SessionID'):
        if len(group) >= 2:
            # Primera página
            duration_first_page = group['marca de tiempo'].iloc[1] - group['marca de tiempo'].iloc[0]
            page_type_first = group['PageType'].iloc[0] # Tipo de la página cuya duración se mide
            if duration_first_page >= 0:
                first_page_data.append((duration_first_page, page_type_first))
        
        if len(group) >= 3:
            # Segunda página
            duration_second_page = group['marca de tiempo'].iloc[2] - group['marca de tiempo'].iloc[1]
            page_type_second = group['PageType'].iloc[1] # Tipo de la página cuya duración se mide
            if duration_second_page >= 0:
                second_page_data.append((duration_second_page, page_type_second))

    # Convertir a DataFrames para facilitar el groupby y mean
    df_first_page_durs = pd.DataFrame(first_page_data, columns=['duration', 'PageType'])
    df_second_page_durs = pd.DataFrame(second_page_data, columns=['duration', 'PageType'])

    mean_duration_first_page_by_type = None
    mean_duration_second_page_by_type = None
    output_text_content = "Resultados del Análisis de Duración Media de Primera y Segunda Página por Tipo:\n\n"

    if not df_first_page_durs.empty:
        mean_duration_first_page_by_type = df_first_page_durs.groupby('PageType')['duration'].mean().sort_index()
        print("\nDuración media de la PRIMERA página por tipo:")
        print(mean_duration_first_page_by_type.to_string())
        output_text_content += "Duración media de la PRIMERA página por tipo (segundos):\n"
        output_text_content += mean_duration_first_page_by_type.to_string() + "\n\n"
    else:
        print("\nNo se pudieron calcular duraciones para la primera página para agrupar por tipo.")
        output_text_content += "No hay datos suficientes para la duración media de la PRIMERA página por tipo.\n\n"

    if not df_second_page_durs.empty:
        mean_duration_second_page_by_type = df_second_page_durs.groupby('PageType')['duration'].mean().sort_index()
        print("\nDuración media de la SEGUNDA página por tipo:")
        print(mean_duration_second_page_by_type.to_string())
        output_text_content += "Duración media de la SEGUNDA página por tipo (segundos):\n"
        output_text_content += mean_duration_second_page_by_type.to_string() + "\n\n"
    else:
        print("\nNo se pudieron calcular duraciones para la segunda página para agrupar por tipo.")
        output_text_content += "No hay datos suficientes para la duración media de la SEGUNDA página por tipo.\n\n"
    
    # Guardar los resultados en un archivo
    file_path = os.path.join(output_dir, filename)
    try:
        with open(file_path, 'w') as f:
            f.write(output_text_content)
        print(f"Estadísticas de duración de primera/segunda página por tipo guardadas en: {file_path}")
    except Exception as e:
        print(f"Error al guardar las estadísticas de duración por tipo: {e}")

    return mean_duration_first_page_by_type, mean_duration_second_page_by_type

def _plot_normalized_duration_histogram_by_type(
    durations_df: pd.DataFrame, 
    page_description: str, 
    output_dir: str,
    filename: str,
    threshold_percentile: float | None = 0.99
):
    """
    Helper function to plot a normalized histogram for page durations by PageType.
    Handles outlier capping and saves notes for the report.
    """
    if durations_df.empty or 'duration' not in durations_df.columns or 'PageType' not in durations_df.columns:
        print(f"No hay datos de duración para {page_description} para generar histograma por tipo.")
        return

    data_to_plot = durations_df.copy()
    # Ensure durations are non-negative before any processing
    data_to_plot = data_to_plot[data_to_plot['duration'] >= 0]
    if data_to_plot.empty:
        print(f"No hay datos de duración no negativos para {page_description}.")
        return
        
    original_count = len(data_to_plot)
    description_for_memoria_parts = []
    cap_value_for_title = None

    if threshold_percentile is not None and 0 < threshold_percentile < 1:
        positive_durations = data_to_plot['duration'] # Already filtered for >= 0
        if not positive_durations.empty:
            cap_value = positive_durations.quantile(threshold_percentile)
            cap_value_for_title = cap_value
            
            # Only apply cap if it makes sense (e.g., cap_value is not extremely small and there are values above it)
            meaningful_cap = cap_value >= 1 or (positive_durations > cap_value).any()
            
            if meaningful_cap:
                data_to_plot_filtered = data_to_plot[data_to_plot['duration'] <= cap_value]
                omitted_count = original_count - len(data_to_plot_filtered)
                if omitted_count > 0:
                    description_for_memoria_parts.append(
                        f"Para {page_description}, se omitieron duraciones por encima del percentil "
                        f"{threshold_percentile*100:.0f} ({cap_value:.2f}s). "
                        f"Afectó a {omitted_count} de {original_count} ({omitted_count/original_count*100:.2f}%) vistas."
                    )
                    data_to_plot = data_to_plot_filtered
                else:
                    description_for_memoria_parts.append(f"No se omitieron valores atípicos para {page_description} (umbral {cap_value:.2f}s). Todas las duraciones están por debajo o igual al umbral.")
            else:
                description_for_memoria_parts.append(f"No se aplicó filtrado de valores atípicos significativos para {page_description} (umbral {cap_value:.2f}s demasiado bajo o sin datos por encima para filtrar). Todas las duraciones se mantienen.")
        else:
             description_for_memoria_parts.append(f"No hay duraciones positivas para {page_description} para aplicar capping.")
    else:
        description_for_memoria_parts.append(f"No se aplicó capping de valores atípicos para {page_description}.")

    full_description = " ".join(description_for_memoria_parts)
    print(f"Notas para {filename}: {full_description}")

    if data_to_plot.empty or data_to_plot['PageType'].nunique() == 0:
        print(f"No hay datos suficientes para {page_description} después del filtrado para generar histograma por tipo.")
        # Still save notes if description was generated
        if full_description:
            memoria_notes_path = os.path.join(output_dir, f"{filename.split('.')[0]}_notes.txt")
            with open(memoria_notes_path, "w") as f_notes:
                f_notes.write(full_description)
            print(f"Notas para la memoria ({filename}) guardadas en: {memoria_notes_path}")
        return

    plt.figure(figsize=(14, 8))
    # Let Seaborn handle legend creation with legend=True (default when hue is used)
    sns.histplot(data=data_to_plot, x='duration', hue='PageType', stat='density', 
                 common_norm=False, kde=True, element='step', bins='auto', legend=True)
    
    ax = plt.gca() # Get current axes to modify legend if needed

    title_cap_note = f"(valores > {cap_value_for_title:.2f}s omitidos)" if cap_value_for_title is not None and 'se omitieron duraciones por encima del percentil' in full_description else "(sin capping significativo o no aplicado)"
    plt.title(f'Histograma Normalizado de Duración de {page_description} por Tipo\n{title_cap_note}')
    plt.xlabel(f"Duración de {page_description} (segundos)")
    plt.ylabel("Densidad")
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # Attempt to set legend title if Seaborn created a legend
    legend_obj = ax.get_legend()
    if legend_obj is not None:
        if data_to_plot['PageType'].nunique() > 1:
            legend_obj.set_title('Tipo de Página')
        else:
            # If only one category, Seaborn might not draw a legend, or we can hide it
            legend_obj.set_visible(False)
            print(f"Solo un tipo de página ({data_to_plot['PageType'].unique()[0]}) presente para {page_description}, leyenda de tipo omitida.")
    elif data_to_plot['PageType'].nunique() > 1:
        # This case should ideally not be reached if sns.histplot legend=True works as expected for multiple hues
        print(f"Advertencia: No se encontró leyenda para {page_description} a pesar de múltiples tipos de página.")

    file_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(file_path)
        print(f"Histograma normalizado de {page_description} por tipo guardado en: {file_path}")
    except Exception as e:
        print(f"Error al guardar el histograma de {page_description}: {e}")
    plt.close()

    memoria_notes_path = os.path.join(output_dir, f"{filename.split('.')[0]}_notes.txt")
    try:
        with open(memoria_notes_path, "w") as f_notes:
            f_notes.write(full_description)
        print(f"Notas para la memoria ({filename}) guardadas en: {memoria_notes_path}")
    except Exception as e:
        print(f"Error al guardar notas para {filename}: {e}")


def plot_first_second_page_duration_histograms_by_type(
    df: pd.DataFrame,
    output_dir: str,
    first_page_filename: str = "first_page_duration_norm_hist_by_type.png",
    second_page_filename: str = "second_page_duration_norm_hist_by_type.png",
    threshold_percentile: float | None = 0.99
) -> None:
    """
    Genera histogramas normalizados y solapados de la duración de la primera y segunda página,
    separados por tipo (navegación vs. contenido).
    """
    print("\nGenerando histogramas normalizados de duración de primera/segunda página por tipo...")
    if not all(col in df.columns for col in ['SessionID', 'marca de tiempo', 'PageType']):
        print("Error: Se requieren las columnas 'SessionID', 'marca de tiempo' y 'PageType'.")
        return

    df_sorted = df.sort_values(by=['SessionID', 'marca de tiempo'])
    
    first_page_data_for_hist = [] 
    second_page_data_for_hist = []

    for session_id, group in df_sorted.groupby('SessionID'):
        # Asegurar que el grupo tiene las columnas necesarias
        if not all(col in group.columns for col in ['marca de tiempo', 'PageType']):
            continue # Saltar grupo si faltan datos
            
        group_timestamps = group['marca de tiempo'].tolist()
        group_pagetypes = group['PageType'].tolist()

        if len(group_timestamps) >= 2:
            duration_first = group_timestamps[1] - group_timestamps[0]
            page_type_first = group_pagetypes[0]
            if duration_first >= 0: 
                first_page_data_for_hist.append({'duration': duration_first, 'PageType': page_type_first})
        
        if len(group_timestamps) >= 3:
            duration_second = group_timestamps[2] - group_timestamps[1]
            page_type_second = group_pagetypes[1]
            if duration_second >= 0: 
                second_page_data_for_hist.append({'duration': duration_second, 'PageType': page_type_second})

    # Plot for First Page Durations
    if first_page_data_for_hist:
        df_first_page_durs_hist = pd.DataFrame(first_page_data_for_hist)
        _plot_normalized_duration_histogram_by_type(
            df_first_page_durs_hist,
            "Primera Página",
            output_dir,
            first_page_filename,
            threshold_percentile
        )
    else:
        print("No hay datos de duración de primera página para generar histograma por tipo.")

    # Plot for Second Page Durations
    if second_page_data_for_hist:
        df_second_page_durs_hist = pd.DataFrame(second_page_data_for_hist)
        _plot_normalized_duration_histogram_by_type(
            df_second_page_durs_hist,
            "Segunda Página",
            output_dir,
            second_page_filename,
            threshold_percentile
        )
    else:
        print("No hay datos de duración de segunda página para generar histograma por tipo.")


# --- Funciones para la Tarea 2.8 --- 

def _extract_display_domain(host_remoto: str) -> str:
    """
    Extrae un "dominio de visualización" del campo 'Host remoto'.
    Si es una IP, la devuelve. Si es un nombre de host, lo devuelve.
    Intenta simplificar un poco los nombres de host comunes de la NASA o gubernamentales si es posible,
    pero principalmente se enfoca en obtener una etiqueta agrupable.
    """
    if pd.isna(host_remoto):
        return "desconocido"
    
    # Comprobar si es una IP (simplificado)
    # Una comprobación más robusta usaría expresiones regulares o la librería ipaddress
    is_ip = all(part.isdigit() for part in host_remoto.split('.')) and len(host_remoto.split('.')) == 4
    if is_ip:
        return host_remoto
    else:
        # Es un nombre de host, podríamos intentar normalizarlo un poco
        # Ejemplo simple: si termina en .arc.nasa.gov, quizás solo queremos arc.nasa.gov
        # O si es proxy.aol.com, quizás solo aol.com. Esto puede volverse complejo.
        # Por ahora, devolvemos el host tal cual para una primera aproximación.
        return host_remoto.lower() # Convertir a minúsculas para consistencia

def get_top_domains_by_hits_and_sessions(df: pd.DataFrame, output_dir: str, top_n: int = 20) -> pd.DataFrame | None:
    """
    Calcula los N dominios más repetidos por número de hits y sesiones únicas.
    Guarda la tabla resultante en un archivo CSV.
    """
    print(f"\n--- Iniciando Tarea 2.8.1: Top {top_n} Dominios por Hits y Sesiones ---")
    if not all(col in df.columns for col in ['Host remoto', 'SessionID']):
        print("Error: Se requieren las columnas 'Host remoto' y 'SessionID'.")
        return None

    df_analysis = df.copy()
    df_analysis['DisplayDomain'] = df_analysis['Host remoto'].apply(_extract_display_domain)

    domain_stats = df_analysis.groupby('DisplayDomain').agg(
        total_hits = pd.NamedAgg(column='SessionID', aggfunc='size'), # Contar filas (hits)
        total_unique_sessions = pd.NamedAgg(column='SessionID', aggfunc='nunique')
    ).reset_index()

    top_domains_df = domain_stats.sort_values(
        by=['total_hits', 'total_unique_sessions'], 
        ascending=[False, False]
    ).head(top_n)

    print(f"\nTop {top_n} dominios más repetidos:")
    print(top_domains_df.to_string())

    filename = f"top_{top_n}_domains_by_hits_sessions.csv"
    file_path = os.path.join(output_dir, filename)
    try:
        top_domains_df.to_csv(file_path, index=False)
        print(f"Tabla de los top {top_n} dominios guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de dominios: {e}")
    
    return top_domains_df 