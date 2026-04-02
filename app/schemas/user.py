from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from ..models.user import UserRole

class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.VIEWER

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")

class User(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
