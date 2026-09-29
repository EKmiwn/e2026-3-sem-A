-- Joe & The Juice – pantsystem for genanvendelige kopper

-- Pantbeløb og pointkurs kan justeres centralt uden ny kode
CREATE TABLE setting (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT NOT NULL UNIQUE,
    value       REAL NOT NULL,
    description TEXT
);

CREATE TABLE store (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    city          TEXT NOT NULL,
    location_type TEXT NOT NULL DEFAULT 'Gade' CHECK (location_type IN ('Gade', 'Storcenter', 'Lufthavn'))
);

-- Kundens app-konto
CREATE TABLE customer (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL,
    email  TEXT NOT NULL UNIQUE,
    points INTEGER NOT NULL DEFAULT 0 CHECK (points >= 0)
);

CREATE TABLE drink (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    price REAL NOT NULL
);

CREATE TABLE sale_order (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_no  TEXT NOT NULL UNIQUE,
    store_id    INTEGER NOT NULL REFERENCES store(id),
    customer_id INTEGER REFERENCES customer(id),     -- NULL = kunde uden app
    drink_id    INTEGER NOT NULL REFERENCES drink(id),
    price       REAL NOT NULL,
    deposit     REAL NOT NULL,
    created_at  TEXT NOT NULL
);

-- Hver kop har en unik kop-kode (QR/RFID)
CREATE TABLE cup (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    code              TEXT NOT NULL UNIQUE,
    order_id          INTEGER NOT NULL REFERENCES sale_order(id),
    status            TEXT NOT NULL DEFAULT 'UDLEVERET' CHECK (status IN ('UDLEVERET', 'RETURNERET')),
    issued_at         TEXT NOT NULL,
    returned_at       TEXT,
    returned_store_id INTEGER REFERENCES store(id)
);

-- Log over alle pant-transaktioner (til revision og bæredygtighedsrapportering)
CREATE TABLE deposit_transaction (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    cup_id      INTEGER REFERENCES cup(id),
    customer_id INTEGER REFERENCES customer(id),
    store_id    INTEGER NOT NULL REFERENCES store(id),
    type        TEXT NOT NULL CHECK (type IN ('PANT_BETALT', 'RETUR_GODKENDT', 'RETUR_AFVIST', 'POINT_INDLØST')),
    amount      REAL NOT NULL DEFAULT 0,
    points      INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL,
    note        TEXT
);
