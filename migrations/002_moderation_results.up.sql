CREATE TABLE IF NOT EXISTS moderation_results (
    id SERIAL PRIMARY KEY,
    item_id BIGINT NOT NULL REFERENCES items(item_id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed', 'failed')),
    is_violation BOOLEAN NULL,
    probability FLOAT NULL,
    error_message TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS idx_moderation_results_item_id
    ON moderation_results(item_id);

CREATE INDEX IF NOT EXISTS idx_moderation_results_status
    ON moderation_results(status);
