import json
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer


class KafkaClient:
    def __init__(
        self,
        bootstrap_servers: str,
        moderation_topic: str = "moderation",
        dlq_topic: str = "moderation_dlq",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.moderation_topic = moderation_topic
        self.dlq_topic = dlq_topic
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send_moderation_request(self, item_id: int, task_id: int):
        message = {
            "task_id": task_id,
            "item_id": item_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.producer.send_and_wait(self.moderation_topic, message)
        return message

    async def send_to_dlq(
        self,
        original_message: dict,
        error: str,
        retry_count: int = 1,
    ):
        dlq_message = {
            "original_message": original_message,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "retry_count": retry_count,
        }
        await self.producer.send_and_wait(self.dlq_topic, dlq_message)
        return dlq_message
