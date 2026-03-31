class ModerationResultRepository:
    def __init__(self, pool):
        self.pool = pool

    async def create_pending(self, item_id: int):
        query = """
        INSERT INTO moderation_results (item_id, status, created_at)
        VALUES ($1, 'pending', NOW())
        RETURNING id, item_id, status, is_violation, probability, error_message, created_at, processed_at
        """
        row = await self.pool.fetchrow(query, item_id)
        return dict(row)

    async def get_by_id(self, task_id: int):
        query = """
        SELECT id, item_id, status, is_violation, probability, error_message, created_at, processed_at
        FROM moderation_results
        WHERE id = $1
        """
        row = await self.pool.fetchrow(query, task_id)
        return dict(row) if row else None

    async def update_completed(self, task_id: int, is_violation: bool, probability: float):
        query = """
        UPDATE moderation_results
        SET status = 'completed',
            is_violation = $2,
            probability = $3,
            error_message = NULL,
            processed_at = NOW()
        WHERE id = $1
        RETURNING id, item_id, status, is_violation, probability, error_message, created_at, processed_at
        """
        row = await self.pool.fetchrow(query, task_id, is_violation, probability)
        return dict(row) if row else None

    async def update_failed(self, task_id: int, error_message: str):
        query = """
        UPDATE moderation_results
        SET status = 'failed',
            error_message = $2,
            processed_at = NOW()
        WHERE id = $1
        RETURNING id, item_id, status, is_violation, probability, error_message, created_at, processed_at
        """
        row = await self.pool.fetchrow(query, task_id, error_message)
        return dict(row) if row else None
