"""
Script para importar recetas de Food.com al sistema de Supabase de NutriVeci.
"""
import os
import sys
import json
import pandas as pd
import ast
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import time
from dotenv import load_dotenv

# Añadir el directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from backend.db.supabase import get_supabase_client
from backend.db.recipes import create_recipe, add_ingredient_to_recipe

# Directorio donde están guardados los datasets
DATA_DIR = os.path.join(ROOT_DIR, "data")
PROCESSED_RECIPES_PATH = os.path.join(DATA_DIR, "processed", "foodcom_recipes.csv")

# Verificar y configurar variables de entorno para Supabase
if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
    # Cargar variables de entorno desde .env si no están ya cargadas
    load_dotenv()

def load_recipe_data():
    """Carga los datos procesados de recetas de Food.com."""
    try:
        if not os.path.exists(PROCESSED_RECIPES_PATH):
            print(f"❌ No se encontró el archivo de recetas procesadas en {PROCESSED_RECIPES_PATH}")
            print("Primero ejecuta el script download_foodcom_dataset.py para descargar y procesar los datos.")
            return None
            
        print(f"Cargando recetas procesadas desde {PROCESSED_RECIPES_PATH}...")
        recipes_df = pd.read_csv(PROCESSED_RECIPES_PATH)
        print(f"✅ Se cargaron {len(recipes_df)} recetas correctamente")
        return recipes_df
    except Exception as e:
        print(f"❌ Error al cargar las recetas: {str(e)}")
        return None

def extract_ingredients_from_recipe(ingredients_str):
    """Extrae los ingredientes desde la cadena de texto almacenada en el dataframe."""
    try:
        # La cadena viene en formato de lista de Python como texto
        ingredients_list = ast.literal_eval(ingredients_str)
        return ingredients_list
    except:
        # Si hay un error en el formato, devolvemos una lista vacía
        print(f"⚠️ Error al procesar ingredientes: {ingredients_str[:50]}...")
        return []

def parse_nutrition_info(nutrition_str):
    """Extrae la información nutricional desde la cadena de texto."""
    try:
        # El formato es como: [Calorías, Total grasas, Azúcar, Sodio, Proteína, Grasas saturadas, Carbohidratos]
        nutrition_values = ast.literal_eval(nutrition_str)
        return {
            "calories": nutrition_values[0],
            "fat": nutrition_values[1], 
            "sugar": nutrition_values[2],
            "sodium": nutrition_values[3],
            "protein": nutrition_values[4],
            "saturated_fat": nutrition_values[5],
            "carbs": nutrition_values[6]
        }
    except:
        print(f"⚠️ Error al procesar información nutricional: {nutrition_str[:50]}...")
        return {}

async def import_recipes_to_supabase(recipes_df, limit=100):
    """Importa las recetas a Supabase para usarlas en NutriVeci."""
    try:
        print(f"Importando {min(limit, len(recipes_df))} recetas a Supabase...")
        
        # Inicializar contador de éxitos
        successful_imports = 0
        
        # Tomar una muestra aleatoria para importar (para evitar sesgo)
        if limit < len(recipes_df):
            sample_df = recipes_df.sample(n=limit)
        else:
            sample_df = recipes_df
            
        # Para cada receta en la muestra
        for idx, row in tqdm(sample_df.iterrows(), total=len(sample_df)):
            try:
                # Extraer datos básicos
                recipe_name = row['name']
                recipe_desc = row['description'] if isinstance(row['description'], str) else "Sin descripción"
                
                # Crear la receta con reintentos
                max_retries = 3
                retry_count = 0
                recipe_data = None
                
                while retry_count < max_retries:
                    try:
                        recipe_data = await create_recipe(recipe_name, recipe_desc)
                        break
                    except Exception as e:
                        retry_count += 1
                        if "proxy" in str(e):
                            print(f"⚠️ Error de proxy al crear receta. Reintentando ({retry_count}/{max_retries})...")
                            time.sleep(1)
                        else:
                            raise e
                
                if not recipe_data or 'id' not in recipe_data:
                    print(f"⚠️ No se pudo crear la receta {recipe_name}")
                    continue
                
                recipe_id = recipe_data['id']
                
                # Procesar ingredientes
                ingredients = extract_ingredients_from_recipe(row['ingredients'])
                for ingredient in ingredients:
                    # Separar cantidad y unidad si es posible
                    parts = ingredient.split(" ")
                    if len(parts) > 1 and parts[0].replace('.', '', 1).isdigit():
                        quantity = f"{parts[0]} {parts[1]}"
                        ingredient_name = " ".join(parts[2:])
                    else:
                        quantity = "Al gusto"
                        ingredient_name = ingredient
                    
                    # Agregar ingrediente a la receta con reintentos
                    retry_count = 0
                    ingredient_added = False
                    
                    while retry_count < max_retries and not ingredient_added:
                        try:
                            ingredient_added = await add_ingredient_to_recipe(recipe_id, ingredient_name, quantity)
                            break
                        except Exception as e:
                            retry_count += 1
                            if "proxy" in str(e):
                                print(f"⚠️ Error de proxy al agregar ingrediente. Reintentando ({retry_count}/{max_retries})...")
                                time.sleep(1)
                            else:
                                raise e
                
                # Incrementar contador de éxitos
                successful_imports += 1
                
                # Pequeña pausa para no sobrecargar la API
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error importando receta {row['name']}: {str(e)}")
                continue
        
        print(f"\n✅ Importación completada: {successful_imports} recetas importadas correctamente")
        return successful_imports
    
    except Exception as e:
        print(f"❌ Error general en la importación: {str(e)}")
        return 0

async def main():
    """Función principal para ejecutar la importación de recetas."""
    print("=== Importando recetas de Food.com a Supabase ===\n")
    
    # Verificar la conexión con Supabase
    try:
        print("Verificando conexión con Supabase...")
        client = get_supabase_client()
        # Intentar una consulta simple para verificar la conexión
        test_response = client.table("recipes").select("count", count="exact").execute()
        count = test_response.count if hasattr(test_response, "count") else "desconocido"
        print(f"✅ Conexión con Supabase establecida. Recetas en la base de datos: {count}")
    except Exception as e:
        print(f"❌ Error de conexión con Supabase: {str(e)}")
        print("Verifica tus variables de entorno SUPABASE_URL y SUPABASE_KEY.")
        return
    
    # Cargar datos
    recipes_df = load_recipe_data()
    if recipes_df is None:
        return
    
    # Solicitar límite
    try:
        limit_str = input("\nIngrese el número de recetas a importar (recomendado: 10-50, deje en blanco para usar 20): ")
        limit = int(limit_str) if limit_str.strip() else 20
    except ValueError:
        print("Valor inválido, usando valor predeterminado de 20")
        limit = 20
    
    print(f"\nImportando {limit} recetas. Esto puede tomar unos minutos...")
    
    # Importar recetas
    import_count = await import_recipes_to_supabase(recipes_df, limit)
    
    if import_count > 0:
        print("\n🎉 Importación exitosa!")
        print(f"Se importaron {import_count} recetas de Food.com a la base de datos de NutriVeci.")
        print("Ahora puedes ver estas recetas en el bot de Telegram utilizando la opción 'Mis recetas'.")
    else:
        print("\n❌ La importación no fue exitosa. Revisa los errores anteriores.")
        print("Posibles soluciones:")
        print("1. Verifica que las variables de entorno SUPABASE_URL y SUPABASE_KEY sean correctas")
        print("2. Revisa la conexión a internet")
        print("3. Reduce el número de recetas a importar")
        print("4. Verifica que las tablas necesarias existan en Supabase: recipes, ingredients, recipe_ingredients")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 