import pandas as pd
import os
import seaborn as sns
from data_loader import load_processed_data
# Import session analysis functions
from session_analyzer import (
    calculate_session_durations,
    plot_session_duration_histogram,
    get_session_duration_stats,
    calculate_per_session_avg_page_time,
    plot_hits_per_session_histogram,
    get_hits_per_session_stats,
    plot_hits_vs_duration_scatter
)
# Import page analysis functions
from page_analyzer import (
    calculate_mean_time_per_page,
    plot_page_view_duration_histogram,
    get_page_view_duration_stats,
    calculate_first_second_page_durations,
    plot_first_page_duration_histogram,
    get_first_second_page_duration_stats
)

# Configuración de Seaborn para los gráficos
sns.set_theme(style="whitegrid")

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

        # --- Tarea 2.2.1: Calcular tiempo medio por página ---
        page_view_durations_seconds, mean_time_per_page_seconds = calculate_mean_time_per_page(df_processed)
        
        if mean_time_per_page_seconds is not None:
            # --- Tarea 2.2.2: Construir histograma del tiempo por página ---
            plot_page_view_duration_histogram(page_view_durations_seconds, output_graphics_dir)
            
            # --- Tarea 2.2.3: Calcular estadísticas de tiempo por página ---
            page_view_stats_df = get_page_view_duration_stats(page_view_durations_seconds, output_graphics_dir)

            # --- Tarea 2.3.1: Identificar 20 sesiones con menor tiempo medio por página ---
            per_session_avg_page_time_df = calculate_per_session_avg_page_time(df_processed)
            if not per_session_avg_page_time_df.empty:
                top_20_low_avg_time_sessions = per_session_avg_page_time_df.head(20)
                print("\nTop 20 sesiones con menor tiempo medio por página (segundos):")
                print(top_20_low_avg_time_sessions.to_string())
                
                # Guardar esta tabla
                output_tables_dir = os.path.join(project_root, 'output', 'tables')
                output_tables_dir = os.path.normpath(output_tables_dir)
                if not os.path.exists(output_tables_dir):
                    os.makedirs(output_tables_dir)
                    print(f"Directorio para tablas creado: {output_tables_dir}")
                
                table_path = os.path.join(output_tables_dir, 'top_20_low_avg_page_time_sessions.csv')
                try:
                    top_20_low_avg_time_sessions.to_csv(table_path, index=False)
                    print(f"Tabla de las 20 sesiones con menor tiempo medio por página guardada en: {table_path}")
                except Exception as e:
                    print(f"Error al guardar la tabla: {e}")

                # --- Tarea 2.3.2: Identificar sesiones con tiempo medio por página < 0.5s ---
                if not per_session_avg_page_time_df.empty:
                    fast_sessions_threshold = 0.5
                    identified_fast_sessions_df = per_session_avg_page_time_df[
                        per_session_avg_page_time_df['avg_page_view_time_seconds'] < fast_sessions_threshold
                    ]
                    print(f"\nSe identificaron {len(identified_fast_sessions_df)} sesiones con un tiempo medio por página menor a {fast_sessions_threshold} segundos.")
                    
                    if not identified_fast_sessions_df.empty:
                        print("Algunas de estas sesiones (hasta 10):")
                        print(identified_fast_sessions_df.head(10).to_string())
                        # Guardar esta tabla también podría ser útil
                        fast_sessions_table_path = os.path.join(output_tables_dir, 'identified_fast_sessions.csv')
                        try:
                            identified_fast_sessions_df.to_csv(fast_sessions_table_path, index=False)
                            print(f"Tabla de sesiones rápidas (<{fast_sessions_threshold}s) guardada en: {fast_sessions_table_path}")
                        except Exception as e:
                            print(f"Error al guardar la tabla de sesiones rápidas: {e}")
                        
                        # Estas SessionIDs se usarán en la tarea 2.3.3
                        session_ids_to_potentially_remove = set(identified_fast_sessions_df['SessionID'])
                    else:
                        session_ids_to_potentially_remove = set()
                else:
                    session_ids_to_potentially_remove = set()
                    print("\nNo se pudo calcular el tiempo medio por página por sesión, saltando la identificación de sesiones rápidas.")

                # --- Tarea 2.3.3: Eliminar sesiones identificadas como rápidas ---
                # Por defecto, eliminamos todas las sesiones identificadas con avg_page_view_time_seconds < 0.5s.
                # Si se decide conservar algunas, esta lógica necesitaría ajustarse manualmente o con una lista de excepciones.
                if session_ids_to_potentially_remove:
                    rows_before_fast_session_removal = len(df_processed)
                    df_processed_no_fast_sessions = df_processed[
                        ~df_processed['SessionID'].isin(session_ids_to_potentially_remove)
                    ].copy() # .copy() para evitar SettingWithCopyWarning más adelante
                    rows_after_fast_session_removal = len(df_processed_no_fast_sessions)
                    print(f"\nSe eliminaron {len(session_ids_to_potentially_remove)} sesiones consideradas demasiado rápidas.")
                    print(f"Filas en el DataFrame antes de eliminar sesiones rápidas: {rows_before_fast_session_removal}")
                    print(f"Filas en el DataFrame después de eliminar sesiones rápidas: {rows_after_fast_session_removal}")
                    print(f"Número de filas eliminadas: {rows_before_fast_session_removal - rows_after_fast_session_removal}")
                    
                    # df_processed_no_fast_sessions será el DataFrame para análisis posteriores si se eliminaron sesiones.
                    # Si no se eliminaron (o no había ninguna que eliminar), podemos seguir usando df_processed
                    # o renombrar/reasignar para consistencia en las tareas siguientes.
                    # Para claridad, vamos a usar df_current_for_analysis para las tareas que siguen este paso.
                    df_current_for_analysis = df_processed_no_fast_sessions
                    sessions_were_removed_in_2_3_3 = True
                else:
                    print("\nNo se eliminaron sesiones en el paso 2.3.3 (ninguna identificada o ninguna que cumpliera criterios de eliminación).")
                    df_current_for_analysis = df_processed # Continuar con el DataFrame original
                    sessions_were_removed_in_2_3_3 = False

                # A partir de aquí, las tareas que dependan de este filtrado (ej. 2.3.4) 
                # deberían usar df_current_for_analysis y la bandera sessions_were_removed_in_2_3_3.

                # --- Tarea 2.3.4: Actualizar histogramas y estadísticas si se eliminaron sesiones ---
                if sessions_were_removed_in_2_3_3:
                    print("\n--- REGENERANDO ANÁLISIS DE 2.1 y 2.2 CON DATAFRAME FILTRADO (SIN SESIONES RÁPIDAS) ---")
                    
                    # --- Actualización para 2.1 (Duración de la sesión) ---
                    print("\n--- Actualizando análisis de Duración de Sesión (2.1) ---")
                    session_durations_seconds_filtered = calculate_session_durations(df_current_for_analysis)
                    if not session_durations_seconds_filtered.empty:
                        plot_session_duration_histogram(
                            session_durations_seconds_filtered, 
                            output_graphics_dir,
                            filename="session_duration_histogram_after_2.3.3_filter.png"
                        )
                        get_session_duration_stats(
                            session_durations_seconds_filtered, 
                            output_graphics_dir,
                            filename="session_duration_stats_after_2.3.3_filter.txt"
                        )
                    else:
                        print("No hay duraciones de sesión para analizar después del filtro 2.3.3.")

                    # --- Actualización para 2.2 (Tiempo medio por página) ---
                    print("\n--- Actualizando análisis de Tiempo Medio por Página (2.2) ---")
                    page_view_durations_seconds_filtered, mean_time_per_page_seconds_filtered = \
                        calculate_mean_time_per_page(df_current_for_analysis)
                    if mean_time_per_page_seconds_filtered is not None:
                        plot_page_view_duration_histogram(
                            page_view_durations_seconds_filtered,
                            output_graphics_dir,
                            filename="page_view_duration_histogram_after_2.3.3_filter.png"
                        )
                        get_page_view_duration_stats(
                            page_view_durations_seconds_filtered,
                            output_graphics_dir,
                            filename="page_view_duration_stats_after_2.3.3_filter.txt"
                        )
                    else:
                        print("No hay duraciones de visualización de página para analizar después del filtro 2.3.3.")
                else:
                    print("\nNo se eliminaron sesiones en 2.3.3, por lo que no es necesario actualizar los análisis de 2.1 y 2.2.")

                # --- Tarea 2.4: Páginas visitadas ---
                print("\n--- Iniciando análisis de Páginas Visitadas por Sesión (2.4) ---")
                session_hit_counts = df_current_for_analysis.groupby('SessionID').size()
                if not session_hit_counts.empty:
                    plot_hits_per_session_histogram(session_hit_counts, output_graphics_dir)
                    hits_per_session_stats_df = get_hits_per_session_stats(session_hit_counts, output_graphics_dir)
                else:
                    print("No hay datos de conteo de hits por sesión para generar el histograma o estadísticas.")

                # --- Tarea 2.5: Relación entre visitas y duración ---
                print("\n--- Iniciando análisis de Relación Visitas-Duración (2.5) ---")
                # Determinar qué serie de duraciones de sesión usar
                active_session_durations = pd.Series(dtype='float64')
                if sessions_were_removed_in_2_3_3:
                    # Recalcular session_durations basado en df_current_for_analysis si no se hizo ya de forma reutilizable
                    # Asumimos que session_durations_seconds_filtered de 2.3.4 es la correcta
                    # Necesitamos asegurar que está disponible o recalcularla aquí.
                    # Por ahora, vamos a recalcularla para asegurar que es sobre df_current_for_analysis
                    # y solo para sesiones > 1 hit.
                    temp_session_durations = calculate_session_durations(df_current_for_analysis)
                    if temp_session_durations is not None and not temp_session_durations.empty:
                        active_session_durations = temp_session_durations
                else:
                    # Usar la original session_durations_seconds calculada en 2.1.2
                    # Esta ya estaba basada en el df_processed (antes del filtro 2.3.3)
                    # y era para sesiones > 1 hit.
                    # Necesitamos que session_durations_seconds esté disponible en este scope.
                    # La estructura actual la define dentro de un if. Rehacer ligeramente.
                    if 'session_durations_seconds' in locals() and not session_durations_seconds.empty:
                         active_session_durations = session_durations_seconds
                    elif 'session_durations_seconds_filtered' in locals() and not session_durations_seconds_filtered.empty():
                        # This case implies sessions_were_removed_in_2_3_3 was true, 
                        # but we are in the else branch - this indicates a logic flaw, should use the filtered one
                        # For safety, let's assume if sessions_were_removed_in_2_3_3 is false, we use original if available
                        # else recalculate on df_current_for_analysis (which is df_processed here)
                         active_session_durations = calculate_session_durations(df_current_for_analysis)
                    else: # Fallback: recalculate if not available
                        active_session_durations = calculate_session_durations(df_current_for_analysis)
                
                # session_hit_counts ya está calculado sobre df_current_for_analysis
                if not active_session_durations.empty and not session_hit_counts.empty:
                    # 2.5.1: Diagrama de dispersión
                    scatter_data_for_regression = plot_hits_vs_duration_scatter(
                        session_hit_counts, 
                        active_session_durations, 
                        output_graphics_dir
                    )
                    # scatter_data_for_regression (DataFrame con 'hits_per_session', 'duration_seconds') 
                    # se usará para la regresión en 2.5.2
                else:
                    print("No se pueden generar datos para el diagrama de dispersión hits vs duración.")

                # --- Tarea 2.6: Duración de la visita a las dos primeras páginas ---
                print("\n--- Iniciando análisis de Duración de las Dos Primeras Páginas (2.6) ---")
                first_page_durations, second_page_durations = calculate_first_second_page_durations(df_current_for_analysis)
                
                if not first_page_durations.empty:
                    print(f"Se calcularon {len(first_page_durations)} duraciones para la primera página de sesiones.")
                    plot_first_page_duration_histogram(first_page_durations, output_graphics_dir)
                else:
                    print("No se pudieron calcular duraciones para la primera página.")
                
                if not second_page_durations.empty:
                    print(f"Se calcularon {len(second_page_durations)} duraciones para la segunda página de sesiones.")
                else:
                    print("No se pudieron calcular duraciones para la segunda página.")

                # --- Tarea 2.6.3: Calcular estadísticos de duración de primera y segunda página ---
                # Asegurarse que las series existen antes de pasarlas
                stats_first_page_df, stats_second_page_df = get_first_second_page_duration_stats(
                    first_page_durations if 'first_page_durations' in locals() and not first_page_durations.empty else pd.Series(dtype='float64'),
                    second_page_durations if 'second_page_durations' in locals() and not second_page_durations.empty else pd.Series(dtype='float64'),
                    output_graphics_dir
                )

                # --- Tarea 2.7: Determinación del tipo de página por su extensión ---
                print("\n--- Iniciando análisis de Tipo de Página por Extensión (2.7) ---")
                
                # 2.7.1: Clasificar páginas y crear columna 'Tipo de Página'
                # Usar df_current_for_analysis que ya tiene la columna 'Extensión'
                # Si 'Extensión' es "" (vacío), tipo es 'navegación', sino 'contenido'.
                df_current_for_analysis['Tipo de Página'] = df_current_for_analysis['Extensión'].apply(
                    lambda ext: 'navegación' if ext == "" else 'contenido'
                )
                print("Columna 'Tipo de Página' creada.")
                print("Distribución de Tipos de Página:")
                print(df_current_for_analysis['Tipo de Página'].value_counts())
                # Mostrar algunas filas para verificar
                # print(df_current_for_analysis[['Página', 'Extensión', 'Tipo de Página']].head(10))

    else:
        print("No se pudieron cargar los datos procesados. Terminando el script de análisis.") 