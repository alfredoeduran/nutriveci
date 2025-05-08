from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.db import crud
from backend.schemas.recipes import (
    RecipeCreate,
    RecipeRead,
    RecipeUpdate
    # RecipeReadWithIngredients # Podríamos usar este si quisiéramos devolver ingredientes
)
# Dependencias de autenticación (si son necesarias, añadirlas)
# from backend.api.dependencies import get_current_user
# from backend.db.models import User

router = APIRouter(
    prefix="/recipes",
    tags=["recipes"],
    # dependencies=[Depends(get_current_user)], # Descomentar si se requiere autenticación
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def create_recipe_endpoint(recipe_in: RecipeCreate):
    """Crea una nueva receta."""
    recipe = await crud.create_recipe(recipe_data=recipe_in)
    if not recipe:
        raise HTTPException(status_code=400, detail="Error al crear la receta")
    # Convertir el modelo de DB a RecipeRead (si crud.create_recipe devuelve Recipe)
    # Si crud.create_recipe ya devolviera RecipeRead, no haría falta
    # Esto asume que los campos coinciden o se pueden mapear directamente
    return RecipeRead.from_orm(recipe) 


@router.get("/", response_model=List[RecipeRead])
async def list_recipes_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """Lista todas las recetas con paginación."""
    recipes_db = await crud.list_recipes(skip=skip, limit=limit)
    # Convertir lista de modelos de DB a lista de RecipeRead
    return [RecipeRead.from_orm(recipe) for recipe in recipes_db]


@router.get("/{recipe_id}", response_model=RecipeRead)
async def get_recipe_endpoint(recipe_id: UUID):
    """Obtiene una receta específica por su ID."""
    recipe = await crud.get_recipe(recipe_id=recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    return RecipeRead.from_orm(recipe)


@router.put("/{recipe_id}", response_model=RecipeRead)
async def update_recipe_endpoint(recipe_id: UUID, recipe_in: RecipeUpdate):
    """Actualiza una receta existente."""
    existing_recipe = await crud.get_recipe(recipe_id=recipe_id)
    if not existing_recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    
    updated_recipe = await crud.update_recipe(recipe_id=recipe_id, recipe_data=recipe_in)
    if not updated_recipe:
        # Esto podría ocurrir si la actualización falla por alguna razón
        raise HTTPException(status_code=400, detail="Error al actualizar la receta")
    return RecipeRead.from_orm(updated_recipe)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe_endpoint(recipe_id: UUID):
    """Elimina una receta."""
    existing_recipe = await crud.get_recipe(recipe_id=recipe_id)
    if not existing_recipe:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
        
    deleted = await crud.delete_recipe(recipe_id=recipe_id)
    if not deleted:
        # Considerar un manejo de error más específico si delete_recipe puede fallar
        raise HTTPException(status_code=500, detail="Error al eliminar la receta")
    # No se retorna contenido en un DELETE exitoso
    return


@router.get("/recommended", response_model=List[RecipeRead])
async def get_recommended_recipes_endpoint(
    user_id: UUID,
    count: int = Query(5, ge=1, le=20),
    filter_by_profile: bool = Query(True)
):
    """
    Obtiene recetas recomendadas para un usuario específico basado en su historial
    y perfil (edad, peso, género, condiciones médicas, alergias, etc.)
    """
    from backend.ai.recommendation import get_recommender
    
    # Obtener el recomendador inicializado
    recommender = get_recommender()
    
    # Obtener recomendaciones personalizadas
    recommended_recipes = recommender.recommend_recipes(
        user_id=str(user_id),
        n=count,
        filter_by_profile=filter_by_profile
    )
    
    if not recommended_recipes:
        # Si no hay recomendaciones específicas, devolver algunas recetas aleatorias
        recipes_db = await crud.list_recipes(skip=0, limit=count)
        return [RecipeRead.from_orm(recipe) for recipe in recipes_db]
    
    # Convertir IDs de recetas recomendadas a objetos Recipe completos
    recipe_ids = [UUID(r['id'].split('_')[1]) if '_' in r['id'] else UUID(r['id']) 
                 for r in recommended_recipes]
    
    recipes_db = await crud.get_recipes_by_ids(recipe_ids=recipe_ids)
    
    # Mapeamos a RecipeRead y retornamos
    return [RecipeRead.from_orm(recipe) for recipe in recipes_db]
