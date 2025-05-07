from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, UUID4


# Modelos Base
class TimestampModel(BaseModel):
    """Modelo base con campos de timestamp"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UUIDModel(BaseModel):
    """Modelo base con campo ID tipo UUID"""
    id: Optional[UUID] = Field(default_factory=uuid4)


# Modelos de Usuario
class UserBase(BaseModel):
    """Información base del usuario"""
    name: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    allergies: Optional[List[str]] = []
    source: Optional[str] = "web"


class UserCreate(UserBase):
    """Datos para crear un usuario"""
    telegram_id: Optional[str] = None
    web_id: Optional[str] = None
    
    @validator('telegram_id', 'web_id')
    def check_id_exists(cls, v, values):
        """Validar que al menos un ID esté presente"""
        if not v and 'telegram_id' not in values and 'web_id' not in values:
            raise ValueError('Al menos uno de telegram_id o web_id debe estar presente')
        return v


class User(UserBase):
    id: str  # Cambiado de UUID4 a str para permitir IDs de prueba
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Actualizado de orm_mode a from_attributes


# Modelos de Perfil de Usuario
class UserPreferenceBase(BaseModel):
    """Información base de preferencias del usuario"""
    favorite_foods: Optional[List[str]] = Field(default_factory=list)
    disliked_foods: Optional[List[str]] = Field(default_factory=list)
    preferred_cuisines: Optional[List[str]] = Field(default_factory=list)
    cooking_skill_level: Optional[str] = None  # principiante, intermedio, avanzado
    meal_planning_frequency: Optional[str] = None  # diario, semanal, ocasional
    cooking_frequency: Optional[str] = None  # diario, semanal, ocasional


class UserPreferenceCreate(UserPreferenceBase):
    """Datos para crear preferencias de usuario"""
    user_id: UUID


class UserPreference(UUIDModel, UserPreferenceBase, TimestampModel):
    """Modelo completo de preferencias de usuario"""
    user_id: UUID
    
    class Config:
        orm_mode = True


class DietaryProfileBase(BaseModel):
    """Información base del perfil dietético"""
    diet_type: Optional[str] = None  # vegetariano, vegano, omnívoro, etc.
    allergens: Optional[List[str]] = Field(default_factory=list)
    intolerances: Optional[List[str]] = Field(default_factory=list)
    medical_conditions: Optional[List[str]] = Field(default_factory=list)
    diet_goals: Optional[List[str]] = Field(default_factory=list)
    nutritional_requirements: Optional[Dict] = Field(default_factory=dict)


class DietaryProfileCreate(DietaryProfileBase):
    """Datos para crear perfil dietético"""
    user_id: UUID


class DietaryProfile(UUIDModel, DietaryProfileBase, TimestampModel):
    """Modelo completo de perfil dietético"""
    user_id: UUID
    
    class Config:
        orm_mode = True


# Modelos de Condiciones de Salud
class HealthConditionBase(BaseModel):
    """Información base de condición de salud"""
    condition_type: str
    severity: Optional[str] = None
    notes: Optional[str] = None


class HealthConditionCreate(HealthConditionBase):
    """Datos para crear una condición de salud"""
    user_id: UUID


class HealthCondition(UUIDModel, HealthConditionBase, TimestampModel):
    """Modelo completo de condición de salud"""
    user_id: UUID
    
    class Config:
        orm_mode = True


# Modelos de Ingredientes
class IngredientBase(BaseModel):
    """Información base de ingrediente"""
    name: str
    category: str
    nutritional_value: Optional[Dict] = Field(default_factory=dict)
    seasonal: Optional[bool] = False
    price_category: Optional[str] = None
    region: Optional[List[str]] = Field(default_factory=list)


class IngredientCreate(IngredientBase):
    """Datos para crear un ingrediente"""
    pass


class Ingredient(UUIDModel, IngredientBase):
    """Modelo completo de ingrediente"""
    
    class Config:
        orm_mode = True


# Modelos de Recetas
class RecipeBase(BaseModel):
    """Información base de receta"""
    name: str
    description: Optional[str] = None
    preparation_steps: List[str]
    cooking_time: Optional[int] = None
    difficulty: Optional[str] = None
    servings: Optional[int] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    nutritional_info: Optional[Dict] = Field(default_factory=dict)
    estimated_cost: Optional[float] = None
    image_url: Optional[str] = None
    healthy_score: Optional[int] = None


class RecipeCreate(RecipeBase):
    """Datos para crear una receta"""
    pass


class Recipe(UUIDModel, RecipeBase):
    """Modelo completo de receta"""
    
    class Config:
        orm_mode = True


# Modelo de ingredientes en receta
class RecipeIngredientBase(BaseModel):
    """Relación entre receta e ingrediente"""
    quantity: float
    unit: str


class RecipeIngredientCreate(RecipeIngredientBase):
    """Datos para crear relación receta-ingrediente"""
    recipe_id: UUID
    ingredient_id: UUID


class RecipeIngredient(UUIDModel, RecipeIngredientBase):
    """Modelo completo de relación receta-ingrediente"""
    recipe_id: UUID
    ingredient_id: UUID
    
    class Config:
        orm_mode = True


# Modelos para interacción y logs
class InteractionLogBase(BaseModel):
    """Registro de interacción con usuario"""
    source: str
    query: str
    intent: Optional[str] = None
    entities: Optional[Dict] = Field(default_factory=dict)
    response_type: Optional[str] = None
    response_id: Optional[UUID] = None
    session_id: Optional[str] = None
    response_time: Optional[int] = None
    feedback: Optional[Dict] = Field(default_factory=dict)


class InteractionLogCreate(InteractionLogBase):
    """Datos para crear un log de interacción"""
    user_id: Optional[UUID] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class InteractionLog(UUIDModel, InteractionLogBase, TimestampModel):
    """Modelo completo de log de interacción"""
    user_id: Optional[UUID] = None
    
    class Config:
        orm_mode = True


# Modelos de Sesiones de Usuario
class SessionBase(BaseModel):
    """Información base de sesión de usuario"""
    user_id: UUID
    device_info: Optional[Dict] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    platform: Optional[str] = None  # web, telegram, etc.
    is_active: bool = True
    expires_at: Optional[datetime] = None


class SessionCreate(SessionBase):
    """Datos para crear una sesión"""
    
    @validator('expires_at', pre=True, always=True)
    def set_expires_at(cls, v, values):
        """Establecer fecha de expiración por defecto (30 días)"""
        if v is None:
            return datetime.now() + timedelta(days=30)
        return v


class Session(UUIDModel, SessionBase, TimestampModel):
    """Modelo completo de sesión"""
    token: Optional[str] = None
    last_activity: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class TokenData(BaseModel):
    """Modelo para datos dentro del token JWT"""
    user_id: str
    session_id: Optional[str] = None
    exp: Optional[datetime] = None


class Token(BaseModel):
    """Modelo para token de autenticación"""
    access_token: str
    token_type: str
    expires_at: datetime


# Modelo temporal para progreso de llenado de perfil
class ProfileProgress(BaseModel):
    user_id: str  # Puede ser UUID, Telegram ID, etc.
    name: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    allergies: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationBase(BaseModel):
    user_id: str  # Cambiado de UUID4 a str para permitir IDs de prueba
    message: str
    response: Dict[str, Any]
    source: str = "web"


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: str  # Cambiado de UUID4 a str para permitir IDs de prueba
    created_at: datetime

    class Config:
        from_attributes = True  # Actualizado de orm_mode a from_attributes 