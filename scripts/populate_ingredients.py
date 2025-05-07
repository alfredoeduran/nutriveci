"""
Script para poblar la base de datos con datos iniciales de ingredientes.
Este script carga un conjunto básico de ingredientes comunes organizados por categorías.
"""

import json
import os
import sys
import asyncio
from uuid import UUID
from typing import Dict, List

# Agregar el directorio raíz al path para poder importar desde backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.models import IngredientCreate
from backend.db import crud
from backend.db.categories import IngredientCategory, REGIONS, PriceCategory, get_nutritional_profile


# Datos de ingredientes básicos organizados por categoría
BASIC_INGREDIENTS = {
    IngredientCategory.FRUTAS.value: [
        {"name": "Manzana", "seasonal": True, "price_category": PriceCategory.BAJO.value, "region": ["local"]},
        {"name": "Plátano", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["latinoamericana"]},
        {"name": "Naranja", "seasonal": True, "price_category": PriceCategory.BAJO.value, "region": ["local", "mediterránea"]},
        {"name": "Fresa", "seasonal": True, "price_category": PriceCategory.MEDIO.value, "region": ["local"]},
        {"name": "Mango", "seasonal": True, "price_category": PriceCategory.MEDIO.value, "region": ["latinoamericana", "asiática"]}
    ],
    IngredientCategory.VERDURAS.value: [
        {"name": "Zanahoria", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["local"]},
        {"name": "Brócoli", "seasonal": True, "price_category": PriceCategory.BAJO.value, "region": ["local", "europea"]},
        {"name": "Cebolla", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["local", "internacional"]},
        {"name": "Tomate", "seasonal": True, "price_category": PriceCategory.BAJO.value, "region": ["local", "mediterránea"]},
        {"name": "Espinaca", "seasonal": True, "price_category": PriceCategory.BAJO.value, "region": ["local", "europea"]}
    ],
    IngredientCategory.CARNES.value: [
        {"name": "Pollo", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["internacional"]},
        {"name": "Carne molida", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["local"]},
        {"name": "Atún", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["internacional"]},
        {"name": "Salmón", "seasonal": True, "price_category": PriceCategory.ALTO.value, "region": ["europea", "norteamericana"]},
        {"name": "Cerdo", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["local", "europea"]}
    ],
    IngredientCategory.LACTEOS.value: [
        {"name": "Leche", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["local"]},
        {"name": "Queso", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["local", "europea"]},
        {"name": "Yogur", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["local", "internacional"]},
        {"name": "Crema", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["local"]},
        {"name": "Mantequilla", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["local", "europea"]}
    ],
    IngredientCategory.GRANOS.value: [
        {"name": "Arroz", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["local", "asiática"]},
        {"name": "Quinoa", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["latinoamericana"]},
        {"name": "Avena", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["local", "europea"]},
        {"name": "Pasta", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["mediterránea", "europea"]},
        {"name": "Maíz", "seasonal": True, "price_category": PriceCategory.BAJO.value, "region": ["local", "latinoamericana"]}
    ],
    IngredientCategory.LEGUMBRES.value: [
        {"name": "Frijoles negros", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["latinoamericana"]},
        {"name": "Lentejas", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["mediterránea", "medio_oriente"]},
        {"name": "Garbanzos", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["mediterránea", "medio_oriente"]},
        {"name": "Soya", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["asiática"]},
        {"name": "Guisantes", "seasonal": True, "price_category": PriceCategory.BAJO.value, "region": ["local", "europea"]}
    ],
    IngredientCategory.ACEITES.value: [
        {"name": "Aceite de oliva", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["mediterránea"]},
        {"name": "Aceite de coco", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["asiática", "caribeña"]},
        {"name": "Aceite vegetal", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["local", "internacional"]}
    ],
    IngredientCategory.FRUTOS_SECOS.value: [
        {"name": "Almendras", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["mediterránea"]},
        {"name": "Nueces", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["norteamericana", "europea"]},
        {"name": "Semillas de chía", "seasonal": False, "price_category": PriceCategory.MEDIO.value, "region": ["latinoamericana"]}
    ],
    IngredientCategory.CONDIMENTOS.value: [
        {"name": "Sal", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["internacional"]},
        {"name": "Pimienta", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["internacional"]},
        {"name": "Oregano", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["mediterránea"]},
        {"name": "Canela", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["medio_oriente", "asiática"]},
        {"name": "Chile", "seasonal": False, "price_category": PriceCategory.BAJO.value, "region": ["latinoamericana"]}
    ]
}


async def create_ingredient_record(category: str, data: Dict) -> UUID:
    """
    Crear un registro de ingrediente en la base de datos
    
    Args:
        category: Categoría del ingrediente
        data: Datos adicionales del ingrediente
        
    Returns:
        UUID: ID del ingrediente creado
    """
    # Obtener perfil nutricional aproximado basado en la categoría
    nutritional_value = get_nutritional_profile(category)
    
    # Crear objeto de ingrediente
    ingredient_data = IngredientCreate(
        name=data["name"],
        category=category,
        seasonal=data.get("seasonal", False),
        price_category=data.get("price_category", PriceCategory.MEDIO.value),
        region=data.get("region", ["local"]),
        nutritional_value=nutritional_value
    )
    
    # Crear ingrediente en la base de datos
    try:
        ingredient = await crud.create_ingredient(ingredient_data)
        print(f"✅ Ingrediente creado: {data['name']} ({category})")
        return ingredient.id
    except Exception as e:
        print(f"❌ Error al crear ingrediente {data['name']}: {str(e)}")
        return None


async def populate_ingredients():
    """Poblar la base de datos con ingredientes iniciales"""
    print("🔄 Iniciando población de ingredientes...")
    
    # Contadores para estadísticas
    total = 0
    success = 0
    errors = 0
    
    # Iterar sobre cada categoría
    for category, ingredients in BASIC_INGREDIENTS.items():
        print(f"\n📋 Procesando categoría: {category}")
        
        # Iterar sobre cada ingrediente en la categoría
        for ingredient_data in ingredients:
            total += 1
            result = await create_ingredient_record(category, ingredient_data)
            if result:
                success += 1
            else:
                errors += 1
    
    # Imprimir estadísticas
    print(f"\n📊 Resumen:")
    print(f"   Total de ingredientes procesados: {total}")
    print(f"   Ingredientes creados exitosamente: {success}")
    print(f"   Errores: {errors}")
    print("\n✅ Proceso de población de ingredientes completado.")


if __name__ == "__main__":
    asyncio.run(populate_ingredients()) 