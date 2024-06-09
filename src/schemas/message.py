from pydantic import BaseModel


class ProducerMessage(BaseModel):
    organization_id: int | None = None
    worker_ids: list[int]

class ConsumerMessage(ProducerMessage):
    pass
