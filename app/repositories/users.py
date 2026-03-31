class UserRepository:
    def __init__(self, pool):
        self.pool = pool

    async def create(self, seller_id: int, is_verified_seller: bool) -> dict:
        query = """
        INSERT INTO users (seller_id, is_verified_seller)
        VALUES ($1, $2)
        RETURNING seller_id, is_verified_seller
        """
        row = await self.pool.fetchrow(query, seller_id, is_verified_seller)
        return dict(row)

    async def get_by_seller_id(self, seller_id: int) -> dict:
        query = """
        SELECT seller_id, is_verified_seller
        FROM users
        WHERE seller_id = $1
        """
        row = await self.pool.fetchrow(query, seller_id)
        return dict(row) if row else None