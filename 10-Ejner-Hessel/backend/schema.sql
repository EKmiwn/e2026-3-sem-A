-- Min Hessel – samlet kundeportal for Ejner Hessels kunder

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
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id       INTEGER NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    brand             TEXT NOT NULL CHECK (brand IN ('Mercedes-Benz', 'Renault', 'Dacia', 'Ford')),
    model             TEXT NOT NULL,
    registration      TEXT NOT NULL UNIQUE,
    vin               TEXT,
    year              INTEGER,
    fuel              TEXT,
    mileage_km        INTEGER,
    ownership         TEXT NOT NULL DEFAULT 'Købt' CHECK (ownership IN ('Købt', 'Leaset')),
    next_service_date TEXT
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
    description     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'MODTAGET'
                    CHECK (status IN ('MODTAGET', 'DIAGNOSE', 'VENTER_PÅ_DELE', 'I_GANG', 'KLAR_TIL_AFHENTNING', 'AFHENTET')),
    estimated_ready TEXT,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    message         TEXT
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

-- Tidsstemplet for reparationsstatus opdateres automatisk, når værkstedet ændrer status
CREATE TRIGGER repair_touch AFTER UPDATE OF status, message, estimated_ready ON repair
BEGIN
    UPDATE repair SET updated_at = datetime('now', 'localtime') WHERE id = NEW.id;
END;
