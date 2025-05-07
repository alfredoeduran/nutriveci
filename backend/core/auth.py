from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError

from backend.core.config import get_settings
from backend.db import crud
from backend.db.models import Session, TokenData, User

# OAuth2PasswordBearer para manejar tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Obtener configuración
settings = get_settings()


async def create_access_token(user_id: UUID, session_id: UUID) -> str:
    """
    Crear un token JWT para una sesión de usuario.
    
    Args:
        user_id: ID del usuario
        session_id: ID de la sesión
        
    Returns:
        Token JWT codificado
    """
    # Datos a incluir en el token
    expires_at = datetime.now() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": str(user_id),
        "sid": str(session_id),
        "exp": expires_at,
    }
    
    # Codificar el token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


async def verify_token(token: str) -> Optional[TokenData]:
    """
    Verificar un token JWT y extraer sus datos.
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        Datos del token o None si es inválido
    """
    try:
        # Decodificar el token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Extraer datos
        user_id = payload.get("sub")
        session_id = payload.get("sid")
        expiration = payload.get("exp")
        
        if user_id is None or session_id is None:
            return None
            
        # Convertir a TokenData
        token_data = TokenData(
            user_id=user_id,
            session_id=session_id,
            exp=datetime.fromtimestamp(expiration) if expiration else None
        )
        
        return token_data
    
    except PyJWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Obtener el usuario actual basado en el token JWT.
    
    Args:
        token: Token JWT de autenticación
    
    Returns:
        Usuario autenticado
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verificar token
    token_data = await verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    # Verificar que la sesión existe y está activa
    session = await crud.get_session(UUID(token_data.session_id))
    if not session or not session.is_active or session.expires_at < datetime.now():
        raise credentials_exception
    
    # Obtener usuario
    user = await crud.get_user(UUID(token_data.user_id))
    if not user:
        raise credentials_exception
    
    # Actualizar última actividad de la sesión
    await crud.update_session_activity(UUID(token_data.session_id))
    
    return user


async def validate_session(session_id: UUID) -> bool:
    """
    Validar si una sesión existe y está activa.
    
    Args:
        session_id: ID de la sesión a validar
    
    Returns:
        True si la sesión es válida, False en caso contrario
    """
    session = await crud.get_session(session_id)
    
    if not session:
        return False
    
    if not session.is_active:
        return False
    
    if session.expires_at and session.expires_at < datetime.now():
        # La sesión ha expirado, actualizarla como inactiva
        await crud.deactivate_session(session_id)
        return False
    
    return True 