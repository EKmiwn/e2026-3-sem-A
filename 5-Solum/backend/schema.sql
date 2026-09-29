-- Solum A/S – vidensdelings- og fejlfindingsapp (ER-diagram fra kravspecifikationens del 5.3)

CREATE TABLE employee (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    experience TEXT NOT NULL DEFAULT 'nyansat' CHECK (experience IN ('nyansat', 'erfaren')),
    role       TEXT NOT NULL DEFAULT 'maskinfører'   -- maskinfører, tekniker, driftsleder
);

CREATE TABLE machine (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL,
    nickname TEXT,                -- mange maskiner er i dag navngivet efter en medarbejder
    location TEXT NOT NULL,
    type     TEXT NOT NULL,
    icon     TEXT NOT NULL DEFAULT '⚙️'
);

CREATE TABLE competence (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id   INTEGER NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
    machine_id    INTEGER NOT NULL REFERENCES machine(id) ON DELETE CASCADE,
    level         TEXT NOT NULL CHECK (level IN ('under oplæring', 'godkendt', 'ekspert')),
    approved_date TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    UNIQUE (employee_id, machine_id)
);

CREATE TABLE article (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id   INTEGER NOT NULL REFERENCES machine(id),
    author_id    INTEGER NOT NULL REFERENCES employee(id),
    fault_type   TEXT NOT NULL,
    title        TEXT NOT NULL,
    steps        TEXT NOT NULL,           -- ét trin pr. linje
    tags         TEXT,                    -- symptomer og fejlkoder, kommasepareret
    level        TEXT NOT NULL DEFAULT 'grundlæggende' CHECK (level IN ('grundlæggende', 'dybdegående')),
    media_url    TEXT,
    created_date TEXT NOT NULL DEFAULT (date('now', 'localtime'))
);

-- Transaktionstabel: hver fejlsituation, hvilken guide der blev brugt, og om den løste problemet
CREATE TABLE fault_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id      INTEGER NOT NULL REFERENCES machine(id),
    employee_id     INTEGER NOT NULL REFERENCES employee(id),
    article_id      INTEGER REFERENCES article(id),
    symptom         TEXT NOT NULL,
    fault_type      TEXT,
    timestamp       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ÅBEN' CHECK (status IN ('ÅBEN', 'LØST', 'ULØST')),
    duration_minutes INTEGER,
    comment         TEXT
);
