-- Amitylux – experience finder and inquiry journey

CREATE TABLE destination (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT NOT NULL,
    country            TEXT NOT NULL,
    description        TEXT,
    high_season_months TEXT NOT NULL DEFAULT '6,7,8'   -- comma separated month numbers
);

-- The three product types that customers must be able to compare (F-02)
CREATE TABLE product_type (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE CHECK (code IN ('public', 'private', 'customised')),
    name            TEXT NOT NULL,
    group_form      TEXT NOT NULL,
    flexibility     TEXT NOT NULL,
    personalisation TEXT NOT NULL,
    price_principle TEXT NOT NULL,
    booking_form    TEXT NOT NULL,
    included        TEXT NOT NULL,
    not_included    TEXT NOT NULL
);

CREATE TABLE experience (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id     INTEGER NOT NULL REFERENCES destination(id),
    type_code          TEXT NOT NULL REFERENCES product_type(code),
    title              TEXT NOT NULL,
    description        TEXT,
    price_per_person   REAL,            -- NULL = price on request
    price_level        TEXT NOT NULL CHECK (price_level IN ('low', 'medium', 'high', 'premium')),
    languages          TEXT NOT NULL,   -- comma separated
    interests          TEXT NOT NULL,   -- comma separated
    min_group          INTEGER NOT NULL DEFAULT 1,
    max_group          INTEGER NOT NULL DEFAULT 12,
    duration_hours     REAL,
    included           TEXT,
    not_included       TEXT,
    value_points       TEXT,            -- ';' separated
    guide_name         TEXT,
    guide_expertise    TEXT,
    rating             REAL,
    review_count       INTEGER DEFAULT 0,
    review_quote       TEXT,
    sustainable_label  TEXT,            -- e.g. 'Walking', 'Bike', NULL
    off_the_beaten_track INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE addon (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT,
    price_hint  TEXT,
    interest    TEXT                    -- interest this add-on is relevant for
);

CREATE TABLE inquiry (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    reference        TEXT NOT NULL UNIQUE,
    created_at       TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'IN_PROGRESS', 'ANSWERED', 'CLOSED')),
    contact_name     TEXT NOT NULL,
    contact_email    TEXT NOT NULL,
    contact_phone    TEXT,
    destination_id   INTEGER NOT NULL REFERENCES destination(id),
    experience_id    INTEGER REFERENCES experience(id),
    date_from        TEXT,
    date_to          TEXT,
    group_type       TEXT,
    group_size       INTEGER,
    interests        TEXT,
    language         TEXT,
    pace             TEXT,
    budget           TEXT,
    addons           TEXT,
    guide_language   TEXT,
    guide_focus      TEXT,
    guide_style      TEXT,
    notes            TEXT,
    recommended_type TEXT
);

-- "Talk to a person" requests from any step in the flow (F-09)
CREATE TABLE help_request (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name       TEXT NOT NULL,
    contact    TEXT NOT NULL,
    step       TEXT,
    context    TEXT,
    status     TEXT NOT NULL DEFAULT 'NEW'
);
