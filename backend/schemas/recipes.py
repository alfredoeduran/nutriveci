from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field

# Schema base que comparte campos comunes
class RecipeBase(BaseModel):
    name: str = Field(..., example="Ensalada César")
    description: Optional[str] = Field(None, example="Una clásica ensalada César con pollo a la parrilla.")
    preparation_steps: List[str] = Field(..., example=["Lavar lechuga", "Cortar pollo", "Mezclar aderezo"])
    cooking_time: Optional[int] = Field(None, example=30, description="Tiempo de cocción en minutos")
    difficulty: Optional[str] = Field(None, example="Fácil")
    servings: Optional[int] = Field(None, example=2)
    tags: Optional[List[str]] = Field(default_factory=list, example=["ensalada", "pollo", "clásico"])
    nutritional_info: Optional[Dict] = Field(default_factory=dict, example={"calorías": 550, "proteínas": "30g"})
    estimated_cost: Optional[float] = Field(None, example=8.50)
    image_url: Optional[str] = Field(None, example="https://example.com/images/ensalada_cesar.jpg")
    healthy_score: Optional[int] = Field(None, ge=0, le=100, example=85)

# Schema para la creación de recetas (lo que recibe la API)
class RecipeCreate(RecipeBase):
    # Hereda todos los campos de RecipeBase
    # Podríamos añadir campos específicos de creación si fuera necesario
    pass

# Schema para la actualización de recetas (campos opcionales)
class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    preparation_steps: Optional[List[str]] = None
    cooking_time: Optional[int] = None
    difficulty: Optional[str] = None
    servings: Optional[int] = None
    tags: Optional[List[str]] = None
    nutritional_info: Optional[Dict] = None
    estimated_cost: Optional[float] = None
    image_url: Optional[str] = None
    healthy_score: Optional[int] = None

# Schema para la lectura de recetas (lo que devuelve la API)
class RecipeRead(RecipeBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True # Permite mapear desde modelos ORM/DB

# --- Schemas para Ingredientes de Receta (si se manejan anidados) ---

class RecipeIngredientBase(BaseModel):
    ingredient_id: UUID
    quantity: float
    unit: str = Field(..., example="gramos")

class RecipeIngredientCreate(RecipeIngredientBase):
     # No necesita recipe_id aquí si se crea junto con la receta
     pass

class RecipeIngredientRead(RecipeIngredientBase):
    id: UUID
    # Podría incluir el nombre del ingrediente aquí si hacemos un join
    # ingredient_name: str 

    class Config:
        orm_mode = True

# Schema de lectura de Receta que incluye sus ingredientes
class RecipeReadWithIngredients(RecipeRead):
    ingredients: List[RecipeIngredientRead] = Field(default_factory=list)

    class Config:
        orm_mode = True
