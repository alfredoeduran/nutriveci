from datetime import datetime
from typing import Dict, List, Optional, TypeVar, Union
from uuid import UUID

from supabase import Client

from backend.db.models import (
    DietaryProfile,
    DietaryProfileCreate,
    HealthCondition,
    HealthConditionCreate,
    Ingredient,
    IngredientCreate,
    InteractionLog,
    InteractionLogCreate,
    Recipe,
    RecipeCreate,
    RecipeIngredient,
    RecipeIngredientCreate,
    Session,
    SessionCreate,
    User,
    UserCreate,
    UserPreference,
    UserPreferenceCreate,
    ProfileProgress,
    Conversation,
    ConversationCreate,
)
from backend.db.supabase import get_supabase_client
from backend.schemas.recipes import RecipeUpdate

# Operaciones CRUD para usuarios
async def create_user(user_data: UserCreate) -> User:
    """Crear un nuevo usuario"""
    supabase = get_supabase_client()
    response = supabase.table("users").insert(user_data.dict()).execute()
    
    if response.data:
        return User(**response.data[0])
    return None


async def get_user(user_id: UUID) -> Optional[User]:
    """Obtener un usuario por ID"""
    supabase = get_supabase_client()
    response = supabase.table("users").select("*").eq("id", str(user_id)).execute()
    
    if response.data:
        return User(**response.data[0])
    return None


async def get_user_by_telegram_id(telegram_id: str) -> Optional[User]:
    """Obtener un usuario por su ID de Telegram"""
    supabase = get_supabase_client()
    response = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    
    if response.data:
        return User(**response.data[0])
    return None


async def update_user(user_id: UUID, user_data: Dict) -> Optional[User]:
    """Actualizar un usuario"""
    supabase = get_supabase_client()
    response = supabase.table("users").update(user_data).eq("id", str(user_id)).execute()
    
    if response.data:
        return User(**response.data[0])
    return None


# Operaciones CRUD para perfiles de usuario
async def create_user_preference(preference_data: UserPreferenceCreate) -> UserPreference:
    """Crear o actualizar preferencias de usuario"""
    supabase = get_supabase_client()
    
    # Verificar si ya existe un registro de preferencias para este usuario
    existing = await get_user_preference(preference_data.user_id)
    
    if existing:
        # Si existe, actualizar
        response = supabase.table("user_preferences").update(
            preference_data.dict()
        ).eq("user_id", str(preference_data.user_id)).execute()
    else:
        # Si no existe, crear nuevo
        response = supabase.table("user_preferences").insert(
            preference_data.dict()
        ).execute()
    
    if response.data:
        return UserPreference(**response.data[0])
    return None


async def get_user_preference(user_id: UUID) -> Optional[UserPreference]:
    """Obtener preferencias de un usuario por ID de usuario"""
    supabase = get_supabase_client()
    response = supabase.table("user_preferences").select("*").eq("user_id", str(user_id)).execute()
    
    if response.data:
        return UserPreference(**response.data[0])
    return None


async def update_user_preference(user_id: UUID, preference_data: Dict) -> Optional[UserPreference]:
    """Actualizar preferencias de un usuario"""
    supabase = get_supabase_client()
    response = supabase.table("user_preferences").update(
        preference_data
    ).eq("user_id", str(user_id)).execute()
    
    if response.data:
        return UserPreference(**response.data[0])
    return None


async def create_dietary_profile(profile_data: DietaryProfileCreate) -> DietaryProfile:
    """Crear o actualizar perfil dietético de usuario"""
    supabase = get_supabase_client()
    
    # Verificar si ya existe un perfil dietético para este usuario
    existing = await get_dietary_profile(profile_data.user_id)
    
    if existing:
        # Si existe, actualizar
        response = supabase.table("dietary_profiles").update(
            profile_data.dict()
        ).eq("user_id", str(profile_data.user_id)).execute()
    else:
        # Si no existe, crear nuevo
        response = supabase.table("dietary_profiles").insert(
            profile_data.dict()
        ).execute()
    
    if response.data:
        return DietaryProfile(**response.data[0])
    return None


async def get_dietary_profile(user_id: UUID) -> Optional[DietaryProfile]:
    """Obtener perfil dietético de un usuario por ID de usuario"""
    supabase = get_supabase_client()
    response = supabase.table("dietary_profiles").select("*").eq("user_id", str(user_id)).execute()
    
    if response.data:
        return DietaryProfile(**response.data[0])
    return None


async def update_dietary_profile(user_id: UUID, profile_data: Dict) -> Optional[DietaryProfile]:
    """Actualizar perfil dietético de un usuario"""
    supabase = get_supabase_client()
    response = supabase.table("dietary_profiles").update(
        profile_data
    ).eq("user_id", str(user_id)).execute()
    
    if response.data:
        return DietaryProfile(**response.data[0])
    return None


# Operaciones CRUD para sesiones de usuario
async def create_session(session_data: SessionCreate) -> Session:
    """Crear una nueva sesión de usuario"""
    supabase = get_supabase_client()
    
    # Establecer última actividad al momento actual
    session_dict = session_data.dict()
    session_dict["last_activity"] = datetime.now()
    
    response = supabase.table("sessions").insert(session_dict).execute()
    
    if response.data:
        return Session(**response.data[0])
    return None


async def get_session(session_id: UUID) -> Optional[Session]:
    """Obtener una sesión por ID"""
    supabase = get_supabase_client()
    response = supabase.table("sessions").select("*").eq("id", str(session_id)).execute()
    
    if response.data:
        return Session(**response.data[0])
    return None


async def get_user_sessions(user_id: UUID, active_only: bool = False) -> List[Session]:
    """Obtener todas las sesiones de un usuario"""
    supabase = get_supabase_client()
    query = supabase.table("sessions").select("*").eq("user_id", str(user_id))
    
    if active_only:
        query = query.eq("is_active", True)
    
    response = query.order("created_at", desc=True).execute()
    
    return [Session(**item) for item in response.data]


async def update_session_activity(session_id: UUID) -> Optional[Session]:
    """Actualizar el timestamp de última actividad de una sesión"""
    supabase = get_supabase_client()
    response = supabase.table("sessions").update({
        "last_activity": datetime.now()
    }).eq("id", str(session_id)).execute()
    
    if response.data:
        return Session(**response.data[0])
    return None


async def update_session(session_id: UUID, session_data: Dict) -> Optional[Session]:
    """Actualizar datos de una sesión"""
    supabase = get_supabase_client()
    response = supabase.table("sessions").update(session_data).eq("id", str(session_id)).execute()
    
    if response.data:
        return Session(**response.data[0])
    return None


async def deactivate_session(session_id: UUID) -> Optional[Session]:
    """Desactivar una sesión"""
    return await update_session(session_id, {"is_active": False})


async def deactivate_user_sessions(user_id: UUID) -> bool:
    """Desactivar todas las sesiones de un usuario"""
    supabase = get_supabase_client()
    response = supabase.table("sessions").update({
        "is_active": False
    }).eq("user_id", str(user_id)).execute()
    
    return bool(response.data)


# Operaciones CRUD para ingredientes
async def create_ingredient(ingredient_data: IngredientCreate) -> Ingredient:
    """Crear un nuevo ingrediente"""
    supabase = get_supabase_client()
    response = supabase.table("ingredients").insert(ingredient_data.dict()).execute()
    
    if response.data:
        return Ingredient(**response.data[0])
    return None


async def get_ingredient(ingredient_id: UUID) -> Optional[Ingredient]:
    """Obtener un ingrediente por ID"""
    supabase = get_supabase_client()
    response = supabase.table("ingredients").select("*").eq("id", str(ingredient_id)).execute()
    
    if response.data:
        return Ingredient(**response.data[0])
    return None


async def list_ingredients(filters: Dict = None, skip: int = 0, limit: int = 100) -> List[Ingredient]:
    """Listar ingredientes con filtros opcionales"""
    supabase = get_supabase_client()
    query = supabase.table("ingredients").select("*")
    
    # Aplicar filtros si existen
    if filters:
        for key, value in filters.items():
            if key == "region":
                # Para búsqueda en arrays
                query = query.contains(key, [value])
            else:
                query = query.eq(key, value)
    
    # Aplicar paginación
    query = query.range(skip, skip + limit - 1)
    
    response = query.execute()
    
    if response.data:
        return [Ingredient(**item) for item in response.data]
    return []


async def update_ingredient(ingredient_id: UUID, ingredient_data: Dict) -> Optional[Ingredient]:
    """Actualizar un ingrediente existente"""
    supabase = get_supabase_client()
    response = supabase.table("ingredients").update(
        ingredient_data
    ).eq("id", str(ingredient_id)).execute()
    
    if response.data:
        return Ingredient(**response.data[0])
    return None


async def delete_ingredient(ingredient_id: UUID) -> bool:
    """Eliminar un ingrediente"""
    supabase = get_supabase_client()
    response = supabase.table("ingredients").delete().eq("id", str(ingredient_id)).execute()
    
    return bool(response.data)


async def search_ingredients(query: str, limit: int = 10) -> List[Ingredient]:
    """Buscar ingredientes por texto"""
    supabase = get_supabase_client()
    
    # Buscar coincidencias en el nombre (ilike para ignorar mayúsculas/minúsculas)
    response = supabase.table("ingredients").select("*").ilike("name", f"%{query}%").limit(limit).execute()
    
    if response.data:
        return [Ingredient(**item) for item in response.data]
    return []


# Operaciones CRUD para recetas

async def get_recipes_by_user(user_id: UUID) -> List[Recipe]:
    """Obtener todas las recetas asociadas a un usuario."""
    supabase = get_supabase_client()
    response = supabase.table("recipes").select("*").eq("user_id", str(user_id)).execute()
    if response.data:
        return [Recipe(**item) for item in response.data]
    return []

async def create_recipe(recipe_data: RecipeCreate) -> Recipe:
    """Crear una nueva receta"""
    supabase = get_supabase_client()
    response = supabase.table("recipes").insert(recipe_data.dict(exclude_unset=True)).execute()

    if response.data:
        return Recipe(**response.data[0])
    return None

async def save_recipe(recipe_dict):
    """Guarda una receta generada dinámicamente en la tabla recipes."""
    supabase = get_supabase_client()
    # Asegura que los campos requeridos existen
    campos = ["id", "name", "description", "instructions", "ingredients"]
    receta = {k: recipe_dict[k] for k in campos if k in recipe_dict}
    response = supabase.table("recipes").insert(receta).execute()
    if response.data:
        from backend.db.models import Recipe
        return Recipe(**response.data[0])
    return None

async def get_recipe_by_name(name: str):
    supabase = get_supabase_client()
    response = supabase.table("recipes").select("*").ilike("name", name).limit(1).execute()
    if response.data:
        from backend.db.models import Recipe
        return Recipe(**response.data[0])
    return None

async def get_recipe(recipe_id: UUID) -> Optional[Recipe]:
    """Obtener una receta por ID"""
    supabase = get_supabase_client()
    response = supabase.table("recipes").select("*").eq("id", str(recipe_id)).execute()

    if response.data:
        # Idealmente, retornar RecipeRead
        return Recipe(**response.data[0])
    return None


async def list_recipes(skip: int = 0, limit: int = 100) -> List[Recipe]:
    """Listar recetas"""
    supabase = get_supabase_client()
    response = supabase.table("recipes").select("*").range(skip, skip + limit - 1).execute()

    # Idealmente, retornar List[RecipeRead]
    return [Recipe(**item) for item in response.data]


async def update_recipe(recipe_id: UUID, recipe_data: RecipeUpdate) -> Optional[Recipe]:
    """Actualizar una receta existente"""
    supabase = get_supabase_client()
    update_data = recipe_data.dict(exclude_unset=True) # Solo incluir campos enviados
    if not update_data:
        # Si no hay datos para actualizar, obtener y devolver el original
        return await get_recipe(recipe_id)

    response = supabase.table("recipes").update(update_data).eq("id", str(recipe_id)).execute()

    if response.data:
        # Idealmente, retornar RecipeRead
        return Recipe(**response.data[0])
    return None


async def delete_recipe(recipe_id: UUID) -> bool:
    """Elimina una receta"""
    supabase = get_supabase_client()
    response = supabase.table("recipes").delete().eq("id", str(recipe_id)).execute()
    return bool(response.data)


async def get_recipes_by_ids(recipe_ids: List[UUID]) -> List[Recipe]:
    """
    Obtiene múltiples recetas por sus IDs
    
    Args:
        recipe_ids: Lista de UUIDs de recetas a recuperar
        
    Returns:
        Lista de objetos Recipe
    """
    if not recipe_ids:
        return []
        
    supabase = get_supabase_client()
    
    # Convertir UUIDs a strings
    ids_str = [str(recipe_id) for recipe_id in recipe_ids]
    
    # Supabase permite filtrar con in() para múltiples valores
    response = supabase.table("recipes").select("*").in_("id", ids_str).execute()
    
    if response.data:
        return [Recipe(**item) for item in response.data]
    return []


async def search_recipes_by_ingredients(
    ingredient_ids: List[UUID], limit: int = 10
) -> List[Recipe]:
    """
    Buscar recetas que contengan los ingredientes especificados.
    Retorna recetas ordenadas por cantidad de ingredientes coincidentes.
    """
    # Esta función es más compleja y requeriría consultas SQL personalizadas en Supabase
    # Aquí se muestra una implementación simplificada
    supabase = get_supabase_client()
    
    # Convertir UUIDs a strings para la consulta
    ingredient_ids_str = [str(id) for id in ingredient_ids]
    
    # Esta consulta es una simplificación y podría necesitar ajustes
    # dependiendo de la estructura exacta de Supabase
    response = supabase.table("recipes").select(
        "*, recipe_ingredients!inner(*)"
    ).in_("recipe_ingredients.ingredient_id", ingredient_ids_str).execute()
    
    # Procesamiento de resultados
    # (En una implementación real, necesitaríamos ordenar por cantidad de coincidencias)
    return [Recipe(**item) for item in response.data[:limit]]


# Operaciones CRUD para logs de interacción
async def create_interaction_log(log_data: InteractionLogCreate) -> InteractionLog:
    """Crear un nuevo registro de interacción"""
    supabase = get_supabase_client()
    response = supabase.table("interaction_logs").insert(log_data.dict()).execute()
    
    if response.data:
        return InteractionLog(**response.data[0])
    return None


async def get_user_interaction_logs(user_id: UUID, limit: int = 10) -> List[InteractionLog]:
    """Obtener los registros de interacción de un usuario"""
    supabase = get_supabase_client()
    response = supabase.table("interaction_logs").select("*").eq("user_id", str(user_id)).order("timestamp", desc=True).limit(limit).execute()
    
    return [InteractionLog(**item) for item in response.data]


# CRUD para progreso de perfil temporal
async def get_profile_progress(user_id: str) -> Optional[ProfileProgress]:
    supabase = get_supabase_client()
    response = supabase.table("profile_progress").select("*").eq("user_id", user_id).limit(1).execute()
    if response.data:
        return ProfileProgress(**response.data[0])
    return None

async def update_profile_progress(user_id: str, data: dict) -> ProfileProgress:
    if not user_id or str(user_id).strip() == "" or user_id == "None":
        raise ValueError("No se recibió un identificador de usuario válido para guardar el progreso de perfil.")
    data["user_id"] = user_id
    supabase = get_supabase_client()
    # Verifica si ya existe
    existing = supabase.table("profile_progress").select("*").eq("user_id", user_id).limit(1).execute()
    if existing.data:
        # Actualiza
        response = supabase.table("profile_progress").update(data).eq("user_id", user_id).execute()
    else:
        # Crea nuevo
        response = supabase.table("profile_progress").insert(data).execute()
    return ProfileProgress(**response.data[0])

async def delete_profile_progress(user_id: str) -> bool:
    supabase = get_supabase_client()
    response = supabase.table("profile_progress").delete().eq("user_id", user_id).execute()
    return bool(response.data)

async def save_conversation(conversation: ConversationCreate) -> Conversation:
    """Guarda una nueva conversación en la base de datos."""
    from uuid import uuid4
    from datetime import datetime
    
    conversation_dict = conversation.dict()
    conversation_dict["id"] = str(uuid4())
    conversation_dict["timestamp"] = datetime.utcnow().isoformat()
    
    supabase = get_supabase_client()
    result = supabase.table("conversations").insert(conversation_dict).execute()
    
    if not result.data:
        raise Exception("Error al guardar la conversación")
    
    return Conversation(**result.data[0])

async def get_user_conversations(user_id: str, limit: int = 50) -> list[Conversation]:
    """Obtiene el historial de conversaciones de un usuario."""
    supabase = get_supabase_client()
    result = supabase.table("conversations")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("timestamp", desc=True)\
        .limit(limit)\
        .execute()
    
    return [Conversation(**conv) for conv in result.data] 