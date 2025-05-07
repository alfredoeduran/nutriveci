from fastapi import APIRouter, Query
from typing import List, Optional
# from backend.db.crud import list_interaction_logs, get_user_by_id

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/conversations")
def get_conversations(source: Optional[str] = Query(None, description="Origen: web o telegram"), user_search: Optional[str] = None):
    """
    Lista conversaciones agrupadas por usuario y canal.
    """
    logs = list_interaction_logs(source=source, user_search=user_search)
    # Agrupar por usuario+source
    conversations = {}
    for log in logs:
        key = (log['user_id'], log['source'])
        if key not in conversations:
            conversations[key] = {
                'user_id': log['user_id'],
                'source': log['source'],
                'user_name': log.get('user_name', ''),
                'last_message': log['query'],
                'last_time': log['timestamp'],
                'conversation_id': f"{log['user_id']}_{log['source']}"
            }
        elif log['timestamp'] > conversations[key]['last_time']:
            conversations[key]['last_message'] = log['query']
            conversations[key]['last_time'] = log['timestamp']
    return list(conversations.values())

@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str):
    """
    Devuelve los mensajes de una conversación (usuario+origen).
    """
    user_id, source = conversation_id.split('_', 1)
    logs = list_interaction_logs(source=source, user_search=None, user_id=user_id)
    # Ordenar por timestamp
    logs.sort(key=lambda x: x['timestamp'])
    messages = [
        {
            'sender': 'user',
            'text': log['query'],
            'timestamp': log['timestamp']
        } if log['source'] == source else {
            'sender': 'bot',
            'text': log['response'],
            'timestamp': log['timestamp']
        }
        for log in logs
    ]
    return messages

@router.get("/users/{user_id}")
def get_user_info(user_id: str):
    return get_user_by_id(user_id)
