-- GreenMobility – reservation af hotspotparkering

CREATE TABLE customer (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL,
    email    TEXT NOT NULL UNIQUE,
    car_plate TEXT
);

CREATE TABLE hotspot (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    address TEXT NOT NULL,
    area    TEXT
);

CREATE TABLE spot (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    hotspot_id INTEGER NOT NULL REFERENCES hotspot(id) ON DELETE CASCADE,
    label      TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'LEDIG'
               CHECK (status IN ('LEDIG', 'RESERVERET', 'OPTAGET', 'SPAERRET')),
    UNIQUE (hotspot_id, label)
);

CREATE TABLE reservation (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_no   TEXT NOT NULL UNIQUE,
    customer_id      INTEGER NOT NULL REFERENCES customer(id),
    spot_id          INTEGER NOT NULL REFERENCES spot(id),
    status           TEXT NOT NULL DEFAULT 'AKTIV'
                     CHECK (status IN ('AKTIV', 'BENYTTET', 'ANNULLERET', 'UDLOEBET')),
    created_at       TEXT NOT NULL,
    arrival_deadline TEXT NOT NULL,
    arrived_at       TEXT,
    closed_at        TEXT
);

-- Højst én aktiv reservation pr. kunde og pr. plads
CREATE UNIQUE INDEX one_active_per_customer ON reservation(customer_id) WHERE status = 'AKTIV';
CREATE UNIQUE INDEX one_active_per_spot ON reservation(spot_id) WHERE status = 'AKTIV';

-- Hændelseslog til administratoren
CREATE TABLE event_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    event       TEXT NOT NULL,
    spot_id     INTEGER,
    reservation_id INTEGER,
    message     TEXT
);
