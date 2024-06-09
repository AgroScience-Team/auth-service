import asyncio
from typing import TYPE_CHECKING

from aiokafka import AIOKafkaConsumer
from fastapi import Depends

from src.broker.config import kafka_settings
from src.schemas.message import ConsumerMessage

if TYPE_CHECKING:
    from src.service import AuthService

event_loop = asyncio.get_event_loop()


class AIOConsumer:
    def __init__(self):
        self.__consumer = AIOKafkaConsumer(
            "delete_users",
            bootstrap_servers=kafka_settings.BOOTSTRAP_SERVERS,
            loop=event_loop,
        )
        self.service: AuthService = Depends()

    async def __start(self) -> None:
        await self.__consumer.start()

    async def __stop(self) -> None:
        await self.__consumer.stop()

    async def delete_users(self) -> None:
        await self.__start()
        try:
            messages = [
                ConsumerMessage(
                    organization_id=msg.value.get("organization_id"),
                    worker_ids=msg.value.get("worker_ids"),
                )
                async for msg in self.__consumer
            ]
            for message in messages:
                if not message.organization_id:
                    await self.service.delete_user(message.worker_ids[0])
                else:
                    user_ids = [message.organization_id].extend(message.worker_ids)
                    for user_id in user_ids:
                        await self.service.delete_user(user_id)
        finally:
            await self.__stop()
                    

def get_consumer() -> AIOConsumer:
    return AIOConsumer()
