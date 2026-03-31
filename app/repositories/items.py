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
        RETURNING item_id, seller_id, name, description, category, images_qty
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
        SELECT item_id, seller_id, name, description, category, images_qty
        FROM items
        WHERE item_id = $1
        """
        row = await self.pool.fetchrow(query, item_id)
        return dict(row) if row else None