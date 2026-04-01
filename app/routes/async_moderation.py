import logging

from fastapi import APIRouter, HTTPException, Path, Request, status

from app.repositories.items import ItemRepository
from app.repositories.moderation_results import ModerationResultRepository
from app.schemas import (
    AsyncPredictRequest,
    AsyncPredictResponse,
    ModerationResultResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/async_predict",
    response_model=AsyncPredictResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def async_predict(payload: AsyncPredictRequest, request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    kafka_producer = getattr(request.app.state, "kafka_producer", None)
    cache = getattr(request.app.state, "prediction_cache", None)

    if pool is None:
        raise HTTPException(status_code=503, detail="Database is not available")

    if kafka_producer is None:
        raise HTTPException(status_code=503, detail="Kafka producer is not available")

    item_repository = ItemRepository(pool)
    moderation_repository = ModerationResultRepository(pool)

    item = await item_repository.get_by_item_id(payload.item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    task = await moderation_repository.create_pending(payload.item_id)

    if cache is not None:
        await cache.set_task_result(
            task["id"],
            {
                "task_id": task["id"],
                "status": "pending",
                "is_violation": None,
                "probability": None,
                "error_message": None,
            },
        )

    try:
        await kafka_producer.send_moderation_request(
            item_id=payload.item_id,
            task_id=task["id"],
        )
    except Exception as exc:
        logger.exception("Failed to send moderation request to Kafka")
        failed_row = await moderation_repository.update_failed(task["id"], str(exc))

        if cache is not None:
            await cache.set_task_result(
                task["id"],
                {
                    "task_id": failed_row["id"],
                    "status": failed_row["status"],
                    "is_violation": failed_row["is_violation"],
                    "probability": failed_row["probability"],
                    "error_message": failed_row["error_message"],
                },
            )

        raise HTTPException(status_code=500, detail="Failed to enqueue moderation request")

    return AsyncPredictResponse(
        task_id=task["id"],
        status="pending",
        message="Moderation request accepted",
    )


@router.get(
    "/moderation_result/{task_id}",
    response_model=ModerationResultResponse,
)
async def moderation_result(
    task_id: int = Path(..., gt=0),
    request: Request = None,
):
    pool = getattr(request.app.state, "db_pool", None)
    cache = getattr(request.app.state, "prediction_cache", None)

    if cache is not None:
        cached = await cache.get_task_result(task_id)
        if cached is not None:
            return ModerationResultResponse(**cached)

    if pool is None:
        raise HTTPException(status_code=503, detail="Database is not available")

    moderation_repository = ModerationResultRepository(pool)
    row = await moderation_repository.get_by_id(task_id)

    if row is None:
        raise HTTPException(status_code=404, detail="Moderation task not found")

    response = ModerationResultResponse(
        task_id=row["id"],
        status=row["status"],
        is_violation=row["is_violation"],
        probability=row["probability"],
        error_message=row["error_message"],
    )

    if cache is not None:
        await cache.set_task_result(task_id, response.model_dump())

    return response
