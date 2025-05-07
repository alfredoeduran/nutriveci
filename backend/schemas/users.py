from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class UserBase(BaseModel):
    name: str
    sex: str
    age: int
    weight: float  # kg
    height: float  # cm
    allergies: Optional[List[str]] = Field(default_factory=list)
    source: str = "web"  # 'web' o 'telegram'

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: UUID

class UserUpdate(BaseModel):
    name: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    allergies: Optional[List[str]] = None
    source: Optional[str] = None
