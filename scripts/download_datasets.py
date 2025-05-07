"""
Script para descargar datasets de Kaggle relacionados con información nutricional.
"""
import os
import sys
import json
import pandas as pd
import kaggle
from pathlib import Path
import zipfile
import csv

# Añadir el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Directorio donde se guardarán los datasets
DATA_DIR = os.path.join(ROOT_DIR, "data")

def setup_directories():
    """Crea los directorios necesarios si no existen."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "raw"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "processed"), exist_ok=True)
    print(f"Directorios creados en {DATA_DIR}")

def authenticate_kaggle():
    """Verifica la autenticación con Kaggle."""
    try:
        kaggle.api.authenticate()
        print("✅ Autenticación con Kaggle exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de autenticación con Kaggle: {str(e)}")
        print("Asegúrate de que tu archivo kaggle.json esté correctamente configurado")
        print("1. Descarga tu archivo kaggle.json desde tu cuenta de Kaggle")
        print("2. Colócalo en ~/.kaggle/ (Linux/Mac) o %USERPROFILE%\\.kaggle\\ (Windows)")
        print("   O configura las variables de entorno KAGGLE_USERNAME y KAGGLE_KEY")
        return False

def download_usda_dataset():
    """Descarga el dataset USDA FoodData Central."""
    try:
        # Buscaremos entre los datasets populares relacionados con USDA
        print("Buscando datasets de USDA FoodData Central...")
        datasets = kaggle.api.dataset_list(search="usda food data central")
        
        if not datasets:
            print("No se encontraron datasets relacionados con USDA FoodData Central")
            return None
        
        # Usaremos el primer resultado que parezca relevante
        selected_dataset = None
        for dataset in datasets:
            if "usda" in dataset.ref.lower() and "food" in dataset.ref.lower():
                selected_dataset = dataset.ref
                break
        
        if not selected_dataset:
            selected_dataset = datasets[0].ref
        
        print(f"Descargando dataset: {selected_dataset}")
        kaggle.api.dataset_download_files(
            selected_dataset, 
            path=os.path.join(DATA_DIR, "raw"),
            unzip=True
        )
        
        print(f"✅ Dataset USDA descargado exitosamente en {os.path.join(DATA_DIR, 'raw')}")
        return selected_dataset
    except Exception as e:
        print(f"❌ Error descargando dataset USDA: {str(e)}")
        return None

def download_open_food_facts():
    """Descarga el dataset Open Food Facts."""
    try:
        print("Buscando datasets de Open Food Facts...")
        datasets = kaggle.api.dataset_list(search="open food facts")
        
        if not datasets:
            print("No se encontraron datasets relacionados con Open Food Facts")
            return None
        
        # Usaremos el primer resultado que parezca relevante
        selected_dataset = None
        for dataset in datasets:
            if "open" in dataset.ref.lower() and "food" in dataset.ref.lower() and "facts" in dataset.ref.lower():
                selected_dataset = dataset.ref
                break
        
        if not selected_dataset:
            selected_dataset = datasets[0].ref
        
        print(f"Descargando dataset: {selected_dataset}")
        kaggle.api.dataset_download_files(
            selected_dataset, 
            path=os.path.join(DATA_DIR, "raw"),
            unzip=True
        )
        
        print(f"✅ Dataset Open Food Facts descargado exitosamente en {os.path.join(DATA_DIR, 'raw')}")
        return selected_dataset
    except Exception as e:
        print(f"❌ Error descargando dataset Open Food Facts: {str(e)}")
        return None

def process_usda_data():
    """Procesa los archivos descargados de USDA para crear un CSV unificado."""
    raw_dir = os.path.join(DATA_DIR, "raw")
    processed_dir = os.path.join(DATA_DIR, "processed")
    
    # Buscar archivos relevantes
    food_files = []
    for file in os.listdir(raw_dir):
        if file.endswith(".csv") and ("food" in file.lower() or "usda" in file.lower()):
            food_files.append(os.path.join(raw_dir, file))
    
    if not food_files:
        print("No se encontraron archivos CSV relevantes para USDA")
        return
    
    print(f"Procesando {len(food_files)} archivos de USDA...")
    
    # Procesar cada archivo y unificar el formato
    processed_data = []
    
    for file_path in food_files:
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            # Comprobar si el archivo tiene la estructura esperada
            if "description" in df.columns or "food_name" in df.columns or "name" in df.columns:
                print(f"Procesando {file_path}...")
                
                # Mapear columnas al formato estándar
                standardized_df = pd.DataFrame()
                
                # Mapear nombre del alimento
                if "description" in df.columns:
                    standardized_df["name"] = df["description"]
                elif "food_name" in df.columns:
                    standardized_df["name"] = df["food_name"]
                elif "name" in df.columns:
                    standardized_df["name"] = df["name"]
                else:
                    continue
                
                # Mapear valores nutricionales
                # Calorías
                if "energy" in df.columns:
                    standardized_df["calories"] = df["energy"]
                elif "calories" in df.columns:
                    standardized_df["calories"] = df["calories"]
                elif "kcal" in df.columns:
                    standardized_df["calories"] = df["kcal"]
                else:
                    standardized_df["calories"] = None
                
                # Proteínas
                if "protein" in df.columns:
                    standardized_df["protein_g"] = df["protein"]
                elif "protein_g" in df.columns:
                    standardized_df["protein_g"] = df["protein_g"]
                else:
                    standardized_df["protein_g"] = None
                
                # Carbohidratos
                if "carbohydrate" in df.columns:
                    standardized_df["carbohydrates_g"] = df["carbohydrate"]
                elif "carbohydrates" in df.columns:
                    standardized_df["carbohydrates_g"] = df["carbohydrates"]
                elif "carbohydrates_g" in df.columns:
                    standardized_df["carbohydrates_g"] = df["carbohydrates_g"]
                else:
                    standardized_df["carbohydrates_g"] = None
                
                # Grasas
                if "fat" in df.columns:
                    standardized_df["fat_g"] = df["fat"]
                elif "total_fat" in df.columns:
                    standardized_df["fat_g"] = df["total_fat"]
                elif "fat_g" in df.columns:
                    standardized_df["fat_g"] = df["fat_g"]
                else:
                    standardized_df["fat_g"] = None
                
                # Añadir los datos a la lista
                processed_data.append(standardized_df)
        except Exception as e:
            print(f"Error procesando {file_path}: {str(e)}")
    
    if not processed_data:
        print("No se pudieron procesar los datos de USDA")
        return
    
    # Combinar todos los dataframes
    combined_df = pd.concat(processed_data, ignore_index=True)
    
    # Eliminar duplicados
    combined_df.drop_duplicates(subset=["name"], inplace=True)
    
    # Eliminar filas con valores nulos en el nombre
    combined_df = combined_df.dropna(subset=["name"])
    
    # Guardar el resultado
    output_path = os.path.join(processed_dir, "usda_food_data.csv")
    combined_df.to_csv(output_path, index=False)
    
    print(f"✅ Datos USDA procesados: {len(combined_df)} alimentos guardados en {output_path}")

def process_open_food_facts():
    """Procesa los archivos descargados de Open Food Facts para crear un CSV unificado."""
    raw_dir = os.path.join(DATA_DIR, "raw")
    processed_dir = os.path.join(DATA_DIR, "processed")
    
    # Buscar archivos relevantes
    food_files = []
    for file in os.listdir(raw_dir):
        if file.endswith(".csv") and ("openfood" in file.lower() or "open_food" in file.lower()):
            food_files.append(os.path.join(raw_dir, file))
    
    if not food_files:
        print("No se encontraron archivos CSV relevantes para Open Food Facts")
        return
    
    print(f"Procesando {len(food_files)} archivos de Open Food Facts...")
    
    # Procesar cada archivo y unificar el formato
    processed_data = []
    
    for file_path in food_files:
        try:
            # Open Food Facts puede ser muy grande, tomamos una muestra
            df = pd.read_csv(file_path, low_memory=False, nrows=10000)
            
            # Comprobar si el archivo tiene la estructura esperada
            if "product_name" in df.columns or "name" in df.columns:
                print(f"Procesando {file_path}...")
                
                # Mapear columnas al formato estándar
                standardized_df = pd.DataFrame()
                
                # Mapear nombre del alimento
                if "product_name" in df.columns:
                    standardized_df["name"] = df["product_name"]
                elif "name" in df.columns:
                    standardized_df["name"] = df["name"]
                else:
                    continue
                
                # Mapear valores nutricionales
                # Calorías
                if "energy-kcal_100g" in df.columns:
                    standardized_df["energy-kcal_100g"] = df["energy-kcal_100g"]
                elif "energy_100g" in df.columns:
                    standardized_df["energy-kcal_100g"] = df["energy_100g"]
                else:
                    standardized_df["energy-kcal_100g"] = None
                
                # Proteínas
                if "proteins_100g" in df.columns:
                    standardized_df["proteins_100g"] = df["proteins_100g"]
                else:
                    standardized_df["proteins_100g"] = None
                
                # Carbohidratos
                if "carbohydrates_100g" in df.columns:
                    standardized_df["carbohydrates_100g"] = df["carbohydrates_100g"]
                else:
                    standardized_df["carbohydrates_100g"] = None
                
                # Grasas
                if "fat_100g" in df.columns:
                    standardized_df["fat_100g"] = df["fat_100g"]
                else:
                    standardized_df["fat_100g"] = None
                
                # Añadir los datos a la lista
                processed_data.append(standardized_df)
        except Exception as e:
            print(f"Error procesando {file_path}: {str(e)}")
    
    if not processed_data:
        print("No se pudieron procesar los datos de Open Food Facts")
        return
    
    # Combinar todos los dataframes
    combined_df = pd.concat(processed_data, ignore_index=True)
    
    # Eliminar duplicados
    combined_df.drop_duplicates(subset=["name"], inplace=True)
    
    # Eliminar filas con valores nulos en el nombre
    combined_df = combined_df.dropna(subset=["name"])
    
    # Guardar el resultado
    output_path = os.path.join(processed_dir, "open_food_facts.csv")
    combined_df.to_csv(output_path, index=False)
    
    print(f"✅ Datos Open Food Facts procesados: {len(combined_df)} alimentos guardados en {output_path}")

def main():
    """Función principal."""
    print("=== Descargando datasets nutricionales ===")
    
    # Configurar directorios
    setup_directories()
    
    # Autenticar con Kaggle
    if not authenticate_kaggle():
        return
    
    # Descargar datasets
    usda_dataset = download_usda_dataset()
    open_food_dataset = download_open_food_facts()
    
    # Procesar datos
    if usda_dataset:
        process_usda_data()
    
    if open_food_dataset:
        process_open_food_facts()
    
    print("=== Proceso completado ===")

if __name__ == "__main__":
    main() 