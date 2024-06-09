import asyncio

from aiokafka import AIOKafkaProducer

from src.broker.config import kafka_settings

event_loop = asyncio.get_event_loop()
    

class AIOProducer:
    def __init__(self):
        self.__producer = AIOKafkaProducer(
            bootstrap_servers=kafka_settings.BOOTSTRAP_SERVERS,
            loop=event_loop,
        )
        self.__topics = "delete_users"

    async def __aenter__(self):
        await self.__producer.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.__producer.stop()

    async def send(self, value: bytes) -> None:
        await self.start()
        try:
            await self.__producer.send(
                topic=self.__topics,
                value=value,
            )
        finally:
            await self.stop()


def get_producer() -> AIOProducer:
    return AIOProducer()
