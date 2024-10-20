import uuid

from fastapi import APIRouter, Depends, status

from src.schemas.token import TokenPayloadSchema
from src.schemas.user import UserCreateSchema, UserResponseSchema, UserUpdateSchema
from src.service import AuthService
from src.token.token import Token


router = APIRouter(
    prefix="/api/auth/users",
    tags=["users"]
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserResponseSchema)
async def create_user(
    schema: UserCreateSchema,
    organization_info: TokenPayloadSchema = Depends(Token.verify_organization),
    service: AuthService = Depends()
):
    user = await service.create_user(schema, uuid.UUID(organization_info.sub))
    return user


@router.get("/me", response_model=UserResponseSchema)
async def get_user(
    user_info: TokenPayloadSchema = Depends(Token.verify_token),
    service: AuthService = Depends()
):
    user = await service.read_user(id=uuid.UUID(user_info.sub))
    return user


@router.put("/me", status_code=status.HTTP_204_NO_CONTENT)
async def update_user(
    schema: UserUpdateSchema,
    user_info: TokenPayloadSchema = Depends(Token.verify_token),
    service: AuthService = Depends(),
    
):
    await service.update_user(uuid.UUID(user_info.sub), schema)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_info: TokenPayloadSchema = Depends(Token.verify_token),
    service: AuthService = Depends()
):
    await service.delete_user(uuid.UUID(user_info.sub))


@router.get("/workers", response_model=list[UserResponseSchema])
async def get_created_users(
    organization_info: TokenPayloadSchema = Depends(Token.verify_organization),
    service: AuthService = Depends()
):
    users = await service.read_created_users(uuid.UUID(organization_info.sub))
    return users


@router.delete("/workers/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worker(
    id: str,
    organization_info: TokenPayloadSchema = Depends(Token.verify_organization),
    service: AuthService = Depends()
):
    await service.delete_worker(uuid.UUID(organization_info.sub), uuid.UUID(id))
