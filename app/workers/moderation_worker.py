import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer

from app.clients.kafka import KafkaClient
from app.db import close_pool, create_pool
from app.model import load_model, save_model, train_model
from app.repositories.items import ItemRepository
from app.repositories.moderation_results import ModerationResultRepository
from app.repositories.users import UserRepository
from app.services.prediction import build_predict_request_from_db, predict_violation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MODERATION_TOPIC = "moderation"
WORKER_GROUP_ID = "moderation-workers"
MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")


def load_or_train_model():
    if os.path.exists(MODEL_PATH):
        return load_model(MODEL_PATH)

    model = train_model()
    save_model(model, MODEL_PATH)
    return model


async def process_message(message: dict, pool, model, kafka_client: KafkaClient):
    moderation_repository = ModerationResultRepository(pool)
    item_repository = ItemRepository(pool)
    user_repository = UserRepository(pool)

    task_id = int(message["task_id"])
    item_id = int(message["item_id"])

    try:

        if model is None:
            raise RuntimeError("Model is not available")

        item = await item_repository.get_by_item_id(item_id)
        if item is None:
            raise ValueError(f"Item with id={item_id} not found")

        user = await user_repository.get_by_seller_id(item["seller_id"])
        if user is None:
            raise ValueError(f"Seller with id={item['seller_id']} not found")

        payload = build_predict_request_from_db(user, item)
        result = predict_violation(model, payload)

        await moderation_repository.update_completed(
            task_id=task_id,
            is_violation=result.is_violation,
            probability=result.probability,
        )

        logger.info("Task %s completed", task_id)

    except Exception as exc:
        logger.exception("Failed to process task %s", task_id)

        try:
            await moderation_repository.update_failed(task_id, str(exc))
        except Exception:
            logger.exception("Failed to mark task %s as failed", task_id)

        await kafka_client.send_to_dlq(
            original_message=message,
            error=str(exc),
            retry_count=1,
        )


async def run_worker():
    pool = await create_pool()
    model = load_or_train_model()

    kafka_client = KafkaClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await kafka_client.start()

    consumer = AIOKafkaConsumer(
        MODERATION_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=WORKER_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )

    await consumer.start()
    logger.info("Moderation worker started")

    try:
        async for msg in consumer:
            await process_message(msg.value, pool, model, kafka_client)
    finally:
        await consumer.stop()
        await kafka_client.stop()
        await close_pool(pool)
        logger.info("Moderation worker stopped")


if __name__ == "__main__":
    asyncio.run(run_worker())
