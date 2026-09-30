-- Sunny AI – beslutningsstøtte til ugeplan og opslag hos Sunny Juice
-- Mængder er heltal i tusindedele af varens basisenhed (1 stk = 1000, 0,5 L = 500).
-- Tid er hele minutter, datoer er YYYY-MM-DD og tidspunkter YYYY-MM-DD HH:MM.

-- Demobrugere. Valget i frontenden er ikke et login og ikke adgangskontrol (N10).
CREATE TABLE bruger (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    navn  TEXT NOT NULL,
    rolle TEXT NOT NULL
);

-- Demo-ur: beregningstidspunktet kan fastlåses, så test giver samme resultat
CREATE TABLE indstilling (
    noegle TEXT PRIMARY KEY,
    vaerdi TEXT NOT NULL
);

-- D1 Snapshot: samlet kopi af kildedata fra den simulerede Uniconta-adapter (F01)
CREATE TABLE snapshot (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    source            TEXT NOT NULL DEFAULT 'demo',
    source_updated_at TEXT NOT NULL,
    imported_at       TEXT NOT NULL,
    schema_version    TEXT NOT NULL DEFAULT '1.0',
    beskrivelse       TEXT
);

CREATE TABLE vare (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    varenummer TEXT NOT NULL UNIQUE,
    navn       TEXT NOT NULL,
    type       TEXT NOT NULL CHECK (type IN ('råvare', 'færdigvare')),
    basisenhed TEXT CHECK (basisenhed IN ('L', 'kg', 'stk'))   -- NULL = manglende enhed (datafejl)
);

CREATE TABLE produktionsrate (
    vare_id         INTEGER PRIMARY KEY REFERENCES vare(id),
    enheder_pr_time INTEGER NOT NULL CHECK (enheder_pr_time > 0)
);

-- Kildedata tjekkes af valideringen (F02), ikke af CHECK, så fejl i kilden kan vises frem for at blive afvist
CREATE TABLE lagerbatch (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id        INTEGER NOT NULL REFERENCES snapshot(id),
    vare_id            INTEGER NOT NULL REFERENCES vare(id),
    batchnummer        TEXT NOT NULL,
    fysisk_maengde     INTEGER NOT NULL,
    reserveret_maengde INTEGER NOT NULL DEFAULT 0,
    udloebsdato        TEXT,                                   -- NULL = ukendt udløb
    kvalitetsstatus    TEXT NOT NULL DEFAULT 'frigivet' CHECK (kvalitetsstatus IN ('frigivet', 'spærret', 'karantæne')),
    data_afklaret      INTEGER NOT NULL DEFAULT 1,
    UNIQUE (snapshot_id, batchnummer)
);

CREATE TABLE ordrelinje (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id     INTEGER NOT NULL REFERENCES snapshot(id),
    ordre_id        TEXT NOT NULL,
    kilde_id        TEXT NOT NULL,                             -- id i kildesystemet
    vare_id         INTEGER NOT NULL REFERENCES vare(id),
    bestilt_maengde INTEGER NOT NULL,
    leveret_maengde INTEGER NOT NULL DEFAULT 0,
    leveringsdato   TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'åben' CHECK (status IN ('åben', 'afsluttet', 'annulleret')),
    prioritet       TEXT NOT NULL DEFAULT 'normal' CHECK (prioritet IN ('normal', 'høj')),
    saesonmaerke    INTEGER NOT NULL DEFAULT 0,
    UNIQUE (snapshot_id, ordre_id, vare_id)
);

-- Kendt registreringsafvigelse, fx en produktion der ikke er færdigmeldt. Ændrer ikke lageret automatisk.
CREATE TABLE produktionsstatus (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id          INTEGER NOT NULL REFERENCES snapshot(id),
    ordrelinje_id        INTEGER REFERENCES ordrelinje(id),
    status               TEXT NOT NULL,
    affected_item_ids    TEXT NOT NULL DEFAULT '',             -- kommasepareret liste af vare-id'er
    afklaring_paakraevet INTEGER NOT NULL DEFAULT 0,
    beskrivelse          TEXT
);

-- Fiktivt råvarebehov pr. produceret enhed. Ukendt behov er en manglende række, ikke nul.
CREATE TABLE ressourcebehov (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ordrelinje_id    INTEGER NOT NULL REFERENCES ordrelinje(id),
    raavare_id       INTEGER NOT NULL REFERENCES vare(id),
    maengde_pr_enhed INTEGER NOT NULL CHECK (maengde_pr_enhed > 0),
    UNIQUE (ordrelinje_id, raavare_id)
);

-- Standardkapacitet pr. dag. Manuelle ændringer gemmes som parametre på planversionen (F11).
CREATE TABLE kapacitetsdag (
    dato                TEXT PRIMARY KEY,
    disponible_minutter INTEGER NOT NULL CHECK (disponible_minutter BETWEEN 0 AND 1440)
);

-- D2 Planer og beslutninger
CREATE TABLE planversion (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id         INTEGER NOT NULL REFERENCES snapshot(id),
    uge_start           TEXT NOT NULL,
    versionsnummer      INTEGER NOT NULL,
    beregningstidspunkt TEXT NOT NULL,
    parametre           TEXT NOT NULL,                         -- JSON: valgte ordrer, kapacitet og prioritet
    manuelle_parametre  TEXT NOT NULL DEFAULT '[]',            -- JSON: hvilke parametre brugeren har ændret
    resultat            TEXT NOT NULL,                         -- JSON: hele planforslaget med forklaringer
    oprettet_at         TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'stale')),
    foraeldet_grund     TEXT,
    godkendt_at         TEXT,
    godkendt_af         TEXT,
    delvis              INTEGER NOT NULL DEFAULT 0,
    UNIQUE (uge_start, versionsnummer)
);

CREATE TABLE planlinje (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id             INTEGER NOT NULL REFERENCES planversion(id) ON DELETE CASCADE,
    ordrelinje_id       INTEGER NOT NULL REFERENCES ordrelinje(id),
    dato                TEXT NOT NULL,
    maengde             INTEGER NOT NULL CHECK (maengde > 0),
    minutter            INTEGER NOT NULL CHECK (minutter > 0),
    allocated_batch_refs TEXT NOT NULL DEFAULT '[]'            -- JSON: råvarebatches foreslået til linjen
);

-- Historik. request_id er unik, så et dobbeltklik på Godkend kun giver én hændelse (R08).
CREATE TABLE haendelse (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id    INTEGER REFERENCES planversion(id),
    type       TEXT NOT NULL,
    timestamp  TEXT NOT NULL,
    actor      TEXT,
    request_id TEXT UNIQUE,
    detaljer   TEXT
);
