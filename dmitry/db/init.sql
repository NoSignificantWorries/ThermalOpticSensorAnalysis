CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_line_id INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    spatial_metadata TEXT,  -- JSON хранится как TEXT
    value REAL  -- вместо DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON sensor_data(timestamp);
