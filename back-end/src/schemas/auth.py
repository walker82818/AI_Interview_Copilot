from pydantic import BaseModel, EmailStr, Field

from src.schemas.base import CamelModel


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=100)


class UserResponse(CamelModel):
    id: str
    email: str
    name: str


class AuthResponse(CamelModel):
    user: UserResponse
    token: str


class TokenPayload(BaseModel):
    sub: str
