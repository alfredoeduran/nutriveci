from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class ConversationBase(BaseModel):
    user_id: str
    message: str
    response: Dict[str, Any]
    source: str = "web"

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True 