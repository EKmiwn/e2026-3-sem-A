-- Min Hessel – samlet kundeportal for Ejner Hessels kunder
-- Version 2 (kravspecifikation-2.md): flere biloplysninger, billeder, reparationslog og forbrug og klima

CREATE TABLE customer (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    email   TEXT NOT NULL UNIQUE,
    phone   TEXT,
    address TEXT
);

CREATE TABLE workshop (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    address TEXT NOT NULL,
    brands  TEXT NOT NULL            -- mærker værkstedet servicerer, kommasepareret
);

CREATE TABLE car (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id          INTEGER NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    brand                TEXT NOT NULL CHECK (brand IN ('Mercedes-Benz', 'Renault', 'Dacia', 'Ford')),
    model                TEXT NOT NULL,
    registration         TEXT NOT NULL UNIQUE,
    vin                  TEXT,
    year                 INTEGER,
    fuel                 TEXT NOT NULL CHECK (fuel IN ('Benzin', 'Diesel', 'El', 'Hybrid', 'Mild hybrid', 'Plug-in hybrid')),
    gearbox              TEXT NOT NULL DEFAULT 'Automatisk' CHECK (gearbox IN ('Automatisk', 'Manuel')),
    body_type            TEXT NOT NULL DEFAULT 'HATCHBACK'
                         CHECK (body_type IN ('LILLE', 'HATCHBACK', 'SEDAN', 'STATIONCAR', 'SUV', 'MPV', 'VAREVOGN')),
    color                TEXT NOT NULL DEFAULT '#9aa5ad',      -- bruges i bilens illustration
    image_url            TEXT,                                 -- valgfrit rigtigt billede af modellen
    mileage_km           INTEGER,
    ownership            TEXT NOT NULL DEFAULT 'Købt' CHECK (ownership IN ('Købt', 'Leaset')),
    next_service_date    TEXT,
    next_inspection_date TEXT,                                 -- næste syn
    warranty_until       TEXT,                                 -- nyvognsgaranti
    battery_kwh          REAL,                                 -- elbiler og plug-in
    range_km             INTEGER,                              -- rækkevidde på el
    leasing_company      TEXT,
    leasing_end          TEXT,
    leasing_km_per_year  INTEGER,
    leasing_monthly      REAL
);

CREATE TABLE service_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id      INTEGER NOT NULL REFERENCES car(id) ON DELETE CASCADE,
    date        TEXT NOT NULL,
    type        TEXT NOT NULL,
    workshop_id INTEGER REFERENCES workshop(id),
    mileage_km  INTEGER,
    price       REAL,
    description TEXT
);

CREATE TABLE booking (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id       INTEGER NOT NULL REFERENCES car(id) ON DELETE CASCADE,
    workshop_id  INTEGER NOT NULL REFERENCES workshop(id),
    date         TEXT NOT NULL,
    time         TEXT NOT NULL,
    service_type TEXT NOT NULL,
    notes        TEXT,
    status       TEXT NOT NULL DEFAULT 'BEKRÆFTET' CHECK (status IN ('BEKRÆFTET', 'AFLYST', 'GENNEMFØRT')),
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE repair (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id          INTEGER NOT NULL REFERENCES car(id) ON DELETE CASCADE,
    workshop_id     INTEGER REFERENCES workshop(id),
    description     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'MODTAGET'
                    CHECK (status IN ('MODTAGET', 'DIAGNOSE', 'VENTER_PÅ_DELE', 'I_GANG', 'KLAR_TIL_AFHENTNING', 'AFHENTET')),
    estimated_ready TEXT,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    message         TEXT                                       -- seneste besked til kunden
);

-- Log over status og beskeder fra værkstedet – vises samlet under "Reparationsstatus"
CREATE TABLE repair_update (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id  INTEGER NOT NULL REFERENCES repair(id) ON DELETE CASCADE,
    status     TEXT NOT NULL,
    message    TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE document (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    car_id      INTEGER REFERENCES car(id) ON DELETE SET NULL,
    title       TEXT NOT NULL,
    category    TEXT NOT NULL CHECK (category IN ('Aftale', 'Faktura', 'Garanti', 'Forsikring', 'Andet')),
    date        TEXT NOT NULL,
    description TEXT
);

-- Forbrug og klima: kørte km og forbrugt brændstof (liter) eller strøm (kWh) pr. måned
CREATE TABLE consumption_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id     INTEGER NOT NULL REFERENCES car(id) ON DELETE CASCADE,
    month      TEXT NOT NULL,                                  -- fx 2026-09
    km         INTEGER NOT NULL CHECK (km > 0),
    amount     REAL NOT NULL CHECK (amount > 0),
    UNIQUE (car_id, month)
);

-- Kundens mål for forbruget (liter eller kWh pr. 100 km)
CREATE TABLE consumption_goal (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id         INTEGER NOT NULL UNIQUE REFERENCES car(id) ON DELETE CASCADE,
    target_per_100 REAL NOT NULL CHECK (target_per_100 > 0),
    created_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Tidsstemplet for reparationsstatus opdateres automatisk, når værkstedet ændrer status
CREATE TRIGGER repair_touch AFTER UPDATE OF status, message, estimated_ready ON repair
BEGIN
    UPDATE repair SET updated_at = datetime('now', 'localtime') WHERE id = NEW.id;
END;

-- Hver ny reparation og hver ændring af status eller besked logges, så kunden kan se forløbet
CREATE TRIGGER repair_log_insert AFTER INSERT ON repair
BEGIN
    INSERT INTO repair_update (repair_id, status, message) VALUES (NEW.id, NEW.status, NEW.message);
END;

CREATE TRIGGER repair_log_update AFTER UPDATE OF status, message ON repair
WHEN NEW.status IS NOT OLD.status OR NEW.message IS NOT OLD.message
BEGIN
    INSERT INTO repair_update (repair_id, status, message)
    VALUES (NEW.id, NEW.status, CASE WHEN NEW.message IS NOT OLD.message THEN NEW.message END);
END;
