from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID

class UserPref(BaseModel):
    user_id: UUID = Field(..., description="Унікальний ID користувача")
    category_id: int = Field(..., gt=0, description="ID категорії з таблиці categories")

    class Config:
        from_attributes = True

class Category(BaseModel):
    name: str = Field(..., max_length=100)
    icon_url: Optional[str] = None

    class Config:
        from_attributes = True