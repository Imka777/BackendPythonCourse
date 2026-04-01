class ItemRepository:
    def __init__(self, pool):
        self.pool = pool

    async def create(
        self,
        item_id: int,
        seller_id: int,
        name: str,
        description: str,
        category: int,
        images_qty: int,
    ) -> dict:
        query = """
        INSERT INTO items (item_id, seller_id, name, description, category, images_qty)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING item_id, seller_id, name, description, category, images_qty, is_closed
        """
        row = await self.pool.fetchrow(
            query,
            item_id,
            seller_id,
            name,
            description,
            category,
            images_qty,
        )
        return dict(row)

    async def get_by_item_id(self, item_id: int) -> dict:
        query = """
        SELECT item_id, seller_id, name, description, category, images_qty, is_closed
        FROM items
        WHERE item_id = $1 AND is_closed = FALSE
        """
        row = await self.pool.fetchrow(query, item_id)
        return dict(row) if row else None

    async def close_and_delete(self, item_id: int) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    UPDATE items
                    SET is_closed = TRUE
                    WHERE item_id = $1 AND is_closed = FALSE
                    RETURNING item_id
                    """,
                    item_id,
                )

                if row is None:
                    return False

                await conn.execute(
                    "DELETE FROM moderation_results WHERE item_id = $1",
                    item_id,
                )
                await conn.execute(
                    "DELETE FROM items WHERE item_id = $1",
                    item_id,
                )

        return True