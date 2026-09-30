-- AGC Biologics – informationshub for QC med Leverancer & Prioritering

CREATE TABLE team (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE user (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL,
    login  TEXT NOT NULL UNIQUE,
    role   TEXT NOT NULL CHECK (role IN ('leder', 'medarbejder', 'administrator')),
    team_id INTEGER REFERENCES team(id),
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE category (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    keywords TEXT NOT NULL,              -- kommasepareret liste af nøgleord/regler
    active   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE category_access (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES category(id) ON DELETE CASCADE,
    permission  TEXT NOT NULL DEFAULT 'læs' CHECK (permission IN ('læs', 'redigér')),
    UNIQUE (user_id, category_id)
);

-- D1 Kilde: original kildepost, ændres aldrig
CREATE TABLE source (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    system            TEXT NOT NULL CHECK (system IN ('Outlook', 'Teams', 'Manuel')),
    external_id       TEXT,
    sender            TEXT,
    channel           TEXT,
    title             TEXT NOT NULL,
    text              TEXT NOT NULL,
    received_at       TEXT NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'MODTAGET'
                      CHECK (processing_status IN ('MODTAGET', 'RELEVANT', 'FRAVALGT')),
    UNIQUE (system, external_id)
);

-- D2 Informationspost: redigerbart udkast med resumé, kategori og version
CREATE TABLE info (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id   INTEGER NOT NULL UNIQUE REFERENCES source(id),
    owner_id    INTEGER NOT NULL REFERENCES user(id),
    title       TEXT NOT NULL,
    summary     TEXT NOT NULL,
    category_id INTEGER REFERENCES category(id),       -- NULL = Uklassificeret
    match_basis TEXT,
    status      TEXT NOT NULL DEFAULT 'UDKAST' CHECK (status IN ('UDKAST', 'GODKENDT', 'FRAVALGT')),
    version     INTEGER NOT NULL DEFAULT 1,
    approver_id INTEGER REFERENCES user(id),
    approved_at TEXT
);

-- D4 Deling: uforanderligt snapshot af en godkendt version
CREATE TABLE share (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    info_id   INTEGER NOT NULL REFERENCES info(id),
    sender_id INTEGER NOT NULL REFERENCES user(id),
    version   INTEGER NOT NULL,
    snapshot  TEXT NOT NULL,
    shared_at TEXT NOT NULL
);

CREATE TABLE share_recipient (
    share_id INTEGER NOT NULL REFERENCES share(id) ON DELETE CASCADE,
    user_id  INTEGER NOT NULL REFERENCES user(id),
    read_at  TEXT,
    PRIMARY KEY (share_id, user_id)
);

-- D5 Hændelseslog (information og leverancer)
CREATE TABLE event (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id      INTEGER,
    info_id        INTEGER,
    deliverable_id INTEGER,
    actor_id    INTEGER,
    type        TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    details     TEXT
);

-- Simuleret connector-feed: fiktive Outlook- og Teams-poster, der endnu ikke er modtaget
CREATE TABLE test_feed (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    system      TEXT NOT NULL,
    external_id TEXT NOT NULL,
    sender      TEXT,
    channel     TEXT,
    title       TEXT NOT NULL,
    text        TEXT NOT NULL,
    delivered   INTEGER NOT NULL DEFAULT 0
);

-- D6 Leverance: prioriteret opgave med ansvarlig, deadline og status (revideret krav, afsnit 5.2)
CREATE TABLE deliverable (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT NOT NULL,
    description    TEXT,
    priority       TEXT NOT NULL CHECK (priority IN ('Business Critical', 'High', 'Normal', 'Low')),
    team_id        INTEGER REFERENCES team(id),       -- ansvarligt team
    owner_id       INTEGER REFERENCES user(id),       -- ansvarlig person
    deadline       TEXT NOT NULL,                     -- YYYY-MM-DD
    status         TEXT NOT NULL DEFAULT 'Ikke startet'
                   CHECK (status IN ('Ikke startet', 'I gang', 'Afventer', 'Blokeret', 'Afsluttet')),
    blocked_reason TEXT,
    info_id        INTEGER REFERENCES info(id),       -- F19: kobling til en informationspost
    version        INTEGER NOT NULL DEFAULT 1,
    created_by     INTEGER NOT NULL REFERENCES user(id),
    created_at     TEXT NOT NULL,
    updated_at     TEXT,
    closed_at      TEXT,
    CHECK (team_id IS NOT NULL OR owner_id IS NOT NULL)
);

CREATE TABLE deliverable_comment (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    deliverable_id INTEGER NOT NULL REFERENCES deliverable(id) ON DELETE CASCADE,
    user_id        INTEGER NOT NULL REFERENCES user(id),
    text           TEXT NOT NULL,
    created_at     TEXT NOT NULL
);
