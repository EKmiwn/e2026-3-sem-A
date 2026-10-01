-- LoopAAS – gamification af New Loops retursystem

-- Pointsatser og grænser kan justeres uden ny kode
CREATE TABLE setting (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key         TEXT NOT NULL UNIQUE,
    value       REAL NOT NULL,
    description TEXT
);

-- User: brugerprofil med pointsaldo (FR01, FR04)
CREATE TABLE app_user (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    points     INTEGER NOT NULL DEFAULT 0 CHECK (points >= 0),
    created_at TEXT NOT NULL
);

-- Restauranter og takeaway-steder, der udleverer New Loop-emballage – og returpunkter
CREATE TABLE location (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    address TEXT NOT NULL,
    kind    TEXT NOT NULL CHECK (kind IN ('RESTAURANT', 'RETURPUNKT'))
);

-- Hver emballage har en unik kode (QR), så en returnering kan identificeres digitalt
CREATE TABLE package (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL CHECK (type IN ('KOP', 'SKÅL', 'BOKS')),
    location_id INTEGER NOT NULL REFERENCES location(id),     -- hvor emballagen er udleveret
    issued_at   TEXT NOT NULL
);

-- Return: godkendt returnering og optjente point (FR02, FR03)
CREATE TABLE return_event (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    package_id    INTEGER NOT NULL UNIQUE REFERENCES package(id),   -- samme emballage kan kun returneres én gang
    location_id   INTEGER NOT NULL REFERENCES location(id),
    points_earned INTEGER NOT NULL CHECK (points_earned > 0),
    returned_at   TEXT NOT NULL
);

CREATE TABLE partner (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    address  TEXT
);

-- Reward hos en samarbejdspartner (FR05)
CREATE TABLE reward (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    partner_id      INTEGER NOT NULL REFERENCES partner(id),
    name            TEXT NOT NULL,
    description     TEXT,
    points_required INTEGER NOT NULL CHECK (points_required > 0),
    stock           INTEGER CHECK (stock IS NULL OR stock >= 0),   -- NULL = ubegrænset
    active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

-- Redemption: indløsning med en kode, som partneren bekræfter (FR06 – FR08)
CREATE TABLE redemption (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    reward_id   INTEGER NOT NULL REFERENCES reward(id),
    points_used INTEGER NOT NULL,
    code        TEXT NOT NULL UNIQUE,
    status      TEXT NOT NULL DEFAULT 'AKTIV' CHECK (status IN ('AKTIV', 'BRUGT')),
    redeemed_at TEXT NOT NULL,
    used_at     TEXT
);
