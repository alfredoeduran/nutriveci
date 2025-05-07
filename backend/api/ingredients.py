from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from uuid import UUID

from backend.db.models import Ingredient, IngredientCreate
from backend.db import crud
from backend.api.auth import get_current_user
from backend.db.categories import get_category_hierarchy, get_subcategories, validate_category

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.post("/", response_model=Ingredient, status_code=status.HTTP_201_CREATED)
async def create_ingredient(
    ingredient: IngredientCreate,
    current_user=Depends(get_current_user)
):
    """
    Crear un nuevo ingrediente en el sistema.
    Solo usuarios autenticados pueden crear ingredientes.
    """
    # Validar que la categoría existe
    if not validate_category(ingredient.category):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría '{ingredient.category}' no válida"
        )
    
    return await crud.create_ingredient(ingredient)


@router.get("/{ingredient_id}", response_model=Ingredient)
async def get_ingredient(ingredient_id: UUID):
    """
    Obtener un ingrediente específico por su ID.
    """
    ingredient = await crud.get_ingredient(ingredient_id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingrediente con ID {ingredient_id} no encontrado"
        )
    return ingredient


@router.get("/", response_model=List[Ingredient])
async def list_ingredients(
    category: Optional[str] = None,
    seasonal: Optional[bool] = None,
    price_category: Optional[str] = None,
    region: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Listar ingredientes con filtros opcionales.
    """
    # Validar categoría si se proporciona
    if category and not validate_category(category):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría '{category}' no válida"
        )
        
    filters = {}
    if category:
        filters["category"] = category
    if seasonal is not None:
        filters["seasonal"] = seasonal
    if price_category:
        filters["price_category"] = price_category
    if region:
        filters["region"] = region
        
    return await crud.list_ingredients(filters, skip, limit)


@router.put("/{ingredient_id}", response_model=Ingredient)
async def update_ingredient(
    ingredient_id: UUID,
    ingredient_data: IngredientCreate,
    current_user=Depends(get_current_user)
):
    """
    Actualizar información de un ingrediente existente.
    Solo usuarios autenticados pueden actualizar ingredientes.
    """
    # Validar que la categoría existe
    if not validate_category(ingredient_data.category):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría '{ingredient_data.category}' no válida"
        )
    
    existing_ingredient = await crud.get_ingredient(ingredient_id)
    if not existing_ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingrediente con ID {ingredient_id} no encontrado"
        )
    
    return await crud.update_ingredient(ingredient_id, ingredient_data.dict())


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(
    ingredient_id: UUID,
    current_user=Depends(get_current_user)
):
    """
    Eliminar un ingrediente del sistema.
    Solo usuarios autenticados pueden eliminar ingredientes.
    """
    existing_ingredient = await crud.get_ingredient(ingredient_id)
    if not existing_ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingrediente con ID {ingredient_id} no encontrado"
        )
    
    await crud.delete_ingredient(ingredient_id)
    return None


@router.get("/search/", response_model=List[Ingredient])
async def search_ingredients(query: str, limit: int = 10):
    """
    Buscar ingredientes por nombre o propiedades.
    """
    return await crud.search_ingredients(query, limit)


@router.get("/categories/", response_model=Dict)
async def get_categories():
    """
    Obtener todas las categorías y subcategorías disponibles para ingredientes.
    """
    return get_category_hierarchy()


@router.get("/categories/{category}/subcategories", response_model=List[str])
async def get_category_subcategories(category: str):
    """
    Obtener todas las subcategorías de una categoría específica.
    """
    if not validate_category(category):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría '{category}' no encontrada"
        )
    
    subcategories = get_subcategories(category)
    if not subcategories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron subcategorías para la categoría '{category}'"
        )
    
    return subcategories 