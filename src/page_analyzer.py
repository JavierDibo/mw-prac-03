import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de Seaborn para los gráficos (si es específico o global)
# sns.set_theme(style="whitegrid") # Puede ser global en el main script

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