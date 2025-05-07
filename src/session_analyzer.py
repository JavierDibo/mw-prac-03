import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.linear_model import LinearRegression

# Configuración de Seaborn para los gráficos (si es específico de estas funciones o global)
# sns.set_theme(style="whitegrid") # Puede ser global en el main script

def calculate_session_durations(df: pd.DataFrame) -> pd.Series:
    """
    Filtra sesiones que contienen más de una visita y calcula la duración de estas sesiones.
    La duración es la diferencia entre el timestamp del último y primer hit de la sesión.
    Devuelve una Serie de Pandas con las duraciones de las sesiones (en segundos).
    """
    print("\nCalculando duraciones de sesión para sesiones con más de una visita...")
    
    session_hit_counts = df.groupby('SessionID')['marca de tiempo'].count()
    multi_hit_sessions = session_hit_counts[session_hit_counts > 1].index
    
    if len(multi_hit_sessions) == 0:
        print("No se encontraron sesiones con más de una visita.")
        return pd.Series(dtype='float64')
        
    print(f"Se encontraron {len(multi_hit_sessions)} sesiones con más de una visita (de un total de {df['SessionID'].nunique()} sesiones).")
    
    df_multi_hit = df[df['SessionID'].isin(multi_hit_sessions)]
    session_min_max_times = df_multi_hit.groupby('SessionID')['marca de tiempo'].agg(['min', 'max'])
    session_durations = session_min_max_times['max'] - session_min_max_times['min']
    
    print(f"Duraciones calculadas para {len(session_durations)} sesiones.")
    print("Primeras 5 duraciones de sesión (en segundos):")
    print(session_durations.head())
    
    return session_durations

def plot_session_duration_histogram(
    session_durations_seconds: pd.Series, 
    output_dir: str,
    filename: str = "session_duration_histogram.png",
    threshold_percentile: float | None = 0.99
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
            durations_to_plot = durations_to_plot_filtered
        else:
            description_for_memoria = "No se omitieron valores atípicos para este histograma."
    else:
        description_for_memoria = "No se aplicó filtrado de valores atípicos para este histograma."
    print(description_for_memoria)

    plt.figure(figsize=(12, 7))
    sns.histplot(durations_to_plot, kde=True, bins='auto') 
    
    max_duration_to_plot = durations_to_plot.max()
    if max_duration_to_plot > 300:
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
    stats_desc = session_durations_seconds.describe()
    modes = session_durations_seconds.mode()
    stats_df = stats_desc.to_frame().T

    if not modes.empty:
        stats_df['mode'] = ", ".join(map(str, modes.tolist()))
    else:
        stats_df['mode'] = 'N/A'
        
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

def calculate_per_session_avg_page_time(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the average page view time for each session that has more than one hit.
    """
    print("\nCalculando el tiempo medio de visualización de página por sesión...")
    df_sorted = df.sort_values(by=['SessionID', 'marca de tiempo'])
    df_sorted['page_view_duration'] = df_sorted.groupby('SessionID')['marca de tiempo'].diff().shift(-1)
    valid_page_durations = df_sorted.dropna(subset=['page_view_duration'])
    valid_page_durations = valid_page_durations[valid_page_durations['page_view_duration'] >= 0]

    if valid_page_durations.empty:
        print("No se encontraron vistas de página con duración calculable para promediar por sesión.")
        return pd.DataFrame(columns=['SessionID', 'avg_page_view_time_seconds', 'num_page_views_in_session'])

    session_avg_page_time = valid_page_durations.groupby('SessionID').agg(
        avg_page_view_time_seconds=('page_view_duration', 'mean'),
        num_page_views_in_session=('page_view_duration', 'count')
    ).reset_index()
    
    session_avg_page_time_sorted = session_avg_page_time.sort_values(by='avg_page_view_time_seconds')
    
    print(f"Se calculó el tiempo medio por página para {len(session_avg_page_time_sorted)} sesiones.")
    return session_avg_page_time_sorted

def plot_hits_per_session_histogram(
    session_hit_counts: pd.Series,
    output_dir: str,
    filename: str = "hits_per_session_histogram.png",
    threshold_percentile: float | None = 0.99
) -> None:
    """
    Genera y guarda un histograma del número de visitas de página (hits) por sesión.
    Permite el filtrado de valores atípicos basado en un percentil.
    """
    if session_hit_counts.empty:
        print("No hay datos de conteo de hits por sesión para generar el histograma.")
        return

    counts_to_plot = session_hit_counts.copy()
    original_count = len(counts_to_plot)
    description_for_memoria = ""

    if threshold_percentile is not None and 0 < threshold_percentile < 1:
        cap_value = counts_to_plot.quantile(threshold_percentile)
        cap_value = int(round(cap_value))
        if cap_value < counts_to_plot.min() and (counts_to_plot > cap_value).any():
             description_for_memoria = f"No se aplicó filtrado de valores atípicos significativos (umbral de percentil {threshold_percentile*100:.0f} resultó en cap={cap_value}, que es menor que el mínimo)."
        else:
            counts_to_plot_filtered = counts_to_plot[counts_to_plot <= cap_value]
            omitted_count = original_count - len(counts_to_plot_filtered)
            if omitted_count > 0:
                description_for_memoria = (
                    f"Para mejorar la visualización, se omitieron sesiones con más de "
                    f"{cap_value} hits (correspondiente al percentil {threshold_percentile*100:.0f}). "
                    f"Esto afectó a {omitted_count} sesiones ({omitted_count/original_count*100:.2f}% del total de sesiones)."
                )
                counts_to_plot = counts_to_plot_filtered
            else:
                description_for_memoria = "No se omitieron valores atípicos para este histograma."
    else:
        description_for_memoria = "No se aplicó filtrado de valores atípicos para este histograma."
    print(description_for_memoria)

    plt.figure(figsize=(12, 7))
    max_hits = int(counts_to_plot.max())
    min_hits = int(counts_to_plot.min())
    if max_hits - min_hits < 50 and max_hits > 0:
        bins = range(min_hits, max_hits + 2)
    else:
        bins = 'auto'

    sns.histplot(counts_to_plot, kde=False, bins=bins, discrete=True)
    
    title_note = description_for_memoria.split(". ")[0]
    plt.title(f'Histograma del Número de Visitas de Página por Sesión\n{title_note}')
    plt.xlabel("Número de Visitas de Página por Sesión")
    plt.ylabel("Número de Sesiones")
    plt.grid(True, axis='y', linestyle='--', linewidth=0.5)

    file_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(file_path)
        print(f"Histograma de visitas por sesión guardado en: {file_path}")
    except Exception as e:
        print(f"Error al guardar el histograma: {e}")
    plt.close()

    memoria_notes_path = os.path.join(output_dir, "hits_per_session_histogram_notes.txt")
    with open(memoria_notes_path, "w") as f:
        f.write(description_for_memoria)
    print(f"Notas para la memoria (histograma visitas por sesión) guardadas en: {memoria_notes_path}")

def get_hits_per_session_stats(
    session_hit_counts: pd.Series,
    output_dir: str,
    filename: str = "hits_per_session_stats.txt"
) -> pd.DataFrame | None:
    """
    Calcula y guarda un resumen estadístico del número de visitas de página (hits) por sesión.
    """
    if session_hit_counts.empty:
        print("No hay datos de conteo de hits por sesión para calcular estadísticas.")
        return None

    print("\nCalculando estadísticas descriptivas para el número de visitas por sesión...")
    stats_desc = session_hit_counts.describe()
    modes = session_hit_counts.mode()
    stats_df = stats_desc.to_frame().T
    stats_df.columns = ['count_sessions', 'mean_hits', 'std_hits', 'min_hits', '25%_hits', '50%_hits(median)', '75%_hits', 'max_hits']

    if not modes.empty:
        stats_df['mode_hits'] = ", ".join(map(str, modes.tolist()))
    else:
        stats_df['mode_hits'] = 'N/A'
    
    print("\nResumen Estadístico del Número de Visitas de Página por Sesión:")
    print(stats_df.to_string())

    file_path = os.path.join(output_dir, filename)
    try:
        with open(file_path, 'w') as f:
            f.write("Resumen Estadístico del Número de Visitas de Página por Sesión:\n")
            f.write(stats_df.to_string())
        print(f"Estadísticas de visitas por sesión guardadas en: {file_path}")
    except Exception as e:
        print(f"Error al guardar las estadísticas de visitas por sesión: {e}")
        
    return stats_df

def plot_hits_vs_duration_scatter(
    session_hit_counts: pd.Series,
    session_durations: pd.Series,
    output_dir: str,
    filename: str = "hits_vs_duration_scatter.png",
    threshold_percentile_hits: float | None = 0.99,
    threshold_percentile_duration: float | None = 0.99,
    perform_regression: bool = True
) -> tuple[pd.DataFrame | None, dict | None]:
    """
    Genera un diagrama de dispersión de visitas de página vs. duración de la sesión.
    """
    regression_results = None
    if session_hit_counts.empty or session_durations.empty:
        print("Datos insuficientes para generar el diagrama de dispersión hits vs. duración.")
        return None, None

    combined_df = pd.DataFrame({
        'hits_per_session': session_hit_counts,
        'duration_seconds': session_durations
    }).dropna()

    if combined_df.empty:
        print("No hay sesiones comunes con conteo de hits y duración para el scatter plot.")
        return None, None

    plot_df = combined_df.copy()
    original_rows = len(plot_df)
    notes_list = []

    if threshold_percentile_hits is not None and 0 < threshold_percentile_hits < 1:
        cap_hits = plot_df['hits_per_session'].quantile(threshold_percentile_hits)
        cap_hits = int(round(cap_hits))
        if cap_hits < plot_df['hits_per_session'].min() and (plot_df['hits_per_session'] > cap_hits).any():
            pass
        else:
            plot_df = plot_df[plot_df['hits_per_session'] <= cap_hits]
            note = f"Se omitieron sesiones con > {cap_hits} hits (P{threshold_percentile_hits*100:.0f})."
            notes_list.append(note)
            
    if threshold_percentile_duration is not None and 0 < threshold_percentile_duration < 1:
        cap_duration = plot_df['duration_seconds'].quantile(threshold_percentile_duration)
        if cap_duration < 1 and (plot_df['duration_seconds'] > cap_duration).any():
            pass
        else: 
            plot_df = plot_df[plot_df['duration_seconds'] <= cap_duration]
            note = f"Se omitieron sesiones con duración > {cap_duration:.2f}s (P{threshold_percentile_duration*100:.0f})."
            notes_list.append(note)

    omitted_rows = original_rows - len(plot_df)
    if omitted_rows > 0:
        description_for_memoria = "Para mejorar la visualización: " + " ".join(notes_list) + \
                                  f" Total sesiones omitidas por capping: {omitted_rows} ({omitted_rows/original_rows*100:.2f}%)."
    elif not notes_list:
        description_for_memoria = "No se aplicó filtrado de valores atípicos significativo para este diagrama."
    else:
        description_for_memoria = "No se omitieron valores atípicos para este diagrama."
    print(description_for_memoria)

    if plot_df.empty:
        print("No quedan datos para graficar después del capping.")
        memoria_notes_path = os.path.join(output_dir, "hits_vs_duration_scatter_notes.txt")
        with open(memoria_notes_path, "w") as f:
            f.write(description_for_memoria)
        print(f"Notas para la memoria guardadas en: {memoria_notes_path}")
        return combined_df, regression_results

    plt.figure(figsize=(12, 8))
    sns.scatterplot(data=plot_df, x='hits_per_session', y='duration_seconds', alpha=0.5)
    
    if perform_regression and not combined_df.empty:
        X = combined_df[['hits_per_session']]
        y = combined_df['duration_seconds']
        model = LinearRegression()
        try:
            model.fit(X, y)
            slope = model.coef_[0]
            intercept = model.intercept_
            equation = f"duration_seconds = {slope:.2f} * hits_per_session + {intercept:.2f}"
            print(f"\nEcuación de Regresión Lineal: {equation}")
            regression_results = {'slope': slope, 'intercept': intercept, 'equation': equation}
            x_reg_min = plot_df['hits_per_session'].min()
            x_reg_max = plot_df['hits_per_session'].max()
            x_line = np.array([[x_reg_min], [x_reg_max]])
            y_line = model.predict(x_line)
            plt.plot(x_line, y_line, color='red', linewidth=2, label=f'Regresión Lineal\n{equation}')
            plt.legend()
        except ValueError as ve:
            print(f"Error al ajustar el modelo de regresión: {ve}.")
            regression_results = {'error': str(ve)}

    title_note = description_for_memoria.split(" Total sesiones omitidas")[0]
    plt.title(f'Diagrama de Dispersión: Visitas por Sesión vs. Duración de Sesión\n{title_note}')
    plt.xlabel("Número de Visitas de Página por Sesión")
    plt.ylabel("Duración de la Sesión (segundos)")
    plt.grid(True, linestyle='--', linewidth=0.5)

    file_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(file_path)
        print(f"Diagrama de dispersión guardado en: {file_path}")
    except Exception as e:
        print(f"Error al guardar el diagrama: {e}")
    plt.close()

    memoria_notes_path = os.path.join(output_dir, "hits_vs_duration_scatter_notes.txt")
    with open(memoria_notes_path, "w") as f:
        f.write(description_for_memoria)
    print(f"Notas para la memoria (scatter plot) guardadas en: {memoria_notes_path}")
    
    return combined_df, regression_results 