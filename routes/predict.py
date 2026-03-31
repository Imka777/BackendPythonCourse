import logging

from fastapi import APIRouter, HTTPException, Request

from schemas import PredictRequest, PredictResponse
from services.prediction import predict_violation

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest, request: Request) -> PredictResponse:
    model = getattr(request.app.state, "model", None)

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not available"
        )

    try:
        return predict_violation(model, payload)
    except Exception:
        logger.exception(
            "Prediction failed for seller_id=%s item_id=%s",
            payload.seller_id,
            payload.item_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Internal prediction error"
        )
