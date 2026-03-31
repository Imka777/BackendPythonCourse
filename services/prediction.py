import logging
import numpy as np

from schemas import PredictRequest, PredictResponse

logger = logging.getLogger(__name__)


def build_features(payload: PredictRequest) -> np.ndarray:
    is_verified_seller = 1.0 if payload.is_verified_seller else 0.0
    images_qty = min(payload.images_qty, 10) / 10.0
    description_length = len(payload.description) / 1000.0
    category = payload.category / 100.0

    features = np.array([
        [is_verified_seller, images_qty, description_length, category]
    ], dtype=float)

    return features


def predict_violation(model, payload: PredictRequest) -> PredictResponse:
    features = build_features(payload)

    logger.info(
        "Prediction request: seller_id=%s item_id=%s features=%s",
        payload.seller_id,
        payload.item_id,
        features[0].tolist(),
    )

    prediction = bool(model.predict(features)[0])
    probability = float(model.predict_proba(features)[0][1])

    logger.info(
        "Prediction result: seller_id=%s item_id=%s is_violation=%s probability=%.4f",
        payload.seller_id,
        payload.item_id,
        prediction,
        probability,
    )

    return PredictResponse(
        is_violation=prediction,
        probability=probability,
    )


def build_predict_request_from_db(user: dict, item: dict) -> PredictRequest:
    return PredictRequest(
        seller_id=user["seller_id"],
        is_verified_seller=user["is_verified_seller"],
        item_id=item["item_id"],
        name=item["name"],
        description=item["description"],
        category=item["category"],
        images_qty=item["images_qty"],
    )
