"""
Script para exportar recetas a CSV para importación manual en Supabase.
"""
import os
import sys
import csv
import json
import pandas as pd
from pathlib import Path
import ast
from datetime import datetime

# Añadir directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Directorios de datos
DATA_DIR = os.path.join(ROOT_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
OUTPUT_DIR = os.path.join(DATA_DIR, "supabase_import")

# Asegurar que existe el directorio de salida
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_ingredients_from_recipe(ingredients_str):
    """Extrae los ingredientes desde la cadena de texto almacenada en el dataframe."""
    try:
        ingredients_list = ast.literal_eval(ingredients_str)
        return ingredients_list
    except:
        print(f"⚠️ Error al procesar ingredientes: {ingredients_str[:50]}...")
        return []

def load_foodcom_recipes(limit=100):
    """Carga recetas de Food.com y las convierte al formato para Supabase."""
    print(f"Cargando datos de recetas de Food.com (limitados a {limit})...")
    
    # Archivo de entrada
    input_file = os.path.join(PROCESSED_DIR, "foodcom_recipes.csv")
    
    if not os.path.exists(input_file):
        print(f"❌ No se encontró el archivo {input_file}")
        return None
    
    # Cargar solo las primeras filas para procesamiento más rápido
    recipes_df = pd.read_csv(input_file, nrows=limit)
    print(f"✅ Se cargaron {len(recipes_df)} recetas correctamente")
    
    return recipes_df

def prepare_recipe_data(recipes_df):
    """Prepara los datos de recetas para el formato CSV de Supabase."""
    # Crear dataframes para cada tabla
    print("Preparando datos para exportación...")
    
    # 1. Tabla de recetas
    recipes_data = []
    ingredients_data = []
    recipe_ingredients_data = []
    
    # Generar un timestamp para todas las recetas
    timestamp = datetime.now().isoformat()
    
    # Procesar cada receta
    for idx, row in recipes_df.iterrows():
        # ID de receta (usamos idx + 1000 para evitar colisiones)
        recipe_id = f"manual-import-{idx + 1000}"
        
        # Datos de la receta
        recipe_name = row['name']
        recipe_desc = row['description'] if isinstance(row['description'], str) else "Sin descripción"
        
        # Agregar a la lista de recetas
        recipes_data.append({
            "id": recipe_id,
            "name": recipe_name,
            "description": recipe_desc,
            "created_at": timestamp
        })
        
        # Procesar ingredientes
        ingredients = extract_ingredients_from_recipe(row['ingredients'])
        
        for ing_idx, ingredient in enumerate(ingredients):
            # Separar cantidad y unidad si es posible
            parts = ingredient.split(" ")
            if len(parts) > 1 and parts[0].replace('.', '', 1).isdigit():
                quantity = f"{parts[0]} {parts[1]}"
                ingredient_name = " ".join(parts[2:])
            else:
                quantity = "Al gusto"
                ingredient_name = ingredient
            
            # ID para el ingrediente
            ingredient_id = f"ing-{recipe_id}-{ing_idx}"
            
            # Agregar a la lista de ingredientes
            ingredients_data.append({
                "id": ingredient_id,
                "name": ingredient_name,
                "description": f"Ingrediente: {ingredient_name}"
            })
            
            # Agregar a la lista de relaciones receta-ingrediente
            recipe_ingredients_data.append({
                "id": f"rel-{recipe_id}-{ing_idx}",
                "recipe_id": recipe_id,
                "ingredient_id": ingredient_id,
                "quantity": quantity
            })
    
    return {
        "recipes": recipes_data,
        "ingredients": ingredients_data,
        "recipe_ingredients": recipe_ingredients_data
    }

def export_to_csv(data_dict):
    """Exporta los datos a archivos CSV para importar en Supabase."""
    print("Exportando datos a archivos CSV...")
    
    for table_name, data in data_dict.items():
        if not data:
            continue
            
        output_file = os.path.join(OUTPUT_DIR, f"{table_name}.csv")
        
        # Escribir CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                print(f"✅ Tabla {table_name}: {len(data)} filas exportadas a {output_file}")
            else:
                print(f"⚠️ No hay datos para la tabla {table_name}")

def print_supabase_sql_schema():
    """Imprime el esquema SQL para las tablas en Supabase."""
    print("\n=== ESTRUCTURA DE TABLAS PARA SUPABASE ===")
    print("""
-- Tabla de recetas
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de ingredientes
CREATE TABLE ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT
);

-- Tabla relacional recetas-ingredientes
CREATE TABLE recipe_ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id UUID REFERENCES ingredients(id) ON DELETE RESTRICT,
    quantity TEXT NOT NULL
);

-- Tabla de historial de recetas
CREATE TABLE recipe_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source TEXT DEFAULT 'user_created'
);
""")

def main():
    """Función principal para ejecutar la exportación."""
    print("=== Exportando recetas a CSV para importación manual en Supabase ===\n")
    
    # Solicitar cantidad de recetas
    try:
        limit_str = input("Ingrese el número de recetas a exportar (recomendado: 20-100, deje en blanco para usar 50): ")
        limit = int(limit_str) if limit_str.strip() else 50
    except ValueError:
        print("Valor inválido, usando valor predeterminado de 50")
        limit = 50
    
    # Cargar y preparar datos
    recipes_df = load_foodcom_recipes(limit=limit)
    if recipes_df is None:
        return
    
    # Preparar datos
    data_dict = prepare_recipe_data(recipes_df)
    
    # Exportar a CSV
    export_to_csv(data_dict)
    
    # Imprimir información sobre estructura SQL
    print_supabase_sql_schema()
    
    print("\n=== INSTRUCCIONES PARA IMPORTAR EN SUPABASE ===")
    print("1. Accede a tu proyecto en Supabase")
    print("2. Ve a la sección 'Table Editor'")
    print("3. Crea las tablas según el esquema SQL mostrado arriba")
    print("4. Para cada tabla, usa la opción 'Import data from CSV'")
    print(f"5. Sube los archivos CSV generados en la carpeta: {OUTPUT_DIR}")
    print("6. Asegúrate de mapear correctamente las columnas durante la importación")
    print("\n¡Listo! Los datos estarán disponibles en Supabase para tu bot NutriVeci")

if __name__ == "__main__":
    main() 