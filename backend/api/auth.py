from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.core.auth import create_access_token, get_current_user
from backend.core.config import get_settings
from backend.db import crud
from backend.db.models import Session, SessionCreate, Token, User

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "No autorizado"}},
)

settings = get_settings()


class LoginResponse(BaseModel):
    """Respuesta para login exitoso"""
    access_token: str
    token_type: str
    expires_at: datetime
    user: User


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint para obtener token de acceso mediante OAuth2 (para integración con herramientas).
    """
    # Este endpoint sólo funcionará si el usuario ha iniciado sesión previamente por telegram
    # o ha configurado un usuario web específico.
    # Por simplicidad, usamos el campo de usuario como telegram_id o web_id
    
    # Intentar autenticar por telegram_id
    user = await crud.get_user_by_telegram_id(form_data.username)
    
    # Si no existe, intentar por web_id (si se implementa en el futuro)
    if not user:
        # Aquí se podría implementar la autenticación por web_id y contraseña
        # por ahora simplemente devolvemos error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear sesión para el usuario
    session_data = SessionCreate(
        user_id=user.id,
        platform="api",
        device_info={"user_agent": "OAuth2 Client"}
    )
    session = await crud.create_session(session_data)
    
    # Crear token de acceso
    access_token = await create_access_token(user.id, session.id)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_at=session.expires_at,
    )


@router.post("/login/telegram", response_model=LoginResponse)
async def login_telegram(
    telegram_id: str,
    user_name: Optional[str] = None,
    device_info: Optional[Dict] = None,
    response: Response = None,
):
    """
    Endpoint para iniciar sesión via Telegram.
    Crea un usuario si no existe.
    
    - **telegram_id**: ID único de Telegram
    - **user_name**: Nombre de usuario (opcional)
    - **device_info**: Información sobre el dispositivo (opcional)
    """
    # Buscar usuario por telegram_id
    user = await crud.get_user_by_telegram_id(telegram_id)
    
    # Si no existe, crear nuevo usuario
    if not user:
        user_create = UserCreate(
            telegram_id=telegram_id,
            name=user_name
        )
        user = await crud.create_user(user_create)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear el usuario",
            )
    
    # Crear sesión para el usuario
    session_data = SessionCreate(
        user_id=user.id,
        platform="telegram",
        device_info=device_info or {}
    )
    session = await crud.create_session(session_data)
    
    # Crear token de acceso
    access_token = await create_access_token(user.id, session.id)
    
    # Establecer cookie de sesión
    if response:
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=access_token,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE,
            expires=int(session.expires_at.timestamp())
        )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=session.expires_at,
        user=user
    )


@router.post("/login/web", response_model=LoginResponse)
async def login_web(
    web_id: str,
    user_name: Optional[str] = None,
    device_info: Optional[Dict] = None,
    response: Response = None,
):
    """
    Endpoint para iniciar sesión via Web.
    Crea un usuario si no existe.
    
    - **web_id**: ID único para web
    - **user_name**: Nombre de usuario (opcional)
    - **device_info**: Información sobre el dispositivo (opcional)
    """
    # Buscar usuario por web_id (implementación futura)
    # Por ahora creamos un usuario nuevo si no existe uno con ese ID
    user = None  # Aquí iría la búsqueda por web_id
    
    # Si no existe, crear nuevo usuario
    if not user:
        user_create = UserCreate(
            web_id=web_id,
            name=user_name
        )
        user = await crud.create_user(user_create)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear el usuario",
            )
    
    # Crear sesión para el usuario
    session_data = SessionCreate(
        user_id=user.id,
        platform="web",
        device_info=device_info or {}
    )
    session = await crud.create_session(session_data)
    
    # Crear token de acceso
    access_token = await create_access_token(user.id, session.id)
    
    # Establecer cookie de sesión
    if response:
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=access_token,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE,
            expires=int(session.expires_at.timestamp())
        )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=session.expires_at,
        user=user
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    session_id: Optional[str] = None,
    all_sessions: bool = False,
    response: Response = None,
):
    """
    Cerrar sesión del usuario.
    
    - **session_id**: ID de la sesión a cerrar (opcional)
    - **all_sessions**: Si es True, cierra todas las sesiones del usuario
    """
    if all_sessions:
        # Cerrar todas las sesiones del usuario
        await crud.deactivate_user_sessions(current_user.id)
    elif session_id:
        # Cerrar una sesión específica
        await crud.deactivate_session(UUID(session_id))
    
    # Eliminar cookie de sesión
    if response:
        response.delete_cookie(
            key=settings.SESSION_COOKIE_NAME,
            secure=settings.SESSION_COOKIE_SECURE,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
        )
    
    return {"message": "Sesión cerrada correctamente"}


@router.get("/sessions", response_model=List[Session])
async def get_sessions(
    current_user: User = Depends(get_current_user),
    active_only: bool = True,
):
    """
    Obtener todas las sesiones del usuario actual.
    
    - **active_only**: Si es True, sólo retorna sesiones activas
    """
    sessions = await crud.get_user_sessions(current_user.id, active_only)
    return sessions


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Obtener información del usuario autenticado.
    """
    return current_user 