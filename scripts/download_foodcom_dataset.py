"""
Script para descargar el dataset 'Food.com Recipes and Interactions' de Kaggle.
"""
import os
import sys
import kaggle
import pandas as pd
import zipfile
from pathlib import Path

# Añadir el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Directorio donde se guardarán los datasets
DATA_DIR = os.path.join(ROOT_DIR, "data")
DATASET_NAME = "shuyangli94/food-com-recipes-and-user-interactions"

def setup_directories():
    """Crea los directorios necesarios si no existen."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "raw"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "processed"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "datasets", "foodcom"), exist_ok=True)
    print(f"✅ Directorios creados en {DATA_DIR}")

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

def download_foodcom_dataset():
    """Descarga el dataset Food.com Recipes and Interactions."""
    try:
        print(f"Descargando dataset: {DATASET_NAME}")
        
        # Directorio específico para este dataset
        target_dir = os.path.join(DATA_DIR, "datasets", "foodcom")
        
        # Descargar el dataset
        kaggle.api.dataset_download_files(
            DATASET_NAME, 
            path=target_dir,
            unzip=True
        )
        
        print(f"✅ Dataset Food.com descargado exitosamente en {target_dir}")
        
        # Listar archivos descargados
        print("\nArchivos descargados:")
        for file in os.listdir(target_dir):
            file_path = os.path.join(target_dir, file)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"- {file} ({size_mb:.2f} MB)")
        
        return True
    except Exception as e:
        print(f"❌ Error descargando dataset Food.com: {str(e)}")
        return False

def process_recipe_data():
    """Procesa los datos de recetas para integrarlos con el sistema NutriVeci."""
    try:
        # Directorios de archivos
        foodcom_dir = os.path.join(DATA_DIR, "datasets", "foodcom")
        processed_dir = os.path.join(DATA_DIR, "processed")
        
        # Verificar si existen los archivos esperados
        recipes_path = os.path.join(foodcom_dir, "RAW_recipes.csv")
        interactions_path = os.path.join(foodcom_dir, "RAW_interactions.csv")
        
        if not os.path.exists(recipes_path) or not os.path.exists(interactions_path):
            print("❌ Archivos de recetas no encontrados. Asegúrate de que el dataset se descargó correctamente.")
            return False
        
        # Cargar datos
        print("Cargando datos de recetas...")
        recipes_df = pd.read_csv(recipes_path)
        
        # Información básica
        print(f"\nInformación del dataset de recetas:")
        print(f"- Total de recetas: {len(recipes_df)}")
        print(f"- Columnas disponibles: {', '.join(recipes_df.columns)}")
        
        # Procesar para NutriVeci (simplificar para uso inicial)
        print("\nProcesando datos para integración con NutriVeci...")
        
        # Seleccionar columnas relevantes
        simplified_recipes = recipes_df[['id', 'name', 'description', 'ingredients', 'steps', 'nutrition']]
        simplified_recipes.rename(columns={'id': 'recipe_id'}, inplace=True)
        
        # Guardar versión procesada
        processed_path = os.path.join(processed_dir, "foodcom_recipes.csv")
        simplified_recipes.to_csv(processed_path, index=False)
        
        print(f"✅ Datos procesados guardados en {processed_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error procesando datos de recetas: {str(e)}")
        return False

def main():
    """Función principal que ejecuta el proceso completo."""
    print("=== Descargando dataset Food.com Recipes and Interactions ===\n")
    
    # Crear directorios
    setup_directories()
    
    # Autenticar con Kaggle
    if not authenticate_kaggle():
        print("\n❌ No se pudo autenticar con Kaggle. Proceso detenido.")
        return
    
    # Descargar dataset
    if not download_foodcom_dataset():
        print("\n❌ Error al descargar el dataset. Proceso detenido.")
        return
    
    # Procesar datos
    if not process_recipe_data():
        print("\n❌ Error al procesar los datos. Proceso detenido.")
        return
    
    print("\n✅ Proceso completado exitosamente!")
    print("El dataset Food.com Recipes and Interactions está listo para ser utilizado.")
    print("Los datos procesados están disponibles en data/processed/foodcom_recipes.csv")

if __name__ == "__main__":
    main() 