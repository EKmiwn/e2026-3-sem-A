-- Learnify – elevevaluering af trivsel, læring og læringsmiljø (Læringsrum 2.0)
-- Opdateret efter "Ændringer til vores produkt": månedlig test, login med rolle, elevprofil, arbejdsstil og uddybende tekst

CREATE TABLE school (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE class (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL REFERENCES school(id),
    name      TEXT NOT NULL,
    grade     INTEGER NOT NULL
);

CREATE TABLE student (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id      INTEGER NOT NULL REFERENCES class(id),
    name          TEXT NOT NULL,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    age           INTEGER CHECK (age BETWEEN 5 AND 20)
);

-- Lærer (ser elever i sin klasse) eller virksomhed (Læringsrum 2.0 – ser filtrerede besvarelser)
CREATE TABLE teacher (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id     INTEGER NOT NULL REFERENCES school(id),
    class_id      INTEGER REFERENCES class(id),      -- NULL = alle klasser
    name          TEXT NOT NULL,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'lærer' CHECK (role IN ('lærer', 'virksomhed'))
);

CREATE TABLE question (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    text     TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('trivsel', 'læring', 'møbler', 'miljø', 'arbejdsstil')),
    style    TEXT CHECK (style IN ('visuel', 'auditiv', 'praktisk', 'tempo')),   -- kun for arbejdsstil
    active   INTEGER NOT NULL DEFAULT 1
);

-- Elev → Besvarelse → Spørgsmål → Resultat. Én besvarelse pr. elev pr. måned
CREATE TABLE response (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
    period       TEXT NOT NULL,          -- måned, fx 2026-09
    submitted_at TEXT NOT NULL,
    comment      TEXT,                   -- uddybende tekst til hele besvarelsen
    wishes       TEXT,                   -- hvilke forbedringer eleven ønsker
    classroom    TEXT,                   -- holdning til klasselokalet og indretningen
    UNIQUE (student_id, period)
);

CREATE TABLE answer (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL REFERENCES response(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES question(id),
    value       INTEGER NOT NULL CHECK (value BETWEEN 1 AND 5),
    note        TEXT                     -- elevens uddybning af netop dette svar
);
