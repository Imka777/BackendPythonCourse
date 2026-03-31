import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

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

    yield


app = FastAPI(
    title="Ads Moderation Service",
    lifespan=lifespan,
)

app.include_router(predict_router)


@app.get("/")
async def root():
    return {"message": "Ads Moderation Service is running"}
