-- StockUP – Strandvejsristeriet: lager af grønne kaffesække og salgsklare kaffeposer

CREATE TABLE green_coffee (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    origin      TEXT,
    supplier    TEXT,
    cost_per_kg REAL,
    min_sacks   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE sack (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    green_coffee_id INTEGER NOT NULL REFERENCES green_coffee(id),
    lot_number      TEXT NOT NULL UNIQUE,
    received_date   TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    initial_kg      REAL NOT NULL DEFAULT 80,
    remaining_kg    REAL NOT NULL DEFAULT 80 CHECK (remaining_kg >= 0),
    status          TEXT NOT NULL DEFAULT 'PAA_LAGER'
                    CHECK (status IN ('PAA_LAGER', 'I_BRUG', 'REST', 'TOM'))
);

CREATE TABLE product (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sku             TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    bag_size_g      INTEGER NOT NULL DEFAULT 250,
    green_coffee_id INTEGER REFERENCES green_coffee(id),   -- NULL = blanding
    stock_bags      INTEGER NOT NULL DEFAULT 0 CHECK (stock_bags >= 0),
    min_bags        INTEGER NOT NULL DEFAULT 20,
    price           REAL
);

CREATE TABLE roast (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sack_id       INTEGER NOT NULL REFERENCES sack(id),
    product_id    INTEGER NOT NULL REFERENCES product(id),
    kg_used       REAL NOT NULL,
    bags_produced INTEGER NOT NULL,
    performed_by  TEXT,
    roasted_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE sale (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES product(id),
    bags       INTEGER NOT NULL CHECK (bags > 0),
    channel    TEXT NOT NULL DEFAULT 'BUTIK',
    sold_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Append-only log over alt, der ændrer lageret
CREATE TABLE movement (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    movement_type TEXT NOT NULL,
    entity_type   TEXT NOT NULL,
    entity_id     INTEGER NOT NULL,
    quantity      REAL NOT NULL,
    unit          TEXT NOT NULL,
    note          TEXT
);
