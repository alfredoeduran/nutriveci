from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel

from backend.core.auth import get_current_user, validate_session
from backend.core.config import get_settings
from backend.core.preference_flow import (
    PreferenceFlow, 
    PreferenceResponse, 
    get_preference_flow,
    save_preference_flow
)
from backend.db import crud
from backend.db.models import DietaryProfile, User, UserPreference

router = APIRouter(
    prefix="/preferences",
    tags=["preferences"],
    responses={404: {"description": "No encontrado"}},
)

settings = get_settings()


class PreferenceInput(BaseModel):
    """Modelo para recibir input de preferencias"""
    user_input: str


class PreferenceFlowResponse(BaseModel):
    """Modelo para respuestas del flujo de preferencias"""
    message: str
    options: List[str] = []
    state: str
    completed: bool = False


async def get_session_id_from_cookie(
    cookie: Optional[str] = Cookie(None, alias=settings.SESSION_COOKIE_NAME),
    authorization: Optional[str] = Header(None)
) -> Optional[UUID]:
    """
    Obtener el ID de sesión desde una cookie o el encabezado de autorización.
    
    Args:
        cookie: Cookie de sesión
        authorization: Encabezado de autorización
        
    Returns:
        ID de sesión si se encuentra, None en caso contrario
    """
    if cookie:
        # Obtener token de la cookie
        token = cookie
    elif authorization and authorization.startswith("Bearer "):
        # Obtener token del encabezado
        token = authorization.replace("Bearer ", "")
    else:
        return None
    
    # Verificar el token y obtener datos
    from backend.core.auth import verify_token
    token_data = await verify_token(token)
    
    if token_data and token_data.session_id:
        # Validar que la sesión existe y está activa
        session_id = UUID(token_data.session_id)
        if await validate_session(session_id):
            return session_id
    
    return None


@router.post("/start", response_model=PreferenceFlowResponse)
async def start_preference_flow(
    response: Response,
    current_user: User = Depends(get_current_user),
    session_id: Optional[UUID] = Depends(get_session_id_from_cookie)
):
    """
    Iniciar el flujo de registro de preferencias para el usuario actual.
    """
    try:
        # Obtener o crear flujo
        flow = await get_preference_flow(current_user.id, session_id)
        flow_response = await flow.start()
        
        # Guardar estado en la sesión si hay una sesión activa
        if session_id:
            await save_preference_flow(flow, session_id)
        
        return PreferenceFlowResponse(
            message=flow_response.message,
            options=flow_response.options,
            state=flow_response.state,
            completed=flow_response.completed
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar el flujo de preferencias: {str(e)}"
        )


@router.post("/process", response_model=PreferenceFlowResponse)
async def process_preference_input(
    preference_input: PreferenceInput,
    response: Response,
    current_user: User = Depends(get_current_user),
    session_id: Optional[UUID] = Depends(get_session_id_from_cookie)
):
    """
    Procesar una entrada del usuario en el flujo de preferencias.
    
    - **user_input**: Texto ingresado por el usuario como respuesta a la pregunta actual
    """
    try:
        # Obtener flujo actual o crear uno nuevo
        flow = await get_preference_flow(current_user.id, session_id)
        
        # Procesar la entrada
        flow_response = await flow.process_input(preference_input.user_input)
        
        # Guardar estado en la sesión si hay una sesión activa
        if session_id:
            await save_preference_flow(flow, session_id)
        
        return PreferenceFlowResponse(
            message=flow_response.message,
            options=flow_response.options,
            state=flow_response.state,
            completed=flow_response.completed
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la entrada: {str(e)}"
        )


@router.get("/summary", response_model=Dict)
async def get_preference_summary(current_user: User = Depends(get_current_user)):
    """
    Obtener un resumen de las preferencias y restricciones del usuario actual.
    """
    user = await crud.get_user(current_user.id)
    user_preferences = await crud.get_user_preference(current_user.id)
    dietary_profile = await crud.get_dietary_profile(current_user.id)
    
    summary = {
        "user": {
            "name": user.name,
            "budget": user.budget,
            "household_size": user.household_size,
            "restrictions": user.restrictions,
        },
        "preferences": None,
        "dietary_profile": None,
    }
    
    if user_preferences:
        summary["preferences"] = {
            "favorite_foods": user_preferences.favorite_foods,
            "disliked_foods": user_preferences.disliked_foods,
            "preferred_cuisines": user_preferences.preferred_cuisines,
            "cooking_skill_level": user_preferences.cooking_skill_level,
            "cooking_frequency": user_preferences.cooking_frequency,
        }
    
    if dietary_profile:
        summary["dietary_profile"] = {
            "diet_type": dietary_profile.diet_type,
            "allergens": dietary_profile.allergens,
            "intolerances": dietary_profile.intolerances,
            "medical_conditions": dietary_profile.medical_conditions,
            "diet_goals": dietary_profile.diet_goals,
        }
    
    return summary 