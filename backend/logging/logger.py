import logging
import time
from typing import Dict, Optional, Union
from uuid import UUID

from backend.db import crud
from backend.db.models import InteractionLogCreate

# Configurar el logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("nutriveci.log")
    ]
)

logger = logging.getLogger("nutriveci")


async def log_interaction(
    source: str,
    query: str,
    user_id: Optional[Union[UUID, str]] = None,
    intent: Optional[str] = None,
    entities: Optional[Dict] = None,
    response_type: Optional[str] = None,
    response_id: Optional[UUID] = None,
    session_id: Optional[str] = None,
):
    """
    Registra una interacción del usuario en la base de datos y en los logs.
    
    Args:
        source: Fuente de la interacción (telegram, web, etc.)
        query: Consulta textual del usuario
        user_id: ID del usuario (opcional)
        intent: Intención identificada (opcional)
        entities: Entidades extraídas (opcional)
        response_type: Tipo de respuesta (receta, plan, consejo, etc.) (opcional)
        response_id: ID del recurso recomendado (opcional)
        session_id: ID de sesión (opcional)
    """
    start_time = time.time()
    
    # Registrar en el log del sistema
    log_data = {
        "source": source,
        "query": query,
        "user_id": str(user_id) if user_id else "anonymous",
        "intent": intent or "unknown",
        "session_id": session_id or "no_session",
    }
    
    logger.info(f"User interaction: {log_data}")
    
    # Calcular tiempo de respuesta
    response_time = int((time.time() - start_time) * 1000)  # en milisegundos
    
    # Crear objeto para la base de datos
    log_entry = InteractionLogCreate(
        source=source,
        query=query,
        user_id=user_id if isinstance(user_id, UUID) else None,
        intent=intent,
        entities=entities or {},
        response_type=response_type,
        response_id=response_id,
        session_id=session_id,
        response_time=response_time,
    )
    
    # Guardar en la base de datos
    try:
        await crud.create_interaction_log(log_entry)
    except Exception as e:
        logger.error(f"Error al guardar log en base de datos: {e}")
    
    return response_time 