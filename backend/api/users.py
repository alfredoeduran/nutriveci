from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.core.config import get_settings
from backend.db import crud
from backend.db.models import (
    DietaryProfile,
    DietaryProfileCreate,
    User, 
    UserCreate,
    UserPreference,
    UserPreferenceCreate,
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "No encontrado"}},
)

# Esquema de seguridad OAuth2 (implementación básica)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    Crear un nuevo usuario.
    
    - **name**: Nombre del usuario
    - **telegram_id**: ID único de Telegram (opcional)
    - **web_id**: ID único para usuarios web (opcional)
    - **age**: Edad del usuario (opcional)
    - **weight**: Peso en kg (opcional)
    - **height**: Altura en cm (opcional)
    - **household_size**: Tamaño del hogar (opcional)
    - **budget**: Presupuesto disponible (opcional)
    - **restrictions**: Lista de restricciones alimenticias (opcional)
    - **location**: Ubicación/región (opcional)
    """
    created_user = await crud.create_user(user)
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo crear el usuario",
        )
    return created_user


@router.get("/{user_id}", response_model=User)
async def read_user(user_id: UUID):
    """
    Obtener información de un usuario por su ID.
    """
    user = await crud.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado",
        )
    return user


@router.get("/{user_id}/recipes")
async def get_user_recipes(user_id: UUID):
    """
    Obtener todas las recetas asociadas a un usuario.
    """
    user = await crud.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {user_id} no encontrado")
    recetas = await crud.get_recipes_by_user(user_id)
    # Si tienes un modelo RecipeRead, conviértelo aquí
    if recetas:
        try:
            from backend.schemas.recipes import RecipeRead
            return [RecipeRead.from_orm(r) for r in recetas]
        except Exception:
            return recetas
    return []


@router.get("/telegram/{telegram_id}", response_model=User)
async def read_user_by_telegram(telegram_id: str):
    """
    Obtener un usuario por su ID de Telegram.
    """
    user = await crud.get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID de Telegram {telegram_id} no encontrado",
        )
    return user


@router.patch("/{user_id}", response_model=User)
async def update_user_info(
    user_id: UUID,
    name: Optional[str] = None,
    age: Optional[int] = None,
    weight: Optional[float] = None,
    height: Optional[float] = None,
    household_size: Optional[int] = None,
    budget: Optional[float] = None,
    location: Optional[str] = None,
):
    """
    Actualizar información del usuario.
    """
    # Construir diccionario con los campos no nulos
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if age is not None:
        update_data["age"] = age
    if weight is not None:
        update_data["weight"] = weight
    if height is not None:
        update_data["height"] = height
    if household_size is not None:
        update_data["household_size"] = household_size
    if budget is not None:
        update_data["budget"] = budget
    if location is not None:
        update_data["location"] = location
    
    # Actualizar solo si hay datos para actualizar
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron datos para actualizar",
        )
    
    updated_user = await crud.update_user(user_id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado",
        )
    
    return updated_user 


@router.post("/{user_id}/preferences", response_model=UserPreference)
async def create_user_preferences(user_id: UUID, preferences: UserPreferenceCreate):
    """
    Crear o actualizar preferencias de un usuario.
    
    - **favorite_foods**: Lista de alimentos favoritos
    - **disliked_foods**: Lista de alimentos que no le gustan
    - **preferred_cuisines**: Tipos de cocina preferidos
    - **cooking_skill_level**: Nivel de habilidad para cocinar
    - **meal_planning_frequency**: Frecuencia de planificación de comidas
    - **cooking_frequency**: Frecuencia con la que cocina
    """
    # Verificar que el usuario existe
    user = await crud.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado",
        )
    
    # Asegurarnos que el user_id en la ruta coincide con el de los datos
    preferences_data = preferences.dict()
    preferences_data["user_id"] = user_id
    
    created_preferences = await crud.create_user_preference(UserPreferenceCreate(**preferences_data))
    if not created_preferences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudieron crear las preferencias",
        )
    return created_preferences


@router.get("/{user_id}/preferences", response_model=UserPreference)
async def get_user_preferences(user_id: UUID):
    """
    Obtener las preferencias de un usuario.
    """
    preferences = await crud.get_user_preference(user_id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron preferencias para el usuario con ID {user_id}",
        )
    return preferences


@router.patch("/{user_id}/preferences", response_model=UserPreference)
async def update_user_preferences(user_id: UUID, preferences: Dict):
    """
    Actualizar preferencias de un usuario.
    
    Se pueden actualizar uno o más campos.
    """
    updated_preferences = await crud.update_user_preference(user_id, preferences)
    if not updated_preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron preferencias para el usuario con ID {user_id}",
        )
    return updated_preferences


@router.post("/{user_id}/dietary-profile", response_model=DietaryProfile)
async def create_user_dietary_profile(user_id: UUID, profile: DietaryProfileCreate):
    """
    Crear o actualizar el perfil dietético de un usuario.
    
    - **diet_type**: Tipo de dieta (vegetariana, vegana, etc.)
    - **allergens**: Lista de alérgenos
    - **intolerances**: Lista de intolerancias alimentarias
    - **medical_conditions**: Condiciones médicas que afectan la dieta
    - **diet_goals**: Objetivos dietéticos
    - **nutritional_requirements**: Requisitos nutricionales específicos
    """
    # Verificar que el usuario existe
    user = await crud.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado",
        )
    
    # Asegurarnos que el user_id en la ruta coincide con el de los datos
    profile_data = profile.dict()
    profile_data["user_id"] = user_id
    
    created_profile = await crud.create_dietary_profile(DietaryProfileCreate(**profile_data))
    if not created_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo crear el perfil dietético",
        )
    return created_profile


@router.get("/{user_id}/dietary-profile", response_model=DietaryProfile)
async def get_user_dietary_profile(user_id: UUID):
    """
    Obtener el perfil dietético de un usuario.
    """
    profile = await crud.get_dietary_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró perfil dietético para el usuario con ID {user_id}",
        )
    return profile


@router.patch("/{user_id}/dietary-profile", response_model=DietaryProfile)
async def update_user_dietary_profile(user_id: UUID, profile: Dict):
    """
    Actualizar el perfil dietético de un usuario.
    
    Se pueden actualizar uno o más campos.
    """
    updated_profile = await crud.update_dietary_profile(user_id, profile)
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró perfil dietético para el usuario con ID {user_id}",
        )
    return updated_profile 