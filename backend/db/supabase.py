"""
Conexión y operaciones con Supabase.
"""
from functools import lru_cache
from typing import Dict, List, Optional, Union

from supabase import Client, create_client

from backend.core.config import settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Crear y devolver un cliente de Supabase.
    Utiliza caché para no crear múltiples instancias.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    
    if not url or not key:
        raise ValueError(
            "SUPABASE_URL y SUPABASE_KEY deben estar configurados en las variables de entorno"
        )
    
    # Crear cliente sin configuración de proxy
    return create_client(url, key)


# Función auxiliar para trabajar con tablas específicas
async def query_table(
    table_name: str,
    select: str = "*",
    filters: Optional[Dict] = None,
    limit: Optional[int] = None,
    order: Optional[str] = None,
    ascending: bool = True,
) -> List[Dict]:
    """
    Consulta genérica para una tabla en Supabase.
    
    Args:
        table_name: Nombre de la tabla.
        select: Campos a seleccionar (por defecto "*").
        filters: Diccionario de filtros {campo: valor}.
        limit: Límite de resultados.
        order: Campo para ordenar.
        ascending: Si es True, ordena ascendente; descendente si es False.
        
    Returns:
        Lista de registros que coincidan con la consulta.
    """
    supabase = get_supabase_client()
    
    # Construir la consulta base
    query = supabase.table(table_name).select(select)
    
    # Aplicar filtros si existen
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    
    # Aplicar ordenamiento
    if order:
        query = query.order(order, ascending=ascending)
    
    # Aplicar límite
    if limit:
        query = query.limit(limit)
    
    # Ejecutar la consulta
    response = query.execute()
    
    return response.data 