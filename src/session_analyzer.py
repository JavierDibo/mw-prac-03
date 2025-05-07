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

# Nueva función para Tarea 2.8.3
def plot_mean_session_duration_by_hour(
    df: pd.DataFrame, 
    output_dir: str, 
    filename: str = "mean_session_duration_by_hour.png"
) -> None:
    """
    Calcula la duración media de las sesiones (>1 hit) para cada hora del día y genera un gráfico de barras.
    """
    print("\n--- Analizando Longitud Media de Sesión por Hora del Día ---")
    if 'Fecha/Hora' not in df.columns or 'SessionID' not in df.columns or 'marca de tiempo' not in df.columns:
        print("Error: Se requieren las columnas 'Fecha/Hora', 'SessionID' y 'marca de tiempo'.")
        return
    
    # 1. Calcular duraciones de sesión (>1 hit)
    session_durations = calculate_session_durations(df) # Esto devuelve una Serie indexada por SessionID
    if session_durations.empty:
        print("No hay duraciones de sesión (>1 hit) para analizar por hora.")
        return

    # 2. Obtener la hora de inicio de las sesiones que tienen duración calculada
    # Nos interesan las sesiones que están en session_durations.index
    df_for_start_time = df[df['SessionID'].isin(session_durations.index)]
    session_start_times = df_for_start_time.groupby('SessionID')['Fecha/Hora'].min()
    session_start_hour = session_start_times.dt.hour.rename('start_hour')

    # 3. Combinar duraciones con hora de inicio
    # Usar pd.concat para asegurar la alineación por SessionID (índice)
    df_hourly_duration = pd.concat([session_durations.rename('duration'), session_start_hour], axis=1)
    df_hourly_duration.dropna(inplace=True) # Por si alguna sesión no tuvo hora de inicio o duración

    if df_hourly_duration.empty:
        print("No se pudieron combinar duraciones de sesión con su hora de inicio.")
        return

    # 4. Calcular duración media por hora
    mean_duration_by_hour = df_hourly_duration.groupby('start_hour')['duration'].mean()

    # 5. Asegurar que todas las horas (0-23) están presentes para el gráfico
    mean_duration_by_hour = mean_duration_by_hour.reindex(range(24), fill_value=0)

    print("\nDuración media de sesión (segundos) por hora del día:")
    print(mean_duration_by_hour.to_string())

    # 6. Generar gráfico de barras
    plt.figure(figsize=(14, 7))
    sns.barplot(x=mean_duration_by_hour.index, y=mean_duration_by_hour.values, palette="viridis")
    plt.title('Longitud Media de las Visitas (Sesiones >1 hit) por Hora del Día')
    plt.xlabel('Hora del Día (0-23)')
    plt.ylabel('Duración Media de la Sesión (segundos)')
    plt.xticks(range(24))
    plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
    plt.tight_layout()

    file_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(file_path)
        print(f"Gráfico de longitud media de sesión por hora guardado en: {file_path}")
    except Exception as e:
        print(f"Error al guardar el gráfico: {e}")
    plt.close()

# Nueva función para Tarea 2.8.4
def get_top_visitors_by_sessions(df: pd.DataFrame, output_dir: str, top_n: int = 10) -> pd.DataFrame | None:
    """
    Identifica los N visitantes (UserID) más repetidos por número de sesiones.
    """
    print("\n--- Analizando Top Visitantes (UserID) por Número de Sesiones ---")
    if 'UserID' not in df.columns or 'SessionID' not in df.columns:
        print("Error: Se requieren las columnas 'UserID' y 'SessionID'.")
        return None

    # Contar sesiones únicas por UserID
    # No necesitamos df.copy() aquí ya que solo estamos agrupando y contando
    sessions_per_user = df.groupby('UserID')['SessionID'].nunique().sort_values(ascending=False)
    
    if sessions_per_user.empty:
        print("No se encontraron datos de sesiones por usuario.")
        return None
        
    top_visitors_df = sessions_per_user.head(top_n).reset_index()
    top_visitors_df.columns = ['UserID', 'SessionCount']

    print(f"\nTop {top_n} Visitantes (UserID) por Número de Sesiones:")
    print(top_visitors_df.to_string())

    # Guardar en CSV
    # output_dir es .../graphics/analysis, necesitamos ir a .../tables
    output_tables_dir = os.path.join(output_dir, '..', 'tables') 
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)

    file_path = os.path.join(output_tables_dir, f'top_{top_n}_visitors_by_sessions.csv')
    try:
        top_visitors_df.to_csv(file_path, index=False)
        print(f"Tabla de los top {top_n} visitantes guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de top visitantes: {e}")

    return top_visitors_df

# Nueva función para Tarea 2.8.5
def get_visitor_session_distribution(df: pd.DataFrame, output_dir: str, max_sessions_to_detail: int = 9) -> pd.DataFrame | None:
    """
    Calcula la distribución del número de visitantes únicos por el número de sesiones que realizan (1 a max_sessions_to_detail).
    """
    print("\n--- Analizando Distribución de Sesiones por Visitante ---")
    if 'UserID' not in df.columns or 'SessionID' not in df.columns:
        print("Error: Se requieren las columnas 'UserID' y 'SessionID'.")
        return None

    # Contar sesiones únicas por UserID
    sessions_per_user = df.groupby('UserID')['SessionID'].nunique()

    if sessions_per_user.empty:
        print("No se encontraron datos de sesiones por usuario para analizar la distribución.")
        return None

    # Contar cuántos usuarios tienen X sesiones
    visitor_counts_by_session_count = sessions_per_user.value_counts().sort_index()
    
    # Filtrar para el rango deseado (1 a max_sessions_to_detail)
    distribution_df = visitor_counts_by_session_count[\
        (visitor_counts_by_session_count.index >= 1) & \
        (visitor_counts_by_session_count.index <= max_sessions_to_detail)
    ].reset_index()
    distribution_df.columns = ['NumberOfSessions', 'NumberOfUniqueVisitors']
    
    # Asegurar que todas las categorías de 1 a max_sessions_to_detail están, incluso si tienen 0 visitantes
    all_session_counts = pd.DataFrame({'NumberOfSessions': range(1, max_sessions_to_detail + 1)})
    distribution_df = pd.merge(all_session_counts, distribution_df, on='NumberOfSessions', how='left').fillna(0)
    distribution_df['NumberOfUniqueVisitors'] = distribution_df['NumberOfUniqueVisitors'].astype(int)

    print(f"\nDistribución de visitantes únicos por número de sesiones (1 a {max_sessions_to_detail}):")
    print(distribution_df.to_string())

    # Guardar en CSV
    output_tables_dir = os.path.join(output_dir, '..', 'tables')
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)

    file_path = os.path.join(output_tables_dir, f'visitor_session_distribution_1_to_{max_sessions_to_detail}.csv')
    try:
        distribution_df.to_csv(file_path, index=False)
        print(f"Tabla de distribución de sesiones por visitante guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de distribución: {e}")

    return distribution_df

# Nueva función para Tarea 2.8.9
def get_top_entry_pages(df: pd.DataFrame, output_dir: str, top_n: int = 10) -> pd.DataFrame | None:
    """
    Identifica las N páginas de entrada (primera página de una sesión) más repetidas.
    """
    print("\n--- Analizando Top Páginas de Entrada ---")
    if 'SessionID' not in df.columns or 'marca de tiempo' not in df.columns or 'Página' not in df.columns:
        print("Error: Se requieren las columnas 'SessionID', 'marca de tiempo' y 'Página'.")
        return None

    # Identificar la primera página de cada sesión
    # Ordenar por SessionID y marca de tiempo, luego tomar la primera de cada grupo SessionID
    # O usar idxmin para encontrar el índice del primer hit de cada sesión
    first_hits_indices = df.groupby('SessionID')['marca de tiempo'].idxmin()
    first_pages_df = df.loc[first_hits_indices]

    if first_pages_df.empty:
        print("No se pudieron identificar las primeras páginas de las sesiones.")
        return None

    # Contar cuántas sesiones iniciaron con cada página
    entry_page_counts = first_pages_df.groupby('Página').size().rename('NumeroDeSesionesIniciadas').sort_values(ascending=False)
    
    df_top_entry_pages = entry_page_counts.head(top_n).reset_index()
    df_top_entry_pages.columns = ['PáginaDeEntrada', 'NumeroDeSesionesIniciadas']

    print(f"\nTop {top_n} Páginas de Entrada por Número de Sesiones Iniciadas:")
    print(df_top_entry_pages.to_string())

    # Guardar en CSV
    output_tables_dir = os.path.join(output_dir, '..', 'tables')
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)
    
    file_path = os.path.join(output_tables_dir, f'top_{top_n}_entry_pages.csv')
    try:
        df_top_entry_pages.to_csv(file_path, index=False)
        print(f"Tabla de las top {top_n} páginas de entrada guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de top páginas de entrada: {e}")

    return df_top_entry_pages

# Nueva función para Tarea 2.8.10
def get_top_exit_pages(df: pd.DataFrame, output_dir: str, top_n: int = 10) -> pd.DataFrame | None:
    """
    Identifica las N páginas de salida (última página de una sesión) más repetidas.
    """
    print("\n--- Analizando Top Páginas de Salida ---")
    if 'SessionID' not in df.columns or 'marca de tiempo' not in df.columns or 'Página' not in df.columns:
        print("Error: Se requieren las columnas 'SessionID', 'marca de tiempo' y 'Página'.")
        return None

    # Identificar la última página de cada sesión usando idxmax
    last_hits_indices = df.groupby('SessionID')['marca de tiempo'].idxmax()
    last_pages_df = df.loc[last_hits_indices]

    if last_pages_df.empty:
        print("No se pudieron identificar las últimas páginas de las sesiones.")
        return None

    # Contar cuántas sesiones terminaron con cada página
    exit_page_counts = last_pages_df.groupby('Página').size().rename('NumeroDeSesionesTerminadas').sort_values(ascending=False)
    
    df_top_exit_pages = exit_page_counts.head(top_n).reset_index()
    df_top_exit_pages.columns = ['PáginaDeSalida', 'NumeroDeSesionesTerminadas']

    print(f"\nTop {top_n} Páginas de Salida por Número de Sesiones Terminadas:")
    print(df_top_exit_pages.to_string())

    # Guardar en CSV
    output_tables_dir = os.path.join(output_dir, '..', 'tables')
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)
    
    file_path = os.path.join(output_tables_dir, f'top_{top_n}_exit_pages.csv')
    try:
        df_top_exit_pages.to_csv(file_path, index=False)
        print(f"Tabla de las top {top_n} páginas de salida guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de top páginas de salida: {e}")

    return df_top_exit_pages

# Nueva función para Tarea 2.8.11
def get_top_single_access_pages(df: pd.DataFrame, output_dir: str, top_n: int = 10) -> pd.DataFrame | None:
    """
    Identifica las N páginas más comunes en sesiones de acceso único (una sola página vista).
    """
    print("\n--- Analizando Top Páginas de Acceso Único ---")
    if 'SessionID' not in df.columns or 'Página' not in df.columns:
        print("Error: Se requieren las columnas 'SessionID' y 'Página'.")
        return None

    # 1. Contar hits por sesión
    session_hit_counts = df.groupby('SessionID').size()
    
    # 2. Identificar sesiones con un solo hit
    single_hit_session_ids = session_hit_counts[session_hit_counts == 1].index
    
    if len(single_hit_session_ids) == 0:
        print("No se encontraron sesiones de acceso único.")
        return None
        
    # 3. Filtrar el DataFrame para incluir solo esas sesiones
    single_hit_df = df[df['SessionID'].isin(single_hit_session_ids)]

    # 4. Contar las páginas en estas sesiones de acceso único
    # Como cada sesión tiene 1 hit, contar las páginas es equivalente a contar las sesiones
    single_access_page_counts = single_hit_df.groupby('Página').size().rename('NumeroDeVisitasUnicas').sort_values(ascending=False)
    
    df_top_single_access = single_access_page_counts.head(top_n).reset_index()
    df_top_single_access.columns = ['PáginaDeAccesoUnico', 'NumeroDeVisitasUnicas']

    print(f"\nTop {top_n} Páginas de Acceso Único (Sesiones con 1 hit):")
    print(df_top_single_access.to_string())

    # Guardar en CSV
    output_tables_dir = os.path.join(output_dir, '..', 'tables')
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)
    
    file_path = os.path.join(output_tables_dir, f'top_{top_n}_single_access_pages.csv')
    try:
        df_top_single_access.to_csv(file_path, index=False)
        print(f"Tabla de las top {top_n} páginas de acceso único guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de páginas de acceso único: {e}")

    return df_top_single_access

# Nueva función para Tarea 2.8.12
def get_session_duration_distribution_minutes(df: pd.DataFrame, output_dir: str) -> pd.DataFrame | None:
    """
    Calcula la distribución de la duración de las sesiones (>1 hit) en rangos de minutos.
    """
    print("\n--- Analizando Distribución de Duración de Sesiones en Minutos ---")
    if 'SessionID' not in df.columns or 'marca de tiempo' not in df.columns:
        print("Error: Se requieren las columnas 'SessionID' y 'marca de tiempo'.")
        return None

    # 1. Calcular duraciones de sesión (>1 hit) en segundos
    session_durations_seconds = calculate_session_durations(df)
    if session_durations_seconds.empty:
        print("No hay duraciones de sesión (>1 hit) para analizar.")
        return None

    # 2. Convertir a minutos
    session_durations_minutes = session_durations_seconds / 60.0

    # 3. Definir los rangos (bins) en minutos
    # Ej: [0, 1), [1, 2), ..., [9, 10), [10, inf)
    # Los bordes de los bins: 0, 1, 2, ..., 10, infinito
    bins = list(range(0, 11)) # Bordes de 0 a 10
    bins.append(np.inf) # Añadir infinito para el último bin "10+"
    
    # Etiquetas para los bins
    labels = [f'{i}-{i+1} min' for i in range(10)] # 0-1 min, 1-2 min, ..., 9-10 min
    labels.append('10+ min')

    # 4. Usar pd.cut para asignar cada duración a un rango
    # right=False para que los rangos sean [inicio, fin), excepto el último
    duration_bins = pd.cut(session_durations_minutes, bins=bins, labels=labels, right=False, include_lowest=True)

    # 5. Contar sesiones por rango
    distribution_counts = duration_bins.value_counts().sort_index()
    
    distribution_df = distribution_counts.reset_index()
    distribution_df.columns = ['DuracionRangoMinutos', 'NumeroDeSesiones']

    print("\nDistribución de la Duración de Sesiones (>1 hit) en Minutos:")
    print(distribution_df.to_string())

    # Guardar en CSV
    output_tables_dir = os.path.join(output_dir, '..', 'tables')
    output_tables_dir = os.path.normpath(output_tables_dir)
    if not os.path.exists(output_tables_dir):
        os.makedirs(output_tables_dir)
    
    file_path = os.path.join(output_tables_dir, 'session_duration_distribution_minutes.csv')
    try:
        distribution_df.to_csv(file_path, index=False)
        print(f"Tabla de distribución de duración de sesiones guardada en: {file_path}")
    except Exception as e:
        print(f"Error al guardar la tabla de distribución de duración: {e}")

    return distribution_df 