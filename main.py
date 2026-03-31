import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from db import close_pool, create_pool
from model import load_model, save_model, train_model
from routes.predict import router as predict_router

MODEL_PATH = "model.pkl"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = None
    app.state.db_pool = None

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

    yield

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


@app.get("/")
async def root():
    return {"message": "Ads Moderation Service is running"}
