import json
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.broker.producer import AIOProducer, get_producer
from src.database.database import get_async_session
from src.models.users import User
from src.schemas.message import ProducerMessage
from src.schemas.token import TokenPayloadSchema, TokenSchema
from src.schemas.user import UserCreateSchema, UserUpdateSchema
from src.token.config import jwt_settings
from src.token.token import Token
from src.utils.roles import RoleEnum


class AuthService:
    def __init__(
        self,
        session: AsyncSession = Depends(get_async_session),
        producer: AIOProducer = Depends(get_producer),
    ):
        self.session = session
        self.producer = producer

    async def read_user(self, id: int = None, email: str = None) -> User:
        if id:
            result = await self.session.execute(select(User).where(User.id == id))
        else:
            result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user

    async def create_user(
        self, schema: UserCreateSchema, creator_id: int = None
    ) -> User:
        try:
            user_duplicate = await self.read_user(email=schema.email)
        except HTTPException:
            user = User(
                email=schema.email,
                password_hashed=Token.get_password_hash(schema.text_password),
                role=schema.role.value,
                created_by=creator_id,
            )
            self.session.add(user)
            await self.session.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{user_duplicate.email}' already exists",
            )
        return user

    async def login(self, email: str, password_text: str) -> TokenSchema:
        try:
            user = await self.read_user(email=email)
        except HTTPException:
            user = None
        if not user or not Token.verify_password(password_text, user.password_hashed):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        now = datetime.now()
        payload = TokenPayloadSchema(
            iat=now,
            exp=now + timedelta(minutes=jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            sub=str(user.id),
            role=user.role,
            email=user.email,
            org=user.created_by if user.created_by else user.id,
        )
        return Token.create_token(payload)

    async def update_user(self, id: int, schema: UserUpdateSchema) -> None:
        user = await self.read_user(id=id)
        user.email = schema.email
        user.password_hashed = Token.get_password_hash(schema.text_password)
        await self.session.commit()

    async def delete_user(self, id: int) -> None:
        await self.session.execute(delete(User).where(User.id == id))
        await self.session.commit()

    async def read_created_users(self, id: int) -> list[User]:
        users = await self.session.execute(select(User).where(User.created_by == id))
        return users.scalars()

    async def delete_worker(self, organization_id: int, worker_id: int) -> None:
        worker = await self.read_user(id=worker_id)
        if worker.created_by != organization_id or worker.role != RoleEnum.WORKER.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with id: {worker_id} is not your worker",
            )
        await self.delete_users_event(worker_id)

    async def delete_users_event(self, user_id: int) -> None:
        current_user = await self.read_user(id=user_id)

        producer_message = None
        
        if current_user.role == RoleEnum.WORKER.value:
            producer_message = ProducerMessage(worker_ids=[current_user.id])

        if current_user.role == RoleEnum.ORGANIZATION.value:
            workers = await self.read_created_users(id=current_user.id)
            producer_message = ProducerMessage(
                organization_id=current_user.id,
                worker_ids=[worker.id for worker in workers],
            )
        
        async with self.producer as producer:
            await producer.send(json.dumps(producer_message.model_dump()).encode())


