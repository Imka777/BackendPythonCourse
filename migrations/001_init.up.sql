CREATE TABLE IF NOT EXISTS users (
    seller_id BIGINT PRIMARY KEY,
    is_verified_seller BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    item_id BIGINT PRIMARY KEY,
    seller_id BIGINT NOT NULL REFERENCES users(seller_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category INTEGER NOT NULL CHECK (category > 0),
    images_qty INTEGER NOT NULL CHECK (images_qty >= 0)
);

CREATE INDEX IF NOT EXISTS idx_items_seller_id ON items(seller_id);
