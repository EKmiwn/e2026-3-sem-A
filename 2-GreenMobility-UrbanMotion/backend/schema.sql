-- GreenMobility – reservation af hotspotparkering

CREATE TABLE customer (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL,
    email    TEXT NOT NULL UNIQUE,
    car_plate TEXT
);

CREATE TABLE hotspot (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    address    TEXT NOT NULL,
    area       TEXT,
    lat        REAL,
    lng        REAL,
    directions TEXT            -- vejvisning til pladserne ("Jeg kan ikke finde pladsen")
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

-- Højst én aktiv reservation pr. kunde og pr. plads (sidste værn mod dobbeltbooking)
CREATE UNIQUE INDEX one_active_per_customer ON reservation(customer_id) WHERE status = 'AKTIV';
CREATE UNIQUE INDEX one_active_per_spot ON reservation(spot_id) WHERE status = 'AKTIV';

-- Kundeservice: medarbejdere, henvendelser og chatbeskeder
CREATE TABLE staff (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL,
    role   TEXT NOT NULL,
    online INTEGER NOT NULL DEFAULT 1 CHECK (online IN (0, 1))
);

CREATE TABLE support_case (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    case_no        TEXT NOT NULL UNIQUE,
    customer_id    INTEGER NOT NULL REFERENCES customer(id),
    reservation_id INTEGER REFERENCES reservation(id),
    staff_id       INTEGER REFERENCES staff(id),
    type           TEXT NOT NULL CHECK (type IN ('KONTAKT', 'PLADS_OPTAGET', 'KAN_IKKE_FINDE')),
    status         TEXT NOT NULL DEFAULT 'AABEN' CHECK (status IN ('AABEN', 'LUKKET')),
    created_at     TEXT NOT NULL
);

CREATE TABLE support_message (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id  INTEGER NOT NULL REFERENCES support_case(id) ON DELETE CASCADE,
    sender   TEXT NOT NULL CHECK (sender IN ('KUNDE', 'MEDARBEJDER', 'SYSTEM')),
    text     TEXT NOT NULL,
    sent_at  TEXT NOT NULL
);

-- Hændelseslog til administratoren
CREATE TABLE event_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    event       TEXT NOT NULL,
    spot_id     INTEGER,
    reservation_id INTEGER,
    message     TEXT
);
