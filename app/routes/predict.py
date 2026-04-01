import logging


from fastapi import APIRouter, HTTPException, Query, Request

from app.repositories.items import ItemRepository
from app.repositories.users import UserRepository
from app.schemas import PredictRequest, PredictResponse
from app.services.prediction import build_predict_request_from_db, predict_violation

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest, request: Request) -> PredictResponse:
    cache = getattr(request.app.state, "prediction_cache", None)

    if cache is not None:
        cached = await cache.get_item_prediction(payload.item_id)
        if cached is not None:
            return PredictResponse(**cached)

    model = getattr(request.app.state, "model", None)
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not available"
        )

    try:
        result = predict_violation(model, payload)

        if cache is not None:
            await cache.set_item_prediction(payload.item_id, result.model_dump())

        return result
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



@router.get("/simple_predict", response_model=PredictResponse)
async def simple_predict(
    item_id: int = Query(..., gt=0),
    request: Request = None,
) -> PredictResponse:
    cache = getattr(request.app.state, "prediction_cache", None)

    if cache is not None:
        cached = await cache.get_item_prediction(item_id)
        if cached is not None:
            return PredictResponse(**cached)

    model = getattr(request.app.state, "model", None)
    pool = getattr(request.app.state, "db_pool", None)

    if model is None:
        raise HTTPException(status_code=503, detail="Model is not available")

    if pool is None:
        raise HTTPException(status_code=503, detail="Database is not available")

    item_repository = ItemRepository(pool)
    user_repository = UserRepository(pool)

    item = await item_repository.get_by_item_id(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    user = await user_repository.get_by_seller_id(item["seller_id"])
    if user is None:
        raise HTTPException(status_code=404, detail="Seller not found")

    payload = build_predict_request_from_db(user, item)

    try:
        result = predict_violation(model, payload)

        if cache is not None:
            await cache.set_item_prediction(item_id, result.model_dump())

        return result
    except Exception:
        logger.exception("Simple prediction failed for item_id=%s", item_id)
        raise HTTPException(status_code=500, detail="Internal prediction error")
