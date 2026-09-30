-- Amitylux Experience Compass – few, explainable experience suggestions from an approved catalogue
-- Kravgrundlag: ../kravspecifikation-2.md (K1–K12)

-- K11: the same structure is used for every destination; only the local content differs
CREATE TABLE destination (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    name               TEXT NOT NULL,
    country            TEXT NOT NULL,
    description        TEXT,
    high_season_months TEXT NOT NULL DEFAULT '6,7,8'   -- comma separated month numbers
);

-- K4: the three product types the customer must be able to tell apart
CREATE TABLE product_type (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE CHECK (code IN ('public', 'private', 'customised')),
    name            TEXT NOT NULL,
    short           TEXT NOT NULL,                -- one-line explanation
    group_form      TEXT NOT NULL,
    flexibility     TEXT NOT NULL,
    personalisation TEXT NOT NULL,
    booking_form    TEXT NOT NULL,
    price_principle TEXT NOT NULL,
    best_for        TEXT NOT NULL
);

-- K5 + K9: the approved Amitylux catalogue. Only rows with catalogue_status = 'approved' are ever suggested.
CREATE TABLE experience (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    destination_id      INTEGER NOT NULL REFERENCES destination(id),
    type_code           TEXT NOT NULL REFERENCES product_type(code),
    title               TEXT NOT NULL,
    description         TEXT NOT NULL,
    location            TEXT NOT NULL,           -- area / meeting point
    experience_type     TEXT NOT NULL,           -- e.g. Walking tour, Food tasting, Bike tour
    duration_hours      REAL NOT NULL,
    min_group           INTEGER NOT NULL DEFAULT 1,
    max_group           INTEGER NOT NULL DEFAULT 12,
    languages           TEXT NOT NULL,           -- comma separated, languages the catalogue confirms
    interests           TEXT NOT NULL,           -- comma separated
    pace                TEXT NOT NULL CHECK (pace IN ('relaxed', 'moderate', 'active')),
    practical           TEXT NOT NULL DEFAULT '',-- comma separated: step_free, kid_friendly, short_walks, indoor_option
    transport_modes     TEXT NOT NULL DEFAULT '',-- comma separated (K12): walk, bike, public_transport, car, boat
    mobility_note       TEXT,                    -- K12: neutral, verified description – no climate claims
    included            TEXT NOT NULL,
    not_included        TEXT NOT NULL,
    price_from          REAL,                    -- NULL = price on request
    price_unit          TEXT NOT NULL CHECK (price_unit IN ('person', 'group', 'request')),
    value_points        TEXT NOT NULL DEFAULT '',-- ';' separated, must match value_claim.code (K7)
    local_alternative   INTEGER NOT NULL DEFAULT 0, -- K6: local feel / outside the busiest areas
    local_note          TEXT,                    -- K6: why it is a local choice (experience, not environment)
    rating              REAL,
    review_count        INTEGER NOT NULL DEFAULT 0,
    review_quote        TEXT,
    review_source       TEXT,
    needs_confirmation  TEXT NOT NULL DEFAULT '',-- K9: ';' separated items that are never shown as facts
    catalogue_status    TEXT NOT NULL DEFAULT 'approved' CHECK (catalogue_status IN ('approved', 'draft')),
    approved_by         TEXT,
    approved_at         TEXT
);

-- K7: documented Amitylux value – every claim has its evidence next to it
CREATE TABLE value_claim (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    code     TEXT NOT NULL UNIQUE,
    label    TEXT NOT NULL,
    text     TEXT NOT NULL,
    evidence TEXT NOT NULL
);

-- K8: elements the customer can add to a private / customised request
CREATE TABLE addon (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT,
    price_hint  TEXT NOT NULL
);

-- K8: structured request handed over to a member of staff
CREATE TABLE inquiry (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    reference        TEXT NOT NULL UNIQUE,
    created_at       TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'IN_PROGRESS', 'ANSWERED', 'CLOSED')),
    wanted_type      TEXT NOT NULL CHECK (wanted_type IN ('public', 'private', 'customised')),
    contact_name     TEXT NOT NULL,
    contact_email    TEXT NOT NULL,
    contact_phone    TEXT,
    destination_id   INTEGER NOT NULL REFERENCES destination(id),
    travel_date      TEXT,
    group_type       TEXT,
    group_size       INTEGER,
    interests        TEXT,
    pace             TEXT,
    language         TEXT,
    practical        TEXT,
    experience_ids   TEXT,                       -- comma separated suggestions the customer kept
    addons           TEXT,
    customer_unsure  TEXT,                       -- what the customer themselves is unsure about
    notes            TEXT
);

-- K8: "Talk to a person" from any step – the answers so far are attached, so nothing is lost
CREATE TABLE help_request (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name       TEXT NOT NULL,
    contact    TEXT NOT NULL,
    step       TEXT,
    context    TEXT,
    answers    TEXT,                             -- JSON snapshot of the preferences at the time
    status     TEXT NOT NULL DEFAULT 'NEW'
);
