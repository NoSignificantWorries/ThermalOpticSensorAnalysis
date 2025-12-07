CREATE DATABASE IF NOT EXISTS sensors_db
ENGINE = Atomic COMMENT 'Database for sensors data';

USE sensors_db;

CREATE TABLE IF NOT EXISTS config0
(
  sensor_id UInt32,
  label Nullable(String),
  description Nullable(String),
  created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (sensor_id)
COMMENT 'Config #0 created as default one';

CREATE TABLE IF NOT EXISTS group0
(
  sensor_id UInt32,
  group_id UInt32,
  start Float32,
  end Float32
)
ENGINE = MergeTree
ORDER BY (sensor_id, group_id)
COMMENT 'Groups table #0 paired with config0 table';

CREATE TABLE IF NOT EXISTS segment0
(
  sensor_id UInt32,
  group_id UInt32,
  segment_id UInt32,
  start Float32,
  end Float32
)
ENGINE = MergeTree
ORDER BY (sensor_id, group_id, segment_id)
COMMENT 'Segments table #0 paired with group0 table';

CREATE TABLE IF NOT EXISTS measurements
(
  timestamp DateTime64(3, 'UTC'),
  sensor_id UInt32,
  group_id UInt32,
  distance Float32,
  temp Float32
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, group_id, sensor_id, distance)
SETTINGS index_granularity = 8192
COMMENT 'Main table of measurements';

