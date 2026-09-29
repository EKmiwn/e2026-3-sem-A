-- Boliga Insight Hub – samlet data-dashboard med AI-sparringspartner

CREATE TABLE property (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    address               TEXT NOT NULL,
    postcode              TEXT NOT NULL,
    city                  TEXT NOT NULL,
    property_type         TEXT NOT NULL,          -- Villa, Ejerlejlighed, Rækkehus
    size_m2               INTEGER NOT NULL,
    rooms                 INTEGER,
    built_year            INTEGER,
    energy_label          TEXT,
    list_price            INTEGER NOT NULL,
    listed_date           TEXT NOT NULL,
    ai_valuation          INTEGER,                -- Boligas AI-vurderingsmodel
    valuation_uncertainty REAL NOT NULL DEFAULT 6.6,
    sales_channel         TEXT NOT NULL DEFAULT 'Mægler' CHECK (sales_channel IN ('Mægler', 'Selvsalg'))
);

CREATE TABLE price_change (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id  INTEGER NOT NULL REFERENCES property(id) ON DELETE CASCADE,
    changed_date TEXT NOT NULL,
    old_price    INTEGER NOT NULL,
    new_price    INTEGER NOT NULL
);

-- DinGeo: risiko, miljø og nabolag for adressen
CREATE TABLE geo_data (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id       INTEGER NOT NULL UNIQUE REFERENCES property(id) ON DELETE CASCADE,
    flood_risk        TEXT NOT NULL CHECK (flood_risk IN ('lav', 'middel', 'høj')),
    cloudburst_risk   TEXT NOT NULL CHECK (cloudburst_risk IN ('lav', 'middel', 'høj')),
    radon_risk        TEXT NOT NULL CHECK (radon_risk IN ('lav', 'middel', 'høj')),
    noise_db          INTEGER,
    school_m          INTEGER,
    station_m         INTEGER,
    grocery_m         INTEGER,
    green_area_m      INTEGER,
    burglary_index    INTEGER,        -- 100 = landsgennemsnit
    broadband_mbit    INTEGER
);

-- Solgte boliger i området (Boliga salgsdata) – bruges til m²-pris og liggetid
CREATE TABLE area_sale (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    postcode       TEXT NOT NULL,
    address        TEXT NOT NULL,
    sold_date      TEXT NOT NULL,
    price          INTEGER NOT NULL,
    size_m2        INTEGER NOT NULL,
    days_on_market INTEGER NOT NULL
);

-- Tvangsauktioner.dk
CREATE TABLE auction (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    postcode     TEXT NOT NULL,
    address      TEXT NOT NULL,
    auction_date TEXT NOT NULL,
    min_bid      INTEGER
);

CREATE TABLE user (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE saved_property (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    property_id INTEGER NOT NULL REFERENCES property(id) ON DELETE CASCADE,
    note        TEXT,
    saved_at    TEXT NOT NULL,
    UNIQUE (user_id, property_id)
);

-- AI-samtaler logges pr. bruger og bolig (FK7)
CREATE TABLE conversation (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    property_id INTEGER NOT NULL REFERENCES property(id) ON DELETE CASCADE,
    started_at  TEXT NOT NULL,
    UNIQUE (user_id, property_id)
);

CREATE TABLE message (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('bruger', 'ai')),
    text            TEXT NOT NULL,
    sources         TEXT,
    created_at      TEXT NOT NULL
);
