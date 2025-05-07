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
    if '.' in str(page_path) and not str(page_path).endswith('/'):
        ext = str(page_path).split('.')[-1].lower()
        ext_cleaned = ext.split('?')[0].split('#')[0]
        if '/' in ext_cleaned:
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
        df['PageType'] = "desconocido"
        return df
    df['extension'] = df['Página'].astype(str).apply(_extract_extension)
    df['PageType'] = np.where(df['extension'] == '', 'navegación', 'contenido')
    print(f"Tipos de página clasificados. Distribución:\n{df['PageType'].value_counts(normalize=True)}")
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
            description_for_memoria = "No se aplicó filtrado de valores atípicos significativos para este histograma (el umbral era demasiado bajo o no había valores extremos)."
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
                description_for_memoria = "No se omitieron valores atípicos para este histograma (todos los valores dentro del umbral)."
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
    memoria_notes_path = os.path.join(output_dir, filename.replace('.png', '_notes.txt'))
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
    stats_df.columns = [
        'Número de Vistas', 'Media (s)', 'Desv. Estándar (s)', 'Mínimo (s)', 
        'Percentil 25 (s)', 'Mediana (s)', 'Percentil 75 (s)', 'Máximo (s)'
    ]
    if not modes.empty:
        stats_df['Moda (s)'] = ", ".join(map(str, modes.tolist()))
    else:
        stats_df['Moda (s)'] = 'N/A'
    stats_df = stats_df[[
        'Número de Vistas', 'Media (s)', 'Desv. Estándar (s)', 'Mínimo (s)', 
        'Percentil 25 (s)', 'Mediana (s)', 'Percentil 75 (s)', 'Máximo (s)', 'Moda (s)'
    ]]
    table_representation = stats_df.to_markdown(index=False)
    print(table_representation)
    file_path = os.path.join(output_dir, filename)
    try:
        with open(file_path, 'w') as f:
            f.write("Métrica                   | Valor\n")
            f.write("---------------------------|------------------\n")
            f.write(f"Número de Vistas          | {stats_df['Número de Vistas'].iloc[0]}\n")
            f.write(f"Media (s)                 | {stats_df['Media (s)'].iloc[0]:.2f}\n")
            f.write(f"Desv. Estándar (s)      | {stats_df['Desv. Estándar (s)'].iloc[0]:.2f}\n")
            f.write(f"Mínimo (s)                | {stats_df['Mínimo (s)'].iloc[0]:.2f}\n")
            f.write(f"Percentil 25 (s)          | {stats_df['Percentil 25 (s)'].iloc[0]:.2f}\n")
            f.write(f"Mediana (s)               | {stats_df['Mediana (s)'].iloc[0]:.2f}\n")
            f.write(f"Percentil 75 (s)          | {stats_df['Percentil 75 (s)'].iloc[0]:.2f}\n")
            f.write(f"Máximo (s)                | {stats_df['Máximo (s)'].iloc[0]:.2f}\n")
            f.write(f"Moda (s)                  | {stats_df['Moda (s)'].iloc[0]}\n")
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
    s_second_page_durations = pd.Series(second_page_durs, dtype='float64')
    print(f"Calculadas {len(s_first_page_durations)} duraciones para primeras páginas.")
    print(f"Calculadas {len(s_second_page_durations)} duraciones para segundas páginas.")
    return s_first_page_durations, s_second_page_durations

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
            description_for_memoria = "No se aplicó filtrado de valores atípicos significativos (umbral bajo o sin extremos)."
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
                description_for_memoria = "No se omitieron valores atípicos para este histograma (todos dentro del umbral)."
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
    memoria_notes_path = os.path.join(output_dir, filename.replace('.png', '_notes.txt'))
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
    Calcula y guarda estadísticas para las duraciones de la primera y segunda página.
    """
    print("\nCalculando estadísticas para las duraciones de la primera y segunda página...")
    output_text_content = ""
    results_dfs = []
    series_to_process = [
        ("Primera Página", first_page_durations),
        ("Segunda Página", second_page_durations)
    ]
    for name, series_data in series_to_process:
        if series_data.empty:
            print(f"No hay datos para la {name.lower()}.")
            output_text_content += f"\n{name}: No hay datos suficientes para calcular estadísticas.\n"
            results_dfs.append(None)
            continue
        stats_desc = series_data.describe()
        modes = series_data.mode()
        stats_df = stats_desc.to_frame().T
        stats_df.columns = [
            'Número de Páginas', 'Media (s)', 'Desv. Estándar (s)', 'Mínimo (s)', 
            'Percentil 25 (s)', 'Mediana (s)', 'Percentil 75 (s)', 'Máximo (s)'
        ]
        if not modes.empty:
            stats_df['Moda (s)'] = ", ".join(map(str, modes.tolist()))
        else:
            stats_df['Moda (s)'] = 'N/A'
        stats_df = stats_df[[
            'Número de Páginas', 'Media (s)', 'Desv. Estándar (s)', 'Mínimo (s)', 
            'Percentil 25 (s)', 'Mediana (s)', 'Percentil 75 (s)', 'Máximo (s)', 'Moda (s)'
        ]]
        results_dfs.append(stats_df)
        output_text_content += f"\n{name}:\n"
        output_text_content += stats_df.to_markdown(index=False) + "\n"
    print(output_text_content)
    file_path = os.path.join(output_dir, filename)
    try:
        with open(file_path, 'w') as f:
            f.write("Estadísticas de Duración de Primera y Segunda Página:\n")
            f.write(output_text_content)
        print(f"Estadísticas de duración de primera/segunda página guardadas en: {file_path}")
    except Exception as e:
        print(f"Error al guardar las estadísticas: {e}")
    return tuple(results_dfs)

def get_first_second_page_durations_by_type(df: pd.DataFrame, output_dir: str, filename: str = "first_second_page_duration_by_type_stats.txt") -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """
    Calcula la duración media de la primera y segunda página, separada por tipo de página (navegación/contenido).
    Guarda las estadísticas en un archivo.
    Devuelve DataFrames con las estadísticas (uno para la primera página, otro para la segunda).
    """
    print("\nCalculando duración media de primera/segunda página por tipo (navegación/contenido)...")
    if 'PageType' not in df.columns:
        print("Error: La columna 'PageType' no existe. Ejecute classify_page_type primero.")
        return None, None
    if df['PageType'].isnull().all():
        print("Error: La columna 'PageType' está vacía o solo contiene NaNs.")
        return None, None
    df_sorted = df.sort_values(by=['SessionID', 'marca de tiempo'])
    df_sorted['next_timestamp_in_session'] = df_sorted.groupby('SessionID')['marca de tiempo'].shift(-1)
    df_sorted['first_page_duration'] = df_sorted['next_timestamp_in_session'] - df_sorted['marca de tiempo']
    first_pages_df = df_sorted.groupby('SessionID').first().reset_index()
    first_pages_df = first_pages_df[first_pages_df['first_page_duration'] >= 0]
    df_sorted['next_next_timestamp_in_session'] = df_sorted.groupby('SessionID')['marca de tiempo'].shift(-2)
    df_sorted['second_page_duration'] = df_sorted['next_next_timestamp_in_session'] - df_sorted['next_timestamp_in_session']
    second_pages_df = df_sorted.groupby('SessionID').nth(1).reset_index()
    second_pages_df = second_pages_df[second_pages_df['second_page_duration'] >= 0]
    stats_output = ""
    all_stats_dfs = {}
    for page_num_str, page_df_data in [("Primera Página", first_pages_df), ("Segunda Página", second_pages_df)]:
        if page_df_data.empty:
            stats_output += f"\n{page_num_str}: No hay datos suficientes.\n"
            all_stats_dfs[page_num_str] = None
            continue
        duration_col = 'first_page_duration' if page_num_str == "Primera Página" else 'second_page_duration'
        if duration_col not in page_df_data.columns:
             stats_output += f"\n{page_num_str}: Columna de duración '{duration_col}' no encontrada.\n"
             all_stats_dfs[page_num_str] = None
             continue
        avg_duration_by_type = page_df_data.groupby('PageType')[duration_col].mean().reset_index()
        avg_duration_by_type.columns = ['PageType', 'MeanDurationSeconds']
        stats_output += f"\n{page_num_str} Visitada:\n"
        stats_output += avg_duration_by_type.to_markdown(index=False) + "\n"
        all_stats_dfs[page_num_str] = avg_duration_by_type
    print(stats_output)
    file_path = os.path.join(output_dir, filename)
    try:
        with open(file_path, 'w') as f:
            f.write("Duración Media de Primera y Segunda Página por Tipo (Navegación vs. Contenido):\n")
            f.write(stats_output)
        print(f"Estadísticas de duración por tipo guardadas en: {file_path}")
    except Exception as e:
        print(f"Error al guardar las estadísticas por tipo: {e}")
    return all_stats_dfs.get("Primera Página"), all_stats_dfs.get("Segunda Página")

def _plot_normalized_duration_histogram_by_type(
    durations_df: pd.DataFrame, 
    page_description: str, 
    output_dir: str,
    filename: str,
    threshold_percentile: float | None = 0.99
):
    """
    Helper para generar histogramas normalizados de duración por tipo de página.
    durations_df debe tener columnas 'duration' y 'PageType'.
    """
    if durations_df.empty or 'duration' not in durations_df.columns or 'PageType' not in durations_df.columns:
        print(f"Datos insuficientes o incorrectos para el histograma de {page_description.lower()} por tipo.")
        return
    data_to_plot = durations_df.copy()
    original_count = len(data_to_plot)
    notes_list = []
    if threshold_percentile is not None and 0 < threshold_percentile < 1:
        cap_value = data_to_plot['duration'].quantile(threshold_percentile)
        if cap_value < 1 and (data_to_plot['duration'] > cap_value).any():
             notes_list.append(f"Para {page_description}, no se aplicó filtrado de valores atípicos significativos (umbral {cap_value:.2f}s bajo o sin extremos).")
        else:
            data_to_plot_filtered = data_to_plot[data_to_plot['duration'] <= cap_value]
            omitted_count = original_count - len(data_to_plot_filtered)
            if omitted_count > 0:
                notes_list.append(
                    f"Para {page_description}, se omitieron duraciones por encima del percentil "
                    f"{threshold_percentile*100:.0f} ({cap_value:.2f}s). Afectó a {omitted_count} de {original_count} ({omitted_count/original_count*100:.2f}%) vistas."
                )
                data_to_plot = data_to_plot_filtered
            else:
                notes_list.append(f"Para {page_description}, no se omitieron valores atípicos (todos dentro del umbral {cap_value:.2f}s).")
    else:
        notes_list.append(f"Para {page_description}, no se aplicó filtrado de valores atípicos.")
    print("\n".join(notes_list))
    if data_to_plot.empty:
        print(f"No quedan datos para graficar para {page_description.lower()} después del filtrado.")
        return
    plt.figure(figsize=(12, 7))
    page_types_present = data_to_plot['PageType'].unique()
    if 'navegación' in page_types_present:
        sns.histplot(
            data_to_plot[data_to_plot['PageType'] == 'navegación'], 
            x='duration', 
            kde=True, 
            stat="density", 
            label='Navegación', 
            color='skyblue',
            bins='auto'
        )
    if 'contenido' in page_types_present:
        sns.histplot(
            data_to_plot[data_to_plot['PageType'] == 'contenido'], 
            x='duration', 
            kde=True, 
            stat="density", 
            label='Contenido', 
            color='orange',
            bins='auto'
        )
    title_note = notes_list[0].split(". Afectó")[0] if notes_list else ""
    plt.title(f'Histograma Normalizado de Duración de {page_description}\nPor Tipo de Página (Navegación vs. Contenido)\n{title_note}')
    plt.xlabel("Duración de la Página (segundos)")
    plt.ylabel("Densidad")
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    file_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(file_path)
        print(f"Histograma normalizado de duración ({page_description.lower()}) por tipo guardado en: {file_path}")
    except Exception as e:
        print(f"Error al guardar el histograma: {e}")
    plt.close()
    memoria_notes_path = os.path.join(output_dir, filename.replace('.png', '_notes.txt'))
    with open(memoria_notes_path, "w") as f:
        f.write("\n".join(notes_list))
    print(f"Notas para la memoria (histograma {page_description.lower()} por tipo) guardadas en: {memoria_notes_path}")

def plot_first_second_page_duration_histograms_by_type(
    df: pd.DataFrame,
    output_dir: str,
    first_page_filename: str = "first_page_duration_norm_hist_by_type.png",
    second_page_filename: str = "second_page_duration_norm_hist_by_type.png",
    threshold_percentile: float | None = 0.99
) -> None:
    """
    Genera histogramas normalizados para la duración de la primera y segunda página, 
    comparando tipos 'navegación' vs. 'contenido'.
    """
    print("\nGenerando histogramas normalizados de duración de primera/segunda página por tipo...")
    if 'PageType' not in df.columns or df['PageType'].isnull().all():
        print("Error: Columna 'PageType' no encontrada o vacía. Ejecute classify_page_type primero.")
        return
    df_sorted = df.sort_values(by=['SessionID', 'marca de tiempo'])
    df_sorted['next_timestamp_in_session'] = df_sorted.groupby('SessionID')['marca de tiempo'].shift(-1)
    df_sorted['first_page_duration'] = df_sorted['next_timestamp_in_session'] - df_sorted['marca de tiempo']
    first_pages_data = df_sorted.groupby('SessionID').first().reset_index()
    first_pages_data = first_pages_data[first_pages_data['first_page_duration'] >= 0][['first_page_duration', 'PageType']].rename(columns={'first_page_duration': 'duration'})
    _plot_normalized_duration_histogram_by_type(first_pages_data, "Primera Página", output_dir, first_page_filename, threshold_percentile)
    df_sorted['next_next_timestamp_in_session'] = df_sorted.groupby('SessionID')['marca de tiempo'].shift(-2)
    df_sorted['second_page_duration'] = df_sorted['next_next_timestamp_in_session'] - df_sorted['next_timestamp_in_session']
    second_pages_data = df_sorted.groupby('SessionID').nth(1).reset_index()
    second_pages_data = second_pages_data[second_pages_data['second_page_duration'] >= 0][['second_page_duration', 'PageType']].rename(columns={'second_page_duration': 'duration'})
    _plot_normalized_duration_histogram_by_type(second_pages_data, "Segunda Página", output_dir, second_page_filename, threshold_percentile)

def _extract_display_domain(host_remoto: str) -> str:
    """
    Extrae un nombre de host/dominio 'limpio' o devuelve la IP si no es un nombre de host.
    Intenta manejar casos comunes de nombres de host vs IPs.
    """
    if pd.isna(host_remoto):
        return "desconocido"
    host_str = str(host_remoto)
    parts = host_str.split('.')
    if len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
        return host_str
    if '.' not in host_str:
        return host_str
    return host_str

def get_top_domains_by_hits_and_sessions(df: pd.DataFrame, output_dir: str, top_n: int = 20) -> pd.DataFrame | None:
    """
    Identifica los N dominios/hosts más repetidos, por número de hits y sesiones.
    Utiliza el campo 'Host remoto' directamente después de una limpieza básica con _extract_display_domain.
    """
    print("\n--- Analizando Top Dominios/Hosts (Host Remoto) ---")
    if 'Host remoto' not in df.columns or 'SessionID' not in df.columns:
        print("Error: Se requieren las columnas 'Host remoto' y 'SessionID'.")
        return None
    df_copy = df.copy()
    df_copy['DisplayDomain'] = df_copy['Host remoto'].apply(_extract_display_domain)
    domain_hits = df_copy.groupby('DisplayDomain').size().rename('HitCount')
    domain_sessions = df_copy.groupby('DisplayDomain')['SessionID'].nunique().rename('SessionCount')
    domain_summary_df = pd.concat([domain_hits, domain_sessions], axis=1).fillna(0)
    domain_summary_df['SessionCount'] = domain_summary_df['SessionCount'].astype(int)
    domain_summary_df = domain_summary_df.sort_values(by=['HitCount', 'SessionCount'], ascending=[False, False])
    df_top_domains = domain_summary_df.head(top_n).reset_index()
    print(f"\nTop {top_n} Dominios/Hosts por Hits y Sesiones:")
    print(df_top_domains.to_string())
    output_tables_dir = os.path.join(output_dir, '..', 'tables')
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)
    file_path = os.path.join(output_tables_dir, f'top_{top_n}_domains_by_hits_sessions.csv')
    try:
        df_top_domains.to_csv(file_path, index=False)
        print(f"Tabla de los top {top_n} dominios/hosts guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de top dominios/hosts: {e}")
    return df_top_domains

def _extract_tld(host: str) -> str:
    """
    Extrae el Top-Level Domain (TLD) de un nombre de host limpio.
    Devuelve una cadena vacía si es una IP o no se puede determinar un TLD simple.
    """
    if pd.isna(host):
        return ""
    parts = host.split('.')
    if all(part.isdigit() for part in parts) and len(parts) == 4:
        return ""
    if '.' in host:
        tld = host.split('.')[-1].lower()
        if not tld.isalpha() or len(tld) < 2:
            if tld not in ['uk', 'us', 'ca', 'de', 'fr', 'au', 'jp', 'cn', 'in', 'br', 'ru']:
                 if len(tld) < 3 and not tld.isalpha():
                     return ""
                 elif not tld.isalpha():
                     return ""
        return tld
    return ""

def get_top_domain_types(df: pd.DataFrame, output_dir: str, top_n: int = 7) -> pd.DataFrame | None:
    """
    Identifica los 7 tipos de dominio (TLD) más repetidos, por número de hits y sesiones.
    """
    print("\n--- Analizando Top Tipos de Dominio (TLD) ---")
    if 'Host remoto' not in df.columns or 'SessionID' not in df.columns:
        print("Error: Se requieren las columnas 'Host remoto' y 'SessionID'.")
        return None
    df_copy = df.copy()
    df_copy['CleanedHost'] = df_copy['Host remoto'].apply(_extract_display_domain)
    df_copy['TLD'] = df_copy['CleanedHost'].apply(_extract_tld)
    df_tlds = df_copy[df_copy['TLD'] != '']
    if df_tlds.empty:
        print("No se pudieron extraer TLDs válidos para el análisis.")
        return None
    tld_hits = df_tlds.groupby('TLD').size().rename('HitCount')
    tld_sessions = df_tlds.groupby('TLD')['SessionID'].nunique().rename('SessionCount')
    tld_summary_df = pd.concat([tld_hits, tld_sessions], axis=1).fillna(0)
    tld_summary_df['SessionCount'] = tld_summary_df['SessionCount'].astype(int)
    tld_summary_df = tld_summary_df.sort_values(by=['HitCount', 'SessionCount'], ascending=[False, False])
    df_top_tlds = tld_summary_df.head(top_n).reset_index()
    print(f"\nTop {top_n} Tipos de Dominio (TLD) por Hits y Sesiones:")
    print(df_top_tlds.to_string())
    output_tables_dir = os.path.join(output_dir, '..', 'tables')
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)
    file_path = os.path.join(output_tables_dir, f'top_{top_n}_domain_types.csv')
    try:
        df_top_tlds.to_csv(file_path, index=False)
        print(f"Tabla de los top {top_n} tipos de dominio guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de tipos de dominio: {e}")
    return df_top_tlds

def get_top_pages_by_hits_and_sessions(df: pd.DataFrame, output_dir: str, top_n: int = 10) -> pd.DataFrame | None:
    """
    Identifica las N páginas más visitadas, por número de hits totales y por número de sesiones distintas.
    """
    print("\n--- Analizando Top Páginas Más Visitadas ---")
    if 'Página' not in df.columns or 'SessionID' not in df.columns:
        print("Error: Se requieren las columnas 'Página' y 'SessionID'.")
        return None
    df_copy = df.copy()
    page_hits = df_copy.groupby('Página').size().rename('HitCount')
    page_sessions = df_copy.groupby('Página')['SessionID'].nunique().rename('SessionCount')
    page_summary_df = pd.concat([page_hits, page_sessions], axis=1).fillna(0)
    page_summary_df['SessionCount'] = page_summary_df['SessionCount'].astype(int)
    page_summary_df = page_summary_df.sort_values(by=['HitCount', 'SessionCount'], ascending=[False, False])
    df_top_pages = page_summary_df.head(top_n).reset_index()
    print(f"\nTop {top_n} Páginas por Hits y Sesiones:")
    print(df_top_pages.to_string())
    output_tables_dir = os.path.join(output_dir, '..', 'tables') 
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)
    file_path = os.path.join(output_tables_dir, f'top_{top_n}_pages_by_hits_sessions.csv')
    try:
        df_top_pages.to_csv(file_path, index=False)
        print(f"Tabla de las top {top_n} páginas guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de top páginas: {e}")
    return df_top_pages

# --- Funciones para Tarea 2.8.7 ---
def _extract_directory(page_path: str) -> str:
    """Helper para extraer el directorio de una ruta de página."""
    if pd.isna(page_path):
        return "/"
    path_str = str(page_path)
    if path_str == "/":
        return "/"
    last_slash_pos = path_str.rfind('/')
    if last_slash_pos == -1:
        return "/" # No slash, assume root directory
    # If path ends with a slash, it's a directory path itself
    if last_slash_pos == len(path_str) - 1:
        return path_str
    # Path before the last slash is the directory
    directory = path_str[:last_slash_pos]
    return directory if directory else "/" # Handle cases like "/file.html" -> "/"

def get_top_directories_by_hits_and_sessions(df: pd.DataFrame, output_dir: str, top_n: int = 10) -> pd.DataFrame | None:
    """
    Identifica los N directorios más visitados, por número de hits y sesiones.
    """
    print("\n--- Analizando Top Directorios Más Visitados ---")
    if 'Página' not in df.columns or 'SessionID' not in df.columns:
        print("Error: Se requieren las columnas 'Página' y 'SessionID'.")
        return None
    df_copy = df.copy()
    df_copy['Directory'] = df_copy['Página'].apply(_extract_directory)
    dir_hits = df_copy.groupby('Directory').size().rename('HitCount')
    dir_sessions = df_copy.groupby('Directory')['SessionID'].nunique().rename('SessionCount')
    dir_summary_df = pd.concat([dir_hits, dir_sessions], axis=1).fillna(0)
    dir_summary_df['SessionCount'] = dir_summary_df['SessionCount'].astype(int)
    dir_summary_df = dir_summary_df.sort_values(by=['HitCount', 'SessionCount'], ascending=[False, False])
    df_top_dirs = dir_summary_df.head(top_n).reset_index()
    print(f"\nTop {top_n} Directorios por Hits y Sesiones:")
    print(df_top_dirs.to_string())
    output_tables_dir = os.path.join(output_dir, '..', 'tables')
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)
    file_path = os.path.join(output_tables_dir, f'top_{top_n}_directories_by_hits_sessions.csv')
    try:
        df_top_dirs.to_csv(file_path, index=False)
        print(f"Tabla de los top {top_n} directorios guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de top directorios: {e}")
    return df_top_dirs

# Nueva función para Tarea 2.8.8
def get_top_file_types_by_hits(df: pd.DataFrame, output_dir: str, top_n: int = 10) -> pd.DataFrame | None:
    """
    Identifica los N tipos de fichero (extensiones) más repetidos por número de accesos/hits.
    Excluye páginas sin extensión.
    """
    print("\n--- Analizando Top Tipos de Fichero (Extensiones) por Hits ---")
    if 'Página' not in df.columns:
        print("Error: Se requiere la columna 'Página'.")
        return None

    df_copy = df.copy()
    
    # Asegurar que tenemos la columna 'extension'
    if 'extension' not in df_copy.columns:
        print("Columna 'extension' no encontrada, extrayéndola...")
        df_copy['extension'] = df_copy['Página'].astype(str).apply(_extract_extension)

    # Filtrar extensiones vacías (páginas de navegación o sin extensión real)
    df_with_extensions = df_copy[df_copy['extension'] != '']

    if df_with_extensions.empty:
        print("No se encontraron páginas con extensiones para analizar.")
        return None

    # Contar hits por extensión
    file_type_hits = df_with_extensions.groupby('extension').size().rename('HitCount').sort_values(ascending=False)
    
    df_top_file_types = file_type_hits.head(top_n).reset_index()
    df_top_file_types.columns = ['Extension', 'HitCount']

    print(f"\nTop {top_n} Tipos de Fichero (Extensiones) por Hits:")
    print(df_top_file_types.to_string())

    # Guardar en CSV
    output_tables_dir = os.path.join(output_dir, '..', 'tables')
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)
    
    file_path = os.path.join(output_tables_dir, f'top_{top_n}_file_types_by_hits.csv')
    try:
        df_top_file_types.to_csv(file_path, index=False)
        print(f"Tabla de los top {top_n} tipos de fichero guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de top tipos de fichero: {e}")

    return df_top_file_types
