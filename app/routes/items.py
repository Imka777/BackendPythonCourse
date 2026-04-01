from fastapi import APIRouter, HTTPException, Request

from app.repositories.items import ItemRepository
from app.repositories.moderation_results import ModerationResultRepository
from app.schemas import CloseItemRequest, CloseItemResponse

router = APIRouter()


@router.post("/close", response_model=CloseItemResponse)
async def close_item(payload: CloseItemRequest, request: Request):
    pool = getattr(request.app.state, "db_pool", None)
    cache = getattr(request.app.state, "prediction_cache", None)

    if pool is None:
        raise HTTPException(status_code=503, detail="Database is not available")

    item_repository = ItemRepository(pool)
    moderation_repository = ModerationResultRepository(pool)

    existing_item = await item_repository.get_by_item_id(payload.item_id)
    if existing_item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    task_ids = await moderation_repository.list_task_ids_by_item_id(payload.item_id)

    closed = await item_repository.close_and_delete(payload.item_id)
    if not closed:
        raise HTTPException(status_code=404, detail="Item not found")

    if cache is not None:
        await cache.delete_item_prediction(payload.item_id)
        await cache.delete_task_results(task_ids)

    return CloseItemResponse(
        item_id=payload.item_id,
        status="closed",
        message="Item was closed and removed from storages",
    )
