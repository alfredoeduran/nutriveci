"""
Operaciones de base de datos relacionadas con recetas.
"""
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from backend.db.supabase import get_supabase_client, query_table


async def create_recipe(name: str, description: str) -> Dict[str, Any]:
    """
    Crea una nueva receta en la base de datos.
    
    Args:
        name: Nombre de la receta
        description: Descripción de la receta
        
    Returns:
        Datos de la receta creada
    """
    supabase = get_supabase_client()
    
    recipe_data = {
        "name": name,
        "description": description,
        "created_at": datetime.now().isoformat()
    }
    
    response = supabase.table("recipes").insert(recipe_data).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    
    return {}


async def add_ingredient_to_recipe(recipe_id: str, ingredient_name: str, quantity: str) -> bool:
    """
    Añade un ingrediente a una receta existente.
    Si el ingrediente no existe, lo crea primero.
    
    Args:
        recipe_id: ID de la receta
        ingredient_name: Nombre del ingrediente
        quantity: Cantidad del ingrediente (ej: "2 cucharadas")
        
    Returns:
        True si se agregó correctamente, False en caso contrario
    """
    supabase = get_supabase_client()
    
    # Buscar si el ingrediente ya existe
    ingredient_response = supabase.table("ingredients").select("*").eq("name", ingredient_name).execute()
    
    ingredient_id = None
    
    if ingredient_response.data and len(ingredient_response.data) > 0:
        # El ingrediente ya existe
        ingredient_id = ingredient_response.data[0]["id"]
    else:
        # Crear nuevo ingrediente
        new_ingredient = {
            "name": ingredient_name,
            "description": f"Ingrediente: {ingredient_name}"
        }
        create_response = supabase.table("ingredients").insert(new_ingredient).execute()
        if create_response.data and len(create_response.data) > 0:
            ingredient_id = create_response.data[0]["id"]
    
    if not ingredient_id:
        return False
    
    # Agregar relación receta-ingrediente
    relation_data = {
        "recipe_id": recipe_id,
        "ingredient_id": ingredient_id,
        "quantity": quantity
    }
    
    relation_response = supabase.table("recipe_ingredients").insert(relation_data).execute()
    
    return bool(relation_response.data)


async def get_recipe_by_id(recipe_id: str) -> Dict[str, Any]:
    """
    Obtiene una receta por su ID con todos sus ingredientes.
    
    Args:
        recipe_id: ID de la receta
        
    Returns:
        Datos de la receta con sus ingredientes
    """
    supabase = get_supabase_client()
    
    # Obtener información básica de la receta
    recipe_response = supabase.table("recipes").select("*").eq("id", recipe_id).execute()
    
    if not recipe_response.data or len(recipe_response.data) == 0:
        return {}
    
    recipe = recipe_response.data[0]
    
    # Obtener ingredientes de la receta
    query = f"""
    recipe_ingredients(quantity, ingredients(id, name, description))
    """
    
    ingredients_response = supabase.table("recipes").select(query).eq("id", recipe_id).execute()
    
    if ingredients_response.data and len(ingredients_response.data) > 0:
        recipe["ingredients"] = []
        
        for rel in ingredients_response.data[0].get("recipe_ingredients", []):
            if "ingredients" in rel and rel["ingredients"]:
                ingredient = rel["ingredients"]
                ingredient["quantity"] = rel["quantity"]
                recipe["ingredients"].append(ingredient)
    
    return recipe


async def get_user_recipes(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Obtiene las recetas que ha consultado un usuario.
    
    Args:
        user_id: ID del usuario
        limit: Número máximo de recetas a devolver
        
    Returns:
        Lista de recetas del usuario
    """
    supabase = get_supabase_client()
    
    # Buscar en recipe_history las recetas del usuario
    query = f"""
    recipe_id, requested_at, source,
    recipes(id, name, description)
    """
    
    response = supabase.table("recipe_history").select(query)\
        .eq("user_id", user_id)\
        .order("requested_at", ascending=False)\
        .limit(limit)\
        .execute()
    
    recipes = []
    if response.data:
        for entry in response.data:
            if "recipes" in entry and entry["recipes"]:
                recipe = entry["recipes"]
                recipe["requested_at"] = entry["requested_at"]
                recipe["source"] = entry["source"]
                recipes.append(recipe)
    
    return recipes


async def add_recipe_to_history(user_id: str, recipe_id: str, source: str = "user_created") -> bool:
    """
    Registra que un usuario ha interactuado con una receta.
    
    Args:
        user_id: ID del usuario
        recipe_id: ID de la receta
        source: Origen de la interacción
        
    Returns:
        True si se registró correctamente
    """
    supabase = get_supabase_client()
    
    history_data = {
        "user_id": user_id,
        "recipe_id": recipe_id,
        "requested_at": datetime.now().isoformat(),
        "source": source
    }
    
    response = supabase.table("recipe_history").insert(history_data).execute()
    
    return bool(response.data)


async def search_recipes(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Busca recetas por nombre o descripción.
    
    Args:
        query: Texto a buscar
        limit: Número máximo de resultados
        
    Returns:
        Lista de recetas que coinciden con la búsqueda
    """
    supabase = get_supabase_client()
    
    # Búsqueda básica por nombre (para una búsqueda más avanzada se necesitaría
    # configurar búsqueda de texto completo en Supabase)
    response = supabase.table("recipes").select("*")\
        .ilike("name", f"%{query}%")\
        .limit(limit)\
        .execute()
    
    return response.data if response.data else [] 