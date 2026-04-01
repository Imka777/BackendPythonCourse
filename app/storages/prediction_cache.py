import json


class PredictionCacheStorage:
    ITEM_PREFIX = "prediction:item"
    TASK_PREFIX = "prediction:task"

    def __init__(self, redis_client, ttl_seconds: int = 300):
        self.redis = redis_client
        # TTL = 5 минут:
        # 1) уменьшает нагрузку на БД и модель при повторных запросах;
        # 2) достаточно короткий, чтобы не держать устаревшие данные слишком долго;
        # 3) после закрытия объявления кэш удаляется вручную, поэтому stale data дополнительно не накапливается.
        self.ttl_seconds = ttl_seconds

    def _item_key(self, item_id: int) -> str:
        return f"{self.ITEM_PREFIX}:{item_id}"

    def _task_key(self, task_id: int) -> str:
        return f"{self.TASK_PREFIX}:{task_id}"

    async def get_item_prediction(self, item_id: int):
        raw = await self.redis.get(self._item_key(item_id))
        if raw is None:
            return None
        return json.loads(raw)

    async def set_item_prediction(self, item_id: int, value: dict):
        await self.redis.set(
            self._item_key(item_id),
            json.dumps(value),
            ex=self.ttl_seconds,
        )

    async def delete_item_prediction(self, item_id: int):
        await self.redis.delete(self._item_key(item_id))

    async def get_task_result(self, task_id: int):
        raw = await self.redis.get(self._task_key(task_id))
        if raw is None:
            return None
        return json.loads(raw)

    async def set_task_result(self, task_id: int, value: dict):
        await self.redis.set(
            self._task_key(task_id),
            json.dumps(value),
            ex=self.ttl_seconds,
        )

    async def delete_task_result(self, task_id: int):
        await self.redis.delete(self._task_key(task_id))

    async def delete_task_results(self, task_ids):
        if not task_ids:
            return
        keys = [self._task_key(task_id) for task_id in task_ids]
        await self.redis.delete(*keys)
