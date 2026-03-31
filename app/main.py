import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.kafka import KafkaClient
from app.db import close_pool, create_pool
from app.model import load_model, save_model, train_model
from app.routes.async_moderation import router as async_moderation_router
from app.routes.predict import router as predict_router

MODEL_PATH = os.getenv("MODEL_PATH", "model.pkl")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = None
    app.state.db_pool = None
    app.state.kafka_producer = None

    try:
        if os.path.exists(MODEL_PATH):
            app.state.model = load_model(MODEL_PATH)
            logger.info("Model loaded from %s", MODEL_PATH)
        else:
            logger.info("Model file not found. Training new model...")
            model = train_model()
            save_model(model, MODEL_PATH)
            app.state.model = model
            logger.info("Model trained and saved to %s", MODEL_PATH)
    except Exception:
        logger.exception("Failed to initialize model")
        app.state.model = None

    try:
        app.state.db_pool = await create_pool()
        logger.info("Database pool created")
    except Exception:
        logger.exception("Failed to initialize database pool")
        app.state.db_pool = None

    try:
        kafka_client = KafkaClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        await kafka_client.start()
        app.state.kafka_producer = kafka_client
        logger.info("Kafka producer started")
    except Exception:
        logger.exception("Failed to initialize Kafka producer")
        app.state.kafka_producer = None

    yield

    try:
        if app.state.kafka_producer is not None:
            await app.state.kafka_producer.stop()
            logger.info("Kafka producer stopped")
    except Exception:
        logger.exception("Failed to stop Kafka producer")

    try:
        await close_pool(app.state.db_pool)
        logger.info("Database pool closed")
    except Exception:
        logger.exception("Failed to close database pool")


app = FastAPI(
    title="Ads Moderation Service",
    lifespan=lifespan,
)

app.include_router(predict_router)
app.include_router(async_moderation_router)


@app.get("/")
async def root():
    return {"message": "Ads Moderation Service is running"}
