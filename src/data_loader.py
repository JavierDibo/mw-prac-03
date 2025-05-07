import pandas as pd
import os

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