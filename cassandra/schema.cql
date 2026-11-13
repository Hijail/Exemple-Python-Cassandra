CREATE KEYSPACE IF NOT EXISTS game_analytics
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS game_analytics.events_by_player_day (
    player_id text,
    event_day date,
    occurred_at timestamp,
    event_id text,
    event_type text,
    session_id text,
    level_id text,
    score double,
    amount double,
    currency text,
    PRIMARY KEY ((player_id, event_day), occurred_at, event_id)
) WITH CLUSTERING ORDER BY (occurred_at DESC, event_id ASC);

CREATE TABLE IF NOT EXISTS game_analytics.events_by_type_day (
    event_type text,
    event_day date,
    occurred_at timestamp,
    event_id text,
    player_id text,
    session_id text,
    level_id text,
    amount double,
    currency text,
    PRIMARY KEY ((event_type, event_day), occurred_at, event_id)
) WITH CLUSTERING ORDER BY (occurred_at DESC, event_id ASC);

CREATE TABLE IF NOT EXISTS game_analytics.purchases_by_player_month (
    player_id text,
    purchase_month text,
    occurred_at timestamp,
    event_id text,
    product_id text,
    category text,
    quantity int,
    amount double,
    currency text,
    anomaly_score double,
    is_anomaly boolean,
    PRIMARY KEY ((player_id, purchase_month), occurred_at, event_id)
) WITH CLUSTERING ORDER BY (occurred_at DESC, event_id ASC);
