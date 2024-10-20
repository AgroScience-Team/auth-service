import uuid

from pydantic import BaseModel, Field, field_validator, validate_email

from src.utils.roles import RoleEnum


class UserUpdateSchema(BaseModel):
    email: str = Field(max_length=128)
    text_password: str = Field(min_length=8, max_length=64)

    @field_validator("email")
    @classmethod
    def check_email(cls, email: str) -> str:
        try:
            _ = validate_email(email)
        except Exception as e:
            raise ValueError(e)
        return email
        
    
class UserCreateSchema(UserUpdateSchema):
    role: RoleEnum


class UserResponseSchema(BaseModel):
    id: uuid.UUID
    email: str = Field(max_length=128)
    role: RoleEnum
    created_by: uuid.UUID | None = None
