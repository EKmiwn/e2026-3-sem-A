-- Learnify – elevevaluering af trivsel, læring og læringsmiljø (Læringsrum 2.0)

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
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL REFERENCES class(id),
    name     TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE teacher (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL REFERENCES school(id),
    name      TEXT NOT NULL,
    username  TEXT NOT NULL UNIQUE,
    role      TEXT NOT NULL DEFAULT 'lærer' CHECK (role IN ('lærer', 'administrator'))
);

CREATE TABLE question (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    text     TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('trivsel', 'læring', 'møbler', 'miljø')),
    active   INTEGER NOT NULL DEFAULT 1
);

-- Elev → Besvarelse → Spørgsmål → Resultat
CREATE TABLE response (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   INTEGER NOT NULL REFERENCES student(id) ON DELETE CASCADE,
    period       TEXT NOT NULL,          -- ISO-uge, fx 2026-W39
    submitted_at TEXT NOT NULL,
    comment      TEXT,
    UNIQUE (student_id, period)
);

CREATE TABLE answer (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL REFERENCES response(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES question(id),
    value       INTEGER NOT NULL CHECK (value BETWEEN 1 AND 5)
);
